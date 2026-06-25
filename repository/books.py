from pymongo.database import Database
from bson import ObjectId
from typing import List, Optional

class BookRepository:
    def __init__(self, db: Database):
        self.collection = db["books"]

    def create(self, book_data: dict) -> dict:
        result = self.collection.insert_one(book_data)
        book_data["_id"] = str(result.inserted_id)
        return book_data

    def get_all(self, limit: int, offset: int) -> List[dict]:
        # Звичайна синхронна пагінація через skip() та limit()
        cursor = self.collection.find({}).skip(offset).limit(limit)
        books = list(cursor)
        for b in books:
            b["_id"] = str(b["_id"])
        return books

    def get_by_id(self, book_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(book_id):
            return None
        book = self.collection.find_one({"_id": ObjectId(book_id)})
        if book:
            book["_id"] = str(book["_id"])
        return book

    def delete(self, book_id: str) -> bool:
        if not ObjectId.is_valid(book_id):
            return False
        response = self.collection.delete_one({"_id": ObjectId(book_id)})
        return response.deleted_count > 0
