"""Lee datos/movies.csv, valida los datos y genera public/index.html.

Uso:
    python -m unittest discover -v
    python analizar.py

Solo usa la biblioteca estándar de Python 3.12. No descarga nada: el informe
siempre se genera con el CSV que está en el repositorio.
"""
import csv
import html
import math
import os
import sys
from datetime import datetime, timezone

ESTUDIANTE = "AMIRA"  # <-- pon aquí tu nombre completo
TITULO = "Cine: taquilla histórica de 1794 películas"
RUTA_CSV = os.path.join("datos", "movies.csv")
RUTA_SALIDA = os.path.join("public", "index.html")
COLUMNAS_OBLIGATORIAS = ["imdb", "title", "year", "budget", "domgross"]
FALTANTES = {"", "NA", "#N/A"}  # el CSV original usa #N/A además de NA

FUENTE_URL = "https://github.com/fivethirtyeight/data/tree/master/bechdel"
LICENCIA_URL = "https://creativecommons.org/licenses/by/4.0/"


class ErrorDatos(Exception):
    """Los datos no cumplen las reglas de validación."""


# ---------------------------------------------------------------- lectura

def leer_csv(ruta=RUTA_CSV):
    """Devuelve (columnas, filas). Cada fila lleva su número de línea del archivo."""
    with open(ruta, newline="", encoding="utf-8") as f:
        lector = csv.reader(f)
        try:
            columnas = next(lector)
        except StopIteration:
            raise ErrorDatos("El archivo está vacío: falta la cabecera.")
        filas = []
        for crudo in lector:
            numero = lector.line_num
            if not crudo:  # línea en blanco
                continue
            if len(crudo) != len(columnas):
                raise ErrorDatos(
                    f"Fila {numero}: tiene {len(crudo)} campos y la cabecera tiene {len(columnas)}."
                )
            fila = dict(zip(columnas, crudo))
            fila["_linea"] = numero
            filas.append(fila)
    return columnas, filas


# ------------------------------------------------------------- validación

def validar_cabecera(columnas):
    faltan = [c for c in COLUMNAS_OBLIGATORIAS if c not in columnas]
    if faltan:
        raise ErrorDatos("Cabecera: faltan columnas obligatorias: " + ", ".join(faltan))
    repetidas = {c for c in columnas if columnas.count(c) > 1}
    if repetidas:
        raise ErrorDatos("Cabecera: columnas repetidas: " + ", ".join(sorted(repetidas)))


def _numero_no_negativo(texto, fila, columna):
    """Devuelve float, o None si es NA/vacío. Rechaza negativos, texto, NaN e infinitos."""
    valor = (texto or "").strip()
    if valor in FALTANTES:
        return None
    try:
        numero = float(valor)
    except ValueError:
        raise ErrorDatos(f"Fila {fila}, columna {columna}: {texto!r} no es un número.")
    if not math.isfinite(numero):
        raise ErrorDatos(f"Fila {fila}, columna {columna}: {texto!r} no es un número finito.")
    if numero < 0:
        raise ErrorDatos(f"Fila {fila}, columna {columna}: {texto!r} no puede ser negativo.")
    return numero


def validar_y_convertir(columnas, filas):
    """Valida todo el contenido y devuelve la lista de películas ya convertidas."""
    validar_cabecera(columnas)
    if not filas:
        raise ErrorDatos("El archivo no tiene ningún registro.")
    vistos = {}
    peliculas = []
    for fila in filas:
        n = fila["_linea"]
        imdb = (fila["imdb"] or "").strip()
        if not imdb:
            raise ErrorDatos(f"Fila {n}, columna imdb: no puede estar vacío.")
        if imdb in vistos:
            raise ErrorDatos(
                f"Fila {n}, columna imdb: {imdb!r} está repetido (ya aparece en la fila {vistos[imdb]})."
            )
        vistos[imdb] = n

        titulo = html.unescape(fila["title"] or "").strip()
        if not titulo:
            raise ErrorDatos(f"Fila {n}, columna title: no puede estar vacío.")

        anio_txt = (fila["year"] or "").strip()
        if not anio_txt.isascii() or not anio_txt.isdigit() or int(anio_txt) <= 0:
            raise ErrorDatos(f"Fila {n}, columna year: {fila['year']!r} no es un entero positivo.")

        peliculas.append({
            "imdb": imdb,
            "title": titulo,
            "year": int(anio_txt),
            "budget": _numero_no_negativo(fila["budget"], n, "budget"),
            "domgross": _numero_no_negativo(fila["domgross"], n, "domgross"),
            "budget_txt": (fila["budget"] or "").strip() or "NA",
            "domgross_txt": (fila["domgross"] or "").strip() or "NA",
        })
    return peliculas


# ----------------------------------------------------------------- cálculo

def calcular(peliculas):
    ingresos = [p["domgross"] for p in peliculas if p["domgross"] is not None]
    presupuestos = [p["budget"] for p in peliculas if p["budget"] is not None]
    con_ingreso = [p for p in peliculas if p["domgross"] is not None]
    top = sorted(con_ingreso, key=lambda p: p["domgross"], reverse=True)[:10]
    return {
        "total": len(peliculas),
        "suma_domgross": sum(ingresos),
        "media_budget": (sum(presupuestos) / len(presupuestos)) if presupuestos else None,
        "domgross_faltantes": len(peliculas) - len(ingresos),
        "top10": top,
        "primeras10": peliculas[:10],
    }


# --------------------------------------------------------------------- HTML

def usd(valor):
    return "NA" if valor is None else f"USD {valor:,.0f}"


def grafico_barras(top):
    if not top:
        return "<p>No hay ingresos disponibles para graficar.</p>"
    maximo = top[0]["domgross"] or 1
    filas = []
    for p in top:
        ancho = max(0.5, p["domgross"] / maximo * 100)
        filas.append(
            f'<li><span class="nombre">{html.escape(p["title"])} <small>({p["year"]})</small></span>'
            f'<span class="pista"><span class="barra" style="width:{ancho:.1f}%"></span></span>'
            f'<span class="valor">{usd(p["domgross"])}</span></li>'
        )
    return '<ol class="barras" aria-label="Diez películas con mayor domgross">' + "".join(filas) + "</ol>"


CSS = """
:root{--fondo:#f6f3ee;--tinta:#1d1b2a;--suave:#5f5b6e;--linea:#d9d3c7;--acento:#7a1f3d;--aviso:#fff1c9}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--tinta);font:16px/1.55 Georgia,"Times New Roman",serif}
main{max-width:980px;margin:0 auto;padding:2.5rem 1.25rem 3rem}
h1{font-size:clamp(1.9rem,5vw,3rem);line-height:1.08;margin:0 0 .6rem;letter-spacing:-.01em}
h2{font-size:1.35rem;margin:2.4rem 0 .8rem}
a{color:var(--acento)}
a:focus-visible{outline:3px solid var(--acento);outline-offset:2px}
.aviso{background:var(--aviso);border-left:5px solid #c9962b;padding:.7rem 1rem;margin:1rem 0;font-family:system-ui,sans-serif;font-size:.95rem}
.meta{color:var(--suave);font-family:system-ui,sans-serif;font-size:.92rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0;margin:1.5rem 0;border-block:2px solid var(--tinta)}
.kpi{padding:1rem 1rem 1.1rem 0}
.kpi+.kpi{padding-left:1rem;border-left:1px solid var(--linea)}
.kpi strong{display:block;font-size:1.7rem;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi span{font-family:system-ui,sans-serif;font-size:.88rem;color:var(--suave)}
.nota{font-family:system-ui,sans-serif;font-size:.88rem;color:var(--suave);max-width:70ch}
.barras{list-style:none;margin:0;padding:0;font-family:system-ui,sans-serif;font-size:.9rem}
.barras li{display:grid;grid-template-columns:minmax(120px,230px) 1fr minmax(110px,140px);gap:.7rem;align-items:center;padding:.3rem 0}
.barras small{color:var(--suave)}
.pista{display:block;height:16px;background:#ebe5d8;border-radius:3px}
.barra{display:block;height:100%;background:var(--acento);border-radius:3px}
.valor{text-align:right;font-variant-numeric:tabular-nums}
.tabla{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:620px;font-family:system-ui,sans-serif;font-size:.92rem}
th{text-align:left;border-bottom:2px solid var(--tinta);padding:.45rem .6rem .45rem 0}
td{border-bottom:1px solid var(--linea);padding:.5rem .6rem .5rem 0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
footer{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--linea)}
@media (max-width:640px){
 .barras li{grid-template-columns:1fr;gap:.1rem}.valor{text-align:left}
 .kpi+.kpi{border-left:0;padding-left:0;border-top:1px solid var(--linea)}
}
"""


def generar_html(peliculas, estudiante=ESTUDIANTE, sha=None, ahora=None):
    r = calcular(peliculas)
    sha = sha or "local"
    ahora = ahora or datetime.now(timezone.utc)
    media = "NA" if r["media_budget"] is None else usd(r["media_budget"])
    filas = "".join(
        f'<tr><td>{html.escape(p["imdb"])}</td><td>{html.escape(p["title"])}</td><td>{p["year"]}</td>'
        f'<td class="num">{html.escape(p["budget_txt"])}</td><td class="num">{html.escape(p["domgross_txt"])}</td></tr>'
        for p in r["primeras10"]
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITULO)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>{html.escape(TITULO)}</h1>
<p class="meta">Estudiante: <strong>{html.escape(estudiante)}</strong></p>
<p class="aviso"><strong>Copia educativa: contiene modificaciones simuladas.</strong>
Los cambios de esta práctica son simulaciones y no representan correcciones de la investigación original.</p>

<div class="kpis">
<div class="kpi"><strong>{r['total']:,}</strong><span>películas</span></div>
<div class="kpi"><strong>{usd(r['suma_domgross'])}</strong><span>suma de domgross disponible (USD nominales, esta muestra histórica)</span></div>
<div class="kpi"><strong>{media}</strong><span>media del presupuesto disponible (USD nominales, esta muestra histórica)</span></div>
<div class="kpi"><strong>{r['domgross_faltantes']:,}</strong><span>películas sin ingreso (domgross faltante)</span></div>
</div>
<p class="nota">domgross son los ingresos de taquilla en Estados Unidos, en dólares nominales del año de estreno.
Las sumas corresponden a esta muestra histórica y no son una comparación ajustada por inflación.</p>

<h2>Las diez películas con mayor domgross</h2>
{grafico_barras(r['top10'])}

<h2>Las primeras diez filas del CSV, en su orden original</h2>
<div class="tabla">
<table>
<thead><tr><th>imdb</th><th>title</th><th>year</th><th class="num">budget</th><th class="num">domgross</th></tr></thead>
<tbody>{filas}</tbody>
</table>
</div>

<footer class="meta">
<p>Datos: <a href="{FUENTE_URL}">FiveThirtyEight, conjunto de datos Bechdel</a>, bajo licencia
<a href="{LICENCIA_URL}">CC BY 4.0</a>. Atribución: FiveThirtyEight.</p>
<p>Generado el {ahora.strftime('%Y-%m-%d %H:%M:%S')} UTC · Versión (GITHUB_SHA): <code>{html.escape(sha)}</code></p>
</footer>
</main>
</body>
</html>
"""


# ------------------------------------------------------------------ principal

def main(ruta_csv=RUTA_CSV, salida=RUTA_SALIDA):
    columnas, filas = leer_csv(ruta_csv)
    peliculas = validar_y_convertir(columnas, filas)
    contenido = generar_html(peliculas, sha=os.environ.get("GITHUB_SHA"))
    carpeta = os.path.dirname(salida)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        f.write(contenido)
    resumen = calcular(peliculas)
    print(f"Informe generado: {salida} ({resumen['total']} películas, "
          f"suma domgross = {resumen['suma_domgross']:.0f})")


if __name__ == "__main__":
    try:
        main()
    except (ErrorDatos, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
