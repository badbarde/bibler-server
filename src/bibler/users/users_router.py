import logging
from typing import List

import sqlalchemy
from fastapi import APIRouter
from sqlalchemy.sql import functions

from ..dataclasses.Book import BookTable
from ..dataclasses.BorrowingUser import BorrowingUserTable
from ..dataclasses.User import User, UserIn, UserTable
from ..db.repository import Session
from ..responses.BorrowingUsersResponse import BorrowingUserRecord
from ..responses.DeleteUserResponse import (DeleteUserResponseModel,
                                            DeleteUserResponseStatus)
from ..responses.PatchUserResponse import (PatchUserResponseModel,
                                           PatchUserResponseStatus)
from ..responses.PutUserResponse import (PutUserResponseModel,
                                         PutUserResponseStatus)

users = APIRouter()

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)


@users.get("/")
async def get_users():
    """returns a list of users and the amount of books that they have borrowed"""
    session: Session = Session()
    count_table = session.query(
        BorrowingUserTable.user_key,
        functions.count(
            BorrowingUserTable.key).label("borrowed_books")
    ).filter(
        BorrowingUserTable.return_date == None
    ).group_by(
        BorrowingUserTable.user_key
    ).subquery()
    ret = session.query(
        UserTable,
        functions.coalesce(
            count_table.c.borrowed_books, 0
        ).label("borrowed_books")
    ).outerjoin(
        count_table,
        UserTable.key == count_table.c.user_key
    ).order_by(
        UserTable.lastname,
        UserTable.firstname,
        UserTable.classname
    ).all()
    logger.info(ret)
    return ret


@users.put("/", response_model=PutUserResponseModel)
async def put_user(user: UserIn):
    """inserts a new user `user` into the list of existing users"""
    try:
        session = Session()
        session.add(UserTable(user))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PutUserResponseStatus.fail}
    return {"status": PutUserResponseStatus.success}


@users.patch("/user", response_model=PatchUserResponseModel)
async def patch_user(user: User):
    """update a `user` in the list of users"""
    try:
        session = Session()
        selected_user = session.query(
            UserTable
        ).filter(
            UserTable.key == user.key
        ).first()
        selected_user.firstname = user.firstname
        selected_user.lastname = user.lastname
        selected_user.classname = user.classname
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PatchUserResponseStatus.fail}
    return {"status": PatchUserResponseStatus.success}


@users.delete("/user/{user_key}", response_model=DeleteUserResponseModel)
async def delete_user(user_key: int):
    """delete a `user` in the list of users"""
    try:
        session = Session()
        if session.query(BorrowingUserTable).filter(
            BorrowingUserTable.return_date != None,
            BorrowingUserTable.user_key == user_key
        ).first() is not None:
            return {"status": DeleteUserResponseStatus.borrowing}
        selected_user = session.query(UserTable).filter(
            UserTable.key == user_key).first()
        session.delete(selected_user)
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": DeleteUserResponseStatus.fail}
    return {"status": DeleteUserResponseStatus.success}


@users.get("/borrowing", response_model=List[BorrowingUserRecord])
async def get_borrowing_users():
    """returns a list of all Books together with the user that borrows it"""
    session = Session()
    ret = session.query(
        BorrowingUserTable.key,
        BorrowingUserTable.book_key,
        BorrowingUserTable.user_key,
        BorrowingUserTable.return_date,
        BorrowingUserTable.expiration_date,
        BorrowingUserTable.start_date,
        BookTable.title,
        BookTable.author,
        BookTable.category,
        BookTable.isbn,
        BookTable.number,
        BookTable.shorthand,
        UserTable.firstname,
        UserTable.lastname,
        UserTable.classname,
    ).join(
        BookTable
    ).join(
        UserTable
    ).filter(
        BorrowingUserTable.return_date == None
    ).order_by(BorrowingUserTable.expiration_date).all()
    return [
        {
            "key": i[0],
            "book_key": i[1],
            "user_key": i[2],
            "return_date": i[3],
            "expiration_date": i[4],
            "start_date": i[5],
            "title": i[6],
            "author": i[7],
            "category": i[8],
            "isbn": i[9],
            "number": i[10],
            "shorthand": i[11],
            "firstname": i[12],
            "lastname": i[13],
            "classname": i[14],
        }
        for i in ret
    ]
