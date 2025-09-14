# backend/models.py
from sqlmodel import SQLModel, Field
from datetime import datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Photo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    filename: str
    caption: str | None = None
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
