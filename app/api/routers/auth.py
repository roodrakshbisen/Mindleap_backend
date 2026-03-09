from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, User as UserSchema
from app.api import deps
from jose import jwt, JWTError

router = APIRouter()

@router.post("/signup", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create a new student or general user.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, getting an access token and refresh token for future requests.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(subject=user.id),
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh access token using a valid refresh token.
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found or inactive")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(subject=user.id),
        "token_type": "bearer",
    }
