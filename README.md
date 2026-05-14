# 🏃‍♂️ SportZoom – Plataforma de E-commerce para Calzado Deportivo

## 📋 Descripción

SportZoom es una plataforma web desarrollada para facilitar la venta de calzado deportivo y apoyar la digitalización de pequeños y medianos negocios en Colombia. El proyecto integra gestión de catálogo, inventario, carrito de compras y un panel administrativo completo.

### Contexto del Problema

Hoy en día, vender calzado en Colombia no es tan sencillo, sobre todo para los pequeños y medianos negocios que quieren competir con las grandes marcas. Abrir una tienda física es costoso, la visibilidad en internet es limitada y manejar el inventario puede ser difícil. Todo esto hace que se pierdan oportunidades de venta y que muchos emprendimientos no puedan crecer como deberían.

**SportZoom** busca resolver estos problemas ofreciendo una solución digital accesible que integra ventas en línea, gestión de inventario y procesamiento de pagos en una sola plataforma.

---

# ✨ Características Principales

## Para Compradores

- 🛍️ Catálogo organizado con filtros por marca, talla y precio
- 🔍 Búsqueda avanzada de productos
- 🛒 Carrito de compras intuitivo
- 💳 Checkout simplificado con simulación de pago
- 📧 Confirmación por email con detalles del pedido
- 📦 Consulta de pedidos mediante código único

## Para Administradores

- ➕ CRUD completo de productos
- 📊 Gestión de inventario en tiempo real
- 🏷️ Organización por marcas y tallas
- 🔐 Autenticación JWT segura
- 👤 Panel administrativo dedicado

---

# 🛠️ Tecnologías Utilizadas

## Backend

- Django 5.2.6
- Django REST Framework 3.16.1
- PostgreSQL (Supabase)
- Supabase Storage
- JWT
- Pillow
- django-cors-headers

## Frontend

- Angular 20
- Tailwind CSS 3.4
- RxJS
- EmailJS
- jsPDF

## Herramientas

- Git / GitHub
- GitKraken
- Python venv
- Node.js npm

---

# 📦 Instalación y Configuración

## Prerrequisitos

- Python 3.8+
- Node.js 18+
- npm
- Git
- Cuenta en Supabase

---

# 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/ProyectoIntegrado-SportZoom-2025.git
cd ProyectoIntegrado-SportZoom-2025
```

---

# 2️⃣ Configurar Backend (Django)

## Entrar al backend

```bash
cd backend
```

---

## Crear entorno virtual

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Configurar variables de entorno (.env)

Crear un archivo llamado `.env` dentro de la carpeta `backend`.

Contenido:

```env
SECRET_KEY=tu-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql://USUARIO:PASSWORD@HOST:6543/postgres

SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SERVICE_KEY=TU_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=Productos

FRONTEND_URL=http://localhost:4200
MP_ACCESS_TOKEN=
```

⚠️ El archivo `.env` NO debe subirse a GitHub.

Cada integrante del equipo debe copiar manualmente el `.env` en su entorno local.

---

# Configuración de Supabase

El proyecto utiliza:

- Supabase PostgreSQL como base de datos principal
- Supabase Storage para almacenar imágenes de productos

Todos los desarrolladores trabajan sobre la misma base de datos cloud mediante `DATABASE_URL`.

---

# Aplicar migraciones

```bash
python manage.py migrate
```

---

# Crear superusuario

```bash
python manage.py createsuperuser
```

---

# Ejecutar backend

```bash
python manage.py runserver
```

Backend disponible en:

```text
http://localhost:8000
```

---

# 3️⃣ Configurar Frontend (Angular)

Abrir una nueva terminal:

```bash
cd frontend
```

---

# Instalar dependencias frontend

```bash
npm install
```

---

# Ejecutar frontend

```bash
npm start
```

o:

```bash
ng serve
```

Frontend disponible en:

```text
http://localhost:4200
```

---

# 🚀 Uso del Sistema

## Usuario Comprador

1. Acceder a:
   ```
   http://localhost:4200
   ```

2. Navegar por productos

3. Agregar productos al carrito

4. Realizar checkout

5. Consultar pedidos mediante código

---

## Administrador

1. Acceder a:
   ```
   http://localhost:4200/login
   ```

2. Iniciar sesión con superusuario

3. Gestionar productos e inventario

---

# 📂 Estructura del Proyecto

```text
ProyectoIntegrado-SportZoom-2025/
├── backend/
│   ├── config/
│   ├── tienda/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── angular.json
│
└── README.md
```

---

# 👥 Equipo de Desarrollo

- Max Daniel Pérez Quintero
- Santiago Villegas Naranjo
- Ricardo Medina Herrera

---

# 📄 Licencia

Proyecto académico desarrollado para la Universidad de Antioquia.
