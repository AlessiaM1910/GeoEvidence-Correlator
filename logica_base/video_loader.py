# -*- coding: utf-8 -*-
import json
import os
import subprocess
from video_metadata import (
    EXIFTOOL_FIELDS,
    INVALID_GPS,
    NO_GPS,
    SUPPORTED_VIDEO_TYPES,
    VALID_GPS,
    VIDEO_EXTENSION,
    classify_video_metadata,
    extract_video_gps_info,
    extract_video_timestamp,
    is_zero_date,
    validate_decimal_coordinate,
)
#stessa logica di exif_loader solo che invece di usare pillow richiameremo exiftool.exe

class UnreadableVideoError(Exception):
    """Raised when a video cannot be read or is unsupported."""
    pass


class ExifToolUnavailableError(Exception):
    """Raised when the ExifTool executable cannot be started."""
    pass


def extract_video_metadata(video_path, exiftool_path):
    """Extract selected video metadata using ExifTool.

    Args:
        video_path: Path of the MP4 or MOV file.
        exiftool_path: Path of the ExifTool executable.

    Returns:
        The first metadata dictionary returned by ExifTool.

    Raises:
        UnreadableVideoError: If the file is missing, invalid or unsupported.
        ExifToolUnavailableError: If ExifTool cannot be executed.
    """

    if not os.path.isfile(video_path):
        raise UnreadableVideoError(
            "File not found: {}".format(video_path)
        )

    command = [exiftool_path,"-j","-n", "-s"]

    command.extend(EXIFTOOL_FIELDS)
    command.append(video_path)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ExifToolUnavailableError(str(error))
    except OSError as error:
        raise ExifToolUnavailableError(str(error))

    if result.returncode != 0:
        raise UnreadableVideoError(
            result.stderr.strip()
        )

    try:
        metadata_list = json.loads(result.stdout)
    except json.JSONDecodeError as errore:
        raise UnreadableVideoError(str(errore))

    if not metadata_list:
        raise UnreadableVideoError(
            "ExifTool returned no metadata.")

    metadata = metadata_list[0]

    file_type = metadata.get("FileType")
    if file_type not in SUPPORTED_VIDEO_TYPES:
        raise UnreadableVideoError("Unsupported video format: {}".format(
                    file_type or "unknown"
                )
            )

    return metadata


def scan_video_directory(base_directory, exiftool_path):
    """Scan videos recursively and return files with valid GPS coordinates.

    Args:
        base_directory: Root directory to scan.
        exiftool_path: Path of the ExifTool executable.

    Returns:
        Tuples in the format
        (latitude, longitude, relative_path, timestamp).
    """
    candidate_videos = 0
    videos_with_valid_gps = 0
    videos_without_gps = 0
    videos_with_invalid_gps = 0
    unreadable_videos = 0

    gps_results = []

    for root, directories, filenames in os.walk(base_directory):
        directories.sort()
        filenames.sort()

        for filename in filenames:
            if not filename.lower().endswith(
                VIDEO_EXTENSION):
                continue

            candidate_videos += 1

            full_path = os.path.join(root,filename)

            relative_path = os.path.relpath(full_path,base_directory)

            try:
                metadata = extract_video_metadata(full_path,exiftool_path)

                status, latitude, longitude, timestamp = (classify_video_metadata(metadata))

                if status == NO_GPS:
                    videos_without_gps += 1
                    continue

                if status == INVALID_GPS:
                    videos_with_invalid_gps += 1
                    continue

                gps_results.append(
                    (latitude, longitude, relative_path, timestamp)
                )

                videos_with_valid_gps += 1

            except UnreadableVideoError:
                unreadable_videos += 1

    print("Candidate videos:", candidate_videos)
    print("Videos with valid GPS:",videos_with_valid_gps)
    print("Videos without GPS:",videos_without_gps)
    print("Videos with invalid GPS:",videos_with_invalid_gps)
    print("Unreadable or corrupt videos:",unreadable_videos)

    return gps_results