

from enum import Enum

from pydantic import BaseModel


class PutUserResponseStatus(Enum):
    """status codes for creating a user"""
    success = "user created"
    fail = "user not created"


class PutUserResponseModel(BaseModel):
    """"""
    status: PutUserResponseStatus
