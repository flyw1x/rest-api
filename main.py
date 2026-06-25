import os
from flask import Flask, request
from flask_restful import Api, Resource
from flasgger import Swagger
from motor.motor_asyncio import AsyncIOMotorClient
from repository.books import BookRepository

app = Flask(__name__)
api = Api(app)

app.config["SWAGGER"] = {
    "title": "Library Flask NoSQL API",
    "uiversion": 3
}
swagger = Swagger(app)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo_admin:password@mongo_db:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["library_db"]
repo = BookRepository(db)

class BookListResource(Resource):
    def get(self):
        """
        Отримати список книг з пагінацією Limit-Offset
        ---
        parameters:
          - name: limit
            in: query
            type: integer
            default: 10
          - name: offset
            in: query
            type: integer
            default: 0
        responses:
          200:
            description: Успішно
        """
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)
        return repo.get_all(limit, offset), 200

    def post(self):
        """
        Створити книгу
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                title: {type: string}
                release_year: {type: integer}
                author_id: {type: integer}
        responses:
          201:
            description: Створено
        """
        data = request.get_json()
        return repo.create(data), 201

class BookResource(Resource):
    def get(self, book_id):
        book = repo.get_by_id(book_id)
        if not book: return {"message": "Not found"}, 404
        return book, 200

    def delete(self, book_id):
        if not repo.delete(book_id): return {"message": "Not found"}, 404
        return "", 204

api.add_resource(BookListResource, "/books")
api.add_resource(BookResource, "/books/<string:book_id>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
