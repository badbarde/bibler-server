
import logging
from datetime import datetime
from typing import Any, List, Optional

from dateutil.relativedelta import relativedelta
from fastapi.routing import APIRouter

from ..dataclasses.Book import BookTable
from ..dataclasses.BorrowingUser import BorrowingUser, BorrowingUserTable
from ..dataclasses.User import UserTable
from ..db.repository import Session
from ..responses.BorrowResponse import (BorrowResponseModel,
                                        BorrowResponseStatus)
from ..responses.ExtendingResponse import (ExtendingResponseModel,
                                           ExtendingResponseStatus)
from ..responses.ReturningResponse import (ReturningResponseModel,
                                           ReturningResponseStatus)

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)
workflows = APIRouter()


@workflows.patch("/borrow/{user_key}/{book_key}", response_model=BorrowResponseModel)
async def borrow_book(user_key: int, book_key: int, duration: int = 3):
    """borrow a book with the key `book_key` for the user `user_key`"""
    session = Session()
    if session.query(UserTable).filter(UserTable.key == user_key).first() is None:
        logger.error(f"User with key:{user_key} does not exist")
        return {"status": BorrowResponseStatus.user_unknown}
    if session.query(BookTable).filter(BookTable.key == book_key).first() is None:
        logger.error(f"Book with key:{book_key} does not exist")
        return {"status": BorrowResponseStatus.book_unknown}
    if session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key
    ).filter(
            BorrowingUserTable.return_date == None
    ).first() is not None:
        logger.error(f"Book is already borrowed")
        return {"status": BorrowResponseStatus.already_borrowed}
    current_date = datetime.now()
    expiration_date = (
        current_date + relativedelta(weeks=duration)).date()
    session.add(BorrowingUserTable(BorrowingUser(
        key=-1,
        book_key=book_key,
        user_key=user_key,
        start_date=current_date.date(),
        expiration_date=expiration_date,
        return_date=None
    )))
    logger.info(
        f"user: {user_key} is borrowing {book_key} at {current_date} until {expiration_date}")
    session.commit()
    return {
        "status": BorrowResponseStatus.success,
        "return_date": expiration_date
    }


@workflows.patch("/return/{user_key}/{book_key}", response_model=ReturningResponseModel)
async def return_book(user_key: int, book_key: int):
    """return a book with the key `book_key` as the user with the key `user_key`"""
    session = Session()
    if session.query(UserTable).filter(UserTable.key == user_key).first() is None:
        logger.error(f"User with key:{user_key} does not exist")
        return {"status": ReturningResponseStatus.user_unknown}
    if session.query(BookTable).filter(BookTable.key == book_key).first() is None:
        logger.error(f"Book with key:{book_key} does not exist")
        return {"status": ReturningResponseStatus.book_unknown}
    if session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key
    ).filter(
        BorrowingUserTable.return_date == None
    ).first() is None:
        logger.error(f"Book is not lend to anyone")
        return {"status": ReturningResponseStatus.book_not_borrowed}
    return_record = session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key
    ).filter(
        BorrowingUserTable.user_key == user_key
    ).filter(
        BorrowingUserTable.return_date == None
    ).first()
    if return_record is None:
        logger.error(
            f"Book with id '{book_key}' is not lend to user with id '{user_key}''")
        return {"status": ReturningResponseStatus.book_not_borrowed}
    return_record.return_date = datetime.now().date()
    session.commit()
    return {"status": ReturningResponseStatus.success}


@workflows.patch("/extend/{user_key}/{book_key}", response_model=ExtendingResponseModel)
async def extend_borrow_period(user_key: int, book_key: int, duration: int = 1):
    """extend the borrowing period for a a book with the key `book_key` for the user with the key `user_key`"""
    session = Session()
    if session.query(UserTable).filter(UserTable.key == user_key).first() is None:
        logger.error(f"User with key:{user_key} does not exist")
        return {"status": ExtendingResponseStatus.user_unknown}
    if session.query(BookTable).filter(BookTable.key == book_key).first() is None:
        logger.error(f"Book with key:{book_key} does not exist")
        return {"status": ExtendingResponseStatus.book_unknown}
    if session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key
    ).filter(
        BorrowingUserTable.return_date == None
    ).first() is None:
        logger.error(f"Book is not lend to anyone")
        return {"status": ExtendingResponseStatus.book_not_borrowed}
    extend_record = session.query(BorrowingUserTable).filter(
        BorrowingUserTable.book_key == book_key
    ).filter(
        BorrowingUserTable.user_key == user_key
    ).filter(
        BorrowingUserTable.return_date == None
    ).first()
    if extend_record is None:
        logger.error(
            f"Book with id '{book_key}' is not lend to user with id '{user_key}'")
        return {"status": ExtendingResponseStatus.book_not_borrowed}
    new_expiration_date = (extend_record.expiration_date +
                           relativedelta(weeks=duration))
    if (extend_record.start_date + relativedelta(weeks=5)) < new_expiration_date:
        logger.info(f"Book can't be extended to loger than 5 weeks")
        return {"status": ExtendingResponseStatus.limit_exceeded}
    extend_record.expiration_date = new_expiration_date
    session.commit()
    return {"status": ExtendingResponseStatus.success, "return_date": new_expiration_date}
