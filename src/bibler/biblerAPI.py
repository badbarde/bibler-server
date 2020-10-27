"""
HTTP Verb 	                CRUD Entire Collection (e.g. /customers)                                                                Item (e.g. /customers/{id})
POST   Create               201 (Created), 'Location' header with link to /customers/{id} containing new ID. 	                    404 (Not Found), 409 (Conflict) if resource already exists..
GET    Read                 200 (OK), list of customers. Use pagination, sorting and filtering to navigate big lists. 	            200 (OK), single customer. 404 (Not Found), if ID not found or invalid.
PUT    Update/Replace       405 (Method Not Allowed), unless you want to update/replace every resource in the entire collection. 	200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
PATCH  Update/Modify        405 (Method Not Allowed), unless you want to modify the collection itself. 	                            200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
DELETE Delete               405 (Method Not Allowed), unless you want to delete the whole collection—not often desirable. 	        200 (OK). 404 (Not Found), if ID not found or invalid."""
import configparser
import csv
import io
import logging
import os
from datetime import datetime
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import sqlalchemy
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic.types import confloat
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import functions
from starlette.responses import (FileResponse, RedirectResponse,
                                 StreamingResponse)

from .dataclasses.Book import Book, BookTable
from .dataclasses.BorrowingUser import BorrowingUser, BorrowingUserTable
from .dataclasses.Category import Category, CategoryTable
from .dataclasses.model import Base
from .dataclasses.User import User, UserIn, UserTable
from .responses.BorrowResponse import BorrowResponseModel, BorrowResponseStatus
from .responses.ExtendingResponse import (ExtendingResponseModel,
                                          ExtendingResponseStatus)
from .responses.ImportBooksResponse import ImportBooksResponseStatus
from .responses.PutBookResponse import (PutBookResponseModel,
                                        PutBookResponseStatus)
from .responses.PutUserResponse import (PutUserResponseModel,
                                        PutUserResponseStatus)
from .responses.ReturningResponse import (ReturningResponseModel,
                                          ReturningResponseStatus)
from .testdata.TestData import (create_books_test_data, create_categories_data,
                                create_overdue_borrowed_book,
                                create_users_test_data)

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)

config = configparser.ConfigParser()
config.read("bibler.ini")
default_conf = config["DEFAULT"]
logger.info(f"{[i for i in default_conf]}")
DB_PREFIX = "sqlite:///"
DB_URL = "data/bibler.db"
if os.path.exists(DB_URL) and config["DEFAULT"]["production"] == "false":
    logger.warn("Removing existing database")
    os.remove(DB_URL)
engine = sqlalchemy.create_engine(
    f"{DB_PREFIX}{DB_URL}",
    echo=True,
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# create console handler and set level to debug

save_path = "data/"
file_ending = ".json"
dateformat = "%d.%m.%Y"
origins = [
    "*",
]

bibler = FastAPI()
bibler.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bibler.mount(
    "/static",
    StaticFiles(directory="../bibler-client/build/"),
    name="static"
)


@bibler.on_event("startup")
async def startup_event():
    if config["DEFAULT"]["production"] == "true":
        return
    session = Session()
    create_users_test_data(session)
    session.commit()
    session = Session()
    create_categories_data(session)
    session.commit()
    session = Session()
    create_overdue_borrowed_book(session)
    session.commit()
    await __import_books_csv("data/Bücherliste.csv")
    await __import_books_csv("data/Bücherliste2.csv")

    await borrow_book(1, 1)
    await borrow_book(2, 2)
    await borrow_book(2, 3)
    await borrow_book(2, 4)
    await borrow_book(1, 5)


@bibler.get("/users")
async def get_users():
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


@bibler.put("/user", response_model=PutUserResponseModel)
async def put_user(user: UserIn):
    try:
        session = Session()
        session.add(UserTable(user))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PutUserResponseStatus.fail}
    return {"status": PutUserResponseStatus.success}


@bibler.get("/books")
async def get_books(user_key: Optional[int] = None):
    session = Session()
    ret = session.query(BookTable)
    if user_key is not None:
        ret = ret.join(BorrowingUserTable).filter(
            BorrowingUserTable.user_key == user_key
        ).filter(
            BorrowingUserTable.return_date == None
        )
    return ret.all()


@bibler.get("/books/available")
async def get_available_books():
    session = Session()
    ret = session.query(BookTable).filter(
        ~BookTable.key.in_(
            session.query(BorrowingUserTable.book_key).filter(
                BorrowingUserTable.return_date == None
            ).subquery()
        )
    ).all()
    return ret


@bibler.put("/book", response_model=PutBookResponseModel)
async def db_put_book(book: Book):
    try:
        session = Session()
        ret = session.add(BookTable(book))
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        return {"status": PutBookResponseStatus.fail}
    return {"status": PutBookResponseStatus.success}


@bibler.patch("/borrow/{user_key}/{book_key}", response_model=BorrowResponseModel)
async def borrow_book(user_key: int, book_key: int, duration: int = 3):
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


@bibler.patch("/return/{user_key}/{book_key}", response_model=ReturningResponseModel)
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


@bibler.patch("/extend/{user_key}/{book_key}", response_model=ExtendingResponseModel)
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


@bibler.get("/users/borrowing")
async def get_borrowing_users():
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


@bibler.get("/media/exists/{book_key}", response_model=str)
async def book_cover_existes(book_key: int):
    if os.path.exists(os.path.join("data/media", str(book_key) + ".png")):
        return "True"
    return "False"


@bibler.get("/media/{book_key}")
async def get_book_cover(book_key: int):
    path = os.path.join("data/media", str(book_key) + ".png")
    logger.info(f"loading {path}")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")


@bibler.get("/books/export/csv/", response_class=FileResponse)
async def export_books_csv():
    """export `Book`s to csv file"""
    session = Session()
    books = session.query(
        BookTable.title,
        BookTable.author,
        BookTable.publisher,
        BookTable.shorthand,
        BookTable.number,
        BookTable.category,
        BookTable.isbn,
    ).all()
    f = io.StringIO()
    csv_f = csv.writer(f)
    csv_f.writerow(
        [
            "title",
            "author",
            "publisher",
            "shorthand",
            "number",
            "category",
            "isbn",
        ]
    )
    csv_f.writerows(books)
    return StreamingResponse(io.StringIO(f.getvalue()), media_type="text/csv")


@bibler.get("/users/export/csv/", response_class=FileResponse)
async def export_books_csv():
    """export `Users`s to csv file"""
    session = Session()
    books = session.query(
        UserTable.firstname,
        UserTable.lastname,
        UserTable.classname,
    ).all()
    f = io.StringIO()
    csv_f = csv.writer(f)
    csv_f.writerow(
        [
            "firstname",
            "lastname",
            "classname",
        ]
    )
    csv_f.writerows(books)
    return StreamingResponse(io.StringIO(f.getvalue()), media_type="text/csv")


@bibler.post("/users/import/csv/")
async def import_user_csv(file: UploadFile = File(...)):
    """import `Users`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(file.file).replace({np.nan: None})
    logger.info(f"importing csv with columns:  {df.columns}")
    logger.info(f"shape:  {df.shape}")
    df = df[
        (~df.title.isnull())
        & (~df.author.isnull())
        & (~df.publisher.isnull())
        & (~df.number.isnull())
        & (~df.shorthand.isnull())
        & (~df.category.isnull())
    ].drop_duplicates(subset=["number"])
    logger.info(f"duplicate remove shape:  {df.shape}")
    records = [UserTable(User(key=-1, **i))
               for i in df.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}


async def __import_books_csv(file):
    """import `Book`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(file).replace({np.nan: None})
    logger.info(f"importing csv with columns:  {df.columns}")
    logger.info(f"shape:  {df.shape}")
    df = df[
        (~df.title.isnull())
        & (~df.author.isnull())
        & (~df.publisher.isnull())
        & (~df.number.isnull())
        & (~df.shorthand.isnull())
        & (~df.category.isnull())
    ].drop_duplicates(subset=["number"])
    logger.info(f"duplicate remove shape:  {df.shape}")
    records = [BookTable(Book(key=-1, **i))
               for i in df.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}


@bibler.post("/books/import/csv/")
async def import_books_csv(file: UploadFile = File(...)):
    """import `Book`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(file.file).replace({np.nan: None})
    logger.info(f"importing csv with columns:  {df.columns}")
    logger.info(f"shape:  {df.shape}")
    df = df[
        (~df.title.isnull())
        & (~df.author.isnull())
        & (~df.publisher.isnull())
        & (~df.number.isnull())
        & (~df.shorthand.isnull())
        & (~df.category.isnull())
    ].drop_duplicates(subset=["number"])
    logger.info(f"duplicate remove shape:  {df.shape}")
    records = [BookTable(Book(key=-1, **i))
               for i in df.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}


@bibler.get("/book/borrowed/{book_key}", response_model=str)
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


@bibler.get("/category", response_model=List[Category])
async def get_category():
    """"""
    session = Session()
    return [Category(**(i.__dict__)) for i in session.query(CategoryTable).all()]


@bibler.get("/stats/books/borrowed")
async def get_borrowed_count():
    """returns the number of currently borrowed books"""
    session = Session()
    count = session.query(functions.count(BorrowingUserTable.key)).filter(
        BorrowingUserTable.return_date == None
    ).all()
    return count[0][0]


@bibler.get("/stats/books/overdue")
async def get_overdue_count():
    """returns the number of books that are overdue"""
    session = Session()
    count = session.query(functions.count(BorrowingUserTable.key)).filter(
        BorrowingUserTable.expiration_date < datetime.now().date()
    ).all()
    return count[0][0]


@bibler.get("/stats/books/count")
async def get_books_count():
    """return number of books"""
    session = Session()
    count = session.query(functions.count(BookTable.key)).all()
    return count[0][0]


@bibler.get("/stats/users/count")
async def get_books_count():
    """return number of users"""
    session = Session()
    count = session.query(functions.count(UserTable.key)).all()
    return count[0][0]


@bibler.get("/")
async def index():
    return RedirectResponse("static/index.html")
