import csv
import json

def crea_punto(lat,lon,nome): #qui stabiliamo se un punto è valido o no
    try:
        lat=float(lat)
        lon=float(lon)
    except (ValueError, TypeError):
        return None

    if not(-90<= lat <=90):
        return None
    
    if not(-180<= lon <= 180):
        return None

    return (lat,lon,nome)



def carica_csv(percorso, campo_lat="lat", campo_lon="lon",campo_nome="nome"):
    punti=[]
    scartate= 0
    with open(percorso,newline="", encoding="utf-8") as f:
        lettore= csv.DictReader(f) #legge file aperto e lo converte in dizionario
        for riga in lettore:
            punto=crea_punto(riga[campo_lat],riga[campo_lon],riga[campo_nome])
            if punto is None:
                scartate+=1
            else:
                punti.append(punto)
        print("Righe scartate", scartate)
    return punti

def carica_json(percorso, campo_lat="lat", campo_lon="lon",campo_nome="nome" ):
    punti=[]
    scartate=0
    with open(percorso, encoding="utf-8") as f:
        dati=json.load(f)

    for elemento in dati:
        lat=elemento.get(campo_lat)
        lon=elemento.get(campo_lon)
        nome=elemento.get(campo_nome)

        punto=crea_punto(lat,lon,nome)
        if punto is None:
            scartate+=1
        else:
            punti.append(punto)
    print("Righe scartate", scartate)
    return punti