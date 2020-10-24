
import json
import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import session

from ..dataclasses.Book import Book, BookTable
from ..dataclasses.BorrowingUser import BorrowingUser, BorrowingUserTable
from ..dataclasses.Category import Category, CategoryTable
from ..dataclasses.User import User, UserTable


def create_books_test_data(session):
    data = [
        {
            "key": 0,
            "title": "Sabriel",
            "author": "Garth Nix",
            "publisher": "Carlsen",
            "number": 1,
            "shorthand": "Car",
            "category": "Fantasy",
            "isbn": "3-551-58128-2",
        },
        {
            "key": 5,
            "title": "Lirael",
            "author": "Garth Nix",
            "publisher": "Carlsen",
            "number": 5,
            "shorthand": "Car",
            "category": "Fantasy",
            "isbn": "3-551-58129-2",
        },
        {
            "key": 6,
            "title": "Abhorsen",
            "author": "Garth Nix",
            "publisher": "Carlsen",
            "number": 6,
            "shorthand": "Car",
            "category": "Fantasy",
            "isbn": "3-551-58130-2",
        },
        {
            "key": 1,
            "title": "Die granulare Gesellschaft",
            "author": "Christoph Kucklick",
            "publisher": "Ullstein",
            "number": 2,
            "shorthand": "Ull",
            "category": "Sachbuch",
            "isbn": "978-3-548-37625-7",
        },
        {
            "key": 2,
            "title": "Bartimäus Die Pforte des Magiers",
            "author": "Jonathan Stroud",
            "publisher": "cbj",
            "number": 3,
            "shorthand": "cbj",
            "category": "Fantasy",
            "isbn": "978-3-570-12777-3",
        },
        {
            "key": 3,
            "title": "Der Pfad der Winde",
            "author": "Brandon Sanderson",
            "publisher": "Heyne",
            "number": 7,
            "shorthand": "Hey",
            "category": "Fantasy",
            "isbn": "978-3-453-26768-8",
        },
        {
            "key": 4,
            "title": "Eragon Der auftrag des Ältesten",
            "author": "Christopher Paolini",
            "publisher": "cbj",
            "number": 4,
            "shorthand": "cbj",
            "category": "Fantasy",
            "isbn": "978-3-570-12804-6",
        },
    ]
    session.add_all([BookTable(Book(**i)) for i in data])


def create_users_test_data(session):
    data = [
        {
            "key": 0,
            "firstname": "Lukas",
            "lastname": "Schmidt",
            "classname": "5c"
        },
        {
            "key": 1,
            "firstname": "Alice",
            "lastname": "Schmidt",
            "classname": "Lehrer*in"
        },
        {
            "key": 2,
            "firstname": "Randolf",
            "lastname": "Ravenclaw",
            "classname": "3a"

        }
    ]
    session.add_all([UserTable(User(**i)) for i in data])


def create_categories_data(session):
    data = [
        {
            "name": "Bilderbücher",
            "color": "blue",
        },
        {
            "name": "Erstleser",
            "color": "yellow",
        },
        {
            "name": "Fortgeschrittene Leser",
            "color": "red",
        },
        {
            "name": "Sachbuch",
            "color": "green",
        },
        {
            "name": "Krimi",
            "color": "black",
        },
    ]
    session.add_all([CategoryTable(Category(**i)) for i in data])


def create_overdue_borrowed_book(session):
    data = [
        {
            "key": -1,
            "book_key": 10,
            "user_key": 3,
            "return_date": None,
            "expiration_date": (datetime.now() - relativedelta(weeks=1)).date(),
            "start_date": (datetime.now() - relativedelta(weeks=4)).date(),
        }
    ]
    session.add_all([BorrowingUserTable(BorrowingUser(**i)) for i in data])
