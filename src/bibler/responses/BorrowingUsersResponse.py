from typing import List

from pydantic import BaseModel

from ..dataclasses.Book import Book
from ..dataclasses.User import User


class BorrowUserResponset(User):
    """"""
    borrowed_books: List[Book]
