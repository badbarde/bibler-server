from datetime import date
from typing import Optional

import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.sql.schema import ForeignKey

from ..dataclasses.Book import BookTable
from ..dataclasses.User import UserTable
from .model import Base


class BorrowingUser(BaseModel):
    key: int
    user_key: int
    book_key: int
    start_date: date
    expiration_date: date
    return_date: Optional[date]


class BorrowingUserTable(Base):
    __tablename__ = "borrowing_users"
    key = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True)
    user_key = sqlalchemy.Column(sqlalchemy.Integer, ForeignKey(
        f"{UserTable.__tablename__}.key"))
    book_key = sqlalchemy.Column(sqlalchemy.Integer,  ForeignKey(
        f"{BookTable.__tablename__}.key"))
    start_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    expiration_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    return_date = sqlalchemy.Column(sqlalchemy.Date)

    def __init__(self, borrowing_user: BorrowingUser):
        self.user_key = borrowing_user.user_key
        self.book_key = borrowing_user.book_key
        self.start_date = borrowing_user.start_date
        self.expiration_date = borrowing_user.expiration_date
        self.return_date = borrowing_user.return_date

    def __repr__(self):
        return f"BorrowingUser<{self.key}, {self.book_key}, {self.user_key}, \
            {self.expiration_date}, {self.start_date}, {self.return_date}>"
