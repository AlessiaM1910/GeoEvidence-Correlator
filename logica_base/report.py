import csv

from core import distanza_haversine

#questo file serve per trasformare i dati di vari formatic (CSV, JSON, Foto) in righe che verranno salvate in un file CSV


CAMPI_REPORT = [
    "id",  #numero progressivo
    "nome_evidenza",
    "lat",
    "lon",
    "distanza_km", #distanza dal punto cercato
    "timestamp", #presente solo per le foto
    "tipo",
    "fonte",
    "esito", #se dentro o fuori raggio
]

def evidenze_da_punti(punti, fonte):
    evidenze=[]

    for lat, lon , nome in punti:
        evidenze.append({
            "nome_evidenza":nome,
            "lat": lat,
            "lon": lon,
            "timestamp": "",
            "tipo": "punto",
            "fonte": fonte
        })

    return evidenze

def evidenze_da_foto(foto):
    evidenze=[]

    for lat, lon, percorso, timestamp in foto:
        evidenze.append({
            "nome_evidenza": percorso,
            "lat": lat,
            "lon": lon,
            "timestamp": timestamp,
            "tipo": "foto",
            "fonte": "EXIF",
        })

    return evidenze

def classifica_reperti(evidenze, lat_centro, lon_centro, raggiokm):
    righe_report=[]

    for elemento in evidenze: #per ogni "prova" calcola la distanza tra quest'ultima e il centro passato alla funzione
        distanza= distanza_haversine(elemento["lat"], elemento["lon"], lat_centro, lon_centro)

        riga=dict(elemento) #crea una copia del dizionario senza alterare l'originale
        riga["distanza_km"]= round(distanza, 6)

        if distanza <= raggiokm:
            riga["esito"] = "DENTRO_RAGGIO"
        else:
            riga["esito"] = "FUORI_RAGGIO"

        righe_report.append(riga)

    righe_report.sort(key=lambda riga: riga["distanza_km"]) #righe ordinate in base alla distanza (da più vicina a più lontana)

    for indice, riga in enumerate(righe_report, start=1): 
        riga["id"] = indice  #assegna id progressivo

    return righe_report

def scrivi_report_csv(percorso_report, righe_report):
    with open(percorso_report, "w", newline="", encoding= "utf-8-sig") as file_report:
        scrittore=csv.DictWriter(file_report, fieldnames=CAMPI_REPORT, delimiter=";")

        scrittore.writeheader()

        for riga in righe_report:
            scrittore.writerow(riga)