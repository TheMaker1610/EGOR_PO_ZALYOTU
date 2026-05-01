import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password(password: str, username: str, role: str = "user") -> list[str]:
    """
    Возвращает список ошибок. Пустой список — пароль валиден.
    Пользователь: ≥6 символов, верхний+нижний регистр + цифра + спецсимвол.
    Администратор: ≥7 символов + те же требования.
    """
    errors = []
    min_len = 7 if role == "admin" else 6

    if len(password) < min_len:
        errors.append(f"Минимальная длина пароля: {min_len} символов")

    if not re.search(r"[A-Z]", password):
        errors.append("Пароль должен содержать заглавную букву")

    if not re.search(r"[a-z]", password):
        errors.append("Пароль должен содержать строчную букву")

    if not re.search(r"\d", password):
        errors.append("Пароль должен содержать цифру")

    if not re.search(r"[~@%&*$^!#]", password):
        errors.append("Пароль должен содержать спецсимвол (~@%&*$^!#)")

    if username and username.lower() in password.lower():
        errors.append("Пароль не должен содержать имя пользователя")

    return errors
