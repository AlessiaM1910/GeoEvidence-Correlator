import os
import shutil

import piexif  #necessario per scrivere i metadati dentro le foto
#pillow lo usiamo per leggerli


CARTELLA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#definizione di input e output

IMMAGINE_BASE = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "sorgenti",
    "base_londra_cc0.jpg",
)

CARTELLA_OUTPUT = os.path.join(
    CARTELLA_ROOT,
    "dati_test",
    "exif_generati",
    "immagini",
)

IMMAGINE_OUTPUT = os.path.join(
    CARTELLA_OUTPUT,
    "prova_gps.jpg",
)


def decimale_in_dms(valore):# conversione da decimale in gradi
    valore = abs(float(valore)) #facciamo valore assoluto perchè il segno lo gestiamo per stabilire l'emisfero

    gradi = int(valore)

    minuti_decimali = (valore - gradi) * 60.0
    minuti = int(minuti_decimali)

    secondi_decimali = (minuti_decimali - minuti) * 60.0

    secondi_numeratore = int(round(secondi_decimali * 1000000))

    return ((gradi, 1),(minuti, 1),(secondi_numeratore, 1000000))  #ogni coppia è una frazione es (39,1) vuol dire che sono 39 gradi


def crea_exif_gps(latitudine, longitudine, timestamp):
    riferimento_lat = b"N" #queste non sono stringhe ma bytes, sono richiesti da piexif (libreria)
    riferimento_lon = b"E"

    if latitudine < 0:
        riferimento_lat = b"S"

    if longitudine < 0:
        riferimento_lon = b"W"

#prepara i campi del gps che andremo a riempire
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: riferimento_lat,
        piexif.GPSIFD.GPSLatitude: decimale_in_dms(latitudine),
        piexif.GPSIFD.GPSLongitudeRef: riferimento_lon,
        piexif.GPSIFD.GPSLongitude: decimale_in_dms(longitudine),
        piexif.GPSIFD.GPSMapDatum: b"WGS-84", #standard usato dal GPS
    }

    #inseriemnto timestamps
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: timestamp.encode("ascii"),
        piexif.ExifIFD.DateTimeDigitized: timestamp.encode("ascii")
    }

    #questo indica il software di provenienza, nel nostro caso il dataset sintetico
    zeroth_ifd = {
        piexif.ImageIFD.Software: (b"GeoEvidence synthetic dataset")
    }

    dizionario_exif = {
        "0th": zeroth_ifd,
        "Exif": exif_ifd,
        "GPS": gps_ifd,
        "1st": {},
        "thumbnail": None,
    }

    return piexif.dump(dizionario_exif)


def main():
    if not os.path.isfile(IMMAGINE_BASE):
        print("Immagine base non trovata:")
        print(IMMAGINE_BASE)
        return

    if not os.path.isdir(CARTELLA_OUTPUT):
        os.makedirs(CARTELLA_OUTPUT)

    latitudine = 39.36336
    longitudine = 16.22622
    timestamp = "2026:01:01 10:00:00"

    shutil.copyfile(IMMAGINE_BASE,IMMAGINE_OUTPUT) #viene effettuata una copia della foto originale

    try:
        piexif.remove(IMMAGINE_OUTPUT)
    except ValueError:
        pass

    exif_bytes = crea_exif_gps(
        latitudine,
        longitudine,
        timestamp,
    )

    piexif.insert(
        exif_bytes,
        IMMAGINE_OUTPUT,
    )

    print("Immagine sintetica creata:")
    print(IMMAGINE_OUTPUT)
    print(
        "Coordinate:",
        latitudine,
        longitudine,
    )
    print("Timestamp:", timestamp)


if __name__ == "__main__":
    main()