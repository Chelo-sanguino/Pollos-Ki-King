// 1. Inicialización Global
let modalInstancia;
let modalExtraInstancia;

document.addEventListener('DOMContentLoaded', () => {
    // Inicializamos el modal de Bootstrap una sola vez
    const elModal = document.getElementById('modalProducto');
    if (elModal) {
        modalInstancia = new bootstrap.Modal(elModal);
    }

    const elModalExtra = document.getElementById('modalExtra');
    if (elModalExtra) {
        modalExtraInstancia = new bootstrap.Modal(elModalExtra);
    }

    cargarEstadisticas();
    cargarListaAdmin();
    cargarListaExtras();
    cargarInventario();
});

// 2. Función Maestra para el Botón "+ Nuevo Producto" y "Editar"
function abrirModal(id = null, nombre = '', categoria = '', precio = '', usa_stock = false, stock = 0, presas = 0) {
    document.getElementById('prod-id').value = id || '';
    document.getElementById('prod-nombre').value = nombre;
    document.getElementById('prod-categoria').value = categoria || 'Hamburguesas';
    document.getElementById('prod-precio').value = precio;
    document.getElementById('prod-usa-stock').checked = usa_stock;
    document.getElementById('prod-stock').value = stock;
    document.getElementById('prod-presas').value = presas;

    document.getElementById('tituloModal').innerText = id ? '✏️ Editar Producto' : '🍔 Nuevo Producto';

    modalInstancia.show();
}

// 3. Guardar Cambios (Crea o Edita)
async function guardarProducto() {
    const id = document.getElementById('prod-id').value;
    const datos = {
        nombre: document.getElementById('prod-nombre').value,
        categoria: document.getElementById('prod-categoria').value,
        precio: parseFloat(document.getElementById('prod-precio').value),
        usa_stock: document.getElementById('prod-usa-stock').checked,
        stock_actual: parseInt(document.getElementById('prod-stock').value) || 0,
        presas_requeridas: parseInt(document.getElementById('prod-presas').value) || 0
    };

    const url = id ? `/api/productos/${id}` : '/api/productos';
    const metodo = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: metodo,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    });

    if (res.ok) {
        modalInstancia.hide();
        cargarListaAdmin();
        Swal.fire({icon: 'success', title: '¡Éxito!', text: 'Operación exitosa', confirmButtonColor: '#FACC15'});
    } else {
        Swal.fire({icon: 'error', title: 'Error', text: 'Error al procesar la solicitud', confirmButtonColor: '#FACC15'});
    }
}

// 5. Estadísticas
async function cargarEstadisticas() {
    const res = await fetch('/api/stats/mensual');
    if (res.ok) {
        const data = await res.json();
        document.getElementById('stat-ganancia').innerText = `${data.ganancia_total} Bs.`;
        document.getElementById('stat-mas-vendido-nombre').innerText = data.mas_vendido.nombre;
        document.getElementById('stat-mas-vendido-cantidad').innerText = `${data.mas_vendido.cantidad} unidades`;
        document.getElementById('stat-menos-vendido-nombre').innerText = data.menos_vendido.nombre;
        document.getElementById('stat-menos-vendido-cantidad').innerText = `${data.menos_vendido.cantidad} unidades`;
    }
}

// 6. Cargar Tabla con Lógica de Estrellas
async function cargarListaAdmin() {
    const res = await fetch('/api/productos');
    const productos = await res.json();
    const tabla = document.getElementById('tabla-productos-admin');
    tabla.innerHTML = '';

    productos.forEach(p => {
        tabla.innerHTML += `
            <tr>
                <td>${p.id}</td>
                <td class="text-white">${p.nombre}</td>
                <td><span class="badge bg-secondary">${p.categoria}</span></td>
                <td class="text-warning fw-bold">${p.precio.toFixed(2)} Bs.</td>
                <td>${p.usa_stock ? `<span class="badge bg-info">${p.stock_actual}</span>` : '<span class="text-muted">-</span>'}</td>
                <td>${p.presas_requeridas > 0 ? `<span class="badge bg-danger">${p.presas_requeridas}</span>` : '<span class="text-muted">-</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning me-1" 
                            onclick="abrirModal(${p.id}, '${p.nombre.replace(/'/g, "\\'")}', '${p.categoria}', ${p.precio}, ${p.usa_stock}, ${p.stock_actual || 0}, ${p.presas_requeridas || 0})">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="eliminarProducto(${p.id})">🗑️</button>
                </td>
            </tr>`;
    });
}

// 7. Eliminar Producto
async function eliminarProducto(id) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: "⚠️ ¿Estás seguro de eliminar este producto?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#E62E2D',
        cancelButtonColor: '#9CA3AF',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });
    
    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`/api/productos/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();

        if (res.ok) {
            Swal.fire({icon: 'success', title: '¡Éxito!', text: "✅ " + data.mensaje, confirmButtonColor: '#FACC15'});
            cargarListaAdmin();
        } else {
            Swal.fire({icon: 'error', title: 'Error', text: "❌ Error: " + data.error, confirmButtonColor: '#FACC15'});
        }
    } catch (error) {
        console.error("Error en la petición DELETE:", error);
        Swal.fire({icon: 'error', title: 'Error', text: 'Hubo un error al conectar con el servidor.', confirmButtonColor: '#FACC15'});
    }
}

// 8. Cierre de Caja a prueba de bloqueos
async function ejecutarCierre() {
    const result = await Swal.fire({
        title: '¿Cerrar Caja?',
        text: "⚠️ ¿Estás seguro de cerrar la caja actual?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#FACC15',
        cancelButtonColor: '#9CA3AF',
        confirmButtonText: 'Sí, cerrar caja',
        cancelButtonText: 'Cancelar'
    });
    
    if (!result.isConfirmed) return;

    // 1. Abrimos la pestaña ANTES de hablar con el servidor (Evita el bloqueo)
    const ventanaPDF = window.open('', '_blank');
    ventanaPDF.document.write('<h2>Generando reporte de cierre... por favor espere.</h2>');

    try {
        const res = await fetch('/api/caja/cerrar', { method: 'POST' });
        const data = await res.json();

        if (res.ok) {
            // 2. Si el servidor nos dio el ID, redirigimos la pestaña al PDF
            if (data.caja_id) {
                ventanaPDF.location.href = `/api/caja/ticket_cierre/${data.caja_id}`;
            } else {
                ventanaPDF.close();
                Swal.fire({icon: 'error', title: 'Error', text: "Error: El servidor no envió el ID de la caja.", confirmButtonColor: '#FACC15'});
            }

            // 3. Pequeña pausa para asegurar la carga, luego recargamos el panel
            setTimeout(() => {
                location.reload();
            }, 1000);

        } else {
            ventanaPDF.close();
            Swal.fire({icon: 'error', title: 'Error', text: data.error || "Error al cerrar la caja", confirmButtonColor: '#FACC15'});
        }
    } catch (error) {
        ventanaPDF.close();
        console.error(error);
        Swal.fire({icon: 'error', title: 'Error', text: "Error de conexión con el servidor.", confirmButtonColor: '#FACC15'});
    }
}

// 9. Imprimir Reporte Diario de Productos
function imprimirReporteProductos() {
    // Abrimos una pestaña en blanco inmediatamente para evitar bloqueos del navegador
    const ventanaReporte = window.open('', '_blank');
    ventanaReporte.document.write('<h2 style="font-family: sans-serif;">Generando reporte de inventario...</h2>');

    // Le decimos a la pestaña que cargue nuestro nuevo PDF de la ruta
    ventanaReporte.location.href = '/api/reportes/diario_productos';
}

// ==========================================
// CRUD PARA EXTRAS Y SALSAS
// ==========================================

async function cargarListaExtras() {
    const res = await fetch('/api/extras');
    const extras = await res.json();
    const tabla = document.getElementById('tabla-extras-admin');
    if (!tabla) return;

    tabla.innerHTML = '';
    extras.forEach(e => {
        tabla.innerHTML += `
            <tr>
                <td>${e.id}</td>
                <td class="text-white">${e.nombre}</td>
                <td class="text-warning fw-bold">${e.precio.toFixed(2)} Bs.</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-warning me-1" 
                            onclick="abrirModalExtra(${e.id}, '${e.nombre}', ${e.precio})">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="eliminarExtra(${e.id})">🗑️</button>
                </td>
            </tr>`;
    });
}

function abrirModalExtra(id = null, nombre = '', precio = '') {
    document.getElementById('extra-id').value = id || '';
    document.getElementById('extra-nombre').value = nombre;
    document.getElementById('extra-precio').value = precio;

    document.getElementById('tituloModalExtra').innerText = id ? '✏️ Editar Extra' : '🥓 Nuevo Extra';
    modalExtraInstancia.show();
}

async function guardarExtra() {
    const id = document.getElementById('extra-id').value;
    const datos = {
        nombre: document.getElementById('extra-nombre').value,
        precio: parseFloat(document.getElementById('extra-precio').value)
    };

    const url = id ? `/api/extras/${id}` : '/api/extras';
    const metodo = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: metodo,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    });

    if (res.ok) {
        modalExtraInstancia.hide();
        cargarListaExtras();
        Swal.fire({icon: 'success', title: '¡Éxito!', text: '¡Extra guardado con éxito!', confirmButtonColor: '#FACC15'});
    } else {
        Swal.fire({icon: 'error', title: 'Error', text: 'Error al procesar la solicitud', confirmButtonColor: '#FACC15'});
    }
}

async function eliminarExtra(id) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: "⚠️ ¿Estás seguro de eliminar este Extra/Salsa?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#E62E2D',
        cancelButtonColor: '#9CA3AF',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`/api/extras/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();

        if (res.ok) {
            Swal.fire({icon: 'success', title: '¡Éxito!', text: "✅ " + data.mensaje, confirmButtonColor: '#FACC15'});
            cargarListaExtras();
        } else {
            Swal.fire({icon: 'error', title: 'Error', text: "❌ Error: " + data.error, confirmButtonColor: '#FACC15'});
        }
    } catch (error) {
        console.error("Error en la petición DELETE:", error);
        Swal.fire({icon: 'error', title: 'Error', text: 'Hubo un error al conectar con el servidor.', confirmButtonColor: '#FACC15'});
    }
}

// Imprimir Reporte Mensual de Productos
function imprimirReporteMensualProductos() {
    const ventanaReporte = window.open('', '_blank');
    ventanaReporte.document.write('<h2 style="font-family: sans-serif;">Generando reporte mensual... por favor espere.</h2>');

    // Redirigimos a la nueva ruta del backend
    ventanaReporte.location.href = '/api/reportes/mensual_productos';
}

// ==========================================
// INVENTARIO DE POLLOS
// ==========================================
async function cargarInventario() {
    const res = await fetch('/api/inventario/pollo');
    if (res.ok) {
        const data = await res.json();
        document.getElementById('inv-crudas').innerText = data.presas_crudas;
        document.getElementById('inv-cocidas').innerText = data.presas_cocidas;
    }
}

let modalCrudoInstancia;
let modalCocinarInstancia;

function abrirModalCrudo() {
    if (!modalCrudoInstancia) modalCrudoInstancia = new bootstrap.Modal(document.getElementById('modalCrudo'));
    document.getElementById('inv-cantidad-crudo').value = '';
    modalCrudoInstancia.show();
}

function abrirModalCocinar() {
    if (!modalCocinarInstancia) modalCocinarInstancia = new bootstrap.Modal(document.getElementById('modalCocinar'));
    document.getElementById('inv-cantidad-cocinar').value = '';
    modalCocinarInstancia.show();
}

async function guardarIngresoCrudo() {
    const cantidad = parseInt(document.getElementById('inv-cantidad-crudo').value);
    if (!cantidad || cantidad <= 0) return;

    const res = await fetch('/api/inventario/pollo/ingresar_crudo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cantidad })
    });

    if (res.ok) {
        modalCrudoInstancia.hide();
        cargarInventario();
        Swal.fire({icon: 'success', title: '¡Éxito!', text: 'Presas ingresadas al inventario.', confirmButtonColor: '#FACC15'});
    }
}

async function guardarCocinar() {
    const cantidad = parseInt(document.getElementById('inv-cantidad-cocinar').value);
    const actuales = parseInt(document.getElementById('inv-crudas').innerText);

    if (!cantidad || cantidad <= 0) return;
    
    if (cantidad > actuales) {
        Swal.fire({icon: 'error', title: 'Stock Insuficiente', text: 'No tienes suficientes presas crudas.', confirmButtonColor: '#FACC15'});
        return;
    }

    const res = await fetch('/api/inventario/pollo/cocinar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cantidad })
    });

    if (res.ok) {
        modalCocinarInstancia.hide();
        cargarInventario();
        Swal.fire({icon: 'success', title: '¡A cocinar!', text: 'Presas movidas a cocidas.', confirmButtonColor: '#FACC15'});
    }
}