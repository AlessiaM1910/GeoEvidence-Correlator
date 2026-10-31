from math import *
from georange import Coordinate

def haversine_distance(lat1,lon1,lat2,lon2):
    """Calculate the distance in kilometers between two coordinates.

    Args:
        lat1: Latitude of the first point.
        lon1: Longitude of the first point.
        lat2: Latitude of the second point.
        lon2: Longitude of the second point.

    Returns:
        Distance between the points in kilometers.
    """

    point_a=Coordinate(lat1,lon1)
    point_b=Coordinate(lat2, lon2)

    return point_a.distance_to(point_b, "km")



def is_within_radius(lat,lon,center_lat,center_lon, radius_km ):
    """Check whether a coordinate is within a radius in kilometers.

    Args:
        lat: Latitude of the point to evaluate.
        lon: Longitude of the point to evaluate.
        center_lat: Latitude of the radius center.
        center_lon: Longitude of the radius center.
        radius_km: Search radius in kilometers.

    Returns:
        True if the point is within the search radius.
    """
    point= Coordinate(lat, lon)
    center= Coordinate(center_lat, center_lon)

    return point.is_within_radius(center, radius_km, "km")

def filter_points(points,center_lat,center_lon,radius_km):
    """Filter and order named points within a geographic radius.

    Args:
        points: Tuples in the format (latitude, longitude, name).
        center_lat: Latitude of the radius center.
        center_lon: Longitude of the radius center.
        radius_km: Search radius in kilometers.

    Returns:
        Tuples in the format (name, distance_km), ordered by distance.
    """
    filtered_points=[]
    for lat,lon,name in points:
        d= haversine_distance(lat,lon,center_lat, center_lon)
        if d<=radius_km:
            filtered_points.append((name,d))
    filtered_points.sort(key=lambda item: item[1]) #prendo secondo elemento tupla e in basee a quello riordino
    return filtered_points