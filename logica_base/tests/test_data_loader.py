import json
import os
import sys
import tempfile
import unittest


LOGIC_DIRECTORY = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if LOGIC_DIRECTORY not in sys.path:
    sys.path.insert(0, LOGIC_DIRECTORY)


from data_loader import (
    create_point,
    load_csv,
    load_json,
)


class TestDataLoader(unittest.TestCase):
    """Test CSV and JSON geographic point loading."""

    def create_temporary_file(self, content, suffix):
        """Create a temporary UTF-8 text file for a test."""
        descriptor, file_path = tempfile.mkstemp(
            suffix=suffix,
        )

        os.close(descriptor)

        with open(
            file_path,
            "w",
            encoding="utf-8",
            newline="",
        ) as temporary_file:
            temporary_file.write(content)

        self.addCleanup(os.remove, file_path)

        return file_path

    def test_create_valid_point(self):
        point = create_point(
            "39.36336",
            "16.22622",
            "Test photo",
        )

        self.assertEqual(
            point,
            (39.36336, 16.22622, "Test photo"),
        )

    def test_create_point_with_non_numeric_coordinates(self):
        point = create_point(
            "text",
            "16.22622",
            "Invalid point",
        )

        self.assertIsNone(point)

    def test_create_point_with_out_of_range_coordinates(self):
        point = create_point(
            91,
            16.22622,
            "Invalid point",
        )

        self.assertIsNone(point)

    def test_create_point_with_nan(self):
        point = create_point(
            float("nan"),
            16.22622,
            "Invalid point",
        )

        self.assertIsNone(point)

    def test_create_point_with_empty_name(self):
        point = create_point(
            39.36336,
            16.22622,
            "   ",
        )

        self.assertIsNone(point)

    def test_load_valid_csv(self):
        content = (
            "lat,lon,name\n"
            "39.36336,16.22622,Photo A\n"
            "39.43231,16.22741,Photo B\n"
        )

        file_path = self.create_temporary_file(
            content,
            ".csv",
        )

        points = load_csv(file_path)

        self.assertEqual(
            points,
            [
                (39.36336, 16.22622, "Photo A"),
                (39.43231, 16.22741, "Photo B"),
            ],
        )

    def test_load_csv_discards_invalid_rows(self):
        content = (
            "lat,lon,name\n"
            "39.36336,16.22622,Valid\n"
            "91,16.22622,Latitude out of range\n"
            "text,16.22622,Non-numeric coordinates\n"
            "39.36336,16.22622,\n"
        )

        file_path = self.create_temporary_file(
            content,
            ".csv",
        )

        points = load_csv(file_path)

        self.assertEqual(
            points,
            [
                (39.36336, 16.22622, "Valid"),
            ],
        )

    def test_load_csv_with_missing_column(self):
        content = (
            "lat,name\n"
            "39.36336,Photo A\n"
        )

        file_path = self.create_temporary_file(
            content,
            ".csv",
        )

        points = load_csv(file_path)

        self.assertEqual(points, [])

    def test_load_csv_with_missing_file(self):
        points = load_csv(
            "missing_csv_file.csv"
        )

        self.assertEqual(points, [])

    def test_load_valid_json(self):
        content = json.dumps(
            [
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "name": "Photo A",
                },
                {
                    "lat": 39.43231,
                    "lon": 16.22741,
                    "name": "Photo B",
                },
            ]
        )

        file_path = self.create_temporary_file(
            content,
            ".json",
        )

        points = load_json(file_path)

        self.assertEqual(
            points,
            [
                (39.36336, 16.22622, "Photo A"),
                (39.43231, 16.22741, "Photo B"),
            ],
        )

    def test_load_json_discards_invalid_items(self):
        content = json.dumps(
            [
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                    "name": "Valid",
                },
                "not a dictionary",
                {
                    "lat": 91,
                    "lon": 16.22622,
                    "name": "Latitude out of range",
                },
                {
                    "lat": 39.36336,
                    "lon": 16.22622,
                },
            ]
        )

        file_path = self.create_temporary_file(
            content,
            ".json",
        )

        points = load_json(file_path)

        self.assertEqual(
            points,
            [
                (39.36336, 16.22622, "Valid"),
            ],
        )

    def test_load_json_with_non_list_root(self):
        content = json.dumps(
            {
                "lat": 39.36336,
                "lon": 16.22622,
                "name": "Not a list",
            }
        )

        file_path = self.create_temporary_file(
            content,
            ".json",
        )

        points = load_json(file_path)

        self.assertEqual(points, [])

    def test_load_invalid_json(self):
        content = (
            "["
            "{\"lat\": 39.36336,"
        )

        file_path = self.create_temporary_file(
            content,
            ".json",
        )

        points = load_json(file_path)

        self.assertEqual(points, [])


if __name__ == "__main__":
    unittest.main()