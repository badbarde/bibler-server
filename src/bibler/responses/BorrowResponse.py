from enum import Enum
from typing import Optional

from pydantic import BaseModel


class BorrowResponseStatus(Enum):
    """status codes for Borrowing a book"""
    success = "successfully borrowed"
    already_borrowed = "already borrowed"
    user_unknown = "user unknown"
    book_unknown = "user unknown"
    limmit_exceeded = "maximum number ob books already borrowed"


class BorrowResponseModel(BaseModel):
    """Response model for borrowing a book"""
    status: BorrowResponseStatus
    return_date: Optional[str]
