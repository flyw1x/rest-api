from fastapi import FastAPI
from api.endpoints import router as books_router

app = FastAPI(title="Library API MongoDB")

app.include_router(books_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Library NoSQL API"}