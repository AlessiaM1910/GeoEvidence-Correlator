import json
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


from exif_loader import (
    UnreadableImageError,
    apply_hemisphere,
    dms_to_decimal,
    extract_exif,
    extract_gps_info,
    extract_timestamp,
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


class TestExifLoader(unittest.TestCase):
    """Test EXIF extraction from the synthetic image dataset."""

    @classmethod
    def setUpClass(cls):
        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8",
        ) as manifest_file:
            manifest = json.load(manifest_file)

        cls.records_by_filename = {}

        for record in manifest:
            cls.records_by_filename[
                record["nome_file"]
            ] = record

    def image_path(self, filename):
        """Return the absolute path of a synthetic test image."""
        return os.path.join(
            TEST_IMAGES_DIRECTORY,
            filename,
        )

    def test_image_with_valid_gps(self):
        filename = "dentro_001.jpg"

        exif_data = extract_exif(
            self.image_path(filename)
        )

        gps_info = extract_gps_info(exif_data)

        latitude = apply_hemisphere(
            dms_to_decimal(
                gps_info["GPSLatitude"]
            ),
            gps_info["GPSLatitudeRef"],
            "latitude",
        )

        longitude = apply_hemisphere(
            dms_to_decimal(
                gps_info["GPSLongitude"]
            ),
            gps_info["GPSLongitudeRef"],
            "longitude",
        )

        expected_record = self.records_by_filename[
            filename
        ]

        self.assertAlmostEqual(
            latitude,
            expected_record["lat"],
            places=5,
        )

        self.assertAlmostEqual(
            longitude,
            expected_record["lon"],
            places=5,
        )

        self.assertEqual(
            extract_timestamp(exif_data),
            expected_record["timestamp"],
        )

    def test_image_without_gps(self):
        exif_data = extract_exif(
            self.image_path("senza_gps_001.jpg")
        )

        gps_info = extract_gps_info(exif_data)

        self.assertFalse(gps_info)

    def test_image_with_incomplete_gps(self):
        exif_data = extract_exif(
            self.image_path(
                "gps_incompleto_001.jpg"
            )
        )

        gps_info = extract_gps_info(exif_data)

        self.assertIsNotNone(gps_info)

        self.assertIn(
            "GPSLatitude",
            gps_info,
        )

        self.assertNotIn(
            "GPSLongitude",
            gps_info,
        )

    def test_unreadable_corrupt_image(self):
        with self.assertRaises(UnreadableImageError):
            extract_exif(
                self.image_path("corrotto_001.jpg")
            )


if __name__ == "__main__":
    unittest.main()