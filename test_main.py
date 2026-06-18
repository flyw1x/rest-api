import pytest
from fastapi.testclient import TestClient
from main import app

# Створюємо віртуального клієнта для тестування нашого API
client = TestClient(app)

@pytest.mark.asyncio
async def test_library_flow():
    # 1. ТЕСТ: Спочатку база даних має бути порожньою
    response = client.get("/books/")
    assert response.status_code == 200
    assert response.json() == []

    # 2. ТЕСТ: Додавання нової книги (POST)
    book_data = {
        "title": "Тестова Книга",
        "author": "Тестовий Автор",
        "description": "Опис тестової книги",
        "status": "available",
        "release_year": 2024
    }
    response = client.post("/books/", json=book_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["title"] == "Тестова Книга"
    book_id = data["id"]  # Запам'ятовуємо згенерований UUID

    # 3. ТЕСТ: Отримання цієї книги за ID (GET)
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Тестова Книга"

    # 4. ТЕСТ: Перевірка валідації Pydantic (Рік з майбутнього)
    bad_book_data = book_data.copy()
    bad_book_data["release_year"] = 2030  # Невалідний рік
    response = client.post("/books/", json=bad_book_data)
    assert response.status_code == 422  # Unprocessable Entity (Помилка валідації)

    # 5. ТЕСТ: Видалення книги (DELETE)
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 204

    # 6. ТЕСТ: Перевірка ідемпотентності DELETE (Видаляємо вдруге)
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 204  # Має знову повернути 204, а не помилку!

    # 7. ТЕСТ: Перевірка, що книга дійсно зникла
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404