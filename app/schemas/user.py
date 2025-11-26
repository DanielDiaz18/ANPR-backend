from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    pass

class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    name: str
    password: str
    phone_number: Optional[str] = ""
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.encode('utf-8')) > 72:
                raise ValueError('Password cannot be longer than 72 bytes')
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
        return v


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
