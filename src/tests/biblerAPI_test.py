import json
import logging
import os
from datetime import datetime

import bibler.biblerAPI as biblerAPI
import pandas as pd
import pytest
from bibler.biblerAPI import Session, bibler
from bibler.dataclasses.BorrowingUser import BorrowingUser
from dateutil.relativedelta import relativedelta
from fastapi.testclient import TestClient
from requests.sessions import session
from starlette import responses


@pytest.fixture
def uut():
    """Unit under test"""
    return TestClient(bibler)


def create_book_test_data(session):
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
        }
    ]


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
            "key": 1,
            "title": "Die granulare Gesellschaft",
            "author": "Christoph Kucklick",
            "publisher": "Ullstein",
            "number": 2,
            "shorthand": "Ull",
            "category": "Sachbuch",
            "isbn": "978-3-548-37625-7",
        }
    ]


def create_user_test_data(session):
    data = [
        {
            "key": 0,
            "firstname": "Lukas",
            "lastname": "Schmidt",
            "classname": "5c"
        }
    ]


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
            "classname": "lehrer*in"
        }
    ]


def test_get_user(uut: TestClient, tmpdir, caplog):
    """test getting a user if only one exists"""
    # given
    caplog.set_level(logging.INFO)
    session = Session()
    create_user_test_data(session)
    session.commit()
    # when
    users = uut.get("/users")
    # then
    assert users.status_code == 200
    assert users.json() == [
        {
            "key": 0,
            "firstname": "Lukas",
            "lastname": "Schmidt",
            "classname": "5c"
        }
    ]


def test_get_users(uut: TestClient, tmpdir, caplog):
    """test getting users"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_users_test_data(tmpdir)
    # when
    users = uut.get("/users")
    # then
    assert users.status_code == 200
    assert users.json() == [
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
            "classname": "lehrer*in"
        }
    ]


def test_put_user(uut: TestClient, tmpdir, caplog):
    """test inserting a user"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    # when
    users = uut.put("/user", json={
        "key": 1,
        "firstname": "Alice",
        "lastname": "Schmidt",
        "classname": "lehrer*in"
    })
    # then
    assert users.json() == {"status": "user created"}


def test_put_user_twice(uut: TestClient, tmpdir, caplog):
    """test inserting a user that is the same as another user
    NOTE: this is INTENTIONALLY allowed"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    # when
    users = uut.put("/user", json={
        "key": 0,
        "firstname": "Lukas",
        "lastname": "Schmidt",
        "classname": "5c"
    })
    # then
    assert users.json() == {"status": "user created"}


def test_get_book(uut: TestClient, tmpdir, caplog):
    """test getting a book"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_book_test_data(tmpdir)
    # when
    users = uut.get("/books")
    # then
    assert users.status_code == 200
    assert users.json() == [
        {
            "key": 0,
            "title": "Sabriel",
            "author": "Garth Nix",
            "publisher": "Carlsen",
            "number": 1,
            "shorthand": "Car",
            "category": "Fantasy",
            "isbn": "3-551-58128-2",
        }
    ]


def test_get_books(uut: TestClient, tmpdir, caplog):
    """test getting books if there is more than one"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_books_test_data(tmpdir)
    # when
    users = uut.get("/books")
    # then
    assert users.status_code == 200
    assert users.json() == [
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
            "key": 1,
            "title": "Die granulare Gesellschaft",
            "author": "Christoph Kucklick",
            "publisher": "Ullstein",
            "number": 2,
            "shorthand": "Ull",
            "category": "Sachbuch",
            "isbn": "978-3-548-37625-7",
        }
    ]


def test_put_book(uut: TestClient, tmpdir, caplog):
    """test inserting a book"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_book_test_data(tmpdir)
    # when
    users = uut.put("/book", json={
        "key": 1,
        "title": "Die granulare Gesellschaft",
        "author": "Christoph Kucklick",
        "publisher": "Ullstein",
        "number": 2,
        "shorthand": "Ull",
        "category": "Sachbuch",
        "isbn": "978-3-548-37625-7",
    })
    # then
    assert users.json() == {"status": "book created"}


def test_put_book_with_existing_key(uut: TestClient, tmpdir, caplog):
    """test that adding a user with an existing key instead generates a 
    new key for the added user"""
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    uut.put("/user", json={
        "key": 0,
        "firstname": "Kira",
        "lastname": "Kylar",
        "class": "13a"
    })
    res = uut.get("/users")
    df = pd.DataFrame.from_records(res.json())
    assert df[df.firstname == "Kira"].key.values[0] == 1


def test_put_book_with_existing_key(uut: TestClient, tmpdir, caplog):
    """test that adding a book with an existing key instead generates a 
    new key for the added book"""
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_book_test_data(tmpdir)
    uut.put("/book", json={
        "key": 0,
        "title": "Axiom's End",
        "author": "Lindsay Ellis",
        "publisher": "St. Martin's Press",
        "number": "1",
        "shorthand": "SMP",
        "category": "SciFi",
        "isbn": " 978-1250256737",
    })
    res = uut.get("/books")
    df = pd.DataFrame.from_records(res.json())
    assert df[df.title == "Axiom's End"].key.values[0] == 1


def test_lend_book(uut: TestClient, tmpdir, caplog):
    """test simple book lendin usecase"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    create_book_test_data(tmpdir)
    # when
    response = uut.patch("/borrow/0/0")
    # then
    caplog.set_level(logging.INFO)
    path = os.path.join(tmpdir, BorrowingUser.__name__ + ".json")
    df = pd.read_json(path)
    expected_return_date = (
        datetime.now() + relativedelta(weeks=3)).strftime("%d.%m.%Y")
    # the returned value is the expected returndate
    assert response.json() == {
        "status": "successfully borrowed",
        "return_date": expected_return_date
    }
    # Expiration date is set 3 weeks from today
    assert df[df.user_key == 0].expiration_date.values[0] == expected_return_date
    # the returned exspiration date is the same as the one saved
    assert df[df.user_key == 0].expiration_date.values[0] == expected_return_date
    # The start date saved is set to today
    assert df[df.user_key == 0].start_date.values[0] == datetime.now(
    ).date().strftime("%d.%m.%Y")


def test_lend_book_that_is_already_borrowed(uut: TestClient, tmpdir, caplog):
    """test book lending usecase when book is already borrowed"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    create_book_test_data(tmpdir)
    # when
    response = uut.patch("/borrow/0/0")
    response = uut.patch("/borrow/0/0")
    # then
    caplog.set_level(logging.INFO)
    path = os.path.join(tmpdir, BorrowingUser.__name__ + ".json")
    df = pd.read_json(path)
    expected_return_date = (
        datetime.now() + relativedelta(weeks=3)).strftime("%d.%m.%Y")
    # the returned value is the expected returndate
    assert response.json() == {
        "status": "already borrowed",
        "return_date": None
    }


def test_return_book(uut: TestClient, tmpdir, caplog):
    """test simple book return usecase"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    create_book_test_data(tmpdir)
    response = uut.patch("/borrow/0/0")

    # when
    response = uut.patch("/return/0/0")
    # then
    path = os.path.join(tmpdir, BorrowingUser.__name__ + ".json")
    df = pd.read_json(path)
    expected_date = datetime.now().strftime("%d.%m.%Y")
    # returns todays date
    assert response.json() == {"status": "successfully returned"}
    # return date is inserted into the dataframe
    assert df[(df.user_key == 0) & (df.book_key == 0)
              ].return_date.values[0] == expected_date


def test_return_not_borrowed_book(uut: TestClient, tmpdir, caplog):
    """test if a user tries to return a book that he/she has not borrowed, nothing happens"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    create_book_test_data(tmpdir)

    # when
    response = uut.patch("/return/0/0")
    # then
    assert response.json() == {"status": "book not borrowed"}


def test_return_book_as_unknown_user(uut: TestClient, tmpdir, caplog):
    """test that if an unknown user tries to return a book nothing happens"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_book_test_data(tmpdir)

    # when
    response = uut.patch("/return/0/0")
    # then
    assert response.json() == {"status": "user unknown"}


def test_borrow_same_book_two_times_with_returning_it(uut: TestClient, tmpdir, caplog):
    """test if a user can borrow, return and then borrow the same book twice"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_user_test_data(tmpdir)
    create_book_test_data(tmpdir)
    expected_return_date = (
        datetime.now() + relativedelta(weeks=3)).strftime("%d.%m.%Y")

    path = os.path.join(tmpdir, BorrowingUser.__name__ + ".json")
    # when
    response = uut.patch("/borrow/0/0")
    response = uut.patch("/return/0/0")
    response = uut.patch("/borrow/0/0")
    # then
    df = pd.read_json(path)
    assert response.json() == {
        "status": "successfully borrowed",
        "return_date": expected_return_date
    }
    assert len(df[df.user_key == 0].key.unique()) == 2
    assert response.json() == {
        "status": "successfully borrowed",
        "return_date": expected_return_date
    }


def test_return_book_as_wrong_user(uut: TestClient, tmpdir, caplog):
    """test that you cant return a book as another person than that borrowed the book"""
    # given
    caplog.set_level(logging.INFO)
    biblerAPI.save_path = tmpdir
    create_users_test_data(tmpdir)
    create_book_test_data(tmpdir)
    # when
    response = uut.patch("/borrow/0/0")
    response = uut.patch("/return/1/0")
    # then
    assert response.json() == {
        "status": "book not borrowed",
    }
