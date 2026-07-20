import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from app.db.session import SessionLocal
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.repositories.audit import AuditLogRepository
from app.core import metrics

logger = logging.getLogger("app.cleanup")


class CleanupService(ABC):
    @abstractmethod
    def start(self) -> None:
        """Start the background cleanup scheduler."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the background cleanup scheduler."""
        pass

    @abstractmethod
    def execute_job(self, job_name: str) -> Dict[str, Any]:
        """Manually trigger and execute a cleanup job by name."""
        pass


class APSchedulerCleanupService(CleanupService):
    def __init__(self, db_session_factory: sessionmaker = SessionLocal):
        self.db_session_factory = db_session_factory
        self.scheduler = BackgroundScheduler()
        self._register_jobs()

    def _register_jobs(self) -> None:
        # Register the 4 required cleanup jobs
        self.scheduler.add_job(
            func=self.cleanup_expired_verification_tokens,
            trigger="interval",
            minutes=60,
            id="cleanup_expired_verification_tokens",
            name="Expired Verification Tokens Cleanup"
        )
        self.scheduler.add_job(
            func=self.cleanup_expired_password_reset_tokens,
            trigger="interval",
            minutes=30,
            id="cleanup_expired_password_reset_tokens",
            name="Expired Password Reset Tokens Cleanup"
        )
        self.scheduler.add_job(
            func=self.cleanup_expired_sessions,
            trigger="interval",
            minutes=15,
            id="cleanup_expired_sessions",
            name="Expired Sessions Cleanup"
        )
        self.scheduler.add_job(
            func=self.cleanup_expired_audit_logs,
            trigger="interval",
            days=1,
            id="cleanup_expired_audit_logs",
            name="Expired Audit Logs Retention Cleanup"
        )

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler background cleanup service started.")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler background cleanup service shut down.")

    def execute_job(self, job_name: str) -> Dict[str, Any]:
        """Runs a job by name immediately, returning standard observability metadata."""
        job_map = {
            "cleanup_expired_verification_tokens": self.cleanup_expired_verification_tokens,
            "cleanup_expired_password_reset_tokens": self.cleanup_expired_password_reset_tokens,
            "cleanup_expired_sessions": self.cleanup_expired_sessions,
            "cleanup_expired_audit_logs": self.cleanup_expired_audit_logs
        }
        
        if job_name not in job_map:
            raise ValueError(f"Job '{job_name}' not registered in the cleanup service.")
            
        return job_map[job_name]()

    def _run_job_safely(self, job_name: str, task_callable) -> Dict[str, Any]:
        """Safely executes a database query task with telemetry and metrics collection."""
        start_time = datetime.utcnow()
        start_perf = time.time()
        status = "SUCCESS"
        deleted_count = 0
        failure_msg = None

        db = self.db_session_factory()
        try:
            # Delegate raw database queries to the target callable running on the db session
            deleted_count = task_callable(db)
        except Exception as e:
            status = "FAILURE"
            failure_msg = str(e)
            logger.error(f"Cleanup job '{job_name}' failed: {failure_msg}", exc_info=True)
        finally:
            db.close()

        duration = time.time() - start_perf
        next_run = None
        
        # Get next scheduled time if scheduler is running
        job = self.scheduler.get_job(job_name)
        if job:
            try:
                if job.next_run_time:
                    next_run = job.next_run_time.isoformat()
            except Exception:
                pass

        # Emit Prometheus metrics
        metrics.CLEANUP_RUNS_TOTAL.labels(job_name=job_name, status=status).inc()
        if status == "SUCCESS":
            metrics.CLEANUP_DELETED_RECORDS_TOTAL.labels(job_name=job_name).inc(deleted_count)
        metrics.CLEANUP_DURATION_SECONDS.labels(job_name=job_name).observe(duration)

        report = {
            "job_name": job_name,
            "start_time": start_time.isoformat() + "Z",
            "duration_seconds": round(duration, 4),
            "deleted_records": deleted_count,
            "failures": failure_msg,
            "next_scheduled_execution": next_run
        }

        logger.info(
            f"Cleanup job completed: {job_name} | Status: {status} | Deleted: {deleted_count} | Duration: {report['duration_seconds']}s",
            extra=report
        )
        return report

    # Clean Tasks Coordination
    def cleanup_expired_verification_tokens(self) -> Dict[str, Any]:
        def task(db):
            repo = UserRepository(db)
            return repo.clear_expired_verification_tokens(datetime.utcnow())
        return self._run_job_safely("cleanup_expired_verification_tokens", task)

    def cleanup_expired_password_reset_tokens(self) -> Dict[str, Any]:
        def task(db):
            repo = UserRepository(db)
            return repo.clear_expired_password_reset_tokens(datetime.utcnow())
        return self._run_job_safely("cleanup_expired_password_reset_tokens", task)

    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        def task(db):
            repo = SessionRepository(db)
            return repo.clear_expired_sessions(datetime.utcnow())
        return self._run_job_safely("cleanup_expired_sessions", task)

    def cleanup_expired_audit_logs(self) -> Dict[str, Any]:
        def task(db):
            repo = AuditLogRepository(db)
            # Retain logs for 90 days
            retention_date = datetime.utcnow() - timedelta(days=90)
            return repo.delete_old_logs(retention_date)
        return self._run_job_safely("cleanup_expired_audit_logs", task)
