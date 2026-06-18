import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from repository.book_repo import BookRepository
from schemas.book import BookCreate, BookResponse, BookStatus

class BookService:
    @staticmethod
    async def get_all_books(
        status: Optional[BookStatus] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[BookResponse]:
        return await BookRepository.get_all(status=status, author=author, sort_by=sort_by)

    @staticmethod
    async def get_book_by_id(book_id: uuid.UUID) -> BookResponse:
        book = await BookRepository.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Книгу з ID {book_id} не знайдено"
            )
        return book

    @staticmethod
    async def create_book(book_data: BookCreate) -> BookResponse:
        return await BookRepository.create(book_data)

    @staticmethod
    async def delete_book(book_id: uuid.UUID) -> None:
        # Ідемпотентність: якщо об'єкт вже видалено або його не існувало, 
        # ми все одно повертаємо успішний статус (204 No Content), а не 404.
        await BookRepository.delete(book_id)