# -*- coding: utf-8 -*-
"""Interpretation of the metadata that ExifTool returns for a video.

Only pure functions: no process is started and no file is read, so this
module also runs in Jython 2.7 (the Autopsy plugin uses a copy of it).
"""

VIDEO_EXTENSION = (".mp4", ".mov")
SUPPORTED_VIDEO_TYPES = ("MP4", "MOV")
VALID_GPS = "VALID_GPS"
NO_GPS = "NO_GPS"
INVALID_GPS = "INVALID_GPS"

EXIFTOOL_FIELDS = (
    "-FileType",
    "-MIMEType",
    "-GPSLatitude",
    "-GPSLongitude",
    "-GPSAltitude",
    "-GPSDateTime",
    "-CreationDate",
    "-MediaCreateDate",
    "-CreateDate",
    "-TrackCreateDate",
)

#restituisce dati GPS trovati da Exiftool, altrimenti retsituisce none
def extract_video_gps_info(metadata):
    """Extract available GPS values from video metadata.

    Args:
        metadata: Metadata dictionary returned by ExifTool.

    Returns:
        GPS metadata dictionary, or None if GPS is unavailable.
    """
    if not metadata:
        return None

    gps_info = {}

    for field in (
        "GPSLatitude",
        "GPSLongitude",
        "GPSAltitude",
    ):
        value = metadata.get(field)

        if value is not None:
            gps_info[field] = value

    if not gps_info:
        return None

    return gps_info


def validate_decimal_coordinate(value, minimum, maximum):
    """Convert and validate a decimal geographic coordinate.

    Args:
        value: Coordinate value to validate.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.

    Returns:
        Valid decimal coordinate, or None if invalid.
    """

    """
    ExifTool con -n restituisce gia coordinate decimali.
    Qui controlliamo che siano numeri validi e nel range terrestre.
    """

    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None

    if not (minimum <= coordinate <= maximum):
        return None

    return coordinate

def is_zero_date(value):
    """Return True for the placeholder dates written by ExifTool."""
    return str(value).startswith("0000:00:00")

def extract_video_timestamp(metadata):
    """Extract the preferred timestamp from video metadata.

    Args:
        metadata: Metadata dictionary returned by ExifTool.

    Returns:
        The first available timestamp, or ``Unknown date``.
    """
    if not metadata:
        return "Unknown date"

    timestamp_field = (
        "GPSDateTime",
        "CreationDate",
        "MediaCreateDate",
        "CreateDate",
        "TrackCreateDate",
    )

    for field in timestamp_field:
        value = metadata.get(field)

        if value and not is_zero_date(value):
            return value

    return "Unknown date"

def classify_video_metadata(metadata):
    """Classify the GPS data found in the metadata of one video.

    Args:
        metadata: Metadata dictionary returned by ExifTool.

    Returns:
        A tuple (status, latitude, longitude, timestamp). Status is
        VALID_GPS, NO_GPS or INVALID_GPS. Latitude and longitude are
        None unless the status is VALID_GPS.
    """
    timestamp = extract_video_timestamp(metadata)
    gps_info = extract_video_gps_info(metadata)

    has_position = (
        gps_info is not None
        and (
            "GPSLatitude" in gps_info
            or "GPSLongitude" in gps_info
        )
    )

    if not has_position:
        return NO_GPS, None, None, timestamp

    if (
        "GPSLatitude" not in gps_info
        or "GPSLongitude" not in gps_info
    ):
        return INVALID_GPS, None, None, timestamp

    latitude = validate_decimal_coordinate(
        gps_info["GPSLatitude"], -90.0, 90.0
    )
    longitude = validate_decimal_coordinate(
        gps_info["GPSLongitude"], -180.0, 180.0
    )

    if latitude is None or longitude is None:
        return INVALID_GPS, None, None, timestamp

    return VALID_GPS, latitude, longitude, timestamp