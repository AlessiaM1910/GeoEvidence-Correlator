import math

#sviluppata con riferimento a metri, poi si fa conversione o in km o in miglia

EARTH_RADIUS_METERS=6371000.0
METERS_PER_KILOMETER= 1000.0
METERS_PER_MILE=1609.344 #internazionale non nautico

VALID_UNITS=("m","km","mi")


try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)


class Coordinate(object):
    '''Represent a geographic coordinate with latitude and longitude'''
    
    def __init__(self,lat,lon):
        '''Create a validated geographic coordinate.
        
        Args:
            latitude: Latitude value between -90 and 90.
            longitude: Longitude value between -180 and 180.
            
        Raises:
            ValueError: if a value is ont numeric, finite or within range.'''
        
        self.lat = _to_finite_float(lat, "Latitude")
        self.lon = _to_finite_float(lon, "Longitude")

        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError("Latitude must be between -90 e 90.")

        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError("Longitude must be between -180 e 180.")

    def as_tupla(self):
        '''Return the coordinates as a latitude and longitude tuple'''
        return (self.lat, self.lon)

    def distance_to(self, other_point, unit="km"): #se non specificata unità viene presa in km di default
        '''Calculate the Haversine distance from this coordinate to another.
        
        Args:
            other_point: Another Coordinate distance.
            unit: output unit (m, km, mi)
        
        Returns:
            The distance between the two coordinates.
            
        Raises: 
        TypeError: If other_point is not a coordinate instance.
        ValueError: If unit is not supported'''
        if not isinstance(other_point, Coordinate):
            raise TypeError("other_point must be a Coordinate instance.")


        unit=_normalize_unit(unit)
        
        #conversione in radianti
        lat1_rad = math.radians(self.lat)
        lon1_rad = math.radians(self.lon)
        lat2_rad = math.radians(other_point.lat)
        lon2_rad = math.radians(other_point.lon)

        latitude_difference= lat2_rad-lat1_rad
        longitude_difference=lon2_rad-lon1_rad
    
        #formula haversine
    
        a=(math.sin(latitude_difference/2)**2)+ math.cos(lat1_rad)*math.cos(lat2_rad)*(math.sin(longitude_difference/2)**2) #valore internedio

        a = min(1.0, max(0.0, a)) #serve per evitare alcuni errori di arrotondamento 
    
        c= 2.0 * math.atan2(math.sqrt(a),math.sqrt(1.0-a)) #distanza angolare

        distance_meters=EARTH_RADIUS_METERS*c
    
        return convert_distance(distance_meters, unit) #distanza finale


    def is_within_radius(self, other_point, radius, unit="km"):
        '''Check whether another coordinate is within a given radius.

        Args:
            other_point: Another Coordinate instance.
            radius: Maximum allowed distance.
            unit: Unit used for the radius: m, km or mi.

        Returns:
            True if the distance is less than or equal to radius.

        Raises:
            ValueError: If radius is negative or unit is unsupported.
        '''
        radius = _to_finite_float(radius, "radius")

        if radius < 0:
            raise ValueError("Radius cannot be negative")

        unit=_normalize_unit(unit)

        return self.distance_to(other_point, unit) <= radius

    

def _to_finite_float(value, field_name): #funzione di supporto
    """Convert a value to a finite float.

    Args:
        value: Value to convert.
        field_name: Name used in validation error messages.

    Returns:
        A finite float value.

    Raises:
        ValueError: If the value is not numeric or is not finite.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be numeric.".format(field_name))

    if math.isnan(value) or math.isinf(value): #nan--> not a number; inf--> valore infinito
        raise ValueError("{} must be finite".format(field_name))

    return value

def _normalize_unit(unit): 
    """Validate and normalize a distance unit.

    Args:
        unit: Unit to validate.

    Returns:
        A normalized unit string.

    Raises:
        ValueError: If the unit is invalid or unsupported.
    """
    if not isinstance(unit, STRING_TYPES):
        raise ValueError("Invalid unit.")

    unit = unit.strip().lower() #strip elimina gli spazi

    if unit not in VALID_UNITS:
        raise ValueError("Unsupported unit: {}".format(unit))

    return unit


def convert_distance(distance_meters, unit):
    """Convert a distance expressed in meters to another unit.

    Args:
        distance_meters: Distance in meters.
        unit: Target unit: m, km or mi.

    Returns:
        Converted distance.

    Raises:
        ValueError: If distance is negative or unit is unsupported.
    """
    distance_meters = _to_finite_float(distance_meters, "Distance")

    if distance_meters < 0:
        raise ValueError("Distance cannot be negative")

    unit = _normalize_unit(unit)

    if unit == "m":
        return distance_meters

    if unit == "km":
        return distance_meters / METERS_PER_KILOMETER

    return distance_meters / METERS_PER_MILE


#interfacce dei metodi della classe
def distance(point_a, point_b, unit="km"): 
    """Calculate the distance between two Coordinate instances.

    Args:
        point_a: First Coordinate instance.
        point_b: Second Coordinate instance.
        unit: Output unit: m, km or mi.

    Returns:
        Distance between point_a and point_b.

    Raises:
        TypeError: If a point is not a Coordinate instance.
    """
    if not isinstance(point_a, Coordinate):
        raise TypeError("point_a must be a Coordinate instance")

    if not isinstance(point_b, Coordinate):
        raise TypeError("point_b must be a Coordinate instance")

    return point_a.distance_to(point_b, unit)


def within_radius(point_a, point_b, radius, unit="km"):
    """Check whether two coordinates are within a given radius.

    Args:
        point_a: First Coordinate instance.
        point_b: Second Coordinate instance.
        radius: Maximum allowed distance.
        unit: Unit used for radius: m, km or mi.

    Returns:
        True if the points are within radius.

    Raises:
        TypeError: If a point is not a Coordinate instance.
    """
    if not isinstance(point_a, Coordinate):
        raise TypeError("point_a must be a Coordinate instance")

    if not isinstance(point_b, Coordinate):
        raise TypeError("point_b must be a Coordinate instance")

    return point_a.is_within_radius(point_b, radius,unit)

        