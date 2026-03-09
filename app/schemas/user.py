from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_active: Optional[bool] = True
    role: UserRole = UserRole.STUDENT

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int

    class Config:
        from_attributes = True

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
