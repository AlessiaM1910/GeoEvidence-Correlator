import json
import os
import tempfile
import unittest

CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if CARTELLA_LOGICA not in os.sys.path:
    os.sys.path.insert(0, CARTELLA_LOGICA)

from data_loader import (
    crea_punto,
    carica_csv,
    carica_json,
)


class TestDataLoader(unittest.TestCase):

    def crea_file_temporaneo(self, contenuto, suffisso):
        descrittore, percorso = tempfile.mkstemp(
            suffix=suffisso,
        )

        os.close(descrittore)

        with open(
            percorso,
            "w",
            encoding="utf-8",
            newline="",
        ) as file_temporaneo:
            file_temporaneo.write(contenuto)

        self.addCleanup(os.remove, percorso)

        return percorso

    def test_crea_punto_valido(self):
        punto = crea_punto(
            "39.36336",
            "16.22622",
            "Foto test",
        )

        self.assertEqual(
            punto,
            (39.36336, 16.22622, "Foto test"),
        )

    def test_crea_punto_coordinate_non_numeriche(self):
        punto = crea_punto(
            "testo",
            "16.22622",
            "Punto non valido",
        )

        self.assertIsNone(punto)

    def test_crea_punto_coordinate_fuori_range(self):
        punto = crea_punto(
            91,
            16.22622,
            "Punto non valido",
        )

        self.assertIsNone(punto)

    def test_crea_punto_nan(self):
        punto = crea_punto(
            float("nan"),
            16.22622,
            "Punto non valido",
        )

        self.assertIsNone(punto)

    def test_crea_punto_nome_vuoto(self):
        punto = crea_punto(
            39.36336,
            16.22622,
            "   ",
        )

        self.assertIsNone(punto)

    def test_carica_csv_valido(self):
        contenuto = (
            "lat,lon,nome\n"
            "39.36336,16.22622,Foto A\n"
            "39.43231,16.22741,Foto B\n"
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".csv",
        )

        punti = carica_csv(percorso)

        self.assertEqual(
            punti,
            [
                (39.36336, 16.22622, "Foto A"),
                (39.43231, 16.22741, "Foto B"),
            ],
        )

    def test_carica_csv_scartando_righe_non_valide(self):
        contenuto = (
            "lat,lon,nome\n"
            "39.36336,16.22622,Valido\n"
            "91,16.22622,Latitudine fuori range\n"
            "testo,16.22622,Coordinate non numeriche\n"
            "39.36336,16.22622,\n"
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".csv",
        )

        punti = carica_csv(percorso)

        self.assertEqual(
            punti,
            [
                (39.36336, 16.22622, "Valido"),
            ],
        )

    def test_carica_csv_colonna_mancante(self):
        contenuto = (
            "lat,nome\n"
            "39.36336,Foto A\n"
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".csv",
        )

        punti = carica_csv(percorso)

        self.assertEqual(punti, [])

    def test_carica_csv_file_inesistente(self):
        punti = carica_csv(
            "file_csv_inesistente.csv"
        )

        self.assertEqual(punti, [])

    def test_carica_json_valido(self):
        contenuto = json.dumps(
            [
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "nome": "Foto A",
                },
                {
                    "lat": 39.43231,
                    "lon": 16.22741,
                    "nome": "Foto B",
                },
            ]
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".json",
        )

        punti = carica_json(percorso)

        self.assertEqual(
            punti,
            [
                (39.36336, 16.22622, "Foto A"),
                (39.43231, 16.22741, "Foto B"),
            ],
        )

    def test_carica_json_scartando_elementi_non_validi(self):
        contenuto = json.dumps(
            [
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "nome": "Valido",
                },
                "elemento non dizionario",
                {
                    "lat": 91,
                    "lon": 16.22622,
                    "nome": "Latitudine fuori range",
                },
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                },
            ]
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".json",
        )

        punti = carica_json(percorso)

        self.assertEqual(
            punti,
            [
                (39.36336, 16.22622, "Valido"),
            ],
        )

    def test_carica_json_radice_non_lista(self):
        contenuto = json.dumps(
            {
                "lat": 39.36336,
                "lon": 16.22622,
                "nome": "Non e una lista",
            }
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".json",
        )

        punti = carica_json(percorso)

        self.assertEqual(punti, [])

    def test_carica_json_non_valido(self):
        contenuto = (
            "["
            "{\"lat\": 39.36336,"
        )

        percorso = self.crea_file_temporaneo(
            contenuto,
            ".json",
        )

        punti = carica_json(percorso)

        self.assertEqual(punti, [])


if __name__ == "__main__":
    unittest.main()