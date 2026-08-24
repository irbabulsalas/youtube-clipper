from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, User
from app.auth import verify_password, create_access_token, get_current_user, init_owner_account
from app.models import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password."""
    init_owner_account(db)
    
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah"
        )
    
    token = create_access_token(user.username, user.is_admin)
    
    return LoginResponse(
        access_token=token,
        is_admin=user.is_admin
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }


@router.get("/logout")
async def logout():
    """Logout (client should delete token)."""
    return {"message": "Logged out"}