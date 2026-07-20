import time
from app.core import metrics


class MetricsService:
    def handle_user_registered(self, event) -> None:
        payload = event.payload
        if payload.get("verification_token"):
            metrics.IAM_VERIFICATION_EMAILS_SENT.inc()

    def handle_email_verified(self, event) -> None:
        metrics.IAM_VERIFICATION_SUCCESS_TOTAL.inc()

    def handle_login_success(self, event) -> None:
        metrics.IAM_LOGINS_SUCCESS_TOTAL.inc()

    def handle_login_failed(self, event) -> None:
        metrics.IAM_LOGINS_FAILED_TOTAL.inc()

    def handle_account_locked(self, event) -> None:
        metrics.IAM_ACCOUNT_LOCKOUTS_TOTAL.inc()

    def handle_password_reset_requested(self, event) -> None:
        metrics.IAM_PASSWORD_RESET_REQUESTS.inc()

    def handle_password_reset_completed(self, event) -> None:
        metrics.IAM_PASSWORD_RESET_SUCCESS.inc()

    def handle_session_created(self, event) -> None:
        metrics.IAM_ACTIVE_SESSIONS.inc()

    def handle_session_revoked(self, event) -> None:
        metrics.IAM_ACTIVE_SESSIONS.dec()

    # Dynamic Latency recording helpers
    def record_login_latency(self, latency_seconds: float) -> None:
        metrics.IAM_LOGIN_LATENCY_SECONDS.observe(latency_seconds)

    def record_verification_latency(self, latency_seconds: float) -> None:
        metrics.IAM_VERIFICATION_LATENCY_SECONDS.observe(latency_seconds)
