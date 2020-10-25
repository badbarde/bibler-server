from typing import Optional

import sqlalchemy
from pydantic import BaseModel

from .model import Base


class User(BaseModel):
    key: int
    firstname: str
    lastname: str
    classname: Optional[str] = None


class UserIn(BaseModel):
    firstname: str
    lastname: str
    classname: Optional[str] = None


class UserWithBookCount(User):
    borrowed_books: int


class UserTable(Base):

    __tablename__ = "users"
    key = sqlalchemy.Column(sqlalchemy.Integer,
                            primary_key=True)
    firstname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    lastname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    classname = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, user: User):
        self.firstname = user.firstname
        self.lastname = user.lastname
        self.classname = user.classname

    def __repr__(self):
        return f"User<{self.key}, {self.firstname}, {self.lastname}, {self.classname}>"
