from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Tabla intermedia para permitir múltiples extras por cada producto pedido
detalle_extras = db.Table('detalle_extras',
    db.Column('detalle_id', db.Integer, db.ForeignKey('detalle_venta.id'), primary_key=True),
    db.Column('extra_id', db.Integer, db.ForeignKey('extra.id'), primary_key=True)
)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio_base = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50)) # Hamburguesas, Milanesas, Sodas, etc.
    activo = db.Column(db.Boolean, default=True)
    usa_stock = db.Column(db.Boolean, default=False)
    stock_actual = db.Column(db.Integer, default=0)
    presas_requeridas = db.Column(db.Integer, default=0)
    tipo_presa_pollo = db.Column(db.String(50), nullable=True) # "Ala", "Pierna", "Pierna con Ala", etc.

class InventarioPollo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presas_crudas = db.Column(db.Integer, default=0)
    presas_cocidas = db.Column(db.Integer, default=0)
    pollos_crudos = db.Column(db.Integer, default=0)
    pollos_cocidos_turno = db.Column(db.Integer, default=0)
    alas_cocidas = db.Column(db.Integer, default=0)
    pechos_cocidos = db.Column(db.Integer, default=0)
    contras_cocidas = db.Column(db.Integer, default=0)
    piernas_cocidas = db.Column(db.Integer, default=0)

class Extra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)

class Caja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_apertura = db.Column(db.DateTime, default=datetime.now)
    fecha_cierre = db.Column(db.DateTime, nullable=True)
    monto_inicial = db.Column(db.Float, default=0.0)
    monto_final = db.Column(db.Float, nullable=True)
    estado = db.Column(db.String(10), default='Abierta')

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.Integer, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.now)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20)) # Efectivo, QR
    caja_id = db.Column(db.Integer, db.ForeignKey('caja.id'))
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    observaciones = db.Column(db.Text) # Ej: "Sin pepinillos"
    subtotal = db.Column(db.Float, nullable=False)
    # Relación para conectar con los extras seleccionados
    extras = db.relationship('Extra', secondary=detalle_extras, lazy='subquery',
                             backref=db.backref('detalles_pedidos', lazy=True))