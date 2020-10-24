
import sqlalchemy
from pydantic import BaseModel

from .model import Base


class Category(BaseModel):
    """"""
    name: str
    color: str


class CategoryTable(Base):
    __tablename__ = "category"
    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    color = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, category: Category):
        self.name = category.name
        self.color = category.color

    def __repr__(self):
        return f"Category<{self.name}, {self.color}>"
