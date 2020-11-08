"""
HTTP Verb 	                CRUD Entire Collection (e.g. /customers)                                                                Item (e.g. /customers/{id})
POST   Create               201 (Created), 'Location' header with link to /customers/{id} containing new ID. 	                    404 (Not Found), 409 (Conflict) if resource already exists..
GET    Read                 200 (OK), list of customers. Use pagination, sorting and filtering to navigate big lists. 	            200 (OK), single customer. 404 (Not Found), if ID not found or invalid.
PUT    Update/Replace       405 (Method Not Allowed), unless you want to update/replace every resource in the entire collection. 	200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
PATCH  Update/Modify        405 (Method Not Allowed), unless you want to modify the collection itself. 	                            200 (OK) or 204 (No Content). 404 (Not Found), if ID not found or invalid.
DELETE Delete               405 (Method Not Allowed), unless you want to delete the whole collection—not often desirable. 	        200 (OK). 404 (Not Found), if ID not found or invalid."""
import io
import logging
import os
from datetime import datetime
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .books.books_router import books
from .configuration import default_conf
from .dataclasses.Category import Category, CategoryTable
from .db.repository import Session
from .files.files_router import (import_books_csv_from_path,
                                 import_user_csv_from_path)
from .media.media_router import media
from .stats.statistics_router import stats
from .testdata.TestData import (create_categories_data,
                                create_overdue_borrowed_book,
                                create_users_test_data)
from .users.users_router import users
from .workflows.workflows_router import borrow_book, workflows

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)


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
    StaticFiles(directory="static/"),
    name="static"
)
bibler.include_router(
    workflows,
    prefix="/workflows"
)
bibler.include_router(
    books,
    prefix="/books"
)
bibler.include_router(
    users,
    prefix="/users"
)
bibler.include_router(
    media,
    prefix="/media"
)
bibler.include_router(
    stats,
    prefix="/stats"
)


@bibler.on_event("startup")
async def startup_event():
    if default_conf["production"] == "true":
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
    await import_books_csv_from_path("data/Bücherliste.csv")
    await import_books_csv_from_path("data/Bücherliste2.csv")
    await import_user_csv_from_path("data/Userliste.csv")

    await borrow_book(1, 1)
    await borrow_book(2, 2)
    await borrow_book(2, 3)
    await borrow_book(2, 4)
    await borrow_book(1, 5)


@bibler.get("/category", response_model=List[Category])
async def get_category():
    """returns a list of all existing categories"""
    session = Session()
    return [Category(**(i.__dict__)) for i in session.query(CategoryTable).all()]


@bibler.get("/")
async def index():
    return RedirectResponse("static/index.html")
