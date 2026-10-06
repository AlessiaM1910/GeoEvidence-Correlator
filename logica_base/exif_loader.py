import os
from PIL import Image, UnidentifiedImageError 
from PIL.ExifTags import TAGS, GPSTAGS

'''
ABbiamo 4 casistiche da distinguere:
1. Foto leggibile con GPS valido
2. Foto leggibile senza GPS
3. Foto leggibile con GPS corrotto/non valido
4. File immagine corrotto o non leggibile'''

class FotoNonLeggibileError(Exception):
    pass

def estrai_exif(foto):   #prima verifichiamo che i dati ci siano ed esistano
    try:
        with Image.open(foto) as img:
            img.verify() #intercetta se è danneggiato 


        with Image.open(foto) as img:
            dati=img._getexif()

        return dati
    
    except (UnidentifiedImageError, OSError, ValueError) as errore:
        raise FotoNonLeggibileError(str(errore))

def estrai_gps_info(dati_exif):
    if not dati_exif:
        return None
    for tag_id, valore in dati_exif.items():
        nome_tag=TAGS.get(tag_id, tag_id)
        if nome_tag == "GPSInfo":
            dizionario_gps = {}
            for sub_id, sub_valore in valore.items():
                nome_sub_tag = GPSTAGS.get(sub_id, sub_id)
                dizionario_gps[nome_sub_tag] = sub_valore
            return dizionario_gps
    return None

def converti_in_decimale(tupla): #converiamo i valori gradi, minuti secondi in gradi decimali
    try:
        if len(tupla)!=3:  #perchè i GPS usano il sistema sessagesimale (come gli orologi)
            return None
    
        gradi=float(tupla[0])
        minuti=float(tupla[1])
        secondi=float(tupla[2])
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    if gradi < 0 or minuti < 0 or secondi < 0:
        return None
    
    if minuti >= 60 or secondi >= 60:
        return None

    decimale=gradi + (minuti/ 60.0) + (secondi /3600.0)
    return decimale

def calcola_emisfero(valore, riferimento, asse): #se la coordinata decimale è a S o W va convertita con segno negativo
    if valore is None or not riferimento:  #la Terra è vista dai GPS come un grande asse cartesiano (nord ed est sono positivi)
        return None

    riferimento = str(riferimento).strip().upper()

    riferimenti_validi = {
        "latitudine": {
            "N": 1,
            "S": -1,
        },
        "longitudine": {
            "E": 1,
            "W": -1,
        },
    }

    if asse not in riferimenti_validi:
        return None

    segno = riferimenti_validi[asse].get(riferimento)

    if segno is None:
        return None

    return segno * valore

def scansiona_cartella(cartella_base):
    candidati=0 #tutte le foto
    con_gps=0 #hanno il gps valido
    senza_gps=0 #niente exif o gps
    gps_non_validi=0 #gps presente ma incompleto
    non_leggibili=0 #file non apribile

    risultati_gps=[]
    estensioni_valide=(".jpg", ".jpeg", ".tif",".tiff")

    for radice,cartelle,file in os.walk(cartella_base): #os.walk data cartella esplora tutti i file e sottocartelle
        cartelle.sort()
        file.sort()
        for nome_file in file:
            if nome_file.lower().endswith(estensioni_valide):
                candidati += 1

                #funzioni per ricostruire percorsi (per evitare errori)
                percorso_completo = os.path.join(radice, nome_file)
                percorso_relativo = os.path.relpath(percorso_completo, cartella_base)

                try:
                    dati=estrai_exif(percorso_completo)
                    if dati:
                        gps_info = estrai_gps_info(dati)

                        if not gps_info:
                            senza_gps += 1

                        elif (
                            "GPSLatitude" not in gps_info
                            or "GPSLongitude" not in gps_info
                        ):
                            gps_non_validi += 1

                        else:
                            lat = calcola_emisfero(
                                converti_in_decimale(gps_info["GPSLatitude"]),
                                gps_info.get("GPSLatitudeRef"),
                                "latitudine",
                            )

                            lon = calcola_emisfero(
                                converti_in_decimale(gps_info["GPSLongitude"]),
                                gps_info.get("GPSLongitudeRef"),
                                "longitudine",
                            )

                            if lat is None or lon is None:
                                gps_non_validi += 1

                            elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
                                gps_non_validi += 1

                            else:
                                timestamp = estrai_timestamp(dati)

                                risultati_gps.append(
                                    (lat, lon, percorso_relativo, timestamp)
                                )

                                con_gps += 1

                    else:
                        senza_gps += 1
                        
                except FotoNonLeggibileError:
                    non_leggibili += 1  # File corrotto

    print(f"File candidati: {candidati}")
    print(f"Foto con GPS valido: {con_gps}")
    print(f"Foto senza GPS: {senza_gps}")
    print(f"Foto con GPS non valido: {gps_non_validi}")
    print(f"File non leggibili/corrotti: {non_leggibili}")
    
    return risultati_gps

def estrai_timestamp(dati_exif):
    if not dati_exif:
        return "Data sconosciuta"

    exif_testuale= {TAGS.get(k,k): v for k, v in dati_exif.items()}  #vado a convertire il codice corrispondente al time stamp in formato testuale

    if "DateTimeOriginal" in exif_testuale:
        return exif_testuale["DateTimeOriginal"]
    elif "DateTimeDigitized" in exif_testuale: #negli smartphone concide con momento dello scatto
        return exif_testuale["DateTimeDigitized"]
    elif "DateTime" in exif_testuale:  #ultima modifica effettuata
        return exif_testuale["DateTime"]

    return "Data sconosciuta"


