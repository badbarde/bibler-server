
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ImportBooksResponseStatus(Enum):
    """status codes for Borrowing a book"""
    success = "successfully imported"
    fail = "import failed"


class BorrowResponseModel(BaseModel):
    """Response model for borrowing a book"""
    status: ImportBooksResponseStatus
    import_count: Optional[int]
