import csv
import json
import math

def create_point(lat,lon,name): 
    """Validate and create a geographic point tuple.

    Args:
        latitude: Latitude value between -90 and 90.
        longitude: Longitude value between -180 and 180.
        name: Non-empty point name.

    Returns:
        A tuple in the format (latitude, longitude, name), or None if invalid.
    """
    try:
        lat=float(lat)  #converto i valori in float (perchè sono stringhe)
        lon=float(lon)
    except (ValueError, TypeError):
        return None

    if math.isnan(lat) or math.isinf(lat):
        return None

    if math.isnan(lon) or math.isinf(lon):
        return None

    if not(-90<= lat <=90): #controllo se la latitudine rientra nel range
        return None
    
    if not(-180<= lon <= 180): #controllo longitudine
        return None

    if name is None or not str(name).strip():
        return None

    return (lat,lon,name)



def load_csv(file_path, latitude_field="lat", longitude_field="lon",name_field="name"):
    """Load valid geographic points from a CSV file.

    Args:
        file_path: Path of the CSV file.
        latitude_field: Name of the latitude column.
        longitude_field: Name of the longitude column.
        name_field: Name of the point-name column.

    Returns:
        A list of valid point tuples.
    """
    points=[]
    discarded_rows= 0 #serve per contare le righe che vengono scartate se non rientrano nei parametri
    try:
        with open(file_path,newline="", encoding="utf-8") as f:
            reader= csv.DictReader(f) #legge file aperto e lo converte in dizionario
            if not reader.fieldnames:
                print("CSV file is empty or has no header")
                return []
            
            if latitude_field not in reader.fieldnames or longitude_field not in reader.fieldnames:
                print ("Columns not found: expected", latitude_field, longitude_field, "found", reader.fieldnames)
                return []

            if name_field not in reader.fieldnames:
                print(" 'Name' column not found", name_field)
                return []

            for row in reader:
                point=create_point(row[latitude_field],row[longitude_field],row[name_field])
                if point is None:
                    discarded_rows+=1
                else:
                    points.append(point) #se il punto è valido lo aggiungiamo alla lista, questa diventerà il paremtro della funzione filtra punti in core.py

    except(FileNotFoundError, PermissionError) as e:
        print("Unable to read file:", file_path, "-", e)
        return []

    print("Discarded rows:", discarded_rows)
    return points

def load_json(file_path, latitude_field="lat", longitude_field="lon",name_field="name" ):
    """Load valid geographic points from a JSON file.

    Args:
        file_path: Path of the JSON file.
        latitude_field: Name of the latitude property.
        longitude_field: Name of the longitude property.
        name_field: Name of the point-name property.

    Returns:
        A list of valid point tuples.
    """
    points=[]
    discarded_rows=0
    try:
        with open(file_path, encoding="utf-8") as f:
            data=json.load(f)

        if not isinstance(data, list):
            print("JSON must contain a list of points")
            return []

        for item in data:
            if not isinstance(item, dict):
                discarded_rows += 1
                continue

            lat=item.get(latitude_field) #qui utilizzo get perchè in caso di dati mancanti o altro restituisce None
            lon=item.get(longitude_field)
            name=item.get(name_field)

            point=create_point(lat,lon,name)
            if point is None:
                discarded_rows+=1
            else:
                points.append(point)
    except(FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
        print("Unable to read file:", file_path, "-", e)
        return []
    print("Discarded rows:", discarded_rows)
    return points