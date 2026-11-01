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


from exif_loader import scan_image_directory
from report import classifica_reperti, evidenze_da_foto


TEST_IMAGES_DIRECTORY = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "exif_sintetici",
    "immagini",
)

MANIFEST_PATH = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "exif_sintetici",
    "manifest.json",
)

CENTER_LATITUDE = 39.36336
CENTER_LONGITUDE = 16.22622
RADIUS_KM = 5.0


class TestSyntheticDataset(unittest.TestCase):
    """Test expected outcomes for the synthetic image dataset."""

    @classmethod
    def setUpClass(cls):
        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8",
        ) as manifest_file:
            cls.manifest = json.load(manifest_file)

    def test_manifest_contains_five_records(self):
        self.assertEqual(len(self.manifest), 5)

        categories = {}

        for record in self.manifest:
            category = record["categoria"]

            if category not in categories:
                categories[category] = 0

            categories[category] += 1

        self.assertEqual(
            categories["gps_valido_dentro"],
            1,
        )

        self.assertEqual(
            categories["gps_valido_fuori"],
            1,
        )

        self.assertEqual(
            categories["senza_gps"],
            1,
        )

        self.assertEqual(
            categories["gps_incompleto"],
            1,
        )

        self.assertEqual(
            categories["file_corrotto"],
            1,
        )

    def test_exif_extraction_returns_two_valid_gps_results(self):
        output = io.StringIO()

        with redirect_stdout(output):
            image_results = scan_image_directory(
                TEST_IMAGES_DIRECTORY
            )

        statistics = output.getvalue()

        self.assertEqual(len(image_results), 2)

        self.assertIn(
            "Candidate files: 5",
            statistics,
        )

        self.assertIn(
            "Images with valid GPS: 2",
            statistics,
        )

        self.assertIn(
            "Images without GPS: 1",
            statistics,
        )

        self.assertIn(
            "Images with invalid GPS: 1",
            statistics,
        )

        self.assertIn(
            "Unreadable or corrupt images: 1",
            statistics,
        )

    def test_classification_matches_manifest(self):
        with redirect_stdout(io.StringIO()):
            image_results = scan_image_directory(
                TEST_IMAGES_DIRECTORY
            )

        report_rows = classifica_reperti(
            evidenze_da_foto(image_results),
            CENTER_LATITUDE,
            CENTER_LONGITUDE,
            RADIUS_KM,
        )

        expected_results = {}

        for record in self.manifest:
            if record["esito_atteso"] in (
                "DENTRO_RAGGIO",
                "FUORI_RAGGIO",
            ):
                expected_results[record["nome_file"]] = (
                    record["esito_atteso"]
                )

        self.assertEqual(len(report_rows), 2)
        self.assertEqual(len(expected_results), 2)

        for row in report_rows:
            filename = os.path.basename(
                row["nome_evidenza"]
            )

            self.assertIn(filename, expected_results)

            self.assertEqual(
                row["esito"],
                expected_results[filename],
            )

        inside_count = sum(
            1
            for row in report_rows
            if row["esito"] == "DENTRO_RAGGIO"
        )

        outside_count = sum(
            1
            for row in report_rows
            if row["esito"] == "FUORI_RAGGIO"
        )

        self.assertEqual(inside_count, 1)
        self.assertEqual(outside_count, 1)


if __name__ == "__main__":
    unittest.main()