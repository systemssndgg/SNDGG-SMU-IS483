import googlemaps
import constants as constants
from datetime import datetime
import math

gmaps = googlemaps.Client(key=constants.GOOGLE_MAPS_KEY)

def get_autocomplete_place(input_text):
    try:
        response = gmaps.places_autocomplete(input_text, components={"country": "SG"})

        if response:
            return response
        else:
            return []
    except Exception as e:
        print(f"An error occurred in get_autocomplete_place: {e}")
        return None
    
def get_details_place(destination_id):
    try:
        response = gmaps.place(place_id=destination_id)

        if response and response.get("result"):
            return response["result"]
        else:
            return None
    except Exception as e:
        print(f"An error occurred in get_details_place: {e}")
        return None

def generate_static_map_url(lat, lng):
    static_map_url = (
        f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=15&size=600x400&markers=color:red%7Clabel:A%7C{lat},{lng}&key={constants.GOOGLE_MAPS_KEY}"
    )
    return static_map_url

def get_address_from_coordinates(lat, lng):
    geocode_result = gmaps.reverse_geocode((lat, lng))
    if geocode_result and len(geocode_result) > 0:
        return geocode_result[0]['formatted_address']
    else:
        return "Address not found"
    
def get_route_duration(lat, long, dest_lat, dest_long, travel_mode):
    # travel_modes can be driving, biking, or walking
    # https://developers.google.com/maps/documentation/distance-matrix/distance-matrix#mode
    now = datetime.now()
    coords_0 = f"{lat}, {long}"
    coords_1 = f"{dest_lat}, {dest_long}"
    directions_result = gmaps.directions(coords_0, coords_1, mode=travel_mode, departure_time=now, avoid='tolls')
    # print("directions_result:", directions_result)
    value = math.ceil(directions_result[0]['legs'][0]['duration']['value']/60)
    return value