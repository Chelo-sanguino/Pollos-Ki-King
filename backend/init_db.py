import os
from app import app
from models import db, InventarioPollo

# La base de datos es creada por el contenedor de MySQL
with app.app_context():
    db.create_all()
    if not InventarioPollo.query.first():
        db.session.add(InventarioPollo(presas_crudas=0, presas_cocidas=0))
        db.session.commit()
    
    # Intentamos agregar las columnas nuevas a Producto por si la tabla ya existía
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE producto ADD COLUMN usa_stock BOOLEAN DEFAULT FALSE;"))
        db.session.execute(text("ALTER TABLE producto ADD COLUMN stock_actual INTEGER DEFAULT 0;"))
        db.session.execute(text("ALTER TABLE producto ADD COLUMN presas_requeridas INTEGER DEFAULT 0;"))
        db.session.commit()
    except Exception as e:
        db.session.rollback() # Probablemente las columnas ya existen
        
    print("Tablas y columnas creadas/actualizadas exitosamente.")
