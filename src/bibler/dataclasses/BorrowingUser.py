from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BorrowingUser(BaseModel):
    key: int
    user_key: int
    book_key: int
    start_date: str
    expiration_date: str
    return_date: Optional[str]
