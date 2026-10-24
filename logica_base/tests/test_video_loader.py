import json
import os
import sys
import unittest
from unittest.mock import Mock, patch


CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)


from video_loader import (
    ExifToolNonDisponibileError,
    VideoNonLeggibileError,
    converti_coordinata_decimale,
    estrai_gps_info_video,
    estrai_metadati_video,
    estrai_timestamp_video,
)


class TestVideoLoader(unittest.TestCase):

    def test_video_con_gps_valido_android(self):
        metadati = {
            "GPSLatitude": 39.8244,
            "GPSLongitude": 16.194,
            "MediaCreateDate": (
                "2026:10:15 19:32:58"
            ),
        }

        gps_info = estrai_gps_info_video(metadati)

        self.assertEqual(
            gps_info["GPSLatitude"],
            39.8244,
        )

        self.assertEqual(
            gps_info["GPSLongitude"],
            16.194,
        )

        self.assertEqual(
            estrai_timestamp_video(metadati),
            "2026:10:15 19:32:58",
        )

    def test_video_con_gps_valido_iphone(self):
        metadati = {
            "GPSLatitude": 39.8244,
            "GPSLongitude": 16.194,
            "GPSAltitude": 410.626,
            "CreationDate": (
                "2026:10:15 20:37:36+02:00"
            ),
            "MediaCreateDate": (
                "2026:10:15 18:37:36"
            ),
        }

        gps_info = estrai_gps_info_video(metadati)

        self.assertEqual(
            gps_info["GPSAltitude"],
            410.626,
        )

        self.assertEqual(
            estrai_timestamp_video(metadati),
            "2026:10:15 20:37:36+02:00",
        )

    def test_video_senza_gps(self):
        metadati = {
            "MediaCreateDate": (
                "2025:09:17 13:03:49"
            ),
        }

        self.assertIsNone(
            estrai_gps_info_video(metadati)
        )

    def test_video_con_gps_incompleto(self):
        metadati = {
            "GPSLatitude": 39.8244,
        }

        gps_info = estrai_gps_info_video(metadati)

        self.assertIsNotNone(gps_info)

        self.assertIn(
            "GPSLatitude",
            gps_info,
        )

        self.assertNotIn(
            "GPSLongitude",
            gps_info,
        )

    def test_coordinate_valide(self):
        self.assertEqual(
            converti_coordinata_decimale(
                39.8244,
                -90.0,
                90.0,
            ),
            39.8244,
        )

        self.assertEqual(
            converti_coordinata_decimale(
                16.194,
                -180.0,
                180.0,
            ),
            16.194,
        )

    def test_coordinate_fuori_intervallo(self):
        self.assertIsNone(
            converti_coordinata_decimale(
                91.0,
                -90.0,
                90.0,
            )
        )

        self.assertIsNone(
            converti_coordinata_decimale(
                -181.0,
                -180.0,
                180.0,
            )
        )

    def test_timestamp_sconosciuto(self):
        self.assertEqual(
            estrai_timestamp_video({}),
            "Data sconosciuta",
        )

    def test_estrai_metadati_video_da_json(self):
        risposta_exiftool = [
            {
                "SourceFile": "video.mp4",
                "GPSLatitude": 39.8244,
                "GPSLongitude": 16.194,
            }
        ]

        processo_finto = Mock()
        processo_finto.returncode = 0
        processo_finto.stdout = json.dumps(
            risposta_exiftool
        )
        processo_finto.stderr = ""

        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                return_value=processo_finto,
            ):
                metadati = estrai_metadati_video(
                    "video.mp4",
                    "exiftool.exe",
                )

        self.assertEqual(
            metadati["GPSLatitude"],
            39.8244,
        )

        self.assertEqual(
            metadati["GPSLongitude"],
            16.194,
        )

    def test_exiftool_non_disponibile(self):
        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                side_effect=FileNotFoundError(
                    "ExifTool non trovato"
                ),
            ):
                with self.assertRaises(
                    ExifToolNonDisponibileError
                ):
                    estrai_metadati_video(
                        "video.mp4",
                        "exiftool.exe",
                    )

    def test_video_con_json_non_valido(self):
        processo_finto = Mock()
        processo_finto.returncode = 0
        processo_finto.stdout = "JSON_NON_VALIDO"
        processo_finto.stderr = ""

        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                return_value=processo_finto,
            ):
                with self.assertRaises(
                    VideoNonLeggibileError
                ):
                    estrai_metadati_video(
                        "video.mp4",
                        "exiftool.exe",
                    )


if __name__ == "__main__":
    unittest.main()