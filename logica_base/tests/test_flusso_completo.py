import os
import sys
import unittest


LOGIC_DIRECTORY = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROJECT_ROOT = os.path.dirname(LOGIC_DIRECTORY)

if LOGIC_DIRECTORY not in sys.path:
    sys.path.insert(0, LOGIC_DIRECTORY)


from exif_loader import scan_image_directory
from video_loader import scansiona_cartella_video
from report import (
    classifica_reperti,
    evidenze_da_foto,
    evidenze_da_video,
)


@unittest.skipUnless(
    os.environ.get("EXIFTOOL_PATH"),
    "EXIFTOOL_PATH is not set",
)
class TestMediaIntegration(unittest.TestCase):
    """Test combined image and video geographic evidence."""

    def test_images_and_videos_are_added_to_the_same_report(self):
        image_directory = os.path.join(
            PROJECT_ROOT,
            "dati_test",
            "exif_sintetici",
            "immagini",
        )

        video_directory = os.path.join(
            PROJECT_ROOT,
            "dati_test",
            "video_sintetici",
            "video",
        )

        image_results = scan_image_directory(
            image_directory
        )

        video_results = scansiona_cartella_video(
            video_directory,
            os.environ["EXIFTOOL_PATH"],
        )

        evidence = (
            evidenze_da_foto(image_results)
            + evidenze_da_video(video_results)
        )

        report_rows = classifica_reperti(
            evidence,
            39.375155,
            16.271693,
            1,
        )

        rows_by_name = {}

        for row in report_rows:
            rows_by_name[row["nome_evidenza"]] = row

        self.assertEqual(len(report_rows), 3)

        self.assertIn("con_gps.mp4", rows_by_name)
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["tipo"],
            "video",
        )
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["fonte"],
            "ExifTool",
        )
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertIn("dentro_001.jpg", rows_by_name)
        self.assertEqual(
            rows_by_name["dentro_001.jpg"]["tipo"],
            "foto",
        )
        self.assertEqual(
            rows_by_name["dentro_001.jpg"]["esito"],
            "DENTRO_RAGGIO",
        )

        self.assertIn("fuori_001.jpg", rows_by_name)
        self.assertEqual(
            rows_by_name["fuori_001.jpg"]["esito"],
            "FUORI_RAGGIO",
        )


if __name__ == "__main__":
    unittest.main()