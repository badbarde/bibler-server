

from enum import Enum

from pydantic import BaseModel


class PatchUserResponseStatus(Enum):
    """status codes for updating a user"""
    success = "user updated"
    fail = "user not updated"


class PatchUserResponseModel(BaseModel):
    """"""
    status: PatchUserResponseStatus
