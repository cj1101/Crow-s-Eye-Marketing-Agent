from pydantic import BaseModel, EmailStr
from typing import Optional

# --- Base Schemas ---
# Properties shared by all user-related schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# --- Schemas for Creation ---
# Properties received when creating a new user.
# It inherits from UserBase and adds the password.
class UserCreate(UserBase):
    password: str

# --- Schemas for Updating ---
# Properties that can be updated on an existing user.
class UserUpdate(UserBase):
    password: Optional[str] = None

# --- Schemas for API Responses ---
# Properties that are safe to be returned from the API.
# It does NOT include the password.
class User(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

# Schema for the user stored in the database, including the hashed password.
class UserInDB(User):
    hashed_password: str


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None 