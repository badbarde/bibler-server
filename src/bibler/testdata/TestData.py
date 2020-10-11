
import json
import os

from ..dataclasses.Book import Book
from ..dataclasses.User import User


def create_books_test_data(savedir):
    with open(os.path.join(savedir, Book.__name__ + ".json"), "w") as f:
        json.dump([
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
                "number": 3,
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
        ], f)


def create_users_test_data(savedir):
    with open(os.path.join(savedir, User.__name__ + ".json"), "w") as f:
        json.dump([
            {
                "key": 0,
                "firstname": "Lukas",
                "lastname": "Schmidt",
                "clazz": "5c"
            },
            {
                "key": 1,
                "firstname": "Alice",
                "lastname": "Schmidt",
                "clazz": "Lehrer*in"
            },
            {
                "key": 2,
                "firstname": "Randolf",
                "lastname": "Ravenclaw",
                "clazz": "3a"

            }
        ], f)
