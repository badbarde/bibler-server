"""
HTTP Verb 	                CRUD Entire Collection (e.g. /customers)                                                                Item (e.g. /customers/{id})
POST   Create               201 (Created), 'Location' header with link to /customers/{id} containing new ID. 	                    404 (Not Found), 409 (Conflict) if resource already exists..
GET    Read                 200 (OK), list of customers. Use pagination, sorting and filtering to navigate big lists. 	            200 (OK), single customer. 404 (Not Found), if ID not found or invalid.
PUT    Update/Replace       405 (Method Not Allowed), unless you want to update/replace every resource in the entire collection. 	200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
PATCH  Update/Modify        405 (Method Not Allowed), unless you want to modify the collection itself. 	                            200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
DELETE Delete               405 (Method Not Allowed), unless you want to delete the whole collection—not often desirable. 	        200 (OK). 404 (Not Found), if ID not found or invalid."""
import io
import logging
import math
import os
import pprint as pp
from datetime import datetime
from typing import Any, List, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Query
from pandas.errors import EmptyDataError
from pydantic import BaseModel
from sqlalchemy import create_engine
from starlette.responses import StreamingResponse

from .dataclasses.Book import Book
from .dataclasses.BorrowingUser import BorrowingUser
from .dataclasses.User import User
from .responses.BorrowResponse import BorrowResponseModel, BorrowResponseStatus
from .responses.ImportBooksResponse import ImportBooksResponseStatus
from .responses.PutBookResponse import (PutBookResponseModel,
                                        PutBookResponseStatus)
from .responses.PutUserResponse import (PutUserResponseModel,
                                        PutUserResponseStatus)
from .responses.ReturningResponse import (ReturningResponseModel,
                                          ReturningResponseStatus)
from .testdata.TestData import create_books_test_data, create_users_test_data

engine = create_engine('sqlite:///data/bibler.db', echo=True)

logger = logging.getLogger("BiblerAPI")
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
# formatter = logging.Formatter(
# '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
# ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

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


@bibler.on_event("startup")
async def startup_event():
    create_users_test_data(save_path)
    create_books_test_data(save_path)
    with open("data/Bücherliste.csv") as f:
        await __import_csv_file(f)
    with open("data/Bücherliste2.csv") as f:
        await __import_csv_file(f)


def __load_data_class(data_class):
    """load a Dataframe of a Dataclass from disc"""
    path = os.path.join(save_path, data_class.__name__ + file_ending)
    if os.path.exists(path):
        try:
            logger.info(f"loading [{data_class.__name__}] from '{path}'")
            df = pd.read_json(path)
            return df
        except EmptyDataError as e:
            logger.error(f"{data_class.__name__} data is empty '{path}': {e}")
        except ValueError as e:
            logger.error(f"{data_class.__name__} data is empty '{path}': {e}")
    logger.error(f"cant load {data_class.__name__} from '{path}'")
    df = pd.DataFrame(columns=data_class.__fields__)
    df.to_sql(data_class.__name__, con=engine, if_exists="replace")
    df.to_json(path)
    return df


async def __put_data(data: BaseModel):
    """save data of a given base class to a dataframe and then to disc
    TODO: smarter save mechanism for nested stuctures
    """
    df = __load_data_class(data.__class__)
    if all([v for k, v in data.__dict__.items() if k != "key"]):
        return 0
    logger.info(f"add {data.__class__.__name__}: {await __data_class_to_dict(data)}")
    insert = pd.json_normalize(await __data_class_to_dict(data))
    if "key" in insert.keys():
        insert["key"] = df.key.max() + 1
    logger.info(f"put data {insert}")
    new_df = df.append(insert, ignore_index=True)
    new_df.to_sql(data.__class__.__name__, con=engine, if_exists="replace")
    new_df.to_json(os.path.join(
        save_path, data.__class__.__name__ + file_ending))
    return 1


async def __data_class_to_dict(data: BaseModel):
    """"""
    ret = {}
    for k, v in data.__dict__.items():
        val = v
        if isinstance(v, BaseModel):
            val = await __data_class_to_dict(v)
        if isinstance(v, list):
            val = [await __data_class_to_dict(i) for i in v]
        ret[k] = val
    return ret


@bibler.get("/users")
async def get_users():
    """get users"""
    users = __load_data_class(User)
    borrowing_user = __load_data_class(BorrowingUser)
    user_book_count = borrowing_user.groupby(
        ["user_key"]).count()
    # TODO: add sum of borrowed books to user output
    logger.info(f"group by user: {user_book_count}")
    if users is not None:
        return users.fillna("").to_dict(orient="records")


@bibler.put("/user", response_model=PutUserResponseModel)
async def put_user(user: User):
    if (await __put_data(user)) == 0:
        return {"status": PutUserResponseStatus.fail}
    return {"status": PutUserResponseStatus.success}


@bibler.get("/books")
async def get_books(user_key: Optional[int] = None):
    """get books"""
    books = __load_data_class(Book)
    if user_key is not None:
        logger.info(f"filtering books for user: {user_key}")
        borrowing_user = __load_data_class(BorrowingUser)
        books = books[
            books.key.isin(
                borrowing_user[(borrowing_user.user_key == user_key)
                               & (borrowing_user.return_date.isna())].book_key)
        ]
        return books.fillna("").to_dict(orient="records")
    if books is not None:
        return books.fillna("").to_dict(orient="records")


@bibler.put("/book", response_model=PutBookResponseModel)
async def put_book(book: Book):
    if(await __put_data(book)) == 0:
        return {"status": PutBookResponseStatus.fail}
    return {"status": PutBookResponseStatus.success}


@bibler.patch("/borrow/{user_key}/{book_key}", response_model=BorrowResponseModel)
async def borrow_book(user_key: int, book_key: int, duration: int = 3):
    """borrow a book with the key `book_key` to the user with the key `user_key`"""
    users = __load_data_class(User)
    books = __load_data_class(Book)
    borrowing_user = __load_data_class(BorrowingUser)
    logger.info(f"BORROWING USERS:\n {borrowing_user.head()}")
    if user_key not in users.key.values:
        logger.error(f"User with key:{user_key} does not exist")
        return {"status": BorrowResponseStatus.user_unknown}
    if book_key not in books.key.values:
        logger.error(f"Book with key:{book_key} does not exist")
        return {"status": BorrowResponseStatus.book_unknown}
    if book_key in borrowing_user[borrowing_user.return_date.isnull()].book_key.values:
        logger.error(f"Book is already borrowed")
        return {"status": BorrowResponseStatus.already_borrowed}
    max_key = 0 if math.isnan(
        borrowing_user.key.max()
    ) else borrowing_user.key.max()
    new_record = BorrowingUser(
        key=max_key + 1,
        user_key=user_key,
        book_key=book_key,
        start_date=datetime.now().date().strftime(dateformat),
        expiration_date=(
            datetime.now() + relativedelta(weeks=duration)).date().strftime(dateformat),
        return_date=None
    )
    logger.info(f"new record: {new_record.__dict__}")

    borrowing_user = borrowing_user.append(
        await __data_class_to_dict(new_record), ignore_index=True)
    borrowing_user.to_json(os.path.join(
        save_path,  BorrowingUser.__name__ + file_ending))
    logger.info(borrowing_user.head())
    return {
        "status": BorrowResponseStatus.success,
        "return_date": new_record.expiration_date
    }


@bibler.patch("/return/{user_key}/{book_key}", response_model=ReturningResponseModel)
async def return_book(user_key: int, book_key: int):
    """return a book with the key `book_key` borrowed by the user with the key `user_key`"""
    users = __load_data_class(User)
    books = __load_data_class(Book)
    borrowing_user = __load_data_class(BorrowingUser)
    if user_key not in users.key.values:
        logger.error(f"User with key:{user_key} does not exist")
        return {"status": ReturningResponseStatus.user_unknown}
    if book_key not in books.key.values:
        logger.error(f"Book with key:{book_key} does not exist")
        return {"status": ReturningResponseStatus.book_unknown}
    if book_key not in borrowing_user.book_key.values:
        logger.error(f"Book is not lend to anyone")
        return {"status": ReturningResponseStatus.book_not_borrowed}
    if book_key not in borrowing_user[(borrowing_user.user_key == user_key) & (borrowing_user.return_date.isnull())].book_key.values:
        logger.error(
            f"Book with id '{book_key}' is not lend to user with id '{user_key}''")
        return {"status": ReturningResponseStatus.book_not_borrowed}
    retrun_date = datetime.now().date().strftime(dateformat)
    borrowing_user.at[
        (borrowing_user.user_key == user_key) &
        (borrowing_user.book_key == book_key), "return_date"
    ] = retrun_date
    logger.info(
        f"User with key {user_key} sucessfully returned the book with the key {book_key}")
    borrowing_user.to_json(os.path.join(
        save_path, BorrowingUser.__name__ + file_ending))
    return {"status": ReturningResponseStatus.success}


@bibler.get("/borrow/users")
async def get_borrowing_users():
    """returns all users that are currenty borrowing a book and the books they are borrowing"""
    users = __load_data_class(User)
    books = __load_data_class(Book)
    borrowing_user = __load_data_class(BorrowingUser)
    ret = borrowing_user.set_index("user_key").join(
        users.set_index("key")
    ).set_index("book_key").join(books.set_index("key"))
    #user_recs = users.to_dict(orient="records")
    #borrowing_user_recs = []
    # for user in user_recs:
    #    books_keys = borrowing_user[borrowing_user.user_key == user.get(
    #        "key")].book_key
    #    borrowed_books = books[books.key.isin(
    #        books_keys)]
    #    user["borrowed_books"] = borrowed_books.to_dict(orient="records")
    #    borrowing_user_recs += [user]
    # return borrowing_user_recs
    return ret.fillna("").to_dict(orient="records")


@bibler.post("/files/")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}


@bibler.get("/media/{book_key}")
async def create_file(book_key: int):
    path = os.path.join("data/media", str(book_key) + ".png")
    logger.info(f"loading {path}")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")


@bibler.post("/import/csv/")
async def import_csv(file: UploadFile = File(...)):
    """import `Book`s from csv file"""
    return await __import_csv_file(file.file)


async def __import_csv_file(file):
    """private import for csv files"""
    df: pd.DataFrame = pd.read_csv(file)
    logger.info(f"loadled file: {df.head()}")
    books = __load_data_class(Book).dropna(how="all")
    logger.info(f"columns of new data: {set(df.columns)}")
    logger.info(f"columns of existing data: {set(books.columns)}")
    if set(df.columns).issubset(set(books.columns)):
        maxkey = books.key.max()
        df["key"] = pd.Series(range(maxkey + 1, maxkey + len(df.index) + 1))
        books = pd.concat([books, df], ignore_index=True)
        books.to_sql(Book.__name__, con=engine, if_exists="replace")
        books.to_json(
            os.path.join(save_path, Book.__name__ + file_ending),
            index=True,
        )
        return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}
    return {"status": ImportBooksResponseStatus.fail}


def __record_exists(base_model: BaseModel):
    """check if a record is already in a dataframe"""
    data = __load_data_class(base_model.__class__)
    for col, val in __data_class_to_dict(base_model):
        if val not in data[col]:
            return False
    else:
        return True
