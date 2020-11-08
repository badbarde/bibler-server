import io
import logging
import os

from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse

logger = logging.getLogger("Bibler-server")
logger.setLevel(logging.INFO)
media = APIRouter()


@media.get("/exists/{book_key}", response_model=str)
async def book_cover_exists(book_key: int):
    """returns if a book with the key `book_key` exists"""
    if os.path.exists(os.path.join("data/media", str(book_key) + ".png")):
        return "True"
    return "False"


@media.get("/{book_key}")
async def get_book_cover(book_key: int):
    """returns the book cover of a book with the key `book_key`"""
    path = os.path.join("data/media", str(book_key) + ".png")
    logger.info(f"loading {path}")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")
