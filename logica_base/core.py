from math import *

def distanza_haversine(lat1,lon1,lat2,lon2):

    R=6371.0 #raggio della terra

    #conversione in radianti
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    variazione_lat= lat2_rad-lat1_rad
    variazione_lon=lon2_rad-lon1_rad

    #formula haversine

    a=(sin(variazione_lat/2)**2)+ cos(lat1_rad)*cos(lat2_rad)*(sin(variazione_lon/2)**2) #valore internedio

    c= 2.0 * atan2(sqrt(a),sqrt(1.0-a)) #distanza angolare

    return R*c #distanza finale



def rientra_nel_raggio(lat1,lon1,lat2,lon2, raggiokm ):
    dist= distanza_haversine(lat1,lon1,lat2,lon2)
    if dist<=raggiokm: #confronto se la distanza calcolata rientra nel raggio stabilito
        return True
    return False


#la lista punti è definita come (lat,lon,nome)
def filtra_punti(punti,lat_centro,long_centro,raggiokm):
    filtrati=[]
    for lat,lon,nome in punti:
        d=distanza_haversine(lat,lon,lat_centro,long_centro)
        if d<=raggiokm:
            filtrati.append((nome,d))
    filtrati.sort(key=lambda elemento: elemento[1]) #prendo secondo elemento tupla e in basee a quello riordino
    return filtrati