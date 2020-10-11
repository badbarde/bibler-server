

from enum import Enum

from pydantic import BaseModel


class PutBookResponseStatus(Enum):
    """status codes for creating a book"""
    success = "book created"
    fail = "book not created"


class PutBookResponseModel(BaseModel):
    """"""
    status: PutBookResponseStatus
