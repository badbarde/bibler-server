

from enum import Enum

from pydantic import BaseModel


class DeleteUserResponseStatus(Enum):
    """status codes for delete a user"""
    success = "user deleted"
    borrowing = "user is still borrowing books"
    fail = "user not deleted"


class DeleteUserResponseModel(BaseModel):
    """"""
    status: DeleteUserResponseStatus
