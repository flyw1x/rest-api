import uuid
from typing import List, Optional
from fastapi import APIRouter, status, Query
from schemas.book import BookCreate, BookResponse, BookStatus
from services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/", response_model=List[BookResponse], status_code=status.HTTP_200_OK)
async def get_books(
    status: Optional[BookStatus] = Query(None, description="Фільтр за статусом (available/borrowed)"),
    author: Optional[str] = Query(None, description="Фільтр за автором (частковий збіг)"),
    sort_by: Optional[str] = Query(None, regex="^(title|release_year)$", description="Сортування за 'title' або 'release_year'")
):
    return await BookService.get_all_books(status=status, author=author, sort_by=sort_by)


@router.get("/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book(book_id: uuid.UUID):
    return await BookService.get_book_by_id(book_id)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book_in: BookCreate):
    return await BookService.create_book(book_in)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: uuid.UUID):
    await BookService.delete_book(book_id)
    return None  # HTTP 204 не повинен містити тіла відповіді