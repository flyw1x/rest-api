import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from pymongo import MongoClient
import jwt
from passlib.context import CryptContext

# Конфігурація безпеки
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="Library FastAPI NoSQL Security API")

# Підключення до MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo_admin:password@mongo_db:27017")
client = MongoClient(MONGO_URL)
db = client["library_db"]

# Pydantic моделі
class UserRegister(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class BookModel(BaseModel):
    title: str
    release_year: int
    author_id: int

# Утиліти для токенів та паролів
def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if payload.get("type") else None
    except jwt.PyJWTError:
        return None

# Залежність для захисту ендпоінтів
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["sub"]

# --- AUTH ENDPOINTS ---

@app.post("/auth/register", status_code=201)
def register(user: UserRegister):
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db.users.insert_one({"username": user.username, "password": hashed_password})
    return {"message": "User registered successfully"}

@app.post("/auth/login", response_model=TokenResponse)
def login(user: UserRegister):
    db_user = db.users.find_one({"username": user.username})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_token({"sub": user.username, "type": "access"}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token({"sub": user.username, "type": "refresh"}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    
    # Зберігаємо рефреш токен у базі, щоб контролювати сесії
    db.refresh_tokens.update_one(
        {"username": user.username},
        {"$set": {"refresh_token": refresh_token, "created_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    payload = verify_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    username = payload["sub"]
    saved_token = db.refresh_tokens.find_one({"username": username, "refresh_token": body.refresh_token})
    if not saved_token:
        raise HTTPException(status_code=401, detail="Refresh token not recognized or revoked")
    
    new_access = create_token({"sub": username, "type": "access"}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh = create_token({"sub": username, "type": "refresh"}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    
    db.refresh_tokens.update_one({"username": username}, {"$set": {"refresh_token": new_refresh}})
    return {"access_token": new_access, "refresh_token": new_refresh}

# --- PROTECTED BOOKS ENDPOINTS ---

@app.get("/books")
def get_books(limit: int = 10, offset: int = 0, current_user: str = Depends(get_current_user)):
    cursor = db.books.find({}).skip(offset).limit(limit)
    books = list(cursor)
    for b in books:
        b["_id"] = str(b["_id"])
    return books

@app.post("/books", status_code=201)
def create_book(book: BookModel, current_user: str = Depends(get_current_user)):
    book_data = book.model_dump()
    result = db.books.insert_one(book_data)
    book_data["_id"] = str(result.inserted_id)
    return book_data
