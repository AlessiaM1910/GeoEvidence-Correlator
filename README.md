# GeoEvidence-Correlator

## Funzionalita attuali

- Calcolo della distanza geografica tramite formula di Haversine.
- Verifica dell'appartenenza di un punto a un raggio geografico.
- Supporto per metri, chilometri e miglia tramite GeoRange.
- Caricamento di coordinate da file CSV e JSON.
- Estrazione di GPS e timestamp EXIF da immagini JPEG, TIFF e relativi formati supportati.
- Estrazione di GPS e timestamp da video MP4 e MOV tramite ExifTool.
- Dataset sintetico riproducibile con video MP4 e metadati GPS artificiali.
- Classificazione dei reperti dentro o fuori dal raggio.
- Generazione di report CSV.
- Dataset sintetico riproducibile con immagini JPEG e metadati EXIF artificiali.
- Test automatici unitari e di integrazione.


## Struttura del progetto

GeoEvidence-Correlator/
|
|-- README.md                          # documentazione del progetto
|
|-- dati_test/
|   |-- sorgenti/
|   |   `-- base_cc0.jpg               # immagine base con licenza CC0
|   |
|   |-- exif_sintetici/
|   |   |-- manifest.json              # descrizione e risultati attesi di ogni immagine
|   |   `-- immagini/                  # JPEG sintetici per i test
|   |
|   `-- video_sintetici/
|       |-- ATTRIBUTION.MD             # origine e licenza del video base
|       |-- manifest.json              # descrizione e risultati attesi di ogni video
|       |-- sorgenti/
|       |   `-- video_base_cc0.mp4     # video base derivato da sorgente CC0
|       `-- video/
|           |-- con_gps.mp4            # GPS valido
|           |-- senza_gps.mp4          # senza GPS
|           `-- corrotto.mp4           # file volutamente non valido
|
|-- scripts/
|   |-- prova_exif_sintetico.py        # prova scrittura EXIF in una sola immagine
|   |-- genera_dataset_exif.py         # generazione dataset immagini sintetiche
|   `-- genera_dataset_video.py        # generazione dataset video sintetico
|
`-- logica_base/
    |-- georange.py                    # libreria per calcolo distanza geografica
    |-- core.py                        # filtraggio dei punti
    |-- data_loader.py                 # caricamento coordinate da JSON e CSV
    |-- exif_loader.py                 # estrazione GPS e timestamp dalle immagini
    |-- video_loader.py                # estrazione GPS e timestamp dai video
    |-- report.py                      # generazione report CSV
    |-- main.py
    |-- requirements.txt               # dipendenze Python necessarie
    |-- punti.csv                      # dati di esempio
    |-- punti.json                     # dati di esempio
    `-- tests/
        |-- test_core.py
        |-- test_data_loader.py
        |-- test_exif_loader.py
        |-- test_video_loader.py
        |-- test_report.py
        |-- test_dataset_sintetico.py
        `-- test_dataset_video_sintetico.py
        `-- test_integrazione_media.py