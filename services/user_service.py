from sqlalchemy.orm import Session

from auth.password_policy import hash_password, validate_password
from database.models import User
from services.audit_service import AuditService


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def create_user(self, username: str, password: str, role: str = "user",
                    admin_username: str = "system", ip: str = "127.0.0.1") -> User:
        if self.db.query(User).filter_by(username=username).first():
            raise ValueError(f"Пользователь '{username}' уже существует")
        errors = validate_password(password, username, role)
        if errors:
            raise ValueError("; ".join(errors))
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            must_change_password=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.audit.record("USER_CREATED", "user_management", username=admin_username,
                          ip_address=ip, details=f"Created user '{username}' role={role}")
        return user

    def list_users(self) -> list[User]:
        return self.db.query(User).all()

    def get_user(self, user_id: int) -> User | None:
        return self.db.query(User).filter_by(id=user_id).first()

    def update_user(self, user_id: int, is_active: bool | None = None,
                    role: str | None = None, admin_username: str = "system",
                    ip: str = "127.0.0.1") -> User:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("Пользователь не найден")
        changes = []
        if is_active is not None:
            user.is_active = is_active
            changes.append(f"is_active={is_active}")
        if role is not None:
            user.role = role
            changes.append(f"role={role}")
        self.db.commit()
        self.audit.record("USER_UPDATED", "user_management", username=admin_username,
                          ip_address=ip, details=f"User id={user_id}: {', '.join(changes)}")
        return user

    def reset_password(self, user_id: int, new_password: str,
                       admin_username: str = "system", ip: str = "127.0.0.1") -> User:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("Пользователь не найден")
        errors = validate_password(new_password, user.username, user.role)
        if errors:
            raise ValueError("; ".join(errors))
        user.password_hash = hash_password(new_password)
        user.must_change_password = True
        user.failed_attempts = 0
        user.locked_until = None
        self.db.commit()
        self.audit.record("PASSWORD_RESET", "user_management", username=admin_username,
                          ip_address=ip, details=f"Password reset for user id={user_id}")
        return user

    def unlock_user(self, user_id: int, admin_username: str = "system", ip: str = "127.0.0.1") -> User:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("Пользователь не найден")
        user.locked_until = None
        user.failed_attempts = 0
        self.db.commit()
        self.audit.record("USER_UNLOCKED", "user_management", username=admin_username,
                          ip_address=ip, details=f"User id={user_id} unlocked")
        return user
