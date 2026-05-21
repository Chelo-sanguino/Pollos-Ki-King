from app import app
from models import db, Extra

extras_pollo = [
    {"nombre": "Porción de Arroz", "precio": 5},
    {"nombre": "Llajua extra", "precio": 2},
    {"nombre": "Salsa Ajo", "precio": 3},
    {"nombre": "Mayonesa", "precio": 2},
    {"nombre": "Ketchup", "precio": 2},
    {"nombre": "Mostaza", "precio": 2}
]

with app.app_context():
    for ext in extras_pollo:
        db.session.add(Extra(nombre=ext['nombre'], precio=ext['precio']))
    db.session.commit()
    print("¡Extras de Pollos Ki-King cargados!")