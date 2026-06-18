import uuid
from typing import List, Dict, Any, Optional
from models.storage import books_db
from schemas.book import BookCreate, BookStatus

class BookRepository:
    @staticmethod
    async def get_all(
        status: Optional[BookStatus] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        filtered_books = books_db.copy()

        # Фільтрація
        if status:
            filtered_books = [b for b in filtered_books if b["status"] == status]
        if author:
            filtered_books = [b for b in filtered_books if author.lower() in b["author"].lower()]

        # Сортування (title або release_year)
        if sort_by in ["title", "release_year"]:
            filtered_books.sort(key=lambda x: x[sort_by])

        return filtered_books

    @staticmethod
    async def get_by_id(book_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        for book in books_db:
            if book["id"] == book_id:
                return book
        return None

    @staticmethod
    async def create(book_data: BookCreate) -> Dict[str, Any]:
        new_book = book_data.model_dump()
        new_book["id"] = uuid.uuid4()  # Автоматична генерація UUID
        books_db.append(new_book)
        return new_book

    @staticmethod
    async def delete(book_id: uuid.UUID) -> bool:
        global books_db
        for i, book in enumerate(books_db):
            if book["id"] == book_id:
                books_db.pop(i)
                return True
        return False