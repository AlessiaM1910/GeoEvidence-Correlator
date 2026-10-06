import os
from core import filtra_punti
from data_loader import carica_csv, carica_json

def chiedi_parametri_ricerca(): #valori test usati: lat 41.8902 , long 12.4922. raggio 5 
    while True:
        try:
            lat_centro = float(input("Latitudine del centro: "))
            if not (-90 <= lat_centro <= 90): #se metto valori duori dal range chiede di nuovo di reinserirlo
                print("Latitudine non valida, deve essere compresa tra -90 e 90")
                continue
            long_centro = float(input("Longitudine del centro: "))
            if not (-180 <= long_centro <= 180):
                print("Longitudine non valida, deve essere compresa tra -180 e 180")
                continue
            raggiokm = float(input("Raggio di ricerca (km): "))
            if raggiokm <= 0:
                print("Il raggio deve essere maggiore di zero")
                continue

            return lat_centro, long_centro, raggiokm

        except ValueError:
            print("Inserire numeri validi")

def main():
    cartella=os.path.dirname(os.path.abspath(__file__))
    percorso_csv=os.path.join(cartella, "punti.csv")
    percorso_json=os.path.join(cartella, "punti.json")

    punti_csv=carica_csv(percorso_csv)
    punti_json=carica_json(percorso_json)

    tutti_punti=punti_csv + punti_json

    if len(tutti_punti)== 0:
        print("Nessun punto caricato")
        return

    lat_centro, long_centro, raggiokm= chiedi_parametri_ricerca() #prendo i parametri da input

    risultati=filtra_punti(tutti_punti, lat_centro, long_centro, raggiokm) #faccio il calcolo della distanza

    if len(risultati)>0: #stampa per test
        for nome,distanza in risultati:
            print(nome, "a", distanza, "km")
    else:
        print("Nessuna evidenza trovata")

if __name__=="__main__":
    main()




