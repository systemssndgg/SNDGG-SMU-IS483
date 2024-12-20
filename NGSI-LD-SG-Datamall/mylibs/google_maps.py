import googlemaps
import mylibs.constants as constants
import requests
from telegram import Update, InputMediaPhoto

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