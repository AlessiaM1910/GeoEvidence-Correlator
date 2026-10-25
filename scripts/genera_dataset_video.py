import argparse
import json
import os
import shutil
import subprocess


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DEFAULT_SOURCE_VIDEO = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "video_sintetici",
    "sorgenti",
    "video_base_cc0.mp4",
)

OUTPUT_DIRECTORY = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "video_sintetici",
    "video",
)

MANIFEST_PATH = os.path.join(
    PROJECT_ROOT,
    "dati_test",
    "video_sintetici",
    "manifest.json",
)

GPS_LATITUDE = 39.375155
GPS_LONGITUDE = 16.271693
GPS_ALTITUDE = 100.0

GPS_TIMESTAMP = "2026:01:01 10:01:00+01:00"
NO_GPS_TIMESTAMP = "2026:01:01 11:16:00+01:00"


class ExifToolExecutionError(Exception):
    """Eccezione sollevata quando Exiftool non riesce a caricare o aggiornare il video"""


def run_exiftool(exiftool_path, arguments):
    """
    Serve ad eseguire Exiftool
    
    """
    command = [exiftool_path] + arguments

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error_message = result.stderr.strip()

        if not error_message:
            error_message = result.stdout.strip()

        raise ExifToolExecutionError(error_message)


def ensure_output_can_be_created(output_path, overwrite):
    """
    Prevents accidental replacement of an existing generated file.

    Args:
        output_path: Path of the file that will be generated.
        overwrite: True when existing generated files may be replaced.

    Raises:
        FileExistsError: If the file exists and overwrite is disabled.
    """
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(
            "Output file already exists: {0}\n"
            "Run the script again with --overwrite "
            "to replace generated files.".format(output_path)
        )


def copy_source_video(source_path, output_path, overwrite):
    """
    Copies the neutral source video to a generated dataset path.

    Args:
        source_path: Source MP4 path.
        output_path: Destination MP4 path.
        overwrite: True when existing generated files may be replaced.
    """
    ensure_output_can_be_created(output_path, overwrite)
    shutil.copyfile(source_path, output_path)


def write_gps_metadata(exiftool_path, video_path):
    """
    Writes synthetic ISO 6709 GPS metadata and a creation timestamp.

    Args:
        exiftool_path: Absolute path to the ExifTool executable.
        video_path: Generated MP4 that will receive GPS metadata.
    """
    coordinates = (
        "+{0:.6f}+{1:.6f}+{2:.1f}/"
    ).format(
        GPS_LATITUDE,
        GPS_LONGITUDE,
        GPS_ALTITUDE,
    )

    run_exiftool(
        exiftool_path,
        [
            "-overwrite_original",
            "-Keys:GPSCoordinates={0}".format(coordinates),
            "-Keys:CreationDate={0}".format(
                GPS_TIMESTAMP
            ),
            video_path,
        ],
    )


def write_no_gps_metadata(exiftool_path, video_path):
    """
    Ensures that a generated MP4 has no GPS coordinates and has a timestamp.

    Args:
        exiftool_path: Absolute path to the ExifTool executable.
        video_path: Generated MP4 without GPS metadata.
    """
    run_exiftool(
        exiftool_path,
        [
            "-overwrite_original",
            "-Keys:GPSCoordinates=",
            "-Keys:CreationDate={0}".format(
                NO_GPS_TIMESTAMP
            ),
            video_path,
        ],
    )


def create_corrupted_video(output_path, overwrite):
    """
    Creates a file with an MP4 extension but intentionally invalid content.

    Args:
        output_path: Destination path for the invalid test file.
        overwrite: True when existing generated files may be replaced.
    """
    ensure_output_can_be_created(output_path, overwrite)

    with open(output_path, "wb") as corrupted_file:
        corrupted_file.write(
            b"This is intentionally not a valid MP4 file."
        )


def write_manifest():
    """
    Writes the expected properties of all generated video test files.
    """
    manifest = [
        {
            "nome_file": "con_gps.mp4",
            "categoria": "gps_valido",
            "lat": GPS_LATITUDE,
            "lon": GPS_LONGITUDE,
            "altitudine": GPS_ALTITUDE,
            "timestamp": GPS_TIMESTAMP,
            "esito_atteso": "GPS_VALIDO",
        },
        {
            "nome_file": "senza_gps.mp4",
            "categoria": "senza_gps",
            "lat": None,
            "lon": None,
            "altitudine": None,
            "timestamp": NO_GPS_TIMESTAMP,
            "esito_atteso": "SENZA_GPS",
        },
        {
            "nome_file": "corrotto.mp4",
            "categoria": "file_corrotto",
            "lat": None,
            "lon": None,
            "altitudine": None,
            "timestamp": None,
            "esito_atteso": "NON_LEGGIBILE",
        },
    ]

    with open(
        MANIFEST_PATH,
        "w",
        encoding="utf-8",
    ) as manifest_file:
        json.dump(
            manifest,
            manifest_file,
            indent=4,
            ensure_ascii=False,
        )


def generate_dataset(source_path, exiftool_path, overwrite):
    """
    Generates the synthetic MP4 dataset and its manifest.

    Args:
        source_path: Neutral CC0 MP4 used as the visual source.
        exiftool_path: Absolute path to the ExifTool executable.
        overwrite: True when existing generated files may be replaced.

    Raises:
        FileNotFoundError: If the source MP4 or ExifTool executable is missing.
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(
            "Source video not found: {0}".format(source_path)
        )

    if not os.path.isfile(exiftool_path):
        raise FileNotFoundError(
            "ExifTool executable not found: {0}".format(
                exiftool_path
            )
        )

    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    gps_video = os.path.join(
        OUTPUT_DIRECTORY,
        "con_gps.mp4",
    )

    no_gps_video = os.path.join(
        OUTPUT_DIRECTORY,
        "senza_gps.mp4",
    )

    corrupted_video = os.path.join(
        OUTPUT_DIRECTORY,
        "corrotto.mp4",
    )

    copy_source_video(
        source_path,
        gps_video,
        overwrite,
    )

    write_gps_metadata(
        exiftool_path,
        gps_video,
    )

    copy_source_video(
        source_path,
        no_gps_video,
        overwrite,
    )

    write_no_gps_metadata(
        exiftool_path,
        no_gps_video,
    )

    create_corrupted_video(
        corrupted_video,
        overwrite,
    )

    write_manifest()

    print("Synthetic video dataset created.")
    print("Output directory: {0}".format(
        OUTPUT_DIRECTORY
    ))
    print("Manifest: {0}".format(MANIFEST_PATH))


def main():
    """
    Reads command-line arguments and starts dataset generation.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a small synthetic MP4 dataset "
            "for GeoEvidence Correlator."
        )
    )

    parser.add_argument(
        "--exiftool",
        required=True,
        help="Absolute path to exiftool.exe.",
    )

    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE_VIDEO,
        help=(
            "Optional path to the neutral source MP4. "
            "The project default is used when omitted."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace previously generated dataset files.",
    )

    arguments = parser.parse_args()

    generate_dataset(
        arguments.source,
        arguments.exiftool,
        arguments.overwrite,
    )


if __name__ == "__main__":
    main()