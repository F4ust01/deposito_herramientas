# -*- coding: utf-8 -*-
"""Capa web: API REST + servido del front. Punto de entrada de la aplicacion."""

import webbrowser
from pathlib import Path
from threading import Timer

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
import etiquetas
import servicios
from servicios import ErrorNegocio

BASE = Path(__file__).parent
PUERTO = 8000

@asynccontextmanager
async def ciclo_de_vida(_app):
    db.inicializar()
    yield


app = FastAPI(
    title="Deposito de Herramientas",
    docs_url="/api/docs",
    lifespan=ciclo_de_vida,
)


# ─── Modelos de entrada ──────────────────────────────────────────────────────

class RetiroIn(BaseModel):
    codigo: str
    alumno_id: int
    cantidad: int = 1
    observacion: str | None = None


class DevolucionIn(BaseModel):
    prestamo_id: int
    devuelto_por_id: int | None = None
    observacion: str | None = None


class HerramientaIn(BaseModel):
    nombre: str
    categoria: str = "Otros"
    cantidad: int = 1


class CantidadIn(BaseModel):
    cantidad: int


class AlumnoIn(BaseModel):
    nombre: str
    division: str
    dni: str


# ─── API ─────────────────────────────────────────────────────────────────────

@app.get("/api/resumen")
def api_resumen():
    return servicios.resumen()


@app.get("/api/herramientas")
def api_herramientas():
    return servicios.listar_herramientas()


@app.get("/api/herramientas/{codigo}")
def api_herramienta(codigo: str):
    try:
        herr = servicios.buscar_herramienta(codigo)
    except ErrorNegocio as e:
        raise HTTPException(404, str(e))
    herr["prestamos"] = servicios.quien_tiene(herr["id"])
    return herr


@app.get("/api/alumnos")
def api_alumnos(q: str = ""):
    return servicios.listar_alumnos(q)


@app.get("/api/alumnos/dni/{dni}")
def api_alumno_por_dni(dni: str):
    try:
        return servicios.buscar_alumno_por_dni(dni)
    except ErrorNegocio as e:
        raise HTTPException(404, str(e))


@app.get("/api/historial")
def api_historial(limite: int = 200):
    return servicios.historial(limite)


@app.post("/api/retiros")
def api_retiro(datos: RetiroIn):
    try:
        return servicios.registrar_retiro(
            datos.codigo, datos.alumno_id, datos.cantidad, datos.observacion
        )
    except ErrorNegocio as e:
        raise HTTPException(400, str(e))


@app.post("/api/devoluciones")
def api_devolucion(datos: DevolucionIn):
    try:
        return servicios.registrar_devolucion(
            datos.prestamo_id, datos.devuelto_por_id, datos.observacion
        )
    except ErrorNegocio as e:
        raise HTTPException(400, str(e))


@app.post("/api/herramientas")
def api_alta_herramienta(datos: HerramientaIn):
    return servicios.alta_herramienta(datos.nombre, datos.categoria, datos.cantidad)


@app.put("/api/herramientas/{herramienta_id}/cantidad")
def api_editar_cantidad(herramienta_id: int, datos: CantidadIn):
    try:
        servicios.editar_cantidad(herramienta_id, datos.cantidad)
    except ErrorNegocio as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/alumnos")
def api_alta_alumno(datos: AlumnoIn):
    try:
        return servicios.alta_alumno(datos.nombre, datos.division, datos.dni)
    except ErrorNegocio as e:
        raise HTTPException(400, str(e))


@app.get("/etiquetas", response_class=HTMLResponse)
def api_etiquetas():
    """Hoja imprimible con los codigos de barras de todas las herramientas."""
    return etiquetas.hoja_html(servicios.listar_herramientas())


# ─── Front ───────────────────────────────────────────────────────────────────

if not (BASE / "static").is_dir():
    raise SystemExit(
        "\n  FALTA LA CARPETA 'static'\n\n"
        f"  Deberia estar en: {BASE / 'static'}\n"
        "  y contener: index.html, app.js, style.css, escudo.png\n\n"
        "  Si esos archivos quedaron sueltos junto a app.py, crea una\n"
        "  carpeta llamada 'static' y movelos adentro.\n"
    )

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def raiz():
    return FileResponse(BASE / "static" / "index.html")


def _abrir_navegador():
    webbrowser.open(f"http://localhost:{PUERTO}")


if __name__ == "__main__":
    import socket

    import uvicorn

    ip = socket.gethostbyname(socket.gethostname())
    print("\n" + "=" * 52)
    print("  DEPOSITO DE HERRAMIENTAS")
    print("=" * 52)
    print(f"  En esta notebook : http://localhost:{PUERTO}")
    print(f"  Desde el celular : http://{ip}:{PUERTO}  (misma red wifi)")
    print("\n  Para cerrar: Ctrl+C  o  cerra esta ventana")
    print("=" * 52 + "\n")
    Timer(1.5, _abrir_navegador).start()
    uvicorn.run(app, host="0.0.0.0", port=PUERTO, log_level="warning")
