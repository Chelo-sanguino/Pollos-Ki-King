# backend/inventario_logic.py

# Rendimiento base al cocinar un pollo entero
RENDIMIENTO_POLLO = {
    "alas": 2,
    "pechos": 2,
    "contras": 2,
    "piernas": 2
}

# Composición exacta de cada tipo de presa
# Las llaves deben coincidir exactamente con los valores permitidos en `tipo_presa_pollo`
COMPOSICION_PRODUCTOS = {
    "Ala": {"alas": 1},
    "Pierna": {"piernas": 1},
    "Contra": {"contras": 1},
    "Pecho": {"pechos": 1},
    "Pierna con Ala": {"alas": 1, "piernas": 1},
    "Cuarto de Contra": {"contras": 1, "piernas": 1},
    "Cuarto de Pecho": {"pechos": 1, "alas": 1},
    "Medio Pollo": {"alas": 1, "pechos": 1, "contras": 1, "piernas": 1},
    "Pollo Entero": {"alas": 2, "pechos": 2, "contras": 2, "piernas": 2}
}

def cocinar_pollo(inventario, cantidad):
    """
    Descuenta pollos crudos, aumenta el contador del turno y 
    añade el rendimiento a las piezas cocidas correspondientes.
    """
    if inventario.pollos_crudos < cantidad:
        return False, f"No hay suficientes pollos crudos. Disponibles: {inventario.pollos_crudos}"
        
    inventario.pollos_crudos -= cantidad
    inventario.pollos_cocidos_turno += cantidad
    
    inventario.alas_cocidas += cantidad * RENDIMIENTO_POLLO["alas"]
    inventario.pechos_cocidos += cantidad * RENDIMIENTO_POLLO["pechos"]
    inventario.contras_cocidas += cantidad * RENDIMIENTO_POLLO["contras"]
    inventario.piernas_cocidas += cantidad * RENDIMIENTO_POLLO["piernas"]
    
    return True, "Pollos cocinados con éxito"

def descontar_presas_venta(inventario, tipo_presa_pollo, cantidad_vendida):
    """
    Descuenta del inventario las piezas exactas necesarias para el tipo de presa.
    Si no hay stock suficiente de alguna pieza, retorna False y un mensaje de error.
    """
    if not tipo_presa_pollo or tipo_presa_pollo not in COMPOSICION_PRODUCTOS:
        return True, "" # No requiere presas (ej: hamburguesas)
        
    composicion = COMPOSICION_PRODUCTOS[tipo_presa_pollo]
    
    # Validación previa
    for pieza, req_unitario in composicion.items():
        req_total = req_unitario * cantidad_vendida
        col_name = "pechos_cocidos" if pieza == "pechos" else f"{pieza}_cocidas"
        stock_actual = getattr(inventario, col_name, 0)
        
        if stock_actual < req_total:
            return False, f"No hay suficiente stock de {pieza}. Requerido: {req_total}, Disponible: {stock_actual}."
            
    # Descuento
    for pieza, req_unitario in composicion.items():
        req_total = req_unitario * cantidad_vendida
        col_name = "pechos_cocidos" if pieza == "pechos" else f"{pieza}_cocidas"
        stock_actual = getattr(inventario, col_name)
        setattr(inventario, col_name, stock_actual - req_total)
        
    return True, "Descuento exitoso"
