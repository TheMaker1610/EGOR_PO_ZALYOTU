from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.jwt_handler import decode_token
from database.engine import get_db
from database.models import User
from schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from services.auth_service import AuthService
from ё.middleware import limiter, extract_headers

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    hdrs = extract_headers(request)
    svc = AuthService(db)
    try:
        result = svc.login(body.username, body.password, ip=ip, headers=hdrs)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return result


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    hdrs = extract_headers(request)
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    payload = decode_token(token)
    jti = payload.get("jti", "")
    AuthService(db).logout(jti, current_user.username, current_user.id, ip=ip, headers=hdrs)
    return {"detail": "Выход выполнен"}


@router.post("/change-password")
def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    hdrs = extract_headers(request)
    try:
        AuthService(db).change_password(
            current_user, body.current_password, body.new_password, ip=ip, headers=hdrs)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "Пароль успешно изменён"}
