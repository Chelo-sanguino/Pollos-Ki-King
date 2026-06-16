import os
from app import app
from models import db, InventarioPollo

# La base de datos es creada por el contenedor de MySQL
with app.app_context():
    db.create_all()
    
    from sqlalchemy import text
    def add_column(table, column, definition):
        try:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition};"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
    # Intentamos agregar las columnas nuevas individualmente
    add_column("producto", "usa_stock", "BOOLEAN DEFAULT FALSE")
    add_column("producto", "stock_actual", "INTEGER DEFAULT 0")
    add_column("producto", "presas_requeridas", "INTEGER DEFAULT 0")
    add_column("producto", "tipo_presa_pollo", "VARCHAR(50)")
    
    add_column("inventario_pollo", "pollos_crudos", "INTEGER DEFAULT 0")
    add_column("inventario_pollo", "pollos_cocidos_turno", "INTEGER DEFAULT 0")
    add_column("inventario_pollo", "alas_cocidas", "INTEGER DEFAULT 0")
    add_column("inventario_pollo", "pechos_cocidos", "INTEGER DEFAULT 0")
    add_column("inventario_pollo", "contras_cocidas", "INTEGER DEFAULT 0")
    add_column("inventario_pollo", "piernas_cocidas", "INTEGER DEFAULT 0")
    
    # Ahora que las columnas existen seguro, podemos usar el ORM
    if not InventarioPollo.query.first():
        db.session.add(InventarioPollo(presas_crudas=0, presas_cocidas=0))
        db.session.commit()
        
    print("Tablas y columnas creadas/actualizadas exitosamente.")
