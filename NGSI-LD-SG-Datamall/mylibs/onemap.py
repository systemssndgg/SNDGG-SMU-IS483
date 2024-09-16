
import sys
from onemapsg import OneMapClient

import requests

def create_onemap_link(latitude, longitude):
    """
    Converts latitude and longitude coordinates into a OneMap link.
    
    Parameters:
    latitude (float): The latitude coordinate.
    longitude (float): The longitude coordinate.
    
    Returns:
    str: A OneMap link with the specified coordinates.
    """
    base_url = "https://www.onemap.sg/main/v2/?lat={}&lng={}&zoomLevel=17"
    onemap_link = base_url.format(latitude, longitude)
    return onemap_link






def get_walking_distance(api_key, start_lat, start_lng, end_lat, end_lng):
    """
    Uses the OneMap API to find the walking distance between two points.
    
    Parameters:
    api_key (str): Your OneMap API key.
    start_lat (float): The latitude of the starting point.
    start_lng (float): The longitude of the starting point.
    end_lat (float): The latitude of the ending point.
    end_lng (float): The longitude of the ending point.
    
    Returns:
    dict: A dictionary containing the distance and duration.
    """
    client = OneMapClient(api_key=api_key)
    route = client.route(start=(start_lat, start_lng), end=(end_lat, end_lng), route_type='walk')

    if route and 'route_summary' in route:
        distance = route['route_summary']['total_distance']
        duration = route['route_summary']['total_time']
        return {'distance': distance, 'duration': duration}
    else:
        return {'error': 'No route summary found in the response'}
        
