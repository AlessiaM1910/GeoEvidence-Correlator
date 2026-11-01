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
from video_loader import scan_video_directory
from report import classify_evidence, evidence_from_images,evidence_from_videos


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

        video_results = scan_video_directory(
            video_directory,
            os.environ["EXIFTOOL_PATH"],
        )

        evidence = (
            evidence_from_images(image_results)
            + evidence_from_videos(video_results)
        )

        report_rows = classify_evidence(
            evidence,
            39.375155,
            16.271693,
            1,
        )

        rows_by_name = {}

        for row in report_rows:
            rows_by_name[row["evidence_name"]] = row

        self.assertEqual(len(report_rows), 3)

        self.assertIn("con_gps.mp4", rows_by_name)
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["evidence_type"],
            "video",
        )
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["source"],
            "ExifTool",
        )
        self.assertEqual(
            rows_by_name["con_gps.mp4"]["result"],
            "INSIDE_RADIUS",
        )

        self.assertIn("dentro_001.jpg", rows_by_name)
        self.assertEqual(
            rows_by_name["dentro_001.jpg"]["evidence_type"],
            "image",
        )
        self.assertEqual(
            rows_by_name["dentro_001.jpg"]["result"],
            "INSIDE_RADIUS",
        )

        self.assertIn("fuori_001.jpg", rows_by_name)
        self.assertEqual(
            rows_by_name["fuori_001.jpg"]["result"],
            "OUTSIDE_RADIUS",
        )


if __name__ == "__main__":
    unittest.main()