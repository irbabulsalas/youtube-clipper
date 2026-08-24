from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db, User
from app.auth import get_password_hash, get_current_admin
from app.models import CreateUserRequest, UserInfo

router = APIRouter()


@router.get("/admin/users", response_model=List[UserInfo])
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return [UserInfo(username=u.username, is_admin=u.is_admin) for u in users]


@router.post("/admin/users", response_model=UserInfo)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah ada"
        )
    
    new_user = User(
        username=request.username,
        password_hash=get_password_hash(request.password),
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    
    return UserInfo(username=new_user.username, is_admin=new_user.is_admin)


@router.delete("/admin/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa menghapus akun sendiri"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa menghapus admin"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {username} berhasil dihapus"}