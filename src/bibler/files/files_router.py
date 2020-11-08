
import csv
import datetime
import io
import logging

import numpy as np
import pandas as pd
from bs4.dammit import UnicodeDammit
from fastapi import APIRouter
from fastapi.datastructures import UploadFile
from fastapi.params import File
from starlette.responses import FileResponse, StreamingResponse

from ..dataclasses.Book import Book, BookTable
from ..dataclasses.User import User, UserTable
from ..db.repository import Session
from ..responses.ImportBooksResponse import ImportBooksResponseStatus

files = APIRouter()
logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)


@files.get("/books/export/csv/", response_class=FileResponse)
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
    today = datetime.now().strftime("%d.%m.%Y")
    return StreamingResponse(
        io.BytesIO(f.getvalue().encode("iso-8859-1")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=Benutzerliste {today}.csv"}
    )


@files.get("/users/export/csv/", response_class=FileResponse)
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
    today = datetime.now().strftime("%d.%m.%Y")
    return StreamingResponse(
        io.BytesIO(f.getvalue().encode("iso-8859-1")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=Benutzerliste {today}.csv", }
    )


async def import_user_csv_from_path(file):
    """import `Users`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(file).replace({np.nan: None})
    logger.info(f"importing csv with columns:  {df.columns}")
    logger.info(f"shape:  {df.shape}")
    df = df[
        (~df.firstname.isnull())
        & (~df.lastname.isnull())
        & (~df.classname.isnull())
    ]
    records = [UserTable(User(key=-1, **i))
               for i in df.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}


@files.post("/users/import/csv/")
async def import_user_csv(file: UploadFile = File(...)):
    """import `Users`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(
        io.StringIO(UnicodeDammit(file.file.read()).unicode_markup)
    ).replace({np.nan: None})
    logger.info(f"importing csv with columns:  {df.columns}")
    logger.info(f"shape:  {df.shape}")
    df = df[
        (~df.firstname.isnull())
        & (~df.lastname.isnull())
        & (~df.classname.isnull())
    ]
    records = [UserTable(User(key=-1, **i))
               for i in df.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return {"status": ImportBooksResponseStatus.success, "import_count": len(df.index)}


async def import_books_csv_from_path(file):
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


@files.post("/books/import/csv/")
async def import_books_csv(file: UploadFile = File(...)):
    """import `Book`s from csv file"""
    session = Session()
    df: pd.DataFrame = pd.read_csv(
        io.StringIO(UnicodeDammit(file.file.read()).unicode_markup)
    ).replace({np.nan: None})
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
