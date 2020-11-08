

import datetime
import logging

from fastapi import APIRouter
from sqlalchemy.sql import functions

from ..dataclasses.Book import BookTable
from ..dataclasses.BorrowingUser import BorrowingUserTable
from ..dataclasses.User import UserTable
from ..db.repository import Session

stats = APIRouter()

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)


@stats.get("/stats/books/borrowed")
async def get_borrowed_count():
    """returns the number of currently borrowed books"""
    session = Session()
    count = session.query(functions.count(BorrowingUserTable.key)).filter(
        BorrowingUserTable.return_date == None
    ).all()
    return count[0][0]


@stats.get("/stats/books/overdue")
async def get_overdue_count():
    """returns the number of books that are overdue"""
    session = Session()
    count = session.query(functions.count(BorrowingUserTable.key)).filter(
        BorrowingUserTable.expiration_date < datetime.now().date()
    ).all()
    return count[0][0]


@stats.get("/stats/books/count")
async def get_books_count():
    """return number of books"""
    session = Session()
    count = session.query(functions.count(BookTable.key)).all()
    return count[0][0]


@stats.get("/stats/users/count")
async def get_users_count():
    """return number of users"""
    session = Session()
    count = session.query(functions.count(UserTable.key)).all()
    return count[0][0]
