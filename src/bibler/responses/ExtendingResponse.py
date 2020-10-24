from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ExtendingResponseStatus(Enum):
    """status codes for extending a book borrowing period"""
    success = "successfully extended"
    book_not_borrowed = "book not borrowed"
    user_unknown = "user unknown"
    book_unknown = "user unknown"
    limit_exceeded = "maximum borrow period reached"


class ExtendingResponseModel(BaseModel):
    """Response model for extending a book borrowing period"""
    status: ExtendingResponseStatus
    return_date: Optional[date]
