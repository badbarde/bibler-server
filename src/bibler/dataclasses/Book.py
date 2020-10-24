from typing import Optional

import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.sql.schema import ForeignKey

from .Category import CategoryTable
from .Media import Media
from .model import Base


class Book(BaseModel):
    key: int
    title: str
    author: str
    publisher: str
    number: str
    shorthand: str
    category: str
    isbn: Optional[str] = None
    media: Optional[Media] = None


class BookTable(Base):
    __tablename__ = "books"
    key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    category = sqlalchemy.Column(sqlalchemy.String,
                                 ForeignKey(f"{CategoryTable.__tablename__}.name"))
    author = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    publisher = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    number = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=True)
    shorthand = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    isbn = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, book: Book):
        self.title = book.title
        self.author = book.author
        self.publisher = book.publisher
        self.number = book.number
        self.shorthand = book.shorthand
        self.category = book.category
        self.isbn = book.isbn

    def __repr__(self):
        return f"Book<{self.key}, {self.title}, {self.author}, {self.publisher}, \
            {self.category}, {self.number}, {self.shorthand}, {self.shorthand}>"
