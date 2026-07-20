import pytest
from datetime import datetime, timedelta
from app.db.models import User, UserSession, AuditLog
from app.services.cleanup import APSchedulerCleanupService
from app.core import metrics


def test_cleanup_scheduler_registration():
    cleanup_service = APSchedulerCleanupService()
    
    # Retrieve jobs from APScheduler
    jobs = cleanup_service.scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    
    # Assert the 4 required cleanup jobs are registered
    assert "cleanup_expired_verification_tokens" in job_ids
    assert "cleanup_expired_password_reset_tokens" in job_ids
    assert "cleanup_expired_sessions" in job_ids
    assert "cleanup_expired_audit_logs" in job_ids


def test_expired_verification_and_reset_tokens_cleanup(db_session):
    # Mock session close to prevent detaching instances during test transaction
    orig_close = db_session.close
    db_session.close = lambda: None

    try:
        def session_factory():
            return db_session
            
        cleanup_service = APSchedulerCleanupService(db_session_factory=session_factory)

        # 1. Create test users with expired/active tokens
        now = datetime.utcnow()
        
        # Expired verification token user
        user_exp_verify = User(
            email="exp_verify@test.com",
            hashed_password="...",
            verification_token_hash="hash1",
            verification_token_expiry=now - timedelta(seconds=1)
        )
        # Active verification token user
        user_act_verify = User(
            email="act_verify@test.com",
            hashed_password="...",
            verification_token_hash="hash2",
            verification_token_expiry=now + timedelta(hours=1)
        )
        # Expired reset token user
        user_exp_reset = User(
            email="exp_reset@test.com",
            hashed_password="...",
            password_reset_token_hash="hash3",
            password_reset_token_expiry=now - timedelta(seconds=1)
        )
        # Active reset token user
        user_act_reset = User(
            email="act_reset@test.com",
            hashed_password="...",
            password_reset_token_hash="hash4",
            password_reset_token_expiry=now + timedelta(hours=1)
        )

        db_session.add_all([user_exp_verify, user_act_verify, user_exp_reset, user_act_reset])
        db_session.commit()

        # 2. Run verification token cleanup
        before_runs = metrics.CLEANUP_RUNS_TOTAL.labels(job_name="cleanup_expired_verification_tokens", status="SUCCESS")._value.get()
        
        report = cleanup_service.execute_job("cleanup_expired_verification_tokens")
        
        assert report["deleted_records"] == 1
        assert report["failures"] is None
        assert metrics.CLEANUP_RUNS_TOTAL.labels(job_name="cleanup_expired_verification_tokens", status="SUCCESS")._value.get() == before_runs + 1

        # Verify expired verification token was cleared, active remained
        db_session.refresh(user_exp_verify)
        db_session.refresh(user_act_verify)
        assert user_exp_verify.verification_token_hash is None
        assert user_act_verify.verification_token_hash == "hash2"

        # 3. Run reset token cleanup
        report_reset = cleanup_service.execute_job("cleanup_expired_password_reset_tokens")
        assert report_reset["deleted_records"] == 1

        db_session.refresh(user_exp_reset)
        db_session.refresh(user_act_reset)
        assert user_exp_reset.password_reset_token_hash is None
        assert user_act_reset.password_reset_token_hash == "hash4"

        # 4. Idempotency check: running the job again should yield 0 deleted records
        report_idem = cleanup_service.execute_job("cleanup_expired_verification_tokens")
        assert report_idem["deleted_records"] == 0
    finally:
        db_session.close = orig_close


def test_expired_sessions_cleanup(db_session):
    orig_close = db_session.close
    db_session.close = lambda: None

    try:
        def session_factory():
            return db_session
            
        cleanup_service = APSchedulerCleanupService(db_session_factory=session_factory)
        
        now = datetime.utcnow()
        
        # Create an expired session and an active session
        session_exp = UserSession(
            refresh_token_jti="jti-exp",
            user_id=1,
            status="ACTIVE",
            expires_at=now - timedelta(minutes=1),
            ip_address="127.0.0.1",
            browser="Chrome",
            operating_system="Windows"
        )
        session_act = UserSession(
            refresh_token_jti="jti-act",
            user_id=1,
            status="ACTIVE",
            expires_at=now + timedelta(hours=1),
            ip_address="127.0.0.1",
            browser="Chrome",
            operating_system="Windows"
        )
        
        db_session.add_all([session_exp, session_act])
        db_session.commit()
        
        report = cleanup_service.execute_job("cleanup_expired_sessions")
        
        assert report["deleted_records"] >= 1  # Marked expired count
        
        db_session.refresh(session_exp)
        db_session.refresh(session_act)
        
        assert session_exp.status == "EXPIRED"
        assert session_act.status == "ACTIVE"
    finally:
        db_session.close = orig_close


def test_audit_logs_retention_cleanup(db_session):
    orig_close = db_session.close
    db_session.close = lambda: None

    try:
        def session_factory():
            return db_session
            
        cleanup_service = APSchedulerCleanupService(db_session_factory=session_factory)
        
        now = datetime.utcnow()
        
        # Create audit logs: one 95 days old (should delete), one 5 days old (should keep)
        old_log = AuditLog(
            user_id=None,
            event_id="evt-old",
            event_type="TEST_ACTION",
            ip_address="127.0.0.1",
            user_agent="Agent",
            timestamp=now - timedelta(days=95)
        )
        recent_log = AuditLog(
            user_id=None,
            event_id="evt-recent",
            event_type="TEST_ACTION",
            ip_address="127.0.0.1",
            user_agent="Agent",
            timestamp=now - timedelta(days=5)
        )
        
        db_session.add_all([old_log, recent_log])
        db_session.commit()
        
        # Capture IDs to avoid detached lazy-loading errors after delete
        old_log_id = old_log.id
        recent_log_id = recent_log.id
        
        report = cleanup_service.execute_job("cleanup_expired_audit_logs")
        
        # Assert old log was deleted
        assert report["deleted_records"] == 1
        
        remaining_logs = db_session.query(AuditLog).all()
        remaining_ids = [log.id for log in remaining_logs]
        
        assert old_log_id not in remaining_ids
        assert recent_log_id in remaining_ids
    finally:
        db_session.close = orig_close
