from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.dependencies import require_admin
from database.engine import get_db
from database.models import User
from schemas.user import UserCreate, UserRead, UserUpdate
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).list_users()


@router.post("/", response_model=UserRead)
async def create_user(
    request: Request,
    body: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    try:
        return UserService(db).create_user(body.username, body.password, body.role,
                                           admin_username=admin.username, ip=ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    request: Request,
    body: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    try:
        return UserService(db).update_user(
            user_id, is_active=body.is_active, role=body.role,
            admin_username=admin.username, ip=ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    request: Request,
    body: dict,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    new_password = body.get("new_password", "")
    try:
        UserService(db).reset_password(user_id, new_password, admin_username=admin.username, ip=ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "Пароль сброшен"}


@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    try:
        UserService(db).unlock_user(user_id, admin_username=admin.username, ip=ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "Пользователь разблокирован"}
