

from enum import Enum

from pydantic import BaseModel


class PatchBookResponseStatus(Enum):
    """status codes for updating a book"""
    success = "book updated"
    fail = "book not updated"


class PatchBookResponseModel(BaseModel):
    """"""
    status: PatchBookResponseStatus
