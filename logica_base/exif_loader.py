import os
from PIL import Image, UnidentifiedImageError 
from PIL.ExifTags import TAGS, GPSTAGS

'''
ABbiamo 4 casistiche da distinguere:
1. Foto leggibile con GPS valido
2. Foto leggibile senza GPS
3. Foto leggibile con GPS corrotto/non valido
4. File immagine corrotto o non leggibile'''

VALID_IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
)

class UnreadableImageError(Exception):
    """Raised when an image cannot be opened or validated."""
    pass

def extract_exif(image_path):   
    """Extract raw EXIF data from an image file.

    Args:
        image_path: Path of the image file.

    Returns:
        Raw EXIF metadata, or None when metadata is unavailable.

    Raises:
        UnreadableImageError: If the image cannot be read or is corrupt.
    """
    try:
        with Image.open(image_path) as img:
            img.verify() #intercetta se è danneggiato 


        with Image.open(image_path) as img:
            exif_data=img._getexif()

        return exif_data
    
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise UnreadableImageError(str(error))

def extract_gps_info(exif_data):
    """Extract and translate the GPS information from raw EXIF data.

    Args:
        exif_data: Raw EXIF metadata dictionary.

    Returns:
        A GPS metadata dictionary, or None if GPS data is unavailable.
    """
    if not exif_data:
        return None
    for tag_id, value in exif_data.items():
        tag_name=TAGS.get(tag_id, tag_id)
        if tag_name == "GPSInfo":
            gps_data = {}
            for sub_id, sub_value in value.items():
                sub_tag_name = GPSTAGS.get(sub_id, sub_id)
                gps_data[sub_tag_name] = sub_value
            return gps_data
    return None

def dms_to_decimal(dms_tupla):
    """Convert GPS degrees, minutes and seconds to decimal degrees.

    Args:
        dms_tuple: Tuple containing degrees, minutes and seconds.

    Returns:
        Decimal-degree value, or None if the value is invalid.
    """
    try:
        if len(dms_tupla)!=3:  #perchè i GPS usano il sistema sessagesimale (come gli orologi)
            return None
    
        degrees=float(dms_tupla[0])
        minutes=float(dms_tupla[1])
        seconds=float(dms_tupla[2])
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    if degrees < 0 or minutes < 0 or seconds < 0:
        return None
    
    if minutes >= 60 or seconds >= 60:
        return None

    decimal=degrees + (minutes/ 60.0) + (seconds /3600.0)
    return decimal

def apply_hemisphere(decimal_value, reference, axis): #se la coordinata decimale è a S o W va convertita con segno negativo
    """Apply the correct sign to a coordinate using the GPS hemisphere.

    Args:
        decimal_value: Unsigned coordinate in decimal degrees.
        reference: GPS hemisphere reference, such as N, S, E or W.
        axis: Coordinate axis: latitude or longitude.

    Returns:
        Signed coordinate in decimal degrees, or None if invalid.
    """
    if decimal_value is None or not reference:  #la Terra è vista dai GPS come un grande asse cartesiano (nord ed est sono positivi)
        return None

    reference = str(reference).strip().upper()

    valid_references = {
        "latitude": {
            "N": 1,
            "S": -1,
        },
        "longitude": {
            "E": 1,
            "W": -1,
        },
    }

    if axis not in valid_references:
        return None

    sign = valid_references[axis].get(reference)

    if sign is None:
        return None

    return sign * decimal_value

def scan_image_directory(base_directory):
    """Scan images recursively and return files with valid GPS coordinates.

    Args:
        base_directory: Root directory to scan.

    Returns:
        Tuples in the format
        (latitude, longitude, relative_path, timestamp).
    """

    candidate_files=0 #tutte le foto
    valid_gps_image=0 #hanno il gps valido
    without_gps=0 #niente exif o gps
    images_with_invalid_gps=0 #gps presente ma incompleto
    unreadable_images=0 #file non apribile

    gps_results=[]

    for root,directories,files in os.walk(base_directory): #os.walk data cartella esplora tutti i file e sottocartelle
        directories.sort()
        files.sort()
        for filenames in files:
            if filenames.lower().endswith(VALID_IMAGE_EXTENSIONS):
                candidate_files += 1

                #funzioni per ricostruire percorsi (per evitare errori)
                full_path = os.path.join(root, filenames)
                relative_path = os.path.relpath(full_path, base_directory)

                try:
                    exif_data=extract_exif(full_path)
                    if exif_data:
                        gps_info = extract_gps_info(exif_data)

                        if not gps_info:
                            without_gps += 1

                        elif (
                            "GPSLatitude" not in gps_info
                            or "GPSLongitude" not in gps_info
                        ):
                            images_with_invalid_gps += 1

                        else:
                            lat = apply_hemisphere(
                                dms_to_decimal(gps_info["GPSLatitude"]),
                                gps_info.get("GPSLatitudeRef"),
                                "latitude",
                            )

                            lon = apply_hemisphere(
                                dms_to_decimal(gps_info["GPSLongitude"]),
                                gps_info.get("GPSLongitudeRef"),
                                "longitude",
                            )

                            if lat is None or lon is None:
                                images_with_invalid_gps += 1

                            elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
                                images_with_invalid_gps += 1

                            else:
                                timestamp = extract_timestamp(exif_data)

                                gps_results.append(
                                    (lat, lon, relative_path, timestamp)
                                )

                                valid_gps_image += 1

                    else:
                        senza_gps += 1
                        
                except UnreadableImageError:
                    unreadable_images += 1  # File corrotto

    print("Candidate files:", candidate_files)
    print("Images with valid GPS:", valid_gps_image)
    print("Images without GPS:", without_gps)
    print("Images with invalid GPS:",images_with_invalid_gps,)
    print("Unreadable or corrupt images:", unreadable_images)

    return gps_results

def extract_timestamp(exif_data):
    """Extract the preferred timestamp from image EXIF metadata.

    Args:
        exif_data: Raw EXIF metadata dictionary.

    Returns:
        The best available EXIF timestamp, or ``Unknown date``.
    """
    if not exif_data:
        return "Unknown date"

    readable_exif= {TAGS.get(k,k): v for k, v in exif_data.items()}  #vado a convertire il codice corrispondente al time stamp in formato testuale

    if "DateTimeOriginal" in readable_exif:
        return readable_exif["DateTimeOriginal"]
    elif "DateTimeDigitized" in readable_exif: #negli smartphone concide con momento dello scatto
        return readable_exif["DateTimeDigitized"]
    elif "DateTime" in readable_exif:  #ultima modifica effettuata
        return readable_exif["DateTime"]

    return "Unknown date"


