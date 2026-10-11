import math

#sviluppata con riferimento a metri, poi si fa conversione o in km o in miglia

RAGGIO_TERRA=6371000.0
METRI_PER_KM= 1000.0
METRI_PER_MIGLIO=1609.344 #internazionale non nautico

UNITA_VALIDE=("m","km","mi")

class Coordinate(object):
    #rappresenta coordinata dormata da (latitutdine,longitudine)
    
    def __init__(self,lat,lon):
        self.lat = _converti_in_float(lat, "Latitudine")
        self.lon = _converti_in_float(lon, "Longitudine")

        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError("Latitudine non valida deve essere tra -90 e 90.")

        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError("Longitudine non valida deve essere tra -180 e 180.")

    def restituisci_tupla(self):
        return (self.lat, self.lon)

    def distanza(self, altro_punto, unita="km"): #se non specificata unità viene presa in km di default
        if not isinstance(altro_punto, Coordinate):
            raise TypeError("altro_punto deve essere un oggetto Coordinate")
        #calcolo distanza tra questo punto e un altro

        unita=_normalizza_unita(unita)
        
        #conversione in radianti
        lat1_rad = math.radians(self.lat)
        lon1_rad = math.radians(self.lon)
        lat2_rad = math.radians(altro_punto.lat)
        lon2_rad = math.radians(altro_punto.lon)
        variazione_lat= lat2_rad-lat1_rad
        variazione_lon=lon2_rad-lon1_rad
    
        #formula haversine
    
        a=(math.sin(variazione_lat/2)**2)+ math.cos(lat1_rad)*math.cos(lat2_rad)*(math.sin(variazione_lon/2)**2) #valore internedio

        a = min(1.0, max(0.0, a)) #serve per evitare alcuni errori di arrotondamento 
    
        c= 2.0 * math.atan2(math.sqrt(a),math.sqrt(1.0-a)) #distanza angolare

        distanza_in_metri=RAGGIO_TERRA*c
    
        return converti_distanza(distanza_in_metri, unita) #distanza finale


    def rientra_nel_raggio(self, altro_punto, raggio, unita="km"):
        #verifica se un punto rientra nel raggio indicato
        raggio = _converti_in_float(raggio, "radius")

        if raggio < 0:
            raise ValueError("Il raggio non puo essere negativo")

        unita=_normalizza_unita(unita)

        return self.distanza(altro_punto, unita) <= raggio

    

def _converti_in_float(value, field_name): #funzione di supporto
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("{} deve essere un valore numerico".format(field_name))

    if math.isnan(value) or math.isinf(value): #nan--> not a number; inf--> valore infinito
        raise ValueError("{} deve essere un valore finito".format(field_name))

    return value

def _normalizza_unita(unit):  #controlla se rientra tra quelle dichiarate globalmente
    if not isinstance(unit, str):
        raise ValueError("Unita non valida")

    unit = unit.strip().lower() #strip elimina gli spazi

    if unit not in UNITA_VALIDE:
        raise ValueError("Unita non supportata: {}".format(unit))

    return unit


def converti_distanza(val_in_metri, unit): #in input riceve distanza in metri
    val_in_metri = _converti_in_float(val_in_metri, "Distanza")

    if val_in_metri < 0:
        raise ValueError("La distanza non puo essere negativa")

    unit = _normalizza_unita(unit)

    if unit == "m":
        return val_in_metri

    if unit == "km":
        return val_in_metri / METRI_PER_KM

    return val_in_metri / METRI_PER_MIGLIO


#interfacce dei metodi della classe
def distance(punto_a, punto_b, unita="km"): 
    if not isinstance(punto_a, Coordinate):
        raise TypeError("punto_a deve essere un oggetto Coordinate")

    if not isinstance(punto_b, Coordinate):
        raise TypeError("punto_b deve essere un oggetto Coordinate")

    return punto_a.distanza(punto_b, unita)


def within_radius(punto_a, punto_b, raggio, unita="km"):
    if not isinstance(punto_a, Coordinate):
        raise TypeError("punto_a deve essere un oggetto Coordinate")

    if not isinstance(punto_b, Coordinate):
        raise TypeError("punto_b deve essere un oggetto Coordinate")

    return punto_a.rientra_nel_raggio(punto_b, raggio,unita)

        