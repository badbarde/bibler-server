from typing import Optional
from pydantic import BaseModel
from fastapi import Query

class User(BaseModel):
    key: int
    firstname: str
    lastname: str
    clazz: Optional[str] = Query(None, alias="class")