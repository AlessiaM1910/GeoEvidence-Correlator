import os
from PIL import Image 
from PIL.ExifTags import TAGS, GPSTAGS


def estrai_exif(foto):   #prima verifichiamo che i dati ci siano ed esistano
    try:
        with Image.open(foto) as img:
            dati=img._getexif()
            if dati:       #se esistono retun come dizionario
                return dati
            else:
                return None
    except Exception as e:
        print("Impossibile leggere", foto, ":", e)
        return None

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
    if not tupla or len(tupla)!=3:  #perchè i GPS usano il sistema sessagesimale (come gli orologi)
        return None

    gradi=float(tupla[0])
    minuti=float(tupla[1])
    secondi=float(tupla[2])

    decimale=gradi + (minuti/ 60.0) + (secondi /3600.0)
    return decimale

def calcola_emisfero(valore, riferimento): #se la coordinata decimale è a S o W va convertita con segno negativo
    if valore is None or not riferimento:  #la Terra è vista dai GPS come un grande asse cartesiano (nord ed est sono positivi)
        return None

    if riferimento in ["S","W"]:
        return -valore

    return valore

def scansiona_cartella(cartella_base):
    candidati=0
    con_gps=0
    senza_gps=0
    non_leggibili=0

    risultati_gps=[]
    estensioni_valide=(".jpg", ".jpeg", ".tif",".tiff")

    for radice,cartelle,file in os.walk(cartella_base): #os.walk data cartella esplora tutti i file e sottocartelle
        for nome_file in file:
            if nome_file.lower().endswith(estensioni_valide):
                candidati += 1

                #funzioni per ricostruire percorsi (per evitare errori)
                percorso_completo = os.path.join(radice, nome_file)
                percorso_relativo = os.path.relpath(percorso_completo, cartella_base)

                try:
                    dati=estrai_exif(percorso_completo)
                    if dati:
                        gps_info= estrai_gps_info(dati)
                        if gps_info and "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                            
                            lat = calcola_emisfero(
                                converti_in_decimale(gps_info["GPSLatitude"]), 
                                gps_info.get("GPSLatitudeRef")
                            )
                            lon = calcola_emisfero(
                                converti_in_decimale(gps_info["GPSLongitude"]), 
                                gps_info.get("GPSLongitudeRef")
                            )
                            
                            if lat is not None and lon is not None:

                                timestamp= estra_timestamp(dati)

                                risultati_gps.append((lat, lon, percorso_relativo, timestamp))
                                con_gps += 1
                            else:
                                senza_gps += 1  # Formato GPS non valido
                        else:
                            senza_gps += 1  # Ha l'EXIF ma niente GPS
                    else:
                        senza_gps += 1  # Nessun EXIF trovato
                        
                except Exception:
                    non_leggibili += 1  # File corrotto

    print(f"File candidati: {candidati}")
    print(f"Foto con GPS valido: {con_gps}")
    print(f"Foto senza GPS: {senza_gps}")
    print(f"File non leggibili/corrotti: {non_leggibili}")
    
    return risultati_gps

def estra_timestamp(dati_exif):
    if not dati_exif:
        return "Data sconosciuta"

    exif_testuale= {TAGS.get(k,k): v for k, v in dati_exif.items()}  #vado a convertire il codice corrispondente al time stamp in formato testuale

    if "DateTimeOriginal" in exif_testuale:
        return exif_testuale["DateTimeOriginal"]
    elif "DateTimeDigitalized" in exif_testuale: #negli smartphone concide con momento dello scatto
        return exif_testuale["DateTimeDigitalized"]
    elif "DateTime" in exif_testuale:  #ultima modifica effettuata
        return exif_testuale["DateTime"]

    return "Data sconosciuta"


