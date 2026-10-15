import json
import os
import sys
import unittest


CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CARTELLA_ROOT = os.path.dirname(CARTELLA_LOGICA)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)

from exif_loader import (
    FotoNonLeggibileError,
    calcola_emisfero,
    converti_in_decimale,
    estrai_exif,
    estrai_gps_info,
    estrai_timestamp,
)


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


class TestExifLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(
            PERCORSO_MANIFEST,
            "r",
            encoding="utf-8",
        ) as file_manifest:
            manifest = json.load(file_manifest)

        cls.record_per_nome = {}

        for record in manifest:
            cls.record_per_nome[record["nome_file"]] = record

    def percorso_immagine(self, nome_file):
        return os.path.join(
            CARTELLA_IMMAGINI,
            nome_file,
        )

    def test_foto_con_gps_valido(self):
        nome_file = "dentro_001.jpg"

        dati_exif = estrai_exif(
            self.percorso_immagine(nome_file)
        )

        gps_info = estrai_gps_info(dati_exif)

        latitudine = calcola_emisfero(
            converti_in_decimale(
                gps_info["GPSLatitude"]
            ),
            gps_info["GPSLatitudeRef"],
            "latitudine",
        )

        longitudine = calcola_emisfero(
            converti_in_decimale(
                gps_info["GPSLongitude"]
            ),
            gps_info["GPSLongitudeRef"],
            "longitudine",
        )

        record_atteso = self.record_per_nome[nome_file]

        self.assertAlmostEqual(
            latitudine,
            record_atteso["lat"],
            places=5,
        )

        self.assertAlmostEqual(
            longitudine,
            record_atteso["lon"],
            places=5,
        )

        self.assertEqual(
            estrai_timestamp(dati_exif),
            record_atteso["timestamp"],
        )

    def test_foto_senza_gps(self):
        dati_exif = estrai_exif(
            self.percorso_immagine("senza_gps_001.jpg")
        )

        gps_info = estrai_gps_info(dati_exif)

        self.assertFalse(gps_info)

    def test_foto_con_gps_incompleto(self):
        dati_exif = estrai_exif(
            self.percorso_immagine(
                "gps_incompleto_001.jpg"
            )
        )

        gps_info = estrai_gps_info(dati_exif)

        self.assertIsNotNone(gps_info)

        self.assertIn(
            "GPSLatitude",
            gps_info,
        )

        self.assertNotIn(
            "GPSLongitude",
            gps_info,
        )

    def test_file_corrotto_non_legibile(self):
        with self.assertRaises(FotoNonLeggibileError):
            estrai_exif(
                self.percorso_immagine("corrotto_001.jpg")
            )


if __name__ == "__main__":
    unittest.main()