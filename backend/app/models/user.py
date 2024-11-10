from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
from ..utils.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    auth0_id = Column(String, unique=True)
    github_token = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
