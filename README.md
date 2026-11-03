# cine-cicd

Informe sobre películas con validación y publicación automática (CI/CD) con GitHub Actions y GitHub Pages.

- **Página publicada:** https://TU-USUARIO.github.io/cine-cicd/
- **Estudiante:** AMIRA

## Aviso de simulación

**Copia educativa: contiene modificaciones simuladas.** Los cambios de esta práctica son simulaciones
y no representan correcciones de la investigación original.

## Fuente y licencia

Datos: `movies.csv` del conjunto Bechdel de [FiveThirtyEight](https://github.com/fivethirtyeight/data/tree/master/bechdel),
bajo licencia [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Atribución: FiveThirtyEight.
Son datos históricos, no cifras actuales ni un catálogo completo del cine.
`domgross` son ingresos de taquilla en Estados Unidos, en dólares nominales del año de estreno.

## Cómo ejecutarlo

```
python -m unittest discover -v
python analizar.py
```

Después abre `public/index.html`. Si tu sistema usa otro comando, cambia `python` por `python3` o `py`.
El programa solo usa la biblioteca estándar de Python 3.12 y lee siempre `datos/movies.csv`; no descarga nada.

## Cambio válido del CSV

Película modificada: `tt1711425` (21 & Over), columna `domgross`.

| | domgross | Suma total de domgross |
|---|---|---|
| Antes | 25682380 | COMPLETAR (valor inicial en tu informe) |
| Después | 26682380 | COMPLETAR (debe ser exactamente 1000000 más) |

Resultado: COMPLETAR (qué viste en la tabla y en la suma; el número de películas y la media del presupuesto no cambiaron).

Ejecución del cambio válido: COMPLETAR_ENLACE

## Dato inválido bloqueado

Cambié `domgross` de esa película a `-100` y envié el cambio a propósito.
`python analizar.py` falló con `Fila 2, columna domgross: '-100' no puede ser negativo.`
En Actions, el trabajo `verificar` falló y `publicar` quedó omitido, porque depende de `verificar` (`needs: verificar`).
GitHub Pages conservó el ingreso válido anterior.

Ejecución del dato inválido: COMPLETAR_ENLACE

## Corrección

Restauré `domgross` a 26682380 y ambos trabajos volvieron a quedar en verde.

Ejecución de la corrección: COMPLETAR_ENLACE

## Por qué un cambio local llega al sitio solo después de commit y push

Editar el CSV en mi computadora no cambia la página. El cambio llega al sitio solo cuando hago commit y push:
GitHub Actions toma el CSV de ese commit, ejecuta las pruebas, valida los datos y genera el informe, y solo si todo
termina bien publica la página.
