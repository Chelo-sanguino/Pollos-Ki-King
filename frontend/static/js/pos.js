let carrito = [];
let listaExtrasDisponibles = [];
let itemIndexSeleccionado = null;
let procesandoVenta = false;
let todosLosProductos = [];
let inventarioPresasCocidas = 0;

document.addEventListener('DOMContentLoaded', () => {
    cargarProductos();
    cargarExtras();
    verificarEstadoCaja();
    cargarInventarioPresas();
});

async function cargarInventarioPresas() {
    try {
        const res = await fetch('/api/inventario/pollo');
        if (res.ok) {
            const data = await res.json();
            inventarioPresasCocidas = data.presas_cocidas || 0;
        }
    } catch (e) {
        console.error("Error al cargar inventario de presas", e);
    }
}

// 1. Cargar productos (product-card)
async function cargarProductos() {
    const res = await fetch('/api/productos');
    todosLosProductos = await res.json();
    renderizarProductos(todosLosProductos);
}

function filtrarProductos(categoria) {
    // 1. Estética de los botones
    const botones = document.querySelectorAll('#filtro-categorias .btn');
    botones.forEach(btn => {
        btn.classList.remove('active', 'btn-yellow');
        btn.classList.add('btn-outline-warning');
        if (btn.innerText.trim() === categoria || (categoria === 'Todas' && btn.innerText.trim() === 'Todas')) {
            btn.classList.add('active', 'btn-yellow');
            btn.classList.remove('btn-outline-warning');
        }
    });

    // 2. Filtrar y Renderizar
    if (categoria === 'Todas') {
        renderizarProductos(todosLosProductos);
    } else {
        const filtrados = todosLosProductos.filter(p => p.categoria === categoria);
        renderizarProductos(filtrados);
    }
}

function renderizarProductos(lista) {
    const contenedor = document.getElementById('contenedor-productos');
    contenedor.innerHTML = '';

    const gridContainer = document.createElement('div');
    // Grid para forzar exactamente 5 elementos por fila
    gridContainer.style.cssText = 'display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; width: 100%; padding: 0 5px;';

    lista.forEach(v => {
        const div = document.createElement('div');
        div.className = 'btn btn-outline-light p-2 d-flex align-items-center justify-content-center';
        div.style.cssText = 'border-color: #242424; position: relative; height: 75px; border-radius: 8px; cursor: pointer; background: #1A1A1A; transition: all 0.2s;';
        div.onclick = () => agregarAlCarrito(v.id, v.nombre, v.precio, v.categoria);

        let stockHtml = '';
        if (v.usa_stock) {
            stockHtml = `<span class="badge ${v.stock_actual < 10 ? 'bg-danger text-white' : 'bg-info'} position-absolute" style="top: -5px; right: -5px; font-size: 0.75rem; padding: 4px 6px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.5);">${v.stock_actual}</span>`;
        }

        div.innerHTML = `
            ${stockHtml}
            <span class="fw-bold text-center text-warning" style="font-size: 0.85rem; line-height: 1.2; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">${v.nombre.toUpperCase()}</span>
        `;
        
        // Hover effect for better UX
        div.onmouseover = () => { div.style.background = '#FACC15'; div.querySelector('.text-warning').classList.replace('text-warning', 'text-dark'); };
        div.onmouseout = () => { div.style.background = '#1A1A1A'; div.querySelector('.text-dark').classList.replace('text-dark', 'text-warning'); };

        gridContainer.appendChild(div);
    });

    contenedor.appendChild(gridContainer);
}
// 2. Lógica para manejar el pedido
function agregarAlCarrito(id, nombre, precio, categoria) {
    const producto = todosLosProductos.find(p => p.id === id);
    const index = carrito.findIndex(item => item.id === id);
    const cantidadActual = index !== -1 ? carrito[index].cantidad : 0;

    if (producto && producto.usa_stock && cantidadActual + 1 > producto.stock_actual) {
        Swal.fire({icon: 'warning', title: 'Stock Insuficiente', text: `Solo hay ${producto.stock_actual} unidades disponibles.`, confirmButtonColor: '#FACC15'});
        return;
    }

    if (producto && producto.presas_requeridas > 0) {
        let presasUsadasEnCarrito = 0;
        carrito.forEach(item => {
            const p = todosLosProductos.find(x => x.id === item.id);
            if (p && p.presas_requeridas > 0) {
                presasUsadasEnCarrito += (item.cantidad * p.presas_requeridas);
            }
        });
        
        if (presasUsadasEnCarrito + producto.presas_requeridas > inventarioPresasCocidas) {
            // Nota: Es solo una advertencia, no bloquea la venta.
            Swal.fire({
                icon: 'warning', 
                title: 'Atención: Presas Insuficientes', 
                text: `El inventario registra solo ${inventarioPresasCocidas} presas cocidas. Se ha agregado al pedido, pero el inventario quedará en negativo.`, 
                confirmButtonColor: '#E62E2D',
                timer: 4000
            });
        }
    }

    if (index !== -1) {
        carrito[index].cantidad++;
    } else {
        carrito.push({
            id,
            nombre,
            precio,
            categoria, // Guardamos la categoría aquí
            cantidad: 1,
            observaciones: "",
            extras: []
        });
    }
    renderizarCarrito();
}

function cambiarCantidad(index, delta) {
    const item = carrito[index];
    const producto = todosLosProductos.find(p => p.id === item.id);

    if (delta > 0 && producto && producto.usa_stock && item.cantidad + delta > producto.stock_actual) {
        Swal.fire({icon: 'warning', title: 'Stock Insuficiente', text: `Solo hay ${producto.stock_actual} unidades disponibles.`, confirmButtonColor: '#FACC15'});
        return;
    }

    carrito[index].cantidad += delta;
    if (carrito[index].cantidad <= 0) {
        carrito.splice(index, 1);
    }
    renderizarCarrito();
}

async function cargarExtras() {
    const res = await fetch('/api/extras');
    listaExtrasDisponibles = await res.json();
}

function renderizarCarrito() {
    const lista = document.getElementById('lista-carrito');
    const totalTxt = document.getElementById('total-pedido');
    lista.innerHTML = '';
    let total = 0;

    if (carrito.length === 0) {
        lista.innerHTML = `<div class="empty-cart"><span class="icon">🍔</span><p>Agrega productos al pedido</p></div>`;
        totalTxt.innerText = "0.00 Bs.";
        return;
    }

    carrito.forEach((item, index) => {
        const precioExtras = item.extras.reduce((acc, e) => acc + e.precio, 0);
        const subtotal = (item.precio + precioExtras) * item.cantidad;
        total += subtotal;

        // REGLA: No permitir extras en bebidas
        const permiteExtras = item.categoria !== 'Sodas' && item.categoria !== 'Jugos';

        lista.innerHTML += `
            <div class="cart-item flex-column align-items-start py-2 border-bottom border-secondary">
                <div class="d-flex w-100 justify-content-between align-items-center">
                    <div class="cart-item-name">
                        <button class="btn btn-sm p-0 me-2" onclick="eliminarDelCarrito(${index})">🗑️</button>
                        <span class="text-white fw-bold">${item.nombre}</span>
                        <div class="text-warning small">${(item.precio + precioExtras).toFixed(2)} Bs.</div>
                    </div>
                    <div class="cart-qty">
                        <button class="qty-btn" onclick="cambiarCantidad(${index}, -1)">-</button>
                        <span class="qty-value text-white">${item.cantidad}</span>
                        <button class="qty-btn" onclick="cambiarCantidad(${index}, 1)">+</button>
                    </div>
                </div>

                
                    <input type="text" 
                        class="form-control form-control-sm bg-dark text-white border-secondary" 
                        style="font-size: 0.75rem; border-style: dashed;"
                        placeholder="📝 Nota: Sin cebolla, extra mayo..." 
                        value="${item.observaciones || ''}"
                        onchange="actualizarObservacion(${index}, this.value)">
                </div>
                
                <div class="extras-list w-100 mt-1">
                    ${item.extras.map((e, extraIdx) => `
                        <span class="badge bg-dark border border-warning text-warning me-1 mb-1 p-2" 
                              onclick="eliminarExtra(${index}, ${extraIdx})"
                              style="font-size: 0.7rem; cursor: pointer;">
                            + ${e.nombre} <span class="ms-1 text-danger">✕</span>
                        </span>
                    `).join('')}
                    
                    ${permiteExtras ? `
                        <button class="btn btn-link btn-sm text-warning p-0 d-block" onclick="abrirModalSalsas(${index})">
                            <small>✨ +Salsas/Extras</small>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    });
    totalTxt.innerText = `${total.toFixed(2)} Bs.`;
}

// 3. Finalizar Venta (Con Blindaje Anti Doble-Clic)
async function finalizarVenta() {
    if (carrito.length === 0) return Swal.fire({icon: 'warning', title: 'Aviso', text: 'El carrito está vacío', confirmButtonColor: '#FACC15'});

    // Si ya estamos procesando una venta, ignoramos los clics extra
    if (procesandoVenta) return;

    // Ponemos el candado
    procesandoVenta = true;

    // Bloqueamos el botón visualmente para que el cajero sepa que está cargando
    const btnCheckout = document.querySelector('.btn-checkout');
    const textoOriginal = btnCheckout.innerHTML;
    btnCheckout.innerHTML = "⏳ PROCESANDO...";
    btnCheckout.disabled = true;

    try {
        const metodo = document.getElementById('metodo-pago').value;

        const pedido = {
            metodo_pago: metodo,
            productos: carrito.map(i => ({
                id: i.id,
                cantidad: i.cantidad,
                observaciones: i.observaciones,
                extras: i.extras.map(e => e.id)
            }))
        };

        const res = await fetch('/api/venta/nueva', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pedido)
        });

        if (res.ok) {
            const data = await res.json();
            // Truco: Abrimos el PDF ANTES de la alerta para evitar bloqueos del navegador
            if (data.venta_id) window.open(`/api/venta/ticket/${data.venta_id}`, '_blank');

            // Damos una micro pausa antes de la alerta
            setTimeout(() => {
                Swal.fire({
                    icon: 'success',
                    title: '¡Éxito!',
                    text: `Venta registrada en ${metodo}. Pedido #${data.pedido_nro}`,
                    confirmButtonColor: '#FACC15'
                });
                carrito = [];
                renderizarCarrito();
                cargarProductos(); // Actualizar el stock en la pantalla
                cargarInventarioPresas(); // Actualizar inventario de presas en RAM
            }, 100);

        } else {
            const dataError = await res.json();
            Swal.fire({icon: 'error', title: 'Error', text: "Error del servidor: " + (dataError.error || "No se pudo registrar"), confirmButtonColor: '#FACC15'});
        }
    } catch (error) {
        console.error("Error en finalizarVenta:", error);
        Swal.fire({icon: 'error', title: 'Error', text: "Error de conexión con el servidor.", confirmButtonColor: '#FACC15'});
    } finally {
        // Pase lo que pase (éxito o error), quitamos el candado al final
        procesandoVenta = false;
        btnCheckout.innerHTML = textoOriginal;
        btnCheckout.disabled = false;
    }
}

async function verificarEstadoCaja() {
    const btn = document.getElementById('btn-estado-caja');
    if (!btn) return;

    try {
        const res = await fetch('/api/caja/estado');
        const data = await res.json();

        if (data.abierta) {
            // DISEÑO CAJA ABIERTA (Verde)
            btn.innerHTML = '🟢 CAJA ABIERTA';
            btn.style.backgroundColor = '#FACC15'; // Verde éxito
            btn.style.color = 'white';
            btn.style.border = 'none';
            // Cambiamos la acción para que no intente abrirla de nuevo
            btn.onclick = () => Swal.fire({icon: 'info', title: 'Aviso', text: 'La caja ya está abierta. Las ventas se están registrando.', confirmButtonColor: '#FACC15'});
        } else {
            // DISEÑO CAJA CERRADA (Amarillo/Rojo)
            btn.innerHTML = '🔴 ABRIR CAJA';
            btn.style.backgroundColor = 'var(--hb-yellow)';
            btn.style.color = 'black';
            btn.onclick = abrirCaja; // Restaura la función original
        }
    } catch (error) {
        console.error("Error al verificar la caja:", error);
    }
}

// 4. Utilidades
async function abrirCaja() {
    const { value: monto } = await Swal.fire({
        title: 'Abrir Caja',
        input: 'text',
        inputLabel: 'Monto inicial de caja (Efectivo físico):',
        inputValue: '100.00',
        showCancelButton: true,
        confirmButtonText: 'Abrir Caja',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#FACC15',
        cancelButtonColor: '#9CA3AF',
        inputValidator: (value) => {
            if (!value || isNaN(value)) {
                return 'Debes ingresar un monto válido';
            }
        }
    });

    if (!monto) return;

    const res = await fetch('/api/caja/abrir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monto_inicial: parseFloat(monto) })
    });

    const data = await res.json();
    if (res.ok) {
        Swal.fire({icon: 'success', title: '¡Éxito!', text: data.mensaje || "Caja abierta", confirmButtonColor: '#FACC15'});
    } else {
        Swal.fire({icon: 'error', title: 'Error', text: data.error || 'Error al abrir caja', confirmButtonColor: '#FACC15'});
    }

    // Alerta al botón para que cambie de color automáticamente
    verificarEstadoCaja();
}

function abrirModalSalsas(index) {
    itemIndexSeleccionado = index;
    const contIngredientes = document.getElementById('contenedor-ingredientes');
    const contSalsas = document.getElementById('contenedor-salsas');

    contIngredientes.innerHTML = '';
    contSalsas.innerHTML = '';

    listaExtrasDisponibles.forEach(extra => {
        // Creamos un diseño de "Mini-Card" para que sea más fácil de tocar/cliquear
        const htmlBotón = `
            <div class="col-6 col-md-4">
                <button class="btn btn-outline-warning w-100 py-3 h-100 d-flex flex-column align-items-center justify-content-center" 
                        onclick="sumarExtraAlItem(${extra.id})"
                        style="border-color: #242424; transition: 0.2s;">
                    <span class="small fw-bold text-white text-center" style="line-height: 1.1;">${extra.nombre}</span>
                    <span class="text-warning mt-1 fw-bold" style="font-size: 0.8rem;">+${extra.precio} Bs.</span>
                </button>
            </div>
        `;

        // Lógica de separación: Si es salsa va abajo, si no, arriba
        if (extra.nombre.toLowerCase().includes('salsa') ||
            extra.nombre.toLowerCase().includes('mayo') ||
            extra.nombre.toLowerCase().includes('ketchup') ||
            extra.nombre.toLowerCase().includes('mostaza')) {
            contSalsas.innerHTML += htmlBotón;
        } else {
            contIngredientes.innerHTML += htmlBotón;
        }
    });

    const modalSalsas = new bootstrap.Modal(document.getElementById('modalExtras'));
    modalSalsas.show();
}

function sumarExtraAlItem(extraId) {
    const extra = listaExtrasDisponibles.find(e => e.id === extraId);
    carrito[itemIndexSeleccionado].extras.push(extra);
    renderizarCarrito();
}

async function cargarExtras() {
    try {
        const res = await fetch('/api/extras');
        listaExtrasDisponibles = await res.json();
        console.log("Salsas cargadas:", listaExtrasDisponibles);
    } catch (error) {
        console.error("Error al cargar extras:", error);
    }
}

// 1. Eliminar un producto completo del carrito
async function eliminarDelCarrito(index) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: "¿Deseas eliminar este producto del pedido?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#E62E2D',
        cancelButtonColor: '#9CA3AF',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });
    
    if (result.isConfirmed) {
        carrito.splice(index, 1);
        renderizarCarrito();
    }
}

// 2. Eliminar un extra específico de un producto
function eliminarExtra(itemIndex, extraIndex) {
    // Eliminamos solo ese extra del array
    carrito[itemIndex].extras.splice(extraIndex, 1);
    renderizarCarrito();
}

function actualizarObservacion(index, texto) {
    // Guardamos la nota en el array para que se envíe al finalizar la venta
    carrito[index].observaciones = texto;
    console.log(`Nota guardada para ${carrito[index].nombre}: ${texto}`);
}

