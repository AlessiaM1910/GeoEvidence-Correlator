import csv
import json

def crea_punto(lat,lon,nome): #qui stabiliamo se un punto è valido o no
    try:
        lat=float(lat)  #converto i valori in float (perchè sono stringhe)
        lon=float(lon)
    except (ValueError, TypeError):
        return None

    if not(-90<= lat <=90): #controllo se la latitudine rientra nel range
        return None
    
    if not(-180<= lon <= 180): #controllo longitudine
        return None

    return (lat,lon,nome)



def carica_csv(percorso, campo_lat="lat", campo_lon="lon",campo_nome="nome"):
    punti=[]
    scartate= 0 #serve per contare le righe che vengono scartate se non rientrano nei parametri
    try:
        with open(percorso,newline="", encoding="utf-8") as f:
            lettore= csv.DictReader(f) #legge file aperto e lo converte in dizionario
            if campo_lat not in lettore.fieldnames or campo_lon not in lettore.fieldnames:
                print ("Colonne non trovate: attese", campo_lat, campo_lon, "trovate", lettore.fieldnames)
                return []

            for riga in lettore:
                punto=crea_punto(riga[campo_lat],riga[campo_lon],riga[campo_nome])
                if punto is None:
                    scartate+=1
                else:
                    punti.append(punto) #se il punto è valido lo aggiungiamo alla lista, questa diventerà il paremtro della funzione filtra punti in core.py
    except(FileNotFoundError, PermissionError) as e:
        print("Impossibile leggere il file:", percorso, "-", e)
        return []

    print("Righe scartate", scartate)
    return punti

def carica_json(percorso, campo_lat="lat", campo_lon="lon",campo_nome="nome" ):
    punti=[]
    scartate=0
    try:
        with open(percorso, encoding="utf-8") as f:
            dati=json.load(f)

        for elemento in dati:
            lat=elemento.get(campo_lat) #qui utilizzo get perchè in caso di dati mancanti o altro restituisce None
            lon=elemento.get(campo_lon)
            nome=elemento.get(campo_nome)

            punto=crea_punto(lat,lon,nome)
            if punto is None:
                scartate+=1
            else:
                punti.append(punto)
    except(FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
        print("Impossibile leggere il file:", percorso, "-", e)
        return []
    print("Righe scartate", scartate)
    return punti