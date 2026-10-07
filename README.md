# GeoEvidence-Correlator

## Struttura del Progetto

```
GeoEvidence-Correlator/
│
├── logica_base/                         
│       ├── core.py                     # contiene il calcolo della distanza e se un punto rientra nel raggio o no
│       ├── data_loader.py              #contiene la parte di caricamento dati da file csv e json
|       ├── exif_loader.py              # qui andiamo ad estrarre dalle foto i dati GPS che ci servono
│       ├── report.py                   # tutti i dati estratti le convertiamo in righe che andranno a fromare report in formato csv
│       └── main.py                     # 
└── README.md                            # Documentazione del progetto
```