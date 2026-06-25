FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# Примусово ставимо сумісні версії pymongo та motor перед іншими залежностями
RUN pip install --no-cache-dir "pymongo==4.6.3" "motor==3.3.2"
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=main.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000", "--debug"]
