
from enum import Enum

from pydantic import BaseModel


class ReturningResponseStatus(Enum):
    """status codes for Borrowing a book"""
    success = "successfully returned"
    book_not_borrowed = "book not borrowed"
    user_unknown = "user unknown"
    book_unknown = "book unknown"


class ReturningResponseModel(BaseModel):
    """"""
    status: ReturningResponseStatus
