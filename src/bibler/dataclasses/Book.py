from typing import Optional
from pydantic import BaseModel

from .Media import Media

class Book(BaseModel):
    key: int
    title: str
    author: str
    publisher: str
    number: str
    shorthand: str
    category: str
    isbn: str
    media: Optional[Media]


