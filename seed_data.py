# -*- coding: utf-8 -*-
"""Datos iniciales.

El catalogo de herramientas vive aca (no es informacion sensible).
La lista de alumnos se lee del archivo .env, que NO se versiona en git
porque contiene nombres y DNI.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


HERRAMIENTAS = [
    ('HER-001', 'Máscara de soldar', 'Soldadura', 2),
    ('HER-002', 'Soldadora', 'Soldadura', 2),
    ('HER-003', 'Alargue', 'Eléctrica', 3),
    ('HER-004', 'Amoladora', 'Eléctrica', 2),
    ('HER-005', 'Taladro', 'Eléctrica', 1),
    ('HER-006', 'Taladro eléctrico', 'Eléctrica', 1),
    ('HER-007', 'Metro', 'Medición', 5),
    ('HER-008', 'Llave fija 6', 'Llaves', 1),
    ('HER-009', 'Llave fija 7', 'Llaves', 1),
    ('HER-010', 'Llave fija 8', 'Llaves', 1),
    ('HER-011', 'Llave fija 9', 'Llaves', 1),
    ('HER-012', 'Llave fija 10', 'Llaves', 1),
    ('HER-013', 'Llave fija 13', 'Llaves', 1),
    ('HER-014', 'Llave fija 14', 'Llaves', 1),
    ('HER-015', 'Llave fija 19', 'Llaves', 1),
    ('HER-016', 'Llave fija 22', 'Llaves', 1),
    ('HER-017', 'Llave fija 12', 'Llaves', 2),
    ('HER-018', 'Llave Allen 1.5', 'Llaves', 1),
    ('HER-019', 'Llave Allen 2', 'Llaves', 1),
    ('HER-020', 'Llave Allen 3', 'Llaves', 1),
    ('HER-021', 'Llave Allen 4', 'Llaves', 1),
    ('HER-022', 'Llave Allen 5', 'Llaves', 1),
    ('HER-023', 'Llave Allen 5.5', 'Llaves', 1),
    ('HER-024', 'Llave Allen 6', 'Llaves', 1),
    ('HER-025', 'Cepillo de acero', 'Manual', 1),
    ('HER-026', 'Alicate', 'Manual', 5),
    ('HER-027', 'Pinza', 'Manual', 4),
    ('HER-028', 'Llave francesa', 'Llaves', 1),
    ('HER-029', 'Trincheta', 'Corte', 1),
    ('HER-030', 'Cinta aisladora', 'Eléctrica', 1),
    ('HER-031', 'Cerruchito', 'Corte', 1),
    ('HER-032', 'Destornillador Philips', 'Manual', 6),
    ('HER-033', 'Destornillador punta plana', 'Manual', 6),
    ('HER-034', 'Buscapolos', 'Eléctrica', 1),
    ('HER-035', 'Escalera', 'Otros', 1),
    ('HER-036', 'Martillo', 'Manual', 1),
    ('HER-037', 'Pala', 'Otros', 1),
    ('HER-038', 'Remachadora', 'Manual', 1),
    ('HER-039', 'Sargento', 'Manual', 1),
    ('HER-040', 'Machete', 'Corte', 2),
]


def cargar_alumnos():
    """Lee los alumnos del .env. Formato por linea: DIVISION|APELLIDO, NOMBRE|DNI"""
    crudo = os.getenv("ALUMNOS", "").strip()
    if not crudo:
        raise SystemExit(
            "\n  FALTA EL ARCHIVO .env\n"
            "  Copia .env.example como .env y carga la lista de alumnos.\n"
        )

    alumnos = []
    for numero, linea in enumerate(crudo.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split("|")]
        if len(partes) != 3:
            raise SystemExit(f"  Linea {numero} del .env mal formada: {linea!r}")
        division, nombre, dni = partes
        dni = "".join(c for c in dni if c.isdigit())
        alumnos.append((division, nombre, dni))

    duplicados = {d for _, _, d in alumnos if [x[2] for x in alumnos].count(d) > 1}
    if duplicados:
        raise SystemExit(f"  DNI repetidos en el .env: {', '.join(sorted(duplicados))}")

    return alumnos


ALUMNOS = cargar_alumnos()
