import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout


CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CARTELLA_ROOT = os.path.dirname(CARTELLA_LOGICA)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)

from exif_loader import scansiona_cartella
from report import evidenze_da_foto, classifica_reperti


CARTELLA_IMMAGINI = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "exif_sintetici",
    "immagini",
)

PERCORSO_MANIFEST = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "exif_sintetici",
    "manifest.json",
)

LAT_CENTRO = 39.36336
LON_CENTRO = 16.22622
RAGGIO_KM = 5.0


class TestDatasetSintetico(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(
            PERCORSO_MANIFEST,
            "r",
            encoding="utf-8",
        ) as file_manifest:
            cls.manifest = json.load(file_manifest)

    def test_manifest_contiene_100_reperti(self):
        self.assertEqual(len(self.manifest), 100)

        categorie = {}

        for record in self.manifest:
            categoria = record["categoria"]

            if categoria not in categorie:
                categorie[categoria] = 0

            categorie[categoria] += 1

        self.assertEqual(
            categorie["gps_valido_dentro"],
            40,
        )

        self.assertEqual(
            categorie["gps_valido_fuori"],
            35,
        )

        self.assertEqual(
            categorie["senza_gps"],
            10,
        )

        self.assertEqual(
            categorie["gps_incompleto"],
            5,
        )

        self.assertEqual(
            categorie["file_corrotto"],
            10,
        )

    def test_estrazione_exif_restituisce_75_gps_validi(self):
        output = io.StringIO()

        with redirect_stdout(output):
            foto = scansiona_cartella(
                CARTELLA_IMMAGINI
            )

        statistiche = output.getvalue()

        self.assertEqual(len(foto), 75)

        self.assertIn(
            "File candidati: 100",
            statistiche,
        )

        self.assertIn(
            "Foto con GPS valido: 75",
            statistiche,
        )

        self.assertIn(
            "Foto senza GPS: 10",
            statistiche,
        )

        self.assertIn(
            "Foto con GPS non valido: 5",
            statistiche,
        )

        self.assertIn(
            "File non leggibili/corrotti: 10",
            statistiche,
        )

    def test_classificazione_corrisponde_al_manifest(self):
        with redirect_stdout(io.StringIO()):
            foto = scansiona_cartella(
                CARTELLA_IMMAGINI
            )

        righe = classifica_reperti(
            evidenze_da_foto(foto),
            LAT_CENTRO,
            LON_CENTRO,
            RAGGIO_KM,
        )

        esiti_attesi = {}

        for record in self.manifest:
            if record["esito_atteso"] in (
                "DENTRO_RAGGIO",
                "FUORI_RAGGIO",
            ):
                esiti_attesi[record["nome_file"]] = (
                    record["esito_atteso"]
                )

        self.assertEqual(len(righe), 75)
        self.assertEqual(len(esiti_attesi), 75)

        for riga in righe:
            nome_file = os.path.basename(
                riga["nome_evidenza"]
            )

            self.assertIn(nome_file, esiti_attesi)

            self.assertEqual(
                riga["esito"],
                esiti_attesi[nome_file],
            )

        numero_dentro = sum(
            1
            for riga in righe
            if riga["esito"] == "DENTRO_RAGGIO"
        )

        numero_fuori = sum(
            1
            for riga in righe
            if riga["esito"] == "FUORI_RAGGIO"
        )

        self.assertEqual(numero_dentro, 40)
        self.assertEqual(numero_fuori, 35)


if __name__ == "__main__":
    unittest.main()