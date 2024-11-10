from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from ..utils.db import Base

class UserRepository(Base):
    __tablename__ = 'user_repositories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    repo_id = Column(Integer)
    repo_name = Column(String)
    __table_args__ = (UniqueConstraint('user_id', 'repo_id', name='_user_repo_uc'),)

    user = relationship('User', back_populates='repositories')
