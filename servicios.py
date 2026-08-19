# -*- coding: utf-8 -*-
"""Capa de logica: reglas de retiro, devolucion y consultas de inventario."""

from datetime import datetime

from db import conectar


class ErrorNegocio(Exception):
    """Error esperable que se le muestra al usuario tal cual."""


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


# ─── Consultas ───────────────────────────────────────────────────────────────

SQL_HERRAMIENTA = """
SELECT h.id, h.codigo, h.nombre, h.categoria, h.cantidad,
       h.cantidad - COALESCE((
           SELECT SUM(p.cantidad) FROM prestamos p
           WHERE p.herramienta_id = h.id AND p.devolucion_ts IS NULL
       ), 0) AS disponibles,
       (SELECT a.nombre FROM prestamos p JOIN alumnos a ON a.id = p.alumno_id
        WHERE p.herramienta_id = h.id ORDER BY p.retiro_ts DESC, p.id DESC LIMIT 1
       ) AS ultimo_usuario,
       (SELECT p.retiro_ts FROM prestamos p
        WHERE p.herramienta_id = h.id ORDER BY p.retiro_ts DESC, p.id DESC LIMIT 1
       ) AS ultimo_ts
FROM herramientas h
WHERE h.activo = 1
"""


def listar_herramientas():
    con = conectar()
    filas = con.execute(SQL_HERRAMIENTA + " ORDER BY h.nombre").fetchall()
    con.close()
    return [dict(f) for f in filas]


def buscar_herramienta(codigo):
    """Busca por codigo de barras exacto, o por nombre si no es un codigo."""
    con = conectar()
    fila = con.execute(
        SQL_HERRAMIENTA + " AND UPPER(h.codigo) = UPPER(?)", (codigo.strip(),)
    ).fetchone()
    con.close()
    if not fila:
        raise ErrorNegocio(f"No existe ninguna herramienta con el codigo {codigo}")
    return dict(fila)


def quien_tiene(herramienta_id):
    """Prestamos abiertos de una herramienta: quien la tiene ahora."""
    con = conectar()
    filas = con.execute(
        """SELECT p.id, p.cantidad, p.retiro_ts, a.nombre, a.division, a.dni
           FROM prestamos p JOIN alumnos a ON a.id = p.alumno_id
           WHERE p.herramienta_id = ? AND p.devolucion_ts IS NULL
           ORDER BY p.retiro_ts""",
        (herramienta_id,),
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def listar_alumnos(busqueda=""):
    con = conectar()
    if busqueda.strip():
        patron = f"%{busqueda.strip()}%"
        filas = con.execute(
            """SELECT id, dni, division, nombre FROM alumnos
               WHERE activo = 1 AND (nombre LIKE ? OR dni LIKE ?)
               ORDER BY division, nombre LIMIT 40""",
            (patron, patron),
        ).fetchall()
    else:
        filas = con.execute(
            "SELECT id, dni, division, nombre FROM alumnos WHERE activo = 1 "
            "ORDER BY division, nombre"
        ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def buscar_alumno_por_dni(dni):
    """Busca un alumno por DNI exacto, ignorando puntos y espacios."""
    limpio = "".join(c for c in str(dni) if c.isdigit())
    if len(limpio) < 7:
        raise ErrorNegocio("El DNI tiene que tener al menos 7 digitos")

    con = conectar()
    fila = con.execute(
        "SELECT id, dni, division, nombre FROM alumnos WHERE dni = ? AND activo = 1",
        (limpio,),
    ).fetchone()
    con.close()
    if not fila:
        raise ErrorNegocio(f"No hay ningun alumno con el DNI {limpio}")
    return dict(fila)


def historial(limite=200):
    con = conectar()
    filas = con.execute(
        """SELECT p.id, p.cantidad, p.retiro_ts, p.devolucion_ts, p.observacion,
                  h.nombre AS herramienta, h.codigo,
                  a.nombre AS alumno, a.division, a.dni
           FROM prestamos p
           JOIN herramientas h ON h.id = p.herramienta_id
           JOIN alumnos a ON a.id = p.alumno_id
           ORDER BY COALESCE(p.devolucion_ts, p.retiro_ts) DESC, p.id DESC
           LIMIT ?""",
        (limite,),
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def resumen():
    con = conectar()
    tot = con.execute(
        "SELECT COALESCE(SUM(cantidad),0) FROM herramientas WHERE activo = 1"
    ).fetchone()[0]
    fuera = con.execute(
        "SELECT COALESCE(SUM(cantidad),0) FROM prestamos WHERE devolucion_ts IS NULL"
    ).fetchone()[0]
    hoy = datetime.now().strftime("%Y-%m-%d")
    movs = con.execute(
        "SELECT COUNT(*) FROM prestamos WHERE retiro_ts LIKE ? OR devolucion_ts LIKE ?",
        (f"{hoy}%", f"{hoy}%"),
    ).fetchone()[0]
    tipos = con.execute(
        "SELECT COUNT(*) FROM herramientas WHERE activo = 1"
    ).fetchone()[0]
    con.close()
    return {
        "total": tot,
        "fuera": fuera,
        "disponibles": tot - fuera,
        "movimientos_hoy": movs,
        "tipos": tipos,
    }


# ─── Operaciones ─────────────────────────────────────────────────────────────

def registrar_retiro(codigo, alumno_id, cantidad=1, observacion=None):
    herr = buscar_herramienta(codigo)
    if cantidad < 1:
        raise ErrorNegocio("La cantidad tiene que ser 1 o mas")
    if cantidad > herr["disponibles"]:
        raise ErrorNegocio(
            f"Solo quedan {herr['disponibles']} de {herr['nombre']} "
            f"(pediste {cantidad})"
        )

    con = conectar()
    alumno = con.execute(
        "SELECT nombre FROM alumnos WHERE id = ? AND activo = 1", (alumno_id,)
    ).fetchone()
    if not alumno:
        con.close()
        raise ErrorNegocio("El alumno seleccionado no existe")

    con.execute(
        """INSERT INTO prestamos (herramienta_id, alumno_id, cantidad, retiro_ts, observacion)
           VALUES (?,?,?,?,?)""",
        (herr["id"], alumno_id, cantidad, _ahora(), observacion),
    )
    con.commit()
    con.close()
    return {
        "herramienta": herr["nombre"],
        "codigo": herr["codigo"],
        "alumno": alumno["nombre"],
        "cantidad": cantidad,
        "restantes": herr["disponibles"] - cantidad,
    }


def registrar_devolucion(prestamo_id, devuelto_por_id=None, observacion=None):
    con = conectar()
    fila = con.execute(
        """SELECT p.id, p.cantidad, p.devolucion_ts, h.nombre AS herramienta,
                  a.nombre AS alumno
           FROM prestamos p
           JOIN herramientas h ON h.id = p.herramienta_id
           JOIN alumnos a ON a.id = p.alumno_id
           WHERE p.id = ?""",
        (prestamo_id,),
    ).fetchone()
    if not fila:
        con.close()
        raise ErrorNegocio("No se encontro ese prestamo")
    if fila["devolucion_ts"]:
        con.close()
        raise ErrorNegocio("Esa herramienta ya figura devuelta")

    con.execute(
        """UPDATE prestamos
           SET devolucion_ts = ?, devuelto_por_id = ?,
               observacion = COALESCE(?, observacion)
           WHERE id = ?""",
        (_ahora(), devuelto_por_id, observacion, prestamo_id),
    )
    con.commit()
    con.close()
    return {
        "herramienta": fila["herramienta"],
        "alumno": fila["alumno"],
        "cantidad": fila["cantidad"],
    }


# ─── ABM basico ──────────────────────────────────────────────────────────────

def alta_herramienta(nombre, categoria, cantidad):
    con = conectar()
    ultimo = con.execute(
        "SELECT codigo FROM herramientas WHERE codigo LIKE 'HER-%' "
        "ORDER BY codigo DESC LIMIT 1"
    ).fetchone()
    siguiente = int(ultimo["codigo"].split("-")[1]) + 1 if ultimo else 1
    codigo = f"HER-{siguiente:03d}"
    con.execute(
        "INSERT INTO herramientas (codigo, nombre, categoria, cantidad) VALUES (?,?,?,?)",
        (codigo, nombre.strip(), categoria.strip() or "Otros", int(cantidad)),
    )
    con.commit()
    con.close()
    return {"codigo": codigo, "nombre": nombre}


def editar_cantidad(herramienta_id, cantidad):
    prestados = sum(p["cantidad"] for p in quien_tiene(herramienta_id))
    if cantidad < prestados:
        raise ErrorNegocio(
            f"No podes bajar a {cantidad}: hay {prestados} prestadas sin devolver"
        )
    con = conectar()
    con.execute(
        "UPDATE herramientas SET cantidad = ? WHERE id = ?", (int(cantidad), herramienta_id)
    )
    con.commit()
    con.close()


def alta_alumno(nombre, division, dni):
    limpio = "".join(c for c in str(dni) if c.isdigit())
    if len(limpio) < 7:
        raise ErrorNegocio("El DNI tiene que tener al menos 7 digitos")

    con = conectar()
    if con.execute("SELECT 1 FROM alumnos WHERE dni = ?", (limpio,)).fetchone():
        con.close()
        raise ErrorNegocio(f"Ya existe un alumno con el DNI {limpio}")
    con.execute(
        "INSERT INTO alumnos (dni, division, nombre) VALUES (?,?,?)",
        (limpio, division.strip(), nombre.strip()),
    )
    con.commit()
    con.close()
    return {"dni": limpio, "nombre": nombre.strip()}
