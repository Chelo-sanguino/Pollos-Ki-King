# Sistema de Ventas: Pollos Ki-King 🍗

Este es el sistema de punto de venta y administración para Pollos Ki-King, construido con Python (Flask) en el backend y HTML/JS/Bootstrap en el frontend.

## 🚀 Guía de Instalación en un Equipo Nuevo

El sistema está preparado para ejecutarse utilizando **Docker**, lo que hace que la instalación sea rápida y no requiera configurar Python o MySQL manualmente.

### Paso 1: Requisitos Previos
1. Descarga e instala **[Git](https://git-scm.com/downloads)** (para poder descargar el código).
2. Descarga e instala **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**.
   - *Nota: Asegúrate de que Docker Desktop esté abierto y ejecutándose en tu computadora antes del siguiente paso.*

### Paso 2: Descargar el Código
Abre una terminal (Símbolo del sistema o PowerShell) y clona el repositorio desde GitHub:
```bash
git clone https://github.com/Chelo-sanguino/Pollos-Ki-King.git
```
Luego entra a la carpeta que se acaba de descargar:
```bash
cd Pollos-Ki-King
```

### Paso 3: Levantar el Sistema
Una vez dentro de la carpeta `Pollos-Ki-King`, ejecuta el siguiente comando para construir y arrancar el servidor web y la base de datos MySQL:
```bash
docker-compose up -d --build
```
*Este proceso puede tardar un par de minutos la primera vez, ya que descargará las imágenes de Python y MySQL.*

### Paso 4: Inicializar la Base de Datos (Solo la primera vez)
Para crear las tablas iniciales y el inventario en la base de datos, ejecuta este comando:
```bash
docker-compose exec web python backend/init_db.py
```
*(Opcional)* Si deseas cargar el menú base y los extras iniciales, también puedes ejecutar:
```bash
docker-compose exec web python backend/seed_menu.py
docker-compose exec web python backend/seed_extras.py
```

### Paso 5: ¡Listo para Usar!
Abre tu navegador web (Google Chrome, Edge, etc.) y visita:
👉 **[http://localhost:5005](http://localhost:5005)**

- Para ver la pantalla de **Punto de Venta (POS)**, usa la página principal.
- Para entrar al **Panel de Administración** y configurar productos, precios o inventario, haz clic en el botón de configuración o ve a `http://localhost:5005/admin`.

---

## 🛑 Cómo Apagar el Sistema
Si deseas apagar el servidor, abre tu terminal en la carpeta del proyecto y ejecuta:
```bash
docker-compose down
```
*(Tus datos de ventas e inventario no se perderán, están guardados de forma segura en un volumen de Docker).*
