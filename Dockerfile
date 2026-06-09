FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/backend

# Al iniciar, creamos las tablas y arrancamos la app (se removieron los seeders automáticos)
CMD sh -c "python init_db.py && python app.py"
