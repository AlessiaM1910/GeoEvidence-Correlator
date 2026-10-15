# GeoEvidence-Correlator

## Funzionalita attuali

- Calcolo della distanza geografica tramite formula di Haversine.
- Verifica dell'appartenenza di un punto a un raggio geografico.
- Supporto per metri, chilometri e miglia tramite GeoRange.
- Caricamento di coordinate da file CSV e JSON.
- Estrazione di GPS e timestamp EXIF da immagini JPEG, TIFF e relativi formati supportati.
- Classificazione dei reperti dentro o fuori dal raggio.
- Generazione di report CSV.
- Dataset sintetico riproducibile con immagini JPEG e metadati EXIF artificiali.
- Test automatici unitari e di integrazione.

## Struttura del progetto

```text
GeoEvidence-Correlator/
|
|-- README.md                          #documentazione del progetto
|
|-- dati_test/                         #contiene l'immagien base+ dataset riproducibile
|   |-- ATTRIBUTION.md                 #contiene orgine e licenza dell'immagine base
|   |-- sorgenti/
|   |   `-- base_londra_cc0.jpg
|   `-- exif_sintetici/
|       |-- manifest.json              #descrizione e risultati attesi di ogni file
|       `-- immagini/                  #contiene JPEG sintetici
|
|-- scripts/                           #script di supporto per generare dataset
|   |-- prova_exif_sintetico.py        #prova scrittura exif in una sola immagine
|   `-- genera_dataset_exif.py         #generazione 100 immagini
|
`-- logica_base/
    |-- georange.py                    #liberia che contiene funzione che calcola distanza
    |-- core.py                        #contiene filtraggio punti
    |-- data_loader.py                 #caricamento coordinate da JSON e CSV
    |-- exif_loader.py                 #estrazione GPS e timestamp dalle immagini
    |-- report.py                      #genera report CSV
    |-- main.py
    |-- requirements.txt               #dipendenze necessarie
    |-- punti.csv                      #dati esempio
    |-- punti.json                     #dati esempio
    |-- test_georange.py               #test libreria georange
    `-- tests/                         #test unitari
        |-- test_core.py
        |-- test_data_loader.py
        |-- test_exif_loader.py
        |-- test_report.py
        `-- test_dataset_sintetico.py