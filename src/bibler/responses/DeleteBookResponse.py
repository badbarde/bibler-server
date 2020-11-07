

from enum import Enum

from pydantic import BaseModel


class DeleteBookResponseStatus(Enum):
    """status codes for deleting a book"""
    success = "book deleted"
    borrowed = "book still borrowed"
    fail = "book not deleted"


class DeleteBookResponseModel(BaseModel):
    """"""
    status: DeleteBookResponseStatus
