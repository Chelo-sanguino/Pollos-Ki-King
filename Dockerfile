FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/backend

# Al iniciar, creamos las tablas, insertamos la data y arrancamos la app
CMD sh -c "python init_db.py && python seed_menu.py && python seed_extras.py && python app.py"
