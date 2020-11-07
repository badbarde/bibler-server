from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from ..dataclasses.Book import Book
from ..dataclasses.User import User


class BorrowingUserRecord(BaseModel):
    """"""
    key: int
    book_key: int
    user_key: int
    return_date: Optional[date]
    expiration_date: date
    start_date: date
    title: str
    author: str
    category: str
    isbn: Optional[str]
    number: int
    shorthand: str
    firstname: str
    lastname: str
    classname: str
