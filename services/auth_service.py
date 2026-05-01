from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from auth.jwt_handler import create_access_token
from auth.password_policy import hash_password, verify_password, validate_password
from config.settings import settings
from database.models import Session as DBSession, User
from services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def login(self, username: str, password: str, ip: str = "127.0.0.1") -> dict:
        user: User | None = self.db.query(User).filter_by(username=username).first()

        if not user:
            self.audit.record("LOGIN_FAILED", "auth", username=username, ip_address=ip,
                              details="User not found")
            raise ValueError("Неверное имя пользователя или пароль")

        # Check lock
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            self.audit.record("LOGIN_BLOCKED", "auth", username=username, ip_address=ip,
                              details=f"Account locked, {remaining} min remaining")
            raise ValueError(f"Аккаунт заблокирован. Попробуйте через {remaining} мин.")

        if not user.is_active:
            self.audit.record("LOGIN_FAILED", "auth", username=username, ip_address=ip,
                              details="Account inactive")
            raise ValueError("Аккаунт неактивен")

        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= settings.MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
                self.db.commit()
                self.audit.record("LOGIN_LOCKED", "auth", username=username, ip_address=ip,
                                  details=f"Locked after {user.failed_attempts} failed attempts")
                raise ValueError(f"Превышено количество попыток. Аккаунт заблокирован на {settings.LOCKOUT_MINUTES} мин.")
            self.db.commit()
            self.audit.record("LOGIN_FAILED", "auth", username=username, ip_address=ip,
                              details=f"Wrong password, attempt {user.failed_attempts}")
            raise ValueError(f"Неверный пароль. Осталось попыток: {settings.MAX_FAILED_ATTEMPTS - user.failed_attempts}")

        # Success
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        self.db.commit()

        token, jti, expires_at = create_access_token(user.id, user.username, user.role)
        sess = DBSession(
            user_id=user.id,
            jti=jti,
            issued_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        self.db.add(sess)
        self.db.commit()

        self.audit.record("LOGIN_SUCCESS", "auth", username=username, user_id=user.id,
                          ip_address=ip, details=f"role={user.role}")
        return {
            "access_token": token,
            "token_type": "bearer",
            "must_change_password": user.must_change_password,
            "role": user.role,
            "username": user.username,
        }

    def logout(self, jti: str, username: str, user_id: int, ip: str = "127.0.0.1"):
        sess = self.db.query(DBSession).filter_by(jti=jti).first()
        if sess:
            sess.revoked = True
            self.db.commit()
        self.audit.record("LOGOUT", "auth", username=username, user_id=user_id, ip_address=ip)

    def change_password(self, user: User, current_password: str, new_password: str, ip: str = "127.0.0.1"):
        if not verify_password(current_password, user.password_hash):
            self.audit.record("CHANGE_PASSWORD_FAILED", "auth", username=user.username,
                              user_id=user.id, ip_address=ip, details="Wrong current password")
            raise ValueError("Неверный текущий пароль")

        errors = validate_password(new_password, user.username, user.role)
        if errors:
            raise ValueError("; ".join(errors))

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        self.db.commit()
        self.audit.record("CHANGE_PASSWORD_SUCCESS", "auth", username=user.username,
                          user_id=user.id, ip_address=ip)
