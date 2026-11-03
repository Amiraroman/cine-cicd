import unittest

import analizar

CABECERA = ["year", "imdb", "title", "budget", "domgross"]


def filas(*registros):
    """Construye filas como las de leer_csv a partir de tuplas pequeñas."""
    resultado = []
    for i, reg in enumerate(registros, start=2):
        fila = dict(zip(CABECERA, reg))
        fila["_linea"] = i
        resultado.append(fila)
    return resultado


class PruebasAnalizar(unittest.TestCase):
    def test_suma_y_media_conocidas(self):
        datos = filas(
            ("2000", "tt1", "A", "100", "1000"),
            ("2001", "tt2", "B", "300", "2000"),
            ("2002", "tt3", "C", "200", "3000"),
        )
        peliculas = analizar.validar_y_convertir(CABECERA, datos)
        r = analizar.calcular(peliculas)
        self.assertEqual(r["total"], 3)
        self.assertEqual(r["suma_domgross"], 6000)
        self.assertEqual(r["media_budget"], 200)
        self.assertEqual(r["domgross_faltantes"], 0)

    def test_na_no_se_convierte_en_cero(self):
        datos = filas(
            ("2000", "tt1", "A", "100", "1000"),
            ("2001", "tt2", "B", "NA", "NA"),
            ("2002", "tt3", "C", "300", ""),
        )
        peliculas = analizar.validar_y_convertir(CABECERA, datos)
        self.assertIsNone(peliculas[1]["domgross"])
        self.assertIsNone(peliculas[2]["domgross"])
        r = analizar.calcular(peliculas)
        self.assertEqual(r["suma_domgross"], 1000)
        self.assertEqual(r["media_budget"], 200)  # (100 + 300) / 2, no / 3
        self.assertEqual(r["domgross_faltantes"], 2)

    def test_rechaza_domgross_negativo(self):
        datos = filas(("2000", "tt1", "A", "100", "-100"))
        with self.assertRaises(analizar.ErrorDatos) as ctx:
            analizar.validar_y_convertir(CABECERA, datos)
        mensaje = str(ctx.exception)
        self.assertIn("domgross", mensaje)
        self.assertIn("Fila 2", mensaje)

    def test_rechaza_columna_obligatoria_ausente(self):
        cabecera = ["year", "imdb", "title", "budget"]  # falta domgross
        with self.assertRaises(analizar.ErrorDatos) as ctx:
            analizar.validar_cabecera(cabecera)
        self.assertIn("domgross", str(ctx.exception))

    def test_rechaza_imdb_repetido_y_vacio(self):
        with self.assertRaises(analizar.ErrorDatos):
            analizar.validar_y_convertir(CABECERA, filas(
                ("2000", "tt1", "A", "1", "1"), ("2001", "tt1", "B", "1", "1")))
        with self.assertRaises(analizar.ErrorDatos):
            analizar.validar_y_convertir(CABECERA, filas(("2000", "", "A", "1", "1")))

    def test_rechaza_year_invalido(self):
        for malo in ("abc", "0", "-5", "20.5", ""):
            with self.assertRaises(analizar.ErrorDatos, msg=malo):
                analizar.validar_y_convertir(CABECERA, filas((malo, "tt1", "A", "1", "1")))

    def test_rechaza_year_fuera_de_rango(self):
        for fuera in ("20133", "1887", "2101", "1"):
            with self.assertRaises(analizar.ErrorDatos, msg=fuera) as ctx:
                analizar.validar_y_convertir(CABECERA, filas((fuera, "tt1", "A", "1", "1")))
            self.assertIn("year", str(ctx.exception))
            self.assertIn("rango", str(ctx.exception))

    def test_acepta_year_en_los_limites(self):
        for valido in ("1888", "2013", "2100"):
            peliculas = analizar.validar_y_convertir(CABECERA, filas((valido, "tt1", "A", "1", "1")))
            self.assertEqual(peliculas[0]["year"], int(valido))

    def test_rechaza_numeros_no_finitos(self):
        for malo in ("nan", "inf", "abc"):
            with self.assertRaises(analizar.ErrorDatos, msg=malo):
                analizar.validar_y_convertir(CABECERA, filas(("2000", "tt1", "A", malo, "1")))

    def test_html_decodifica_y_escapa_titulos(self):
        datos = filas(("2013", "tt1", "21 &amp; Over <b>", "1", "5"))
        peliculas = analizar.validar_y_convertir(CABECERA, datos)
        self.assertEqual(peliculas[0]["title"], "21 & Over <b>")
        pagina = analizar.generar_html(peliculas, estudiante="Prueba", sha="abc123")
        self.assertIn("21 &amp; Over &lt;b&gt;", pagina)
        self.assertNotIn("<b>", pagina.split("<tbody>")[1])
        self.assertIn("abc123", pagina)
        self.assertIn("Copia educativa: contiene modificaciones simuladas", pagina)
        self.assertIn("CC BY 4.0", pagina)

    def test_sin_registros_es_error(self):
        with self.assertRaises(analizar.ErrorDatos):
            analizar.validar_y_convertir(CABECERA, [])


if __name__ == "__main__":
    unittest.main()