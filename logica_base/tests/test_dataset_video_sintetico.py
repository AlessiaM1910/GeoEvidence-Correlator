import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout


LOGIC_DIRECTORY = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROJECT_ROOT = os.path.dirname(LOGIC_DIRECTORY)

if LOGIC_DIRECTORY not in sys.path:
    sys.path.insert(0, LOGIC_DIRECTORY)


from video_loader import scansiona_cartella_video


VIDEO_DIRECTORY = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "video_sintetici",
    "video",
)

MANIFEST_PATH = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "video_sintetici",
    "manifest.json",
)

EXIFTOOL_PATH = os.environ.get("EXIFTOOL_PATH")


@unittest.skipUnless(
    EXIFTOOL_PATH,
    "Set EXIFTOOL_PATH before running video integration tests.",
)
class TestSyntheticVideoDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Loads the expected metadata and verifies ExifTool availability.
        """
        if not os.path.isfile(EXIFTOOL_PATH):
            raise unittest.SkipTest(
                "ExifTool executable not found: {0}".format(
                    EXIFTOOL_PATH
                )
            )

        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8",
        ) as manifest_file:
            cls.manifest = json.load(manifest_file)

    def test_manifest_contains_three_video_cases(self):
        """
        Verifies that the dataset documents all expected video cases.
        """
        self.assertEqual(len(self.manifest), 3)

        categories = set(
            record["categoria"]
            for record in self.manifest
        )

        self.assertEqual(
            categories,
            {
                "gps_valido",
                "senza_gps",
                "file_corrotto",
            },
        )

    def test_video_loader_matches_the_synthetic_dataset(self):
        """
        Runs ExifTool through video_loader and checks all outcomes.
        """
        output = io.StringIO()

        with redirect_stdout(output):
            videos = scansiona_cartella_video(
                VIDEO_DIRECTORY,
                EXIFTOOL_PATH,
            )

        statistics = output.getvalue()

        self.assertIn(
            "Video candidati: 3",
            statistics,
        )

        self.assertIn(
            "Video con GPS valido: 1",
            statistics,
        )

        self.assertIn(
            "Video senza GPS: 1",
            statistics,
        )

        self.assertIn(
            "Video con GPS non valido: 0",
            statistics,
        )

        self.assertIn(
            "Video non leggibili/corrotti: 1",
            statistics,
        )

        self.assertEqual(len(videos), 1)

        latitude, longitude, name, timestamp = videos[0]

        self.assertAlmostEqual(
            latitude,
            39.375155,
            places=6,
        )

        self.assertAlmostEqual(
            longitude,
            16.271693,
            places=6,
        )

        self.assertEqual(name, "con_gps.mp4")

        self.assertEqual(
            timestamp,
            "2026:01:01 10:01:00+01:00",
        )


if __name__ == "__main__":
    unittest.main()