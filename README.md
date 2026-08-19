# 🔧 Depósito de Herramientas — E.P.E.T. N°9

> Laguna Blanca, Formosa

Sistema de control de préstamos para el depósito de un colegio técnico. Registra quién retiró cada herramienta, quién la tiene actualmente y quién fue el último en llevarla.

Corre completamente **offline en una notebook**, sin hosting ni internet. Se opera desde el navegador con un lector de código de barras USB.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python · FastAPI · Uvicorn |
| Base de datos | SQLite (archivo local `deposito.db`) |
| Frontend | HTML + CSS + JS puro (sin frameworks, sin npm) |
| Códigos de barras | python-barcode (Code128) |

---

## Estructura

```
deposito-herramientas/
├── app.py           # Servidor web: rutas REST y servido del front
├── servicios.py     # Lógica de negocio: retiros, devoluciones, inventario
├── db.py            # Conexión SQLite y creación del esquema
├── etiquetas.py     # Generador de hoja imprimible con códigos de barras
├── seed_data.py     # Datos iniciales: herramientas y alumnos
├── requirements.txt
├── INICIAR.bat      # Lanzador Windows (doble clic)
├── iniciar.sh       # Lanzador Linux/Mac
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Instalación y uso

### Requisitos
- Python 3.10 o superior
- Cualquier lector USB de código de barras (funcionan como teclado, sin driver)

### Windows
```
Doble clic en INICIAR.bat
```
La primera vez instala las dependencias automáticamente (~1-2 min). Luego abre el navegador solo.

### Linux / Mac
```bash
chmod +x iniciar.sh
./iniciar.sh
```

### Manual
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Acceder en `http://localhost:8000`

---

## Base de datos

Se crea automáticamente como `deposito.db` en la misma carpeta al primer arranque. Para hacer backup alcanza con copiar ese archivo.

**Datos iniciales cargados:**
- 40 tipos de herramienta · 68 unidades totales
- 53 alumnos (7° año — divisiones I, II y III)

### ⚠️ Configuración obligatoria: archivo `.env`

Los nombres y DNI de los alumnos **no están en el repositorio** por ser datos
personales. Antes del primer arranque hay que crear el archivo `.env`:

```bash
cp .env.example .env
```

Y completarlo con una línea por alumno:

```
ALUMNOS="
7 I|Apellido, Nombre|12345678
7 II|Otro Apellido, Otro Nombre|23456789
"
```

Los DNI se normalizan solos (se ignoran puntos y espacios). Si hay un DNI
repetido, la app avisa y no arranca.

La lista se **sincroniza en cada arranque**: si agregás o corregís una línea
del `.env`, se refleja en la base sin perder el historial de préstamos.

---

## Funcionalidades

### Retiro
1. Escanear código de barras de la herramienta
2. Ingresar el DNI del alumno (acepta con o sin puntos)
3. Confirmar (con cantidad opcional si hay varias unidades)

Si el alumno no recuerda su DNI, hay un desplegable para buscarlo por apellido.

### Devolución
1. Escanear código de barras de la herramienta
2. Elegir el préstamo abierto a cerrar

### Inventario
- Vista de todas las herramientas con disponibilidad en tiempo real
- Filtros por categoría y estado
- Buscador por nombre o código

### Historial
- Todos los movimientos ordenados por fecha
- Filtrable por alumno o herramienta

### Etiquetas
- Ajustes → **Abrir hoja de etiquetas**
- Genera una página con los códigos de barras de todas las herramientas lista para imprimir
- Imprimir en papel autoadhesivo, recortar, pegar en cada herramienta y cubrir con cinta transparente

### Ajustes
- Alta de herramientas nuevas
- Alta de alumnos nuevos

---

## Lector de código de barras

Cualquier lector USB HID (los comunes de supermercado) funciona sin configuración: se enchufan y el sistema operativo los reconoce como teclado. El front captura la lectura automáticamente desde cualquier pantalla — no hace falta que el cursor esté en ningún campo en particular.

Para verificar que funciona: abrir el Bloc de notas y pasar el lector por una etiqueta. Si escribe caracteres y manda Enter, está listo.

---

## API

Documentación interactiva disponible en `http://localhost:8000/api/docs` mientras el servidor está corriendo.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/resumen` | Totales del panel principal |
| GET | `/api/herramientas` | Listado completo con disponibilidad |
| GET | `/api/herramientas/{codigo}` | Detalle + préstamos abiertos |
| POST | `/api/retiros` | Registrar retiro |
| POST | `/api/devoluciones` | Registrar devolución |
| GET | `/api/alumnos?q=` | Buscar alumnos por nombre o DNI |
| GET | `/api/alumnos/dni/{dni}` | Buscar alumno por DNI exacto |
| POST | `/api/alumnos` | Alta de alumno |
| POST | `/api/herramientas` | Alta de herramienta |
| GET | `/etiquetas` | Hoja imprimible de etiquetas |

---

## Seguridad de datos

Este repositorio es público, por lo que:

- `.env` está en `.gitignore` — **nunca** se sube
- `deposito.db` está en `.gitignore` — contiene el historial real
- `.env.example` sí se versiona, pero solo con datos de ejemplo

Antes de cada push conviene verificar:
```bash
git status --ignored | grep -E "\.env$|\.db$"
```
