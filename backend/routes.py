from flask import Blueprint, request, jsonify
from models import db, Caja, Producto, Venta, DetalleVenta, Extra, InventarioPollo
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import simpleSplit
import io


api_bp = Blueprint('api', __name__)


# --- CONTROL DE CAJA ---
@api_bp.route('/caja/abrir', methods=['POST'])
def abrir_caja():
    # Verificamos si ya hay una caja abierta
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    if caja_abierta:
        # Si ya existe una, devolvemos un mensaje informativo en lugar de error
        return jsonify({"mensaje": "La caja ya se encuentra abierta", "id": caja_abierta.id}), 200
    
    monto_inicial = request.json.get('monto_inicial', 0.0)
    nueva_caja = Caja(monto_inicial=monto_inicial, estado='Abierta')
    db.session.add(nueva_caja)
    db.session.commit()
    
    return jsonify({"mensaje": "Caja abierta correctamente", "id": nueva_caja.id}), 201

@api_bp.route('/caja/estado', methods=['GET'])
def estado_caja():
    # Buscamos si hay alguna caja abierta en este momento
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    
    if caja_abierta:
        return jsonify({"abierta": True, "monto_inicial": caja_abierta.monto_inicial}), 200
    else:
        return jsonify({"abierta": False}), 200

# --- CONTROL DE VENTAS ---
@api_bp.route('/venta/nueva', methods=['POST'])
def nueva_venta():
    # 1. Validar que la caja esté abierta
    caja_activa = Caja.query.filter_by(estado='Abierta').first()
    if not caja_activa:
        return jsonify({"error": "No se puede registrar ventas con la caja cerrada"}), 400

    datos = request.json
    total_venta = 0
    
    # 2. Generar número de pedido correlativo por turno (caja activa)
    ultimo_pedido = Venta.query.filter_by(caja_id=caja_activa.id).order_by(Venta.numero_pedido.desc()).first()
    nuevo_num_pedido = (ultimo_pedido.numero_pedido + 1) if ultimo_pedido else 1

    nueva_venta = Venta(
        numero_pedido=nuevo_num_pedido,
        total=0, # Se actualiza al final
        metodo_pago=datos.get('metodo_pago', 'Efectivo'),
        caja_id=caja_activa.id
    )
    db.session.add(nueva_venta)
    db.session.flush() # Para obtener el ID de la venta antes de procesar detalles

    # 3. Procesar los productos enviados desde el frontend
    inventario = InventarioPollo.query.first()
    for item in datos.get('productos', []):
        prod = Producto.query.get(item['id'])
        if not prod:
            continue

        # Descontar stock
        if prod.usa_stock:
            prod.stock_actual -= item['cantidad']
        if prod.presas_requeridas > 0 and inventario:
            inventario.presas_cocidas -= (item['cantidad'] * prod.presas_requeridas)

        precio_unitario_final = prod.precio_base
        
        detalle = DetalleVenta(
            venta_id=nueva_venta.id,
            producto_id=prod.id,
            cantidad=item['cantidad'],
            observaciones=item.get('observaciones', ''),
            subtotal=0 
        )

        # 4. Procesar Extras e incrementar el precio
        for extra_id in item.get('extras', []):
            ext = Extra.query.get(extra_id)
            if ext:
                precio_unitario_final += ext.precio
                detalle.extras.append(ext)

        # Cálculo final del renglón
        detalle.subtotal = precio_unitario_final * item['cantidad']
        total_venta += detalle.subtotal
        db.session.add(detalle)

    # 5. Guardar total final de la venta
    nueva_venta.total = total_venta
    db.session.commit()

    return jsonify({
        "mensaje": "Venta registrada con éxito", 
        "pedido_nro": nuevo_num_pedido, 
        "total": total_venta,
        "venta_id": nueva_venta.id 
    }), 201
@api_bp.route('/venta/ticket/<int:venta_id>', methods=['GET'])
def imprimir_ticket(venta_id):
    venta = Venta.query.get(venta_id)
    if not venta:
        return jsonify({"error": "Venta no encontrada"}), 40    ancho = 58 * mm
    alto_cliente = max(60, 65 + (len(venta.detalles) * 8)) * mm 
    alto_cocina = max(55, 30 + (len(venta.detalles) * 8)) * mm 
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    c.setPageSize((ancho, alto_cliente))
    dibujar_contenido_ticket(c, venta, ancho, alto_cliente, modo="cliente")
    c.showPage() 
    
    c.setPageSize((ancho, alto_cocina))
    dibujar_contenido_ticket(c, venta, ancho, alto_cocina, modo="cocina")
    c.showPage() 
    
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

def dibujar_contenido_ticket(c, venta, ancho, alto, modo="cliente"):
    y = alto - 2 * mm
    import os
    from reportlab.lib.utils import simpleSplit

    if modo == "cliente":
        # LOGO
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'img', 'Logo-kiking-BlancoNegro.png')
        if os.path.exists(logo_path):
            logo_size = 22 * mm
            c.drawImage(logo_path, (ancho - logo_size) / 2, y - logo_size + 4*mm, width=logo_size, height=logo_size, mask='auto')
            y -= (logo_size + 1*mm)

    titulo = "POLLOS KI-KIN" if modo == "cliente" else "--- COCINA ---"
    c.setFont("Helvetica-Bold", 10 if modo == "cocina" else 9)
    c.drawCentredString(ancho/2, y, titulo)
    
    y -= 3.5 * mm
    
    if modo == "cocina":
        c.setFont("Helvetica", 8)
        c.drawCentredString(ancho/2, y, "[ ] DELIVERY  [ ] LLEVAR  [ ] LOCAL")
        y -= 3.5 * mm

    c.setFont("Helvetica-Bold", 9 if modo == "cocina" else 8)
    c.drawCentredString(ancho/2, y, f"Ticket Nro: {venta.numero_pedido}")
    
    y -= 3.5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Fecha: {venta.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
    y -= 3 * mm
    c.drawString(5 * mm, y, "-" * 32)
    y -= 3.5 * mm

    for detalle in venta.detalles:
        prod = Producto.query.get(detalle.producto_id)
        
        texto_prod = f"{detalle.cantidad} {prod.nombre}"
        fuente_p = "Helvetica-Bold"
        tamano_p = 9 if modo == "cocina" else 8
        
        ancho_texto = ancho - (22 * mm if modo == "cliente" else 10 * mm)
        lineas = simpleSplit(texto_prod, fuente_p, tamano_p, ancho_texto)
        
        y_ini = y
        for linea in lineas:
            c.setFont(fuente_p, tamano_p)
            c.drawString(5 * mm, y, linea)
            y -= 3.5 * mm

        if modo == "cliente":
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(ancho - 5 * mm, y_ini, f"{detalle.subtotal:.2f}")

        # Salsas y Extras
        if detalle.extras:
            y -= 1 * mm
            for extra in detalle.extras:
                c.setFont("Helvetica-Oblique", 7)
                c.drawString(8 * mm, y, f"+ {extra.nombre}")
                y -= 3 * mm
            
        # Observaciones
        if detalle.observaciones:
            c.setFont("Helvetica-BoldOblique", 7)
            c.drawString(8 * mm, y, f"NOTA: {detalle.observaciones}")
            y -= 3.5 * mm
        
        y -= 3 * mm

    # Pie del Ticket
    if modo == "cliente":
        c.drawString(5 * mm, y, "=" * 32)
        y -= 3.5 * mm
        c.setFont("Helvetica-Bold", 10) 
        c.drawString(5 * mm, y, "TOTAL:")
        c.drawRightString(ancho - 5 * mm, y, f"{venta.total:.2f} Bs.")
        
        # --- NUEVO: IMPRIMIR EL MÉTODO DE PAGO ---
        y -= 3.5 * mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(5 * mm, y, f"PAGO: {venta.metodo_pago.upper()}")
        y -= 3.5 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(ancho/2, y, "Av Gamoneda No1559 entre")
        y -= 3 * mm
        c.drawCentredString(ancho/2, y, "Av. Circunvalación y C/Arturo Molina")
        y -= 3 * mm
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(ancho/2, y, "Pedidos: 70231349")
        y -= 4 * mm
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(ancho/2, y, "¡Gracias por su preferencia!")
    else:
        y -= 6 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(ancho/2, y, "--- FIN DE ORDEN ---")DEN ---")

@api_bp.route('/stats/mensual', methods=['GET'])
def estadisticas_mensuales():
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

   # 1. Calcular Ganancia Total del Mes
    ganancia_total = db.session.query(func.sum(Venta.total)).filter(
        extract('month', Venta.fecha_hora) == mes_actual,
        extract('year', Venta.fecha_hora) == anio_actual
    ).scalar() or 0.0

    # 2. Ranking de todos los productos
    stats = db.session.query(
        Producto.nombre, 
        func.sum(DetalleVenta.cantidad).label('total_vendido')
    ).join(DetalleVenta).join(Venta).filter(
        extract('month', Venta.fecha_hora) == mes_actual,
        extract('year', Venta.fecha_hora) == anio_actual
    ).group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).all()

    if not stats:
        return jsonify({"mensaje": "Sin datos", "ganancia_total": 0}), 200

    return jsonify({
        "ganancia_total": round(ganancia_total, 2),
        "mas_vendido": {"nombre": stats[0][0], "cantidad": stats[0][1]},
        "menos_vendido": {"nombre": stats[-1][0], "cantidad": stats[-1][1]}
    })

@api_bp.route('/productos', methods=['GET'])
def listar_productos():
    # Filtrar para que solo devuelva los que tienen activo=True
    productos = Producto.query.filter_by(activo=True).all()
    return jsonify([{
        "id": p.id,
        "nombre": p.nombre,
        "precio": p.precio_base,
        "categoria": p.categoria,
        "usa_stock": p.usa_stock,
        "stock_actual": p.stock_actual,
        "presas_requeridas": p.presas_requeridas
    } for p in productos])

@api_bp.route('/productos', methods=['POST'])
def crear_producto():
    datos = request.json
    nuevo = Producto(
        nombre=datos['nombre'],
        precio_base=datos['precio'],
        categoria=datos.get('categoria', 'Varios'),
        usa_stock=datos.get('usa_stock', False),
        stock_actual=datos.get('stock_actual', 0),
        presas_requeridas=datos.get('presas_requeridas', 0)
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Producto creado con éxito"}), 201


@api_bp.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    datos = request.json
    producto.nombre = datos.get('nombre', producto.nombre)
    producto.precio_base = datos.get('precio', producto.precio_base)
    producto.categoria = datos.get('categoria', producto.categoria)
    if 'usa_stock' in datos: producto.usa_stock = datos['usa_stock']
    if 'stock_actual' in datos: producto.stock_actual = int(datos['stock_actual'])
    if 'presas_requeridas' in datos: producto.presas_requeridas = int(datos['presas_requeridas'])
    
    db.session.commit()
    return jsonify({"mensaje": "Producto actualizado correctamente"})

# ELIMINAR PRODUCTO
@api_bp.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    try:
        # Intentamos borrarlo físicamente de la base de datos
        db.session.delete(producto)
        db.session.commit()
        return jsonify({"mensaje": "Producto eliminado definitivamente"})
    except:
        # Si da error (porque ya se vendió antes), hacemos el "Borrado Lógico"
        db.session.rollback()
        producto.activo = False
        db.session.commit()
        return jsonify({"mensaje": "Producto archivado correctamente (ya tenía ventas registradas)"}), 200
    
# --- GESTIÓN DE EXTRAS ---
@api_bp.route('/extras', methods=['GET'])
def listar_extras():
    extras = Extra.query.all()
    return jsonify([{
        "id": e.id,
        "nombre": e.nombre,
        "precio": e.precio
    } for e in extras])

@api_bp.route('/extras', methods=['POST'])
def crear_extra():
    datos = request.json
    nuevo = Extra(nombre=datos['nombre'], precio=datos['precio'])
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Extra creado"}), 201

@api_bp.route('/extras/<int:id>', methods=['PUT'])
def actualizar_extra(id):
    extra = Extra.query.get(id)
    if not extra:
        return jsonify({"error": "Extra no encontrado"}), 404
    
    datos = request.json
    extra.nombre = datos.get('nombre', extra.nombre)
    extra.precio = datos.get('precio', extra.precio)
    
    db.session.commit()
    return jsonify({"mensaje": "Extra actualizado correctamente"})

@api_bp.route('/extras/<int:id>', methods=['DELETE'])
def eliminar_extra(id):
    extra = Extra.query.get(id)
    if not extra:
        return jsonify({"error": "Extra no encontrado"}), 404
    
    try:
        db.session.delete(extra)
        db.session.commit()
        return jsonify({"mensaje": "Extra eliminado definitivamente"})
    except:
        db.session.rollback()
        # Si da error es porque el extra ya está en una factura guardada
        return jsonify({"error": "No puedes eliminar este extra porque está en ventas pasadas. Te sugerimos editar su nombre agregando '(Agotado)'."}), 400

@api_bp.route('/caja/cerrar', methods=['POST'])
def cerrar_caja():
    caja = Caja.query.filter_by(estado='Abierta').first()
    if not caja:
       return jsonify({
        "mensaje": "Caja cerrada exitosamente",
        "caja_id": caja.id, # <-- ESTA LÍNEA ES NUEVA Y VITAL
        "resumen": {
            "inicial": caja.monto_inicial,
            "ventas_efectivo": total_efectivo,
            "ventas_qr": total_qr,
            "ventas_tarjeta": total_tarjeta,
            "total_en_caja": monto_final_esperado
        }
    }), 200

    # 1. Calculamos totales por método de pago
    ventas = Venta.query.filter_by(caja_id=caja.id).all()
    
    total_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'Efectivo')
    total_qr = sum(v.total for v in ventas if v.metodo_pago == 'QR')
    total_tarjeta = sum(v.total for v in ventas if v.metodo_pago == 'Tarjeta') # Futuro
    
    monto_final_esperado = caja.monto_inicial + total_efectivo

    # 2. Cerramos la caja
    caja.estado = 'Cerrada'
    caja.fecha_cierre = datetime.now()
    # Guardamos el desglose en un campo de notas o similar si tu modelo lo permite
    db.session.commit()

    return jsonify({
        "mensaje": "Caja cerrada exitosamente",
        "caja_id": caja.id, 
        "resumen": {
            "inicial": caja.monto_inicial,
            "ventas_efectivo": total_efectivo,
            "ventas_qr": total_qr,
            "ventas_tarjeta": total_tarjeta,
            "total_en_caja": monto_final_esperado
        }
    }), 200

@api_bp.route('/caja/ticket_cierre/<int:caja_id>', methods=['GET'])
def imprimir_ticket_cierre(caja_id):
    caja = Caja.query.get(caja_id)
    if not caja:
        return jsonify({"error": "Caja no encontrada"}), 404

    # Recalculamos los totales de esa caja específica
    ventas = Venta.query.filter_by(caja_id=caja.id).all()
    total_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'Efectivo')
    total_qr = sum(v.total for v in ventas if v.metodo_pago == 'QR')
    total_ventas = total_efectivo + total_qr
    monto_esperado = caja.monto_inicial + total_efectivo

    # Lienzo de 58mm para tu impresora Knup
    ancho = 58 * mm
    alto = 120 * mm 
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    # --- DISEÑO DEL TICKET DE CIERRE ---
    y = alto - 10 * mm  # <--- AQUÍ NACE LA VARIABLE 'y'
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(ancho/2, y, "CIERRE DE TURNO")

    y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(5 * mm, y, f"Apertura: {caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')}")
    y -= 4 * mm
    c.drawString(5 * mm, y, f"Cierre: {caja.fecha_cierre.strftime('%d/%m/%Y %H:%M')}")
    y -= 4 * mm
    c.drawString(5 * mm, y, "-" * 35)

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5 * mm, y, "DESGLOSE DE INGRESOS:")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(5 * mm, y, "Fondo Inicial:")
    c.drawRightString(ancho - 5 * mm, y, f"{caja.monto_inicial:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "Ventas en Efectivo:")
    c.drawRightString(ancho - 5 * mm, y, f"+ {total_efectivo:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "Ventas por QR:")
    c.drawRightString(ancho - 5 * mm, y, f"+ {total_qr:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "-" * 35)

    # --- PARTE FINAL CORREGIDA ---
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5 * mm, y, "TOTAL VENTAS:")
    c.drawRightString(ancho - 5 * mm, y, f"{total_ventas:.2f} Bs.")

    y -= 6 * mm
    c.drawString(5 * mm, y, "=" * 35)
    
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(ancho/2, y, "EFECTIVO A ENTREGAR")
    
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 14) 
    c.drawCentredString(ancho/2, y, f"> {monto_esperado:.2f} Bs. <")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

@api_bp.route('/reportes/diario_productos', methods=['GET'])
def reporte_diario_productos():
    # 1. Calculamos el inicio del día actual (00:00:00)
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 2. Consultamos todos los detalles de venta de HOY
    detalles_hoy = db.session.query(
        Producto.nombre,
        func.sum(DetalleVenta.cantidad).label('total_cantidad'),
        func.sum(DetalleVenta.subtotal).label('total_recaudado')
    ).join(DetalleVenta, Producto.id == DetalleVenta.producto_id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .filter(Venta.fecha_hora >= hoy_inicio)\
     .group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).all()

    # --- MEDIDAS EXACTAS: HOJA TAMAÑO CARTA (8.5 x 11 pulgadas) ---
    ancho = 215.9 * mm
    alto = 279.4 * mm

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    # Si no hay ventas, mostramos un mensaje centrado
    if not detalles_hoy:
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(ancho/2, alto/2, "SIN VENTAS REGISTRADAS HOY")
        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=False, mimetype='application/pdf')

    # --- FUNCIÓN INTERNA PARA DIBUJAR LA CABECERA DE LA TABLA ---
    def dibujar_encabezado(lienzo, y_pos):
        lienzo.setFont("Helvetica-Bold", 16)
        lienzo.drawCentredString(ancho/2, y_pos, "REPORTE DIARIO DE VENTAS - POLLOS KI-KING")
        y_pos -= 8 * mm
        
        lienzo.setFont("Helvetica", 10)
        lienzo.drawCentredString(ancho/2, y_pos, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y_pos -= 12 * mm
        
        # Columnas de la tabla
        lienzo.setFont("Helvetica-Bold", 11)
        lienzo.drawString(20 * mm, y_pos, "PRODUCTO")
        lienzo.drawCentredString(ancho/2 + 20 * mm, y_pos, "CANTIDAD")
        lienzo.drawRightString(ancho - 20 * mm, y_pos, "RECAUDADO (Bs.)")
        
        y_pos -= 3 * mm
        lienzo.line(20 * mm, y_pos, ancho - 20 * mm, y_pos) # Línea separadora
        y_pos -= 8 * mm
        return y_pos

    # Empezamos a dibujar desde arriba hacia abajo
    y = alto - 25 * mm
    y = dibujar_encabezado(c, y)
    
    total_general = 0
    
    # 3. Llenamos la tabla con los datos
    for nombre, cantidad, recaudado in detalles_hoy:
        # Lógica de Salto de Página: Si llegamos al final de la hoja, creamos una nueva
        if y < 30 * mm:  
            c.showPage()
            y = alto - 25 * mm
            y = dibujar_encabezado(c, y)

        c.setFont("Helvetica", 10)
        
        # Fila de datos
        c.drawString(20 * mm, y, nombre)
        c.drawCentredString(ancho/2 + 20 * mm, y, str(int(cantidad)))
        c.drawRightString(ancho - 20 * mm, y, f"{recaudado:.2f}")
        
        total_general += recaudado
        y -= 7 * mm # Avanzamos a la siguiente línea
        
    # 4. Total Final al pie de la tabla
    y -= 5 * mm
    c.line(20 * mm, y, ancho - 20 * mm, y) # Línea de cierre
    y -= 8 * mm
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "TOTAL INGRESOS POR PRODUCTOS:")
    c.drawRightString(ancho - 20 * mm, y, f"{total_general:.2f} Bs.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

@api_bp.route('/auditoria', methods=['GET'])
def auditoria_ventas():
    # Buscamos si enviaste una fecha específica en la URL (Ej: ?fecha=2026-03-26)
    fecha_str = request.args.get('fecha')
    
    if fecha_str:
        inicio_dia = datetime.strptime(fecha_str, '%Y-%m-%d')
    else:
        # Si no pones fecha, asume que quieres ver los de hoy
        inicio_dia = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
    fin_dia = inicio_dia + timedelta(days=1)
    
    # Filtramos las ventas estrictamente de ese día
    ventas_dia = Venta.query.filter(
        Venta.fecha_hora >= inicio_dia, 
        Venta.fecha_hora < fin_dia
    ).order_by(Venta.numero_pedido.asc()).all()
    
    fecha_mostrar = inicio_dia.strftime('%d/%m/%Y')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auditoría Ki-King</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #121212; color: white; padding: 20px; }}
            h2 {{ color: #ffc107; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e1e1e; }}
            th, td {{ border: 1px solid #ffc107; padding: 12px; text-align: center; }}
            th {{ background-color: #ffc107; color: black; font-weight: bold; }}
            .qr {{ color: #0dcaf0; font-weight: bold; }}
            .efectivo {{ color: #198754; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>🔍 AUDITORÍA FORENSE DE VENTAS Ki-King ({fecha_mostrar})</h2>
        <p style="text-align: center;">Revisa esta lista y compárala <b>uno a uno</b> con los tickets físicos de ese día.</p>
        <table>
            <tr>
                <th>Nº Pedido</th>
                <th>Hora</th>
                <th>Método de Pago</th>
                <th>Total Sistema</th>
            </tr>
    """
    
    suma_total = 0
    for v in ventas_dia:
        clase_pago = "efectivo" if v.metodo_pago == "Efectivo" else "qr"
        html += f"<tr>"
        html += f"<td><b>#{v.numero_pedido}</b></td>"
        html += f"<td>{v.fecha_hora.strftime('%H:%M')}</td>"
        html += f"<td class='{clase_pago}'>{v.metodo_pago}</td>"
        html += f"<td>{v.total:.2f} Bs.</td>"
        html += f"</tr>"
        suma_total += v.total
        
    html += f"""
            <tr>
                <th colspan="3" style="text-align: right; font-size: 1.2em;">Suma Absoluta del Sistema ({fecha_mostrar}):</th>
                <th style="font-size: 1.2em;">{suma_total:.2f} Bs.</th>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

@api_bp.route('/reportes/mensual_productos', methods=['GET'])
def reporte_mensual_productos():
    # 1. Calculamos el inicio del mes actual
    ahora = datetime.now()
    mes_inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 2. Consultamos todos los productos vendidos en el mes
    detalles_mes = db.session.query(
        Producto.nombre,
        func.sum(DetalleVenta.cantidad).label('total_cantidad'),
        func.sum(DetalleVenta.subtotal).label('total_recaudado')
    ).join(DetalleVenta, Producto.id == DetalleVenta.producto_id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .filter(Venta.fecha_hora >= mes_inicio)\
     .group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).all()

    ancho = 215.9 * mm
    alto = 279.4 * mm
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    if not detalles_mes:
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(ancho/2, alto/2, "SIN VENTAS ESTE MES")
        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=False, mimetype='application/pdf')

    def dibujar_encabezado_mensual(lienzo, y_pos):
        lienzo.setFont("Helvetica-Bold", 16)
        lienzo.drawCentredString(ancho/2, y_pos, "REPORTE MENSUAL DE VENTAS - POLLOS KI-KING")
        y_pos -= 8 * mm
        lienzo.setFont("Helvetica", 10)
        lienzo.drawCentredString(ancho/2, y_pos, f"Mes: {ahora.strftime('%B %Y')} | Generado: {ahora.strftime('%d/%m/%Y %H:%M')}")
        y_pos -= 12 * mm
        lienzo.setFont("Helvetica-Bold", 11)
        lienzo.drawString(20 * mm, y_pos, "PRODUCTO")
        lienzo.drawCentredString(ancho/2 + 20 * mm, y_pos, "CANTIDAD")
        lienzo.drawRightString(ancho - 20 * mm, y_pos, "RECAUDADO (Bs.)")
        y_pos -= 3 * mm
        lienzo.line(20 * mm, y_pos, ancho - 20 * mm, y_pos)
        y_pos -= 8 * mm
        return y_pos

    y = alto - 25 * mm
    y = dibujar_encabezado_mensual(c, y)
    total_general = 0
    
    for nombre, cantidad, recaudado in detalles_mes:
        if y < 30 * mm:  
            c.showPage()
            y = alto - 25 * mm
            y = dibujar_encabezado_mensual(c, y)
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, nombre)
        c.drawCentredString(ancho/2 + 20 * mm, y, str(int(cantidad)))
        c.drawRightString(ancho - 20 * mm, y, f"{recaudado:.2f}")
        total_general += recaudado
        y -= 7 * mm
        
    y -= 5 * mm
    c.line(20 * mm, y, ancho - 20 * mm, y)
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "TOTAL INGRESOS MENSUALES POR PRODUCTOS:")
    c.drawRightString(ancho - 20 * mm, y, f"{total_general:.2f} Bs.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

# --- INVENTARIO DE POLLOS ---
@api_bp.route('/inventario/pollo', methods=['GET'])
def estado_inventario_pollo():
    inventario = InventarioPollo.query.first()
    if not inventario:
        inventario = InventarioPollo(presas_crudas=0, presas_cocidas=0)
        db.session.add(inventario)
        db.session.commit()
    return jsonify({
        "presas_crudas": inventario.presas_crudas,
        "presas_cocidas": inventario.presas_cocidas
    })

@api_bp.route('/inventario/pollo/ingresar_crudo', methods=['POST'])
def ingresar_crudo():
    datos = request.json
    cantidad = int(datos.get('cantidad', 0))
    inventario = InventarioPollo.query.first()
    if not inventario:
        inventario = InventarioPollo(presas_crudas=0, presas_cocidas=0)
        db.session.add(inventario)
    inventario.presas_crudas += cantidad
    db.session.commit()
    return jsonify({"mensaje": "Presas crudas ingresadas con éxito"})

@api_bp.route('/inventario/pollo/cocinar', methods=['POST'])
def cocinar_presas():
    datos = request.json
    cantidad = int(datos.get('cantidad', 0))
    inventario = InventarioPollo.query.first()
    if not inventario:
        inventario = InventarioPollo(presas_crudas=0, presas_cocidas=0)
        db.session.add(inventario)
    
    inventario.presas_crudas -= cantidad
    inventario.presas_cocidas += cantidad
    db.session.commit()
    return jsonify({"mensaje": "Presas cocinadas con éxito"})