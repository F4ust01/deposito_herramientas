# -*- coding: utf-8 -*-
"""Capa de datos: conexion a SQLite y creacion del esquema."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "deposito.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS alumnos (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    dni      TEXT NOT NULL UNIQUE,
    division TEXT NOT NULL,
    nombre   TEXT NOT NULL,
    activo   INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS ix_alumnos_dni ON alumnos(dni);

CREATE TABLE IF NOT EXISTS herramientas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo    TEXT NOT NULL UNIQUE,
    nombre    TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'Otros',
    cantidad  INTEGER NOT NULL DEFAULT 1,
    activo    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS prestamos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    herramienta_id  INTEGER NOT NULL REFERENCES herramientas(id),
    alumno_id       INTEGER NOT NULL REFERENCES alumnos(id),
    cantidad        INTEGER NOT NULL DEFAULT 1,
    retiro_ts       TEXT NOT NULL,
    devolucion_ts   TEXT,
    devuelto_por_id INTEGER REFERENCES alumnos(id),
    observacion     TEXT
);

CREATE INDEX IF NOT EXISTS ix_prestamos_abiertos
    ON prestamos(herramienta_id, devolucion_ts);
CREATE INDEX IF NOT EXISTS ix_prestamos_alumno
    ON prestamos(alumno_id);
CREATE INDEX IF NOT EXISTS ix_prestamos_retiro
    ON prestamos(retiro_ts DESC);
"""


def conectar():
    """Devuelve una conexion con filas accesibles por nombre de columna."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar():
    """Crea las tablas si no existen y carga los datos iniciales una sola vez."""
    from seed_data import HERRAMIENTAS, ALUMNOS

    con = conectar()
    con.executescript(ESQUEMA)

    if con.execute("SELECT COUNT(*) FROM herramientas").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO herramientas (codigo, nombre, categoria, cantidad) VALUES (?,?,?,?)",
            HERRAMIENTAS,
        )
        print(f"  [seed] {len(HERRAMIENTAS)} herramientas cargadas")

    # Los alumnos se sincronizan en cada arranque contra el .env:
    # si agregas o corregis una linea ahi, se refleja sin borrar la base.
    for division, nombre, dni in ALUMNOS:
        con.execute(
            """INSERT INTO alumnos (dni, division, nombre) VALUES (?,?,?)
               ON CONFLICT(dni) DO UPDATE SET
                   division = excluded.division,
                   nombre   = excluded.nombre,
                   activo   = 1""",
            (dni, division, nombre),
        )
    print(f"  [seed] {len(ALUMNOS)} alumnos sincronizados desde .env")

    con.commit()
    con.close()
