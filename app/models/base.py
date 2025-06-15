from sqlmodel import SQLModel
from sqlalchemy.orm import DeclarativeBase

class Base(SQLModel,DeclarativeBase):
    pass