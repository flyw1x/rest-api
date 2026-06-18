from fastapi import FastAPI
from api.endpoints import router as book_router

app = FastAPI(
    title="Library API",
    description="Асинхронне API для керування книгами в бібліотеці",
    version="1.0.0"
)

# Підключаємо роутер книг
app.include_router(book_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)