from pydantic import BaseModel, Field, EmailStr

class UserSchema(BaseModel):
    username: str = Field(...)
    email: EmailStr = Field(...)
    password: str | None = None  # Optional for Google Auth users
    google_id: str | None = None
    avatar_url: str | None = None

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"