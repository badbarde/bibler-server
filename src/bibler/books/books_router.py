import logging
from typing import Optional

import sqlalchemy
from fastapi import APIRouter

from ..dataclasses.Book import Book, BookTable
from ..dataclasses.BorrowingUser import BorrowingUserTable
from ..db.repository import Session
from ..responses.DeleteBookResponse import (DeleteBookResponseModel,
                                            DeleteBookResponseStatus)
from ..responses.PatchBookResponse import (PatchBookResponseModel,
                                           PatchBookResponseStatus)
from ..responses.PutBookResponse import (PutBookResponseModel,
                                         PutBookResponseStatus)

books = APIRouter()

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)


@books.get("/")
async def get_books(user_key: Optional[int] = None):
    """returns a list of all books or if `user_key` is specified all 
    books borrowed by the user with the key `user_key`"""
    session = Session()
    ret = session.query(BookTable)
    if user_key is not None:
        ret = ret.join(BorrowingUserTable).filter(
            BorrowingUserTable.user_key == user_key
        ).filter(
            BorrowingUserTable.return_date == None
        )
    return ret.all()


@books.get("/available")
async def get_available_books():
    """returns a list of all availabled books that are not borrowed by anyone"""
    session = Session()
    ret = session.query(BookTable).filter(
        ~BookTable.key.in_(
            session.query(BorrowingUserTable.book_key).filter(
                BorrowingUserTable.return_date == None
            ).subquery()
        )
    ).all()
    return ret


@books.put("/", response_model=PutBookResponseModel)
async def put_book(book: Book):
    """inserts a new `book` into the list of existing books"""
    try:
        session = Session()
        ret = session.add(BookTable(book))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PutBookResponseStatus.fail}
    return {"status": PutBookResponseStatus.success}


@books.patch("/", response_model=PatchBookResponseModel)
async def patch_book(book: Book):
    """Updates an existing `book` in the list of existing books"""
    try:
        session = Session()
        selected_book = session.query(BookTable.key == book.key)
        selected_book.title = book.title
        selected_book.author = book.author
        selected_book.category = book.category
        selected_book.shorthand = book.shorthand
        selected_book.number = book.number
        selected_book.publisher = book.publisher
        selected_book.isbn = book.isbn
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PatchBookResponseStatus.fail}
    return {"status": PatchBookResponseStatus.success}


@books.delete("/{book_key}", response_model=DeleteBookResponseModel)
async def patch_book(book_key: int):
    """Delete an existing book with the key `book_key` in the list of existing books"""
    try:
        session = Session()
        if session.query(BorrowingUserTable).filter(
            BorrowingUserTable.return_date != None,
            BorrowingUserTable.book_key == book_key
        ).first() is not None:
            return {"status": DeleteBookResponseStatus.borrowed}
        selected_book = session.query(
            BookTable
        ).filter(
            BookTable.key == book_key
        )
        session.delete(selected_book)
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": DeleteBookResponseStatus.fail}
    return {"status": DeleteBookResponseStatus.success}


@books.get("/borrowed/{book_key}", response_model=str)
async def is_borrowed(book_key: int):
    """check weather a book with the key `book_key` is currently borrowed by anyone"""
    session = Session()
    borrowed_state = session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key,
        BorrowingUserTable.return_date == None
    ).first()
    logger.info(f"borrowed state: {borrowed_state}")
    if borrowed_state is not None:
        return "True"
    return "False"
