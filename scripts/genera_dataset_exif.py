import json
import math
import os
import random
from datetime import datetime, timedelta

import piexif
from PIL import Image

#generiamo il manifest.json per annotare la risposta attesa dai test


CARTELLA_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

IMMAGINE_BASE = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "sorgenti",
    "base_cc0.jpg",
)

CARTELLA_OUTPUT = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "exif_sintetici",
    "immagini",
)

PERCORSO_MANIFEST = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "exif_sintetici",
    "manifest.json",
)

LAT_CENTRO = 39.36336
LON_CENTRO = 16.22622
RAGGIO_KM = 5.0

RAGGIO_TERRA_METRI = 6371000.0
LARGHEZZA_MASSIMA = 800
SEME_CASUALE = 20261015

NUMERO_DENTRO = 40
NUMERO_FUORI = 35
NUMERO_SENZA_GPS = 10
NUMERO_GPS_INCOMPLETO = 5
NUMERO_CORROTTI = 10


def decimale_in_dms(valore):
    valore = abs(float(valore))

    gradi = int(valore)
    minuti_decimali = (valore - gradi) * 60.0
    minuti = int(minuti_decimali)
    secondi_decimali = (minuti_decimali - minuti) * 60.0

    secondo_numeratore = int(round(secondi_decimali * 1000000))

    return ((gradi, 1),(minuti, 1),(secondo_numeratore, 1000000))

#da qui in poi vengono genrati vari tipi di immagini diversi (cono o senza GPS, corrotte ecc...)

def crea_exif_gps(latitudine, longitudine, timestamp):
    riferimento_lat = b"N"
    riferimento_lon = b"E"

    if latitudine < 0:
        riferimento_lat = b"S"

    if longitudine < 0:
        riferimento_lon = b"W"

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: riferimento_lat,
        piexif.GPSIFD.GPSLatitude: decimale_in_dms(latitudine),
        piexif.GPSIFD.GPSLongitudeRef: riferimento_lon,
        piexif.GPSIFD.GPSLongitude: decimale_in_dms(longitudine),
        piexif.GPSIFD.GPSMapDatum: b"WGS-84",
    }

    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: timestamp.encode("ascii"),
        piexif.ExifIFD.DateTimeDigitized: timestamp.encode("ascii"),
    }

    zeroth_ifd = {
        piexif.ImageIFD.Software: b"GeoEvidence synthetic dataset",
    }

    return piexif.dump({
        "0th": zeroth_ifd,
        "Exif": exif_ifd,
        "GPS": gps_ifd,
        "1st": {},
        "thumbnail": None,
    })


def crea_exif_senza_gps(timestamp):
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: timestamp.encode("ascii"),
        piexif.ExifIFD.DateTimeDigitized: timestamp.encode("ascii"),
    }

    zeroth_ifd = {
        piexif.ImageIFD.Software: b"GeoEvidence synthetic dataset",
    }

    return piexif.dump({
        "0th": zeroth_ifd,
        "Exif": exif_ifd,
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    })


def crea_exif_gps_incompleto(timestamp):
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b"N",
        piexif.GPSIFD.GPSLatitude: (
            (39, 1),
            (21, 1),
            (48, 1),
        ),
    }

    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: timestamp.encode("ascii"),
    }

    zeroth_ifd = {
        piexif.ImageIFD.Software: b"GeoEvidence synthetic dataset",
    }

    return piexif.dump({
        "0th": zeroth_ifd,
        "Exif": exif_ifd,
        "GPS": gps_ifd,
        "1st": {},
        "thumbnail": None,
    })


#vengono generate le immagini vere e proprie
def crea_jpeg_base(percorso_output):
    with Image.open(IMMAGINE_BASE) as immagine:
        immagine = immagine.convert("RGB")

        if immagine.width > LARGHEZZA_MASSIMA:
            rapporto = (float(LARGHEZZA_MASSIMA) / immagine.width)

            altezza = int(immagine.height * rapporto)

            immagine = immagine.resize((LARGHEZZA_MASSIMA, altezza),Image.Resampling.LANCZOS)

        immagine.save(percorso_output,"JPEG",quality=85,optimize=True,)


def crea_jpeg_con_exif(percorso_output, exif_bytes):
    crea_jpeg_base(percorso_output)
    piexif.insert(exif_bytes, percorso_output)


#genera coordinate valide intorno al centro che viene passato alla funzione
def punto_destinazione(latitudine,longitudine,distanza_metri,direzione_gradi):
    direzione = math.radians(direzione_gradi)
    distanza_angolare = (distanza_metri / RAGGIO_TERRA_METRI)

    latitudine_iniziale = math.radians(latitudine)
    longitudine_iniziale = math.radians(longitudine)

    latitudine_finale = math.asin(
        math.sin(latitudine_iniziale)
        * math.cos(distanza_angolare)
        + math.cos(latitudine_iniziale)
        * math.sin(distanza_angolare)
        * math.cos(direzione)
    )

    longitudine_finale = longitudine_iniziale + math.atan2(
        math.sin(direzione)
        * math.sin(distanza_angolare)
        * math.cos(latitudine_iniziale),
        math.cos(distanza_angolare)
        - math.sin(latitudine_iniziale)
        * math.sin(latitudine_finale),
    )

    latitudine_risultato = math.degrees(latitudine_finale)

    longitudine_risultato = (
        math.degrees(longitudine_finale) + 540.0
    ) % 360.0 - 180.0

    return latitudine_risultato, longitudine_risultato


def timestamp_per_indice(indice):  #ogni immagine avrà un timestamp con 1 minuto di differenza
    inizio = datetime(2026, 1, 1, 10, 0, 0)

    return (inizio + timedelta(minutes=indice)).strftime("%Y:%m:%d %H:%M:%S")


def aggiungi_record(
    manifest,
    nome_file,
    categoria,
    latitudine,
    longitudine,
    timestamp,
    esito_atteso,
):
    manifest.append({
        "nome_file": nome_file,
        "categoria": categoria,
        "lat": latitudine,
        "lon": longitudine,
        "timestamp": timestamp,
        "esito_atteso": esito_atteso,
    })


def main():
    if not os.path.isfile(IMMAGINE_BASE):
        print("Immagine base non trovata:")
        print(IMMAGINE_BASE)
        return

    os.makedirs(CARTELLA_OUTPUT, exist_ok=True)

    generatore_casuale = random.Random(SEME_CASUALE)
    manifest = []
    indice = 1

#vengono eseguiti 5 for diversi, ognuno per un tipo diverso di immagini da generare

    for numero in range(1, NUMERO_DENTRO + 1):
        distanza_metri = generatore_casuale.uniform(100.0,4500.0)

        direzione = generatore_casuale.uniform(0.0, 360.0)

        latitudine, longitudine = punto_destinazione(LAT_CENTRO,LON_CENTRO,distanza_metri,direzione)
        
        timestamp = timestamp_per_indice(indice)
        nome_file = "dentro_{:03d}.jpg".format(numero)
        percorso_output = os.path.join(CARTELLA_OUTPUT, nome_file)

        exif_bytes = crea_exif_gps(latitudine,longitudine,timestamp)

        crea_jpeg_con_exif(percorso_output,exif_bytes)

        aggiungi_record(
            manifest,
            nome_file,
            "gps_valido_dentro",
            latitudine,
            longitudine,
            timestamp,
            "DENTRO_RAGGIO",
        )

        indice += 1

    for numero in range(1, NUMERO_FUORI + 1):
        distanza_metri = generatore_casuale.uniform(5500.0,25000.0)

        direzione = generatore_casuale.uniform(0.0, 360.0)

        latitudine, longitudine = punto_destinazione(LAT_CENTRO,LON_CENTRO,distanza_metri,direzione)
        
        timestamp = timestamp_per_indice(indice)
        nome_file = "fuori_{:03d}.jpg".format(numero)
        percorso_output = os.path.join(CARTELLA_OUTPUT,nome_file)

        exif_bytes = crea_exif_gps(latitudine,longitudine,timestamp)

        crea_jpeg_con_exif(percorso_output,exif_bytes)

        aggiungi_record(
            manifest,
            nome_file,
            "gps_valido_fuori",
            latitudine,
            longitudine,
            timestamp,
            "FUORI_RAGGIO",
        )

        indice += 1

    for numero in range(1, NUMERO_SENZA_GPS + 1):
        timestamp = timestamp_per_indice(indice)
        nome_file = "senza_gps_{:03d}.jpg".format(numero)
        percorso_output = os.path.join(CARTELLA_OUTPUT,nome_file)

        exif_bytes = crea_exif_senza_gps(timestamp)

        crea_jpeg_con_exif(percorso_output,exif_bytes)

        aggiungi_record(
            manifest,
            nome_file,
            "senza_gps",
            None,
            None,
            timestamp,
            "SENZA_GPS",
        )

        indice += 1

    for numero in range(1, NUMERO_GPS_INCOMPLETO + 1):
        timestamp = timestamp_per_indice(indice)
        nome_file = "gps_incompleto_{:03d}.jpg".format(numero)
        percorso_output = os.path.join(CARTELLA_OUTPUT,nome_file)

        exif_bytes = crea_exif_gps_incompleto(timestamp)

        crea_jpeg_con_exif(percorso_output,exif_bytes)

        aggiungi_record(
            manifest,
            nome_file,
            "gps_incompleto",
            None,
            None,
            timestamp,
            "GPS_NON_VALIDO",
        )

        indice += 1

    for numero in range(1, NUMERO_CORROTTI + 1):
        nome_file = "corrotto_{:03d}.jpg".format(numero)
        percorso_output = os.path.join(CARTELLA_OUTPUT,nome_file)

        with open(percorso_output, "wb") as file_corrotto:
            file_corrotto.write(
                b"Questo non e un file JPEG valido.")

        aggiungi_record(
            manifest,
            nome_file,
            "file_corrotto",
            None,
            None,
            None,
            "NON_LEGGIBILE",
        )

        indice += 1

    with open(
        PERCORSO_MANIFEST,
        "w",
        encoding="utf-8",
    ) as file_manifest:
        json.dump(
            manifest,
            file_manifest,
            indent=4,
            ensure_ascii=False,
        )

    print("Dataset sintetico creato.")
    print("Cartella immagini:", CARTELLA_OUTPUT)
    print("Manifest:", PERCORSO_MANIFEST)
    print("File candidati attesi: 100")
    print("GPS validi attesi: 75")
    print("Dentro raggio attesi: 40")
    print("Fuori raggio attesi: 35")
    print("Senza GPS attesi: 10")
    print("GPS non validi attesi: 5")
    print("Non leggibili attesi: 10")


if __name__ == "__main__":
    main()