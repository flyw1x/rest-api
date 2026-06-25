import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from pymongo import MongoClient
import jwt
from passlib.context import CryptContext
import redis

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

app = FastAPI(title="Library FastAPI NoSQL RateLimited API")

# Підключення до БД
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo_admin:password@mongo_db:27017")
client = MongoClient(MONGO_URL)
db = client["library_db"]

# Підключення до Redis (для рейт-ліміту)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis_db:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class UserRegister(BaseModel):
    username: str
    password: str

class BookModel(BaseModel):
    title: str
    release_year: int
    author_id: int

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if payload.get("type") == "access" else None
    except jwt.PyJWTError:
        return None

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload["sub"]

# --- RATE LIMITER LOGIC ---
class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    def __call__(self, request: Request, current_user: Optional[str] = Depends(get_current_user)):
        # Якщо юзер авторизований -> ключ по username і ліміт 10. Інакше -> ключ по IP і ліміт 2.
        if current_user:
            rate_key = f"rate_limit:auth:{current_user}"
            limit = 10
        else:
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"rate_limit:anon:{client_ip}"
            limit = 2

        try:
            current_requests = redis_client.incr(rate_key)
            if current_requests == 1:
                redis_client.expire(rate_key, self.window_seconds)
            
            if current_requests > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Rate limit exceeded."
                )
        except redis.RedisError:
            # Якщо Redis тимчасово впав, не ламаємо додаток у продакшені (fail-safe)
            pass

# Створюємо глобальну залежність для ліміту (передаємо дефолтні значення, логіка перевизначить ліміт)
rate_limit_dependency = RateLimiter(requests_limit=2, window_seconds=60)

# --- AUTH ENDPOINTS ---

@app.post("/auth/register", status_code=201)
def register(user: UserRegister):
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db.users.insert_one({"username": user.username, "password": hashed_password})
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login(user: UserRegister):
    db_user = db.users.find_one({"username": user.username})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = jwt.encode({"sub": user.username, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode({"sub": user.username, "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# --- PROTECTED & LIMITED BOOKS ENDPOINTS ---

@app.get("/books", dependencies=[Depends(rate_limit_dependency)])
def get_books(limit: int = 10, offset: int = 0):
    cursor = db.books.find({}).skip(offset).limit(limit)
    books = list(cursor)
    for b in books:
        b["_id"] = str(b["_id"])
    return books
