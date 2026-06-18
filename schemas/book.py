from enum import Enum
from pydantic import BaseModel, Field, UUID4
from typing import Optional

class BookStatus(str, Enum):
    AVAILABLE = "available"  
    BORROWED = "borrowed"    

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=255, description="Автор книги")
    description: Optional[str] = Field(None, description="Опис книги")
    status: BookStatus = Field(BookStatus.AVAILABLE, description="Статус книги")
    release_year: int = Field(..., ge=0, le=2026, description="Рік випуску")

class BookCreate(BookBase):
    pass  

class BookResponse(BookBase):
    id: UUID4  