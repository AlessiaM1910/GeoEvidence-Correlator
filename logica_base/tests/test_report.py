import csv
import os
import sys
import tempfile
import unittest

CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)

from report import (
    CAMPI_REPORT,
    evidenze_da_punti,
    evidenze_da_foto,
    classifica_reperti,
    scrivi_report_csv,
)


class TestReport(unittest.TestCase):

    def crea_percorso_temporaneo(self):
        descrittore, percorso = tempfile.mkstemp(
            suffix=".csv",
        )

        os.close(descrittore)

        self.addCleanup(os.remove, percorso)

        return percorso

    def test_evidenze_da_punti(self):
        punti = [
            (39.36336, 16.22622, "Punto CSV"),
        ]

        evidenze = evidenze_da_punti(
            punti,
            "CSV",
        )

        self.assertEqual(
            evidenze,
            [
                {
                    "nome_evidenza": "Punto CSV",
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "timestamp": "",
                    "tipo": "punto",
                    "fonte": "CSV",
                }
            ],
        )

    def test_evidenze_da_foto(self):
        foto = [
            (
                39.36336,
                16.22622,
                "IMG_2786.JPG",
                "2026:10:02 14:57:17",
            )
        ]

        evidenze = evidenze_da_foto(foto)

        self.assertEqual(
            evidenze,
            [
                {
                    "nome_evidenza": "IMG_2786.JPG",
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "timestamp": "2026:10:02 14:57:17",
                    "tipo": "foto",
                    "fonte": "EXIF",
                }
            ],
        )

    def test_classifica_reperti_esito_dentro_fuori(self):
        evidenze = [
            {
                "nome_evidenza": "Centro",
                "lat": 0,
                "lon": 0,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            },
            {
                "nome_evidenza": "Lontano",
                "lat": 0,
                "lon": 2,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            },
        ]

        righe = classifica_reperti(
            evidenze,
            0,
            0,
            1,
        )

        self.assertEqual(
            righe[0]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertEqual(
            righe[1]["esito"],
            "FUORI_RAGGIO",
        )

    def test_classifica_reperti_ordina_e_assegna_id(self):
        evidenze = [
            {
                "nome_evidenza": "Lontano",
                "lat": 0,
                "lon": 2,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            },
            {
                "nome_evidenza": "Vicino",
                "lat": 0,
                "lon": 0.5,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            },
            {
                "nome_evidenza": "Centro",
                "lat": 0,
                "lon": 0,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            },
        ]

        righe = classifica_reperti(
            evidenze,
            0,
            0,
            112,
        )

        nomi = []

        for riga in righe:
            nomi.append(riga["nome_evidenza"])

        self.assertEqual(
            nomi,
            ["Centro", "Vicino", "Lontano"],
        )

        self.assertEqual(
            righe[0]["id"],
            1,
        )

        self.assertEqual(
            righe[1]["id"],
            2,
        )

        self.assertEqual(
            righe[2]["id"],
            3,
        )

    def test_classifica_non_modifica_evidenze_originali(self):
        evidenze = [
            {
                "nome_evidenza": "Centro",
                "lat": 0,
                "lon": 0,
                "timestamp": "",
                "tipo": "punto",
                "fonte": "TEST",
            }
        ]

        classifica_reperti(
            evidenze,
            0,
            0,
            1,
        )

        self.assertNotIn(
            "distanza_km",
            evidenze[0],
        )

        self.assertNotIn(
            "esito",
            evidenze[0],
        )

        self.assertNotIn(
            "id",
            evidenze[0],
        )

    def test_scrivi_report_csv(self):
        righe = [
            {
                "id": 1,
                "nome_evidenza": "IMG_2786.JPG",
                "lat": 39.36336,
                "lon": 16.22622,
                "distanza_km": 0.0,
                "timestamp": "2026:10:02 14:57:17",
                "tipo": "foto",
                "fonte": "EXIF",
                "esito": "DENTRO_RAGGIO",
            }
        ]

        percorso = self.crea_percorso_temporaneo()

        scrivi_report_csv(
            percorso,
            righe,
        )

        with open(
            percorso,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file_report:

            lettore = csv.DictReader(
                file_report,
                delimiter=";",
            )

            righe_lette = list(lettore)

        self.assertEqual(
            lettore.fieldnames,
            CAMPI_REPORT,
        )

        self.assertEqual(
            len(righe_lette),
            1,
        )

        self.assertEqual(
            righe_lette[0]["nome_evidenza"],
            "IMG_2786.JPG",
        )

        self.assertEqual(
            righe_lette[0]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertEqual(
            righe_lette[0]["fonte"],
            "EXIF",
        )


if __name__ == "__main__":
    unittest.main()