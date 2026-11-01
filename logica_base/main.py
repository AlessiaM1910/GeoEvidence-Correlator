import os
from core import filter_points
from data_loader import load_csv, load_json
from exif_loader import scan_image_directory
from video_loader import scan_video_directory
from report import (classify_evidence,evidence_from_images,evidence_from_videos,evidence_from_points,write_csv_report)



def chiedi_parametri_ricerca(): #valori test usati: lat 41.8902 , long 12.4922. raggio 5 
    while True:
        try:
            lat_centro = float(input("Latitudine del centro: "))
            if not (-90 <= lat_centro <= 90): #se metto valori duori dal range chiede di nuovo di reinserirlo
                print("Latitudine non valida, deve essere compresa tra -90 e 90")
                continue
            lon_centro = float(input("Longitudine del centro: "))
            if not (-180 <= lon_centro <= 180):
                print("Longitudine non valida, deve essere compresa tra -180 e 180")
                continue
            raggiokm = float(input("Raggio di ricerca (km): "))
            if raggiokm < 0:
                print("Il raggio deve essere maggiore di zero")
                continue

            return lat_centro, lon_centro, raggiokm

        except ValueError:
            print("Inserire numeri validi")

def main():
    cartella = os.path.dirname(os.path.abspath(__file__))
    radice_progetto = os.path.dirname(cartella)

    percorso_csv = os.path.join(cartella, "punti.csv")
    percorso_json = os.path.join(cartella, "punti.json")

    cartella_foto = os.path.join(
        radice_progetto,
        "dati_test",
        "exif_sintetici",
        "immagini",
    )

    cartella_video = os.path.join(
        radice_progetto,
        "dati_test",
        "video_sintetici",
        "video",
    )

    percorso_exiftool = os.environ.get("EXIFTOOL_PATH")

    if not percorso_exiftool:
        print("Imposta la variabile EXIFTOOL_PATH prima di eseguire il programma.")
        return

    punti_csv=load_csv(percorso_csv)
    punti_json=load_json(percorso_json)
    evidenze_foto = scan_image_directory(cartella_foto)
    evidenze_video = scan_video_directory(cartella_video,percorso_exiftool)

    punti_foto = []  #qui effettuiamo conversione nel formato richiesto dalla funzione filtra punti

    for lat, lon, percorso_relativo, timestamp in evidenze_foto:
        punti_foto.append((lat, lon, percorso_relativo))

    print("Foto con GPS caricate:", len(punti_foto))

    punti_video = [] #qua carichiamo punti video

    for lat, lon, percorso_relativo, timestamp in evidenze_video:
        punti_video.append((lat, lon, percorso_relativo))

    print("Video con GPS caricati:", len(punti_video))

    tutti_punti=punti_csv + punti_json + punti_foto + punti_video #questo rimane utile per la funzione filtra punti

    evidenze_report= evidence_from_points(punti_csv,"CSV") + evidence_from_points(punti_json, "JSON") + evidence_from_images(evidenze_foto) + evidence_from_videos(evidenze_video) #contiene tutte le informazioni che servono nel CSV

    if len(tutti_punti)== 0:
        print("Nessun punto caricato")
        return

    lat_centro, lon_centro, raggiokm= chiedi_parametri_ricerca() #prendo i parametri da input

    righe_report = classify_evidence(evidenze_report,lat_centro,lon_centro,raggiokm)

    percorso_report = os.path.join(cartella,"report_geoevidence.csv")

    write_csv_report(percorso_report,righe_report)

    print("Report creato:", percorso_report)

    risultati=filter_points(tutti_punti, lat_centro, lon_centro, raggiokm) #faccio il calcolo della distanza

    if len(risultati)>0: #stampa per test
        print("PROVE DENTRO IL RAGGIO")
        for nome,distanza in risultati:
            if distanza < 1:
                print("[DENTRO]", nome, "a", round(distanza * 1000, 1),"m")  #se la distanza è ingferiore a 1km la stampiamo in metri
            else:
                print("[DENTRO]", nome, "a", round(distanza, 3), "km")
    else:
        print("Nessuna evidenza trovata")

    fuori_raggio = len(tutti_punti) - len(risultati)

    print("Numero evidenze fuori raggio:", fuori_raggio)

if __name__=="__main__":
    main()




