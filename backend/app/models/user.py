from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserSchema(BaseModel):
    username: str = Field(...)
    email: EmailStr = Field(...)
    password: str | None = None  # Optional for Google Auth users
    google_id: str | None = None
    avatar_url: Optional[str] = None
    role: str = "user"

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePasswordSchema(BaseModel):
    current_password: str = Field(...)  # No min_length check for current password (legacy support)
    new_password: str = Field(..., min_length=4)