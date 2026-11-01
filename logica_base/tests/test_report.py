import csv
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


from report import (
    REPORT_FIELDS,
    classify_evidence,
    evidence_from_images,
    evidence_from_points,
    evidence_from_videos,
    write_csv_report,
)


class TestReport(unittest.TestCase):
    """Test evidence conversion, classification and CSV reporting."""

    def create_temporary_path(self):
        """Create a temporary CSV path and remove it after the test."""
        descriptor, file_path = tempfile.mkstemp(
            suffix=".csv",
        )

        os.close(descriptor)

        self.addCleanup(os.remove, file_path)

        return file_path

    def test_evidence_from_points(self):
        points = [
            (39.36336, 16.22622, "CSV point"),
        ]

        evidence_items = evidence_from_points(
            points,
            "CSV",
        )

        self.assertEqual(
            evidence_items,
            [
                {
                    "evidence_name": "CSV point",
                    "latitude": 39.36336,
                    "longitude": 16.22622,
                    "timestamp": "",
                    "evidence_type": "point",
                    "source": "CSV",
                }
            ],
        )

    def test_evidence_from_images(self):
        images = [
            (
                39.36336,
                16.22622,
                "IMG_2786.JPG",
                "2026:10:02 14:57:17",
            )
        ]

        evidence_items = evidence_from_images(images)

        self.assertEqual(
            evidence_items,
            [
                {
                    "evidence_name": "IMG_2786.JPG",
                    "latitude": 39.36336,
                    "longitude": 16.22622,
                    "timestamp": "2026:10:02 14:57:17",
                    "evidence_type": "image",
                    "source": "EXIF",
                }
            ],
        )

    def test_evidence_from_videos(self):
        videos = [
            (
                39.375155,
                16.271693,
                "con_gps.mp4",
                "2026:01:01 10:01:00+01:00",
            )
        ]

        evidence_items = evidence_from_videos(videos)

        self.assertEqual(
            evidence_items,
            [
                {
                    "evidence_name": "con_gps.mp4",
                    "latitude": 39.375155,
                    "longitude": 16.271693,
                    "timestamp": "2026:01:01 10:01:00+01:00",
                    "evidence_type": "video",
                    "source": "ExifTool",
                }
            ],
        )

    def test_classify_evidence_inside_and_outside_radius(self):
        evidence_items = [
            {
                "evidence_name": "Center",
                "latitude": 0,
                "longitude": 0,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            },
            {
                "evidence_name": "Distant",
                "latitude": 0,
                "longitude": 2,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            },
        ]

        report_rows = classify_evidence(
            evidence_items,
            0,
            0,
            1,
        )

        self.assertEqual(
            report_rows[0]["result"],
            "INSIDE_RADIUS",
        )

        self.assertEqual(
            report_rows[1]["result"],
            "OUTSIDE_RADIUS",
        )

    def test_classify_evidence_orders_rows_and_assigns_ids(self):
        evidence_items = [
            {
                "evidence_name": "Distant",
                "latitude": 0,
                "longitude": 2,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            },
            {
                "evidence_name": "Near",
                "latitude": 0,
                "longitude": 0.5,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            },
            {
                "evidence_name": "Center",
                "latitude": 0,
                "longitude": 0,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            },
        ]

        report_rows = classify_evidence(
            evidence_items,
            0,
            0,
            112,
        )

        evidence_names = []

        for row in report_rows:
            evidence_names.append(
                row["evidence_name"]
            )

        self.assertEqual(
            evidence_names,
            ["Center", "Near", "Distant"],
        )

        self.assertEqual(report_rows[0]["id"], 1)
        self.assertEqual(report_rows[1]["id"], 2)
        self.assertEqual(report_rows[2]["id"], 3)

    def test_classify_evidence_does_not_modify_original_items(self):
        evidence_items = [
            {
                "evidence_name": "Center",
                "latitude": 0,
                "longitude": 0,
                "timestamp": "",
                "evidence_type": "point",
                "source": "TEST",
            }
        ]

        classify_evidence(
            evidence_items,
            0,
            0,
            1,
        )

        self.assertNotIn(
            "distance_km",
            evidence_items[0],
        )

        self.assertNotIn(
            "result",
            evidence_items[0],
        )

        self.assertNotIn(
            "id",
            evidence_items[0],
        )

    def test_write_csv_report(self):
        report_rows = [
            {
                "id": 1,
                "evidence_name": "IMG_2786.JPG",
                "latitude": 39.36336,
                "longitude": 16.22622,
                "distance_km": 0.0,
                "timestamp": "2026:10:02 14:57:17",
                "evidence_type": "image",
                "source": "EXIF",
                "result": "INSIDE_RADIUS",
            }
        ]

        report_path = self.create_temporary_path()

        write_csv_report(
            report_path,
            report_rows,
        )

        with open(
            report_path,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as report_file:
            reader = csv.DictReader(
                report_file,
                delimiter=";",
            )

            read_rows = list(reader)

        self.assertEqual(
            reader.fieldnames,
            REPORT_FIELDS,
        )

        self.assertEqual(len(read_rows), 1)

        self.assertEqual(
            read_rows[0]["evidence_name"],
            "IMG_2786.JPG",
        )

        self.assertEqual(
            read_rows[0]["result"],
            "INSIDE_RADIUS",
        )

        self.assertEqual(
            read_rows[0]["source"],
            "EXIF",
        )

        self.assertEqual(
            read_rows[0]["latitude"],
            "39,36336",
        )

        self.assertEqual(
            read_rows[0]["longitude"],
            "16,22622",
        )

        self.assertEqual(
            read_rows[0]["distance_km"],
            "0",
        )


if __name__ == "__main__":
    unittest.main()