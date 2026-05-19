FROM python:3.13

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    curl

RUN pip install fastapi uvicorn sqlalchemy pyodbc langchain-ollama

EXPOSE 8000

CMD ["python", "back_end_code/main.py"]

services:

  backend:
    build:
      context: ./BackEnd
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ../my-react-app
    ports:
      - "80:80"
    restart: unless-stopped