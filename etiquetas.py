# -*- coding: utf-8 -*-
"""Genera una hoja imprimible con los codigos de barras Code128 de cada herramienta.

Se abre desde el navegador (/etiquetas) y se imprime con Ctrl+P.
Una etiqueta por unidad fisica: si hay 3 alargues, salen 3 etiquetas iguales.
"""

from html import escape

import barcode
from barcode.writer import SVGWriter

PLANTILLA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Etiquetas - Deposito de Herramientas</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, Helvetica, sans-serif; background: #f4f4f4;
          padding: 16px; color: #111; }}
  .barra {{ background: #111; color: #fff; padding: 14px 18px; border-radius: 4px;
            margin-bottom: 16px; display: flex; justify-content: space-between;
            align-items: center; flex-wrap: wrap; gap: 10px; }}
  .barra h1 {{ font-size: 17px; letter-spacing: 1px; }}
  .barra p {{ font-size: 12px; color: #bbb; margin-top: 3px; }}
  .btn {{ background: #f97316; color: #000; border: none; padding: 9px 18px;
          border-radius: 3px; font-size: 13px; font-weight: bold; cursor: pointer; }}
  .grilla {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
  .etiqueta {{ background: #fff; border: 1px dashed #999; border-radius: 3px;
               padding: 8px 6px; text-align: center; break-inside: avoid; }}
  .etiqueta .nombre {{ font-size: 11px; font-weight: bold; margin-bottom: 2px;
                       white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .etiqueta .cat {{ font-size: 8px; color: #666; text-transform: uppercase;
                    letter-spacing: 0.5px; margin-bottom: 4px; }}
  .etiqueta svg {{ width: 100%; height: auto; max-height: 44px; }}
  .etiqueta .cod {{ font-family: monospace; font-size: 10px; letter-spacing: 1px;
                    margin-top: 2px; }}
  .unidad {{ font-size: 8px; color: #888; }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .barra {{ display: none; }}
    .grilla {{ grid-template-columns: repeat(4, 1fr); gap: 4px; }}
    .etiqueta {{ border: 1px dashed #bbb; }}
  }}
</style></head>
<body>
  <div class="barra">
    <div>
      <h1>ETIQUETAS DE HERRAMIENTAS</h1>
      <p>{total} etiquetas &middot; Imprimi, recorta y pega una en cada herramienta.
         Ideal en papel autoadhesivo, cubierto con cinta transparente.</p>
    </div>
    <button class="btn" onclick="window.print()">IMPRIMIR</button>
  </div>
  <div class="grilla">{etiquetas}</div>
</body></html>
"""


def _svg(codigo):
    """Devuelve el SVG del codigo de barras, sin cabecera XML ni texto propio."""
    escritor = SVGWriter()
    generado = barcode.get("code128", codigo, writer=escritor)
    crudo = generado.render(
        {"module_height": 9.0, "module_width": 0.28, "quiet_zone": 2.0,
         "write_text": False, "background": "white", "foreground": "black"}
    ).decode("utf-8")
    return crudo[crudo.index("<svg"):]


def hoja_html(herramientas):
    partes = []
    for h in herramientas:
        svg = _svg(h["codigo"])
        for n in range(h["cantidad"]):
            unidad = (
                f'<div class="unidad">unidad {n + 1} de {h["cantidad"]}</div>'
                if h["cantidad"] > 1 else ""
            )
            partes.append(
                f'<div class="etiqueta">'
                f'<div class="nombre">{escape(h["nombre"])}</div>'
                f'<div class="cat">{escape(h["categoria"])}</div>'
                f'{svg}'
                f'<div class="cod">{h["codigo"]}</div>{unidad}</div>'
            )
    return PLANTILLA.format(total=len(partes), etiquetas="".join(partes))
