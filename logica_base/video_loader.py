import json
import os
import subprocess


class VideoNonLeggibileError(Exception):
    pass


class ExifToolNonDisponibileError(Exception):
    pass


ESTENSIONI_VIDEO = (".mp4", ".mov")

CAMPI_EXIFTOOL = (
    "-GPSLatitude",
    "-GPSLongitude",
    "-GPSAltitude",
    "-GPSDateTime",
    "-CreationDate",
    "-MediaCreateDate",
    "-CreateDate",
    "-TrackCreateDate",
)


def estrai_metadati_video(percorso_video, exiftool_path):
    """
    Esegue ExifTool in sola lettura e restituisce il primo oggetto JSON.
    """

    if not os.path.isfile(percorso_video):
        raise VideoNonLeggibileError(
            "File non trovato: {}".format(percorso_video)
        )

    comando = [exiftool_path,"-j","-n", "-s"]

    comando.extend(CAMPI_EXIFTOOL)
    comando.append(percorso_video)

    try:
        risultato = subprocess.run(
            comando,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as errore:
        raise ExifToolNonDisponibileError(str(errore))
    except OSError as errore:
        raise ExifToolNonDisponibileError(str(errore))

    if risultato.returncode != 0:
        raise VideoNonLeggibileError(
            risultato.stderr.strip()
        )

    try:
        dati = json.loads(risultato.stdout)
    except json.JSONDecodeError as errore:
        raise VideoNonLeggibileError(str(errore))

    if not dati:
        raise VideoNonLeggibileError(
            "ExifTool non ha restituito metadati"
        )

    return dati[0]


def estrai_gps_info_video(metadati):
    """
    Restituisce solo i dati GPS trovati da ExifTool.
    Se non esiste alcun GPS, restituisce None.
    """

    if not metadati:
        return None

    gps_info = {}

    for campo in (
        "GPSLatitude",
        "GPSLongitude",
        "GPSAltitude",
    ):
        valore = metadati.get(campo)

        if valore is not None:
            gps_info[campo] = valore

    if not gps_info:
        return None

    return gps_info


def converti_coordinata_decimale(valore, minimo, massimo):
    """
    ExifTool con -n restituisce già coordinate decimali.
    Qui controlliamo che siano numeri validi e nel range terrestre.
    """

    try:
        coordinata = float(valore)
    except (TypeError, ValueError):
        return None

    if not (minimo <= coordinata <= massimo):
        return None

    return coordinata


def estrai_timestamp_video(metadati):
    """
    Restituisce la prima data disponibile in ordine di affidabilità.
    """

    if not metadati:
        return "Data sconosciuta"

    campi_timestamp = (
        "GPSDateTime",
        "CreationDate",
        "MediaCreateDate",
        "CreateDate",
        "TrackCreateDate",
    )

    for campo in campi_timestamp:
        valore = metadati.get(campo)

        if valore:
            return valore

    return "Data sconosciuta"


def scansiona_cartella_video(cartella_base, exiftool_path):
    candidati = 0
    con_gps = 0
    senza_gps = 0
    gps_non_validi = 0
    non_leggibili = 0

    risultati_gps = []

    for radice, cartelle, file_nomi in os.walk(cartella_base):
        cartelle.sort()
        file_nomi.sort()

        for nome_file in file_nomi:
            if not nome_file.lower().endswith(
                ESTENSIONI_VIDEO
            ):
                continue

            candidati += 1

            percorso_completo = os.path.join(
                radice,
                nome_file,
            )

            percorso_relativo = os.path.relpath(
                percorso_completo,
                cartella_base,
            )

            try:
                metadati = estrai_metadati_video(
                    percorso_completo,
                    exiftool_path,
                )

                gps_info = estrai_gps_info_video(
                    metadati
                )

                if not gps_info:
                    senza_gps += 1
                    continue

                if (
                    "GPSLatitude" not in gps_info
                    or "GPSLongitude" not in gps_info
                ):
                    gps_non_validi += 1
                    continue

                latitudine = converti_coordinata_decimale(
                    gps_info["GPSLatitude"],
                    -90.0,
                    90.0,
                )

                longitudine = converti_coordinata_decimale(
                    gps_info["GPSLongitude"],
                    -180.0,
                    180.0,
                )

                if latitudine is None or longitudine is None:
                    gps_non_validi += 1
                    continue

                timestamp = estrai_timestamp_video(
                    metadati
                )

                risultati_gps.append((
                    latitudine,
                    longitudine,
                    percorso_relativo,
                    timestamp,
                ))

                con_gps += 1

            except VideoNonLeggibileError:
                non_leggibili += 1

    print("Video candidati: {}".format(candidati))
    print("Video con GPS valido: {}".format(con_gps))
    print("Video senza GPS: {}".format(senza_gps))
    print(
        "Video con GPS non valido: {}".format(
            gps_non_validi
        )
    )
    print(
        "Video non leggibili/corrotti: {}".format(
            non_leggibili
        )
    )

    return risultati_gps