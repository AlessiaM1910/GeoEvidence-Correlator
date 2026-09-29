import os
from core import filtra_punti
from data_loader import carica_csv, carica_json

cartella=os.path.dirname(os.path.abspath(__file__))
percorso_csv=os.path.join(cartella, "punti.csv")
percorso_json=os.path.join(cartella, "punti.json")

punti_csv=carica_csv(percorso_csv)
punti_json=carica_json(percorso_json)


print("Punti da CSV:")
for p in punti_csv:
    print("  ", p)

print("Punti da JSON:")
for p in punti_json:
    print("  ", p)

print("Sono uguali?", punti_csv == punti_json)

print("\nFiltro entro 100 km dal Duomo di Milano:")
print(filtra_punti(punti_csv, 45.4642, 9.1900, 100))