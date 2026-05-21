from app import app, db
from models import Producto, Extra

def poblar_datos():
    with app.app_context():
        # 1. Agregar Productos Base
        p1 = Producto(nombre="Hamburguesa Simple", precio_base=25.0, categoria="Hamburguesas")
        p2 = Producto(nombre="Hamburguesa Doble", precio_base=35.0, categoria="Hamburguesas")
        p3 = Producto(nombre="Milanesa de Pollo", precio_base=30.0, categoria="Milanesas")
        p4 = Producto(nombre="Coca-Cola 500ml", precio_base=10.0, categoria="Sodas")
        
        # 2. Agregar Extras
        e1 = Extra(nombre="Huevo Frito", precio=3.0)
        e2 = Extra(nombre="Tocino", precio=5.0)
        e3 = Extra(nombre="Queso Extra", precio=4.0)

        db.session.add_all([p1, p2, p3, p4, e1, e2, e3])
        db.session.commit()
        print("¡Productos y Extras agregados con éxito!")

if __name__ == '__main__':
    poblar_datos()