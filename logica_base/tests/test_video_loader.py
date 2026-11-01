import json
import os
import sys
import unittest
from unittest.mock import Mock, patch


LOGIC_DIRECTORY = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if LOGIC_DIRECTORY not in sys.path:
    sys.path.insert(0, LOGIC_DIRECTORY)


from video_loader import (
    ExifToolUnavailableError,
    UnreadableVideoError,
    extract_video_gps_info,
    extract_video_metadata,
    extract_video_timestamp,
    validate_decimal_coordinate,
)


class TestVideoLoader(unittest.TestCase):
    """Test video metadata extraction and validation."""

    def test_android_video_with_valid_gps(self):
        metadata = {
            "GPSLatitude": 39.8244,
            "GPSLongitude": 16.194,
            "MediaCreateDate": (
                "2026:10:15 19:32:58"
            ),
        }

        gps_info = extract_video_gps_info(metadata)

        self.assertEqual(
            gps_info["GPSLatitude"],
            39.8244,
        )

        self.assertEqual(
            gps_info["GPSLongitude"],
            16.194,
        )

        self.assertEqual(
            extract_video_timestamp(metadata),
            "2026:10:15 19:32:58",
        )

    def test_iphone_video_with_valid_gps(self):
        metadata = {
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

        gps_info = extract_video_gps_info(metadata)

        self.assertEqual(
            gps_info["GPSAltitude"],
            410.626,
        )

        self.assertEqual(
            extract_video_timestamp(metadata),
            "2026:10:15 20:37:36+02:00",
        )

    def test_video_without_gps(self):
        metadata = {
            "MediaCreateDate": (
                "2025:09:17 13:03:49"
            ),
        }

        self.assertIsNone(
            extract_video_gps_info(metadata)
        )

    def test_video_with_incomplete_gps(self):
        metadata = {
            "GPSLatitude": 39.8244,
        }

        gps_info = extract_video_gps_info(metadata)

        self.assertIsNotNone(gps_info)

        self.assertIn(
            "GPSLatitude",
            gps_info,
        )

        self.assertNotIn(
            "GPSLongitude",
            gps_info,
        )

    def test_valid_coordinates(self):
        self.assertEqual(
            validate_decimal_coordinate(
                39.8244,
                -90.0,
                90.0,
            ),
            39.8244,
        )

        self.assertEqual(
            validate_decimal_coordinate(
                16.194,
                -180.0,
                180.0,
            ),
            16.194,
        )

    def test_coordinates_outside_range(self):
        self.assertIsNone(
            validate_decimal_coordinate(
                91.0,
                -90.0,
                90.0,
            )
        )

        self.assertIsNone(
            validate_decimal_coordinate(
                -181.0,
                -180.0,
                180.0,
            )
        )

    def test_unknown_timestamp(self):
        self.assertEqual(
            extract_video_timestamp({}),
            "Unknown date",
        )

    def test_metadata_extraction_from_json(self):
        exiftool_response = [
            {
                "SourceFile": "video.mp4",
                "FileType": "MP4",
                "MIMEType": "video/mp4",
                "GPSLatitude": 39.8244,
                "GPSLongitude": 16.194,
            }
        ]

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = json.dumps(
            exiftool_response
        )
        mock_process.stderr = ""

        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                return_value=mock_process,
            ):
                metadata = extract_video_metadata(
                    "video.mp4",
                    "exiftool.exe",
                )

        self.assertEqual(
            metadata["GPSLatitude"],
            39.8244,
        )

        self.assertEqual(
            metadata["GPSLongitude"],
            16.194,
        )

    def test_unsupported_file_type_is_rejected(self):
        exiftool_response = [
            {
                "SourceFile": "corrupt.mp4",
                "FileType": "TXT",
                "MIMEType": "text/plain",
            }
        ]

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = json.dumps(
            exiftool_response
        )
        mock_process.stderr = ""

        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                return_value=mock_process,
            ):
                with self.assertRaises(
                    UnreadableVideoError
                ):
                    extract_video_metadata(
                        "corrupt.mp4",
                        "exiftool.exe",
                    )

    def test_exiftool_is_unavailable(self):
        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                side_effect=FileNotFoundError(
                    "ExifTool not found"
                ),
            ):
                with self.assertRaises(
                    ExifToolUnavailableError
                ):
                    extract_video_metadata(
                        "video.mp4",
                        "exiftool.exe",
                    )

    def test_invalid_exiftool_json(self):
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "INVALID_JSON"
        mock_process.stderr = ""

        with patch(
            "video_loader.os.path.isfile",
            return_value=True,
        ):
            with patch(
                "video_loader.subprocess.run",
                return_value=mock_process,
            ):
                with self.assertRaises(
                    UnreadableVideoError
                ):
                    extract_video_metadata(
                        "video.mp4",
                        "exiftool.exe",
                    )


if __name__ == "__main__":
    unittest.main()