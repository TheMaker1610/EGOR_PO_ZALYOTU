from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from database.models import Base, User
from auth.password_policy import hash_password

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_admin()


def _seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(username="admin").first()
        if not existing:
            admin = User(
                username="admin",
                password_hash=hash_password("Admin@123"),
                role="admin",
                is_active=True,
                must_change_password=False,
            )
            db.add(admin)
            # Создаём тестового пользователя
            user = User(
                username="user1",
                password_hash=hash_password("User@12"),
                role="user",
                is_active=True,
                must_change_password=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
