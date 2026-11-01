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
from report import (
    classify_evidence,
    evidence_from_images,
)


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
            category = record["category"]

            if category not in categories:
                categories[category] = 0

            categories[category] += 1

        self.assertEqual(
            categories["valid_gps_inside"],
            1,
        )

        self.assertEqual(
            categories["valid_gps_outside"],
            1,
        )

        self.assertEqual(
            categories["without_gps"],
            1,
        )

        self.assertEqual(
            categories["incomplete_gps"],
            1,
        )

        self.assertEqual(
            categories["corrupt_file"],
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

        report_rows = classify_evidence(
            evidence_from_images(image_results),
            CENTER_LATITUDE,
            CENTER_LONGITUDE,
            RADIUS_KM,
        )

        expected_results = {}

        for record in self.manifest:
            if record["expected_result"] in (
                "INSIDE_RADIUS",
                "OUTSIDE_RADIUS",
            ):
                expected_results[record["filename"]] = (
                    record["expected_result"]
                )

        self.assertEqual(len(report_rows), 2)
        self.assertEqual(len(expected_results), 2)

        for row in report_rows:
            filename = os.path.basename(
                row["evidence_name"]
            )

            self.assertIn(filename, expected_results)

            self.assertEqual(
                row["result"],
                expected_results[filename],
            )

        inside_count = sum(
            1
            for row in report_rows
            if row["result"] == "INSIDE_RADIUS"
        )

        outside_count = sum(
            1
            for row in report_rows
            if row["result"] == "OUTSIDE_RADIUS"
        )

        self.assertEqual(inside_count, 1)
        self.assertEqual(outside_count, 1)


if __name__ == "__main__":
    unittest.main()