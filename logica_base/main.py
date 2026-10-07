import os
from core import filtra_punti
from data_loader import carica_csv, carica_json
from exif_loader import scansiona_cartella
from report import classifica_reperti,evidenze_da_foto,evidenze_da_punti,scrivi_report_csv

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
    cartella=os.path.dirname(os.path.abspath(__file__))
    percorso_csv=os.path.join(cartella, "punti.csv")
    percorso_json=os.path.join(cartella, "punti.json")
    cartella_foto = os.path.join(cartella, "foto_test")

    punti_csv=carica_csv(percorso_csv)
    punti_json=carica_json(percorso_json)
    evidenze_foto = scansiona_cartella(cartella_foto)

    punti_foto = []  #qui effettuiamo conversione nel formato richiesto dalla funzione filtra punti

    for lat, lon, percorso_relativo, timestamp in evidenze_foto:
        punti_foto.append((lat, lon, percorso_relativo))

    print("Foto con GPS caricate:", len(punti_foto))

    tutti_punti=punti_csv + punti_json + punti_foto #questo rimane utile per la funzione filtra punti

    evidenze_report= evidenze_da_punti(punti_csv,"CSV") + evidenze_da_punti(punti_json, "JSON") + evidenze_da_foto(evidenze_foto) #contiene tutte le informazioni che servono nel CSV

    if len(tutti_punti)== 0:
        print("Nessun punto caricato")
        return

    lat_centro, lon_centro, raggiokm= chiedi_parametri_ricerca() #prendo i parametri da input

    righe_report = classifica_reperti(evidenze_report,lat_centro,lon_centro,raggiokm)

    percorso_report = os.path.join(cartella,"report_geoevidence.csv")

    scrivi_report_csv(percorso_report,righe_report)

    print("Report creato:", percorso_report)

    risultati=filtra_punti(tutti_punti, lat_centro, lon_centro, raggiokm) #faccio il calcolo della distanza

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




