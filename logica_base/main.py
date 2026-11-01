import os

from core import filter_points
from data_loader import load_csv, load_json
from exif_loader import scan_image_directory
from report import (classify_evidence,evidence_from_images,evidence_from_points,evidence_from_videos,write_csv_report)
from video_loader import scan_video_directory


def request_search_parameters():
    """Request and validate the geographic search center and radius.

    Returns:
        A tuple containing center latitude, center longitude and radius in km.
    """
    while True:
        try:
            center_latitude = float(input("Center latitude: "))

            if not (-90 <= center_latitude <= 90):
                print("Invalid latitude. It must be between -90 and 90.")
                continue

            center_longitude = float(input("Center longitude: "))

            if not (-180 <= center_longitude <= 180):
                print("Invalid longitude. It must be between -180 and 180.")
                continue

            radius_km = float(input("Search radius (km): "))

            if radius_km < 0:
                print("Radius must be zero or greater.")
                continue

            return (center_latitude,center_longitude,radius_km)

        except ValueError:
            print("Enter valid numeric values.")


def main():
    """Load evidence, classify it by radius and create a CSV report."""
    logic_directory = os.path.dirname(os.path.abspath(__file__))

    project_root = os.path.dirname(logic_directory)

    csv_path = os.path.join(logic_directory,"punti.csv")

    json_path = os.path.join(logic_directory,"punti.json")

    image_directory = os.path.join(project_root,"dati_test","exif_sintetici","immagini")

    video_directory = os.path.join(project_root,"dati_test","video_sintetici","video")

    exiftool_path = os.environ.get("EXIFTOOL_PATH")

    if not exiftool_path:
        print("Set EXIFTOOL_PATH before running the program.")
        return

    csv_points = load_csv(csv_path)
    json_points = load_json(json_path)

    image_results = scan_image_directory(image_directory)

    video_results = scan_video_directory(video_directory,exiftool_path)

    image_points = []

    for latitude, longitude, relative_path, timestamp in image_results:
        image_points.append((latitude,longitude,relative_path,))

    print("Images with GPS loaded:",len(image_points))

    video_points = []

    for latitude, longitude, relative_path, timestamp in video_results:
        video_points.append((latitude,longitude,relative_path))

    print("Videos with GPS loaded:",len(video_points))

    all_points = (csv_points + json_points + image_points + video_points)

    report_evidence = (
        evidence_from_points(csv_points, "CSV")
        + evidence_from_points(json_points, "JSON")
        + evidence_from_images(image_results)
        + evidence_from_videos(video_results)
    )

    if not all_points:
        print("No points loaded.")
        return

    (center_latitude,center_longitude,radius_km) = request_search_parameters()

    report_rows = classify_evidence(
        report_evidence,
        center_latitude,
        center_longitude,
        radius_km,
    )

    report_path = os.path.join(logic_directory,"report_geoevidence.csv")

    write_csv_report(report_path,report_rows)

    print("Report created:", report_path)

    results = filter_points(
        all_points,
        center_latitude,
        center_longitude,
        radius_km,
    )

    if results:
        print("EVIDENCE INSIDE RADIUS")

        for name, distance_km in results:
            if distance_km < 1:
                print("[INSIDE]",name,"at",round(distance_km * 1000, 1),"m",)
            else:
                print("[INSIDE]",name,"at",round(distance_km, 3),"km")
    else:
        print("No evidence found inside radius.")

    outside_radius_count = len(all_points) - len(results)

    print("Evidence outside radius:",outside_radius_count)


if __name__ == "__main__":
    main()