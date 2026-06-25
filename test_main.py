from fastapi.testclient import TestClient
from unittest.mock import patch
import jwt
from datetime import datetime, timedelta, timezone
from main import app, SECRET_KEY, ALGORITHM

client = TestClient(app)

def generate_mock_token(username: str):
    payload = {
        "sub": username,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ==================== ANONYMOUS USER TESTS ====================

@patch("main.redis_client.incr")
@patch("main.redis_client.expire")
def test_anonymous_under_limit(mock_expire, mock_incr):
    # Симулюємо 1-й запит аноніма (ліміт 2)
    mock_incr.return_value = 1
    
    response = client.get("/books")
    assert response.status_code == 200
    mock_incr.assert_called_once()
    mock_expire.assert_called_once()

@patch("main.redis_client.incr")
def test_anonymous_limit_exceeded(mock_incr):
    # Симулюємо 3-й запит аноніма (перевищення ліміту 2)
    mock_incr.return_value = 3
    
    response = client.get("/books")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Rate limit exceeded."


# ==================== AUTHORIZED USER TESTS ====================

@patch("main.redis_client.incr")
@patch("main.redis_client.expire")
def test_authorized_under_limit(mock_expire, mock_incr):
    # Симулюємо 5-й запит авторизованого юзера (ліміт 10)
    mock_incr.return_value = 5
    token = generate_mock_token("test_user")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/books", headers=headers)
    assert response.status_code == 200
    mock_incr.assert_called_once()

@patch("main.redis_client.incr")
def test_authorized_limit_exceeded(mock_incr):
    # Симулюємо 11-й запит авторизованого юзера (перевищення ліміту 10)
    mock_incr.return_value = 11
    token = generate_mock_token("test_user")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/books", headers=headers)
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Rate limit exceeded."
