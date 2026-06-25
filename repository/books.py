from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Optional
from schemas.books import BookCreate

class BookRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["books"]

    async def create(self, book_data: BookCreate) -> dict:
        new_book = book_data.model_dump()
        result = await self.collection.insert_one(new_book)
        new_book["_id"] = result.inserted_id
        return new_book

    async def get_all(self, limit: int, offset: int) -> List[dict]:
        cursor = self.collection.find({}).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_by_id(self, book_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(book_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(book_id)})

    async def delete(self, book_id: str) -> bool:
        if not ObjectId.is_valid(book_id):
            return False
        response = await self.collection.delete_one({"_id": ObjectId(book_id)})
        return response.deleted_count > 0
