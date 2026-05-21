from app import app, db
import pymysql

try:
    with app.app_context():
        print("Intentando conectar a la base de datos...")
        db.create_all()
        print("¡Tablas creadas exitosamente en hamburgueson_db!")
except Exception as e:
    print(f"Ocurrió un error: {e}")