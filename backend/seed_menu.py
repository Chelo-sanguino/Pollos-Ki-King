from app import app
from models import db, Producto

menu_data = [
    # Pollos
    {"nombre": "Cuarto de Pollo", "precio": 20, "cat": "Pollos"},
    {"nombre": "Medio Pollo", "precio": 38, "cat": "Pollos"},
    {"nombre": "Pollo Entero", "precio": 70, "cat": "Pollos"},
    # Alitas
    {"nombre": "Combo Alitas 6 piezas", "precio": 25, "cat": "Alitas"},
    {"nombre": "Combo Alitas 12 piezas", "precio": 45, "cat": "Alitas"},
    # Papas
    {"nombre": "Porción de Papas Pequeña", "precio": 10, "cat": "Papas"},
    {"nombre": "Porción de Papas Grande", "precio": 18, "cat": "Papas"},
    # Bebidas
    {"nombre": "Sodas 750ml", "precio": 9, "cat": "Bebidas"},
    {"nombre": "Sodas 2 lt", "precio": 15, "cat": "Bebidas"},
    {"nombre": "Agua 500ml", "precio": 5, "cat": "Bebidas"}
]

with app.app_context():
    for item in menu_data:
        # Evitamos duplicados por nombre
        existente = Producto.query.filter_by(nombre=item['nombre']).first()
        if not existente:
            p = Producto(nombre=item['nombre'], precio_base=item['precio'], categoria=item['cat'])
            db.session.add(p)
    db.session.commit()
    print("¡Menú de Pollos Ki-King cargado con éxito!")