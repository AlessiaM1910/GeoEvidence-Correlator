import csv

from core import haversine_distance


REPORT_FIELDS = [
    "id",
    "evidence_name",
    "latitude",
    "longitude",
    "distance_km",
    "timestamp",
    "evidence_type",
    "source",
    "result",
]


def evidence_from_points(points, source):
    """Convert geographic point tuples into report evidence dictionaries.

    Args:
        points: Tuples in the format (latitude, longitude, name).
        source: Source label for the points.

    Returns:
        Evidence dictionaries ready for classification.
    """
    evidence_items = []

    for latitude, longitude, name in points:
        evidence_items.append(
            {
                "evidence_name": name,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": "",
                "evidence_type": "point",
                "source": source,
            }
        )

    return evidence_items


def evidence_from_images(images):
    """Convert image GPS results into report evidence dictionaries.

    Args:
        images: Image tuples from scan_image_directory.

    Returns:
        Image evidence dictionaries ready for classification.
    """
    evidence_items = []

    for latitude, longitude, relative_path, timestamp in images:
        evidence_items.append(
            {
                "evidence_name": relative_path,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": timestamp,
                "evidence_type": "image",
                "source": "EXIF",
            }
        )

    return evidence_items


def evidence_from_videos(videos):
    """Convert video GPS results into report evidence dictionaries.

    Args:
        videos: Video tuples from scan_video_directory.

    Returns:
        Video evidence dictionaries ready for classification.
    """
    evidence_items = []

    for latitude, longitude, relative_path, timestamp in videos:
        evidence_items.append(
            {
                "evidence_name": relative_path,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": timestamp,
                "evidence_type": "video",
                "source": "ExifTool",
            }
        )

    return evidence_items


def classify_evidence(evidence_items,center_latitude,center_longitude,radius_km):
    """Classify evidence as inside or outside a geographic radius.

    Args:
        evidence_items: Evidence dictionaries with coordinates.
        center_latitude: Latitude of the search center.
        center_longitude: Longitude of the search center.
        radius_km: Search radius in kilometers.

    Returns:
        Classified and distance-ordered report rows.
    """
    report_rows = []

    for evidence in evidence_items:
        distance_km = haversine_distance(evidence["latitude"],evidence["longitude"],center_latitude,center_longitude)

        row = dict(evidence)
        row["distance_km"] = round(distance_km, 6)

        if distance_km <= radius_km:
            row["result"] = "INSIDE_RADIUS"
        else:
            row["result"] = "OUTSIDE_RADIUS"

        report_rows.append(row)

    report_rows.sort(key=lambda row: row["distance_km"])

    for index, row in enumerate(report_rows, start=1):
        row["id"] = index

    return report_rows


def format_csv_number(value):
    """Format floating-point values for semicolon-delimited Italian CSV.

    Args:
        value: Value to format.

    Returns:
        Value with a comma decimal separator when it is a float.
    """
    if isinstance(value, float):
        text = "{:.6f}".format(value)
        text = text.rstrip("0").rstrip(".")

        return text.replace(".", ",")

    return value


def write_csv_report(report_path, report_rows):
    """Write classified evidence to a semicolon-delimited CSV report.

    Args:
        report_path: Destination CSV path.
        report_rows: Classified evidence dictionaries.
    """
    with open(report_path,"w",newline="",encoding="utf-8-sig",) as report_file:
        writer = csv.DictWriter(report_file,fieldnames=REPORT_FIELDS,delimiter=";")

        writer.writeheader()

        for row in report_rows:
            formatted_row = {}

            for field in REPORT_FIELDS:
                formatted_row[field] = format_csv_number(
                    row.get(field, "")
                )

            writer.writerow(formatted_row)