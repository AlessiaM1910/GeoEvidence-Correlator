import math

RAGGIO_TERRA=6371.0 #in km

class Coordinate(object):
    #rappresenta coordinata dormata da (latitutdine,longitudine)
    
    def __init__(self,lat,lon):
        self.lat = float(lat)
        self.lon = float(lon)

        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError("Latitudine non valida deve essere tra -90 e 90.")

        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError("Longitudine non valida deve essere tra -180 e 180.")

    def distanza(self, altro_punto):
        if not isinstance(altro_punto, Coordinate):
            raise TypeError("altro_punto deve essere un oggetto Coordinate")
        #calcolo distanza in km tra questo punto e un altro

        R=RAGGIO_TERRA#raggio della terra
        
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
    
        return R*c #distanza finale

    def rientra_nel_raggio(self, altro_punto, raggiokm):

        #verifica se un punto rientra nel raggio indicato
        try:
            raggiokm = float(raggiokm)
        except (TypeError, ValueError):
            raise ValueError("Il raggio deve essere numerico")

        if math.isnan(raggiokm) or math.isinf(raggiokm):
            raise ValueError("Il raggio deve essere finito")

        if raggiokm < 0:
            raise ValueError("Il raggio non puo essere negativo")

        return self.distanza(altro_punto) <= raggiokm

        