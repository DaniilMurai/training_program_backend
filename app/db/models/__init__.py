from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .UserModel import User

__all__ = ['Base', 'User']
