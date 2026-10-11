from math import *
from georange import Coordinate

def distanza_haversine(lat1,lon1,lat2,lon2):

    punto_a=Coordinate(lat1,lon1)
    punto_b=Coordinate(lat2, lon2)

    return punto_a.distanza(punto_b, "km")



def rientra_nel_raggio(lat,lon,lat_centro,lon_centro, raggiokm ):
    punto= Coordinate(lat, lon)
    centro= Coordinate(lat_centro, lon_centro)

    return punto.rientra_nel_raggio(centro, raggiokm, "km")


#la lista punti è definita come (lat,lon,nome)
def filtra_punti(punti,lat_centro,long_centro,raggiokm):
    filtrati=[]
    for lat,lon,nome in punti:
        d=distanza_haversine(lat,lon,lat_centro,long_centro)
        if d<=raggiokm:
            filtrati.append((nome,d))
    filtrati.sort(key=lambda elemento: elemento[1]) #prendo secondo elemento tupla e in basee a quello riordino
    return filtrati