import os
import sys
import unittest


CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RADICE_PROGETTO = os.path.dirname(CARTELLA_LOGICA)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)


from exif_loader import scansiona_cartella
from video_loader import scansiona_cartella_video
from report import (
    classifica_reperti,
    evidenze_da_foto,
    evidenze_da_video,
)


@unittest.skipUnless(
    os.environ.get("EXIFTOOL_PATH"),
    "EXIFTOOL_PATH non impostata",
)
class TestIntegrazioneMedia(unittest.TestCase):

    def test_foto_e_video_confluiscono_nello_stesso_report(self):
        cartella_foto = os.path.join(
            RADICE_PROGETTO,
            "dati_test",
            "exif_sintetici",
            "immagini",
        )

        cartella_video = os.path.join(
            RADICE_PROGETTO,
            "dati_test",
            "video_sintetici",
            "video",
        )

        foto = scansiona_cartella(cartella_foto)

        video = scansiona_cartella_video(
            cartella_video,
            os.environ["EXIFTOOL_PATH"],
        )

        evidenze = (
            evidenze_da_foto(foto)
            + evidenze_da_video(video)
        )

        righe_report = classifica_reperti(
            evidenze,
            39.375155,
            16.271693,
            1,
        )

        righe_per_nome = {}

        for riga in righe_report:
            righe_per_nome[riga["nome_evidenza"]] = riga

        self.assertEqual(len(righe_report), 3)

        self.assertIn("con_gps.mp4", righe_per_nome)
        self.assertEqual(
            righe_per_nome["con_gps.mp4"]["tipo"],
            "video",
        )
        self.assertEqual(
            righe_per_nome["con_gps.mp4"]["fonte"],
            "ExifTool",
        )
        self.assertEqual(
            righe_per_nome["con_gps.mp4"]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertIn("dentro_001.jpg", righe_per_nome)
        self.assertEqual(
            righe_per_nome["dentro_001.jpg"]["tipo"],
            "foto",
        )
        self.assertEqual(
            righe_per_nome["dentro_001.jpg"]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertIn("fuori_001.jpg", righe_per_nome)
        self.assertEqual(
            righe_per_nome["fuori_001.jpg"]["esito"],
            "FUORI_RAGGIO",
        )


if __name__ == "__main__":
    unittest.main()