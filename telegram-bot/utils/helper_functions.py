from geopy.distance import geodesic
from datetime import datetime
import numpy as np
import random
import logging
import time
import threading
from typing import Union

from utils.google_maps import get_route_duration
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from import_entities import import_Carpark_entity, import_TrafficAdvisories_entity, import_WeatherForecast_entity

def find_closest_three_carparks(nearest_carparks_list, dest_lat, dest_long, selected_preference):
    closest_three_carparks = []
    distance_dict = {}
    final_three_carparks = []

    for carpark in nearest_carparks_list:
        carpark_dict = carpark.to_dict()
        lat = carpark_dict["location"]["value"]["coordinates"][1]
        long = carpark_dict["location"]["value"]["coordinates"][0]
        distance = geodesic((dest_lat, dest_long), (lat, long)).km #distance from carpark to user's final destination
        distance_dict[carpark_dict["carparkName"]["value"]] = distance
        carpark_dict["distance"] = distance
        if "Car" in carpark_dict["pricing"]["value"] and carpark_dict["parkingAvailability"]["value"] > 0:
            if selected_preference == "sheltered":
                if carpark["sheltered"]["value"] == True:
                    if len(closest_three_carparks) < 3:
                        closest_three_carparks.append(carpark_dict)
                    else: 
                        farthest_carpark = max(closest_three_carparks, key=lambda x: x["distance"])
                        # print("carpark_dict:", carpark_dict)
                        print("farthest_carpark:", farthest_carpark, "farthest_carpark distance:", farthest_carpark["distance"])
                        if farthest_carpark["distance"] > carpark_dict["distance"]:
                            closest_three_carparks.remove(farthest_carpark)
                            closest_three_carparks.append(carpark_dict)
            else:
                if len(closest_three_carparks) < 3:
                    closest_three_carparks.append(carpark_dict)
                else:
                    
                    farthest_carpark = max(closest_three_carparks, key=lambda x: x["distance"])
                    # print("carpark_dict:", carpark_dict)
                    # print("farthest_carpark:", farthest_carpark, "farthest_carpark distance:", farthest_carpark["distance"])
                    if farthest_carpark["distance"] > carpark_dict["distance"]:
                        closest_three_carparks.remove(farthest_carpark)
                        closest_three_carparks.append(carpark_dict)

    # Sort the closest_three_carparks based on distance
    closest_three_carparks.sort(key=lambda x: distance_dict[x["carparkName"]["value"]])

    # Add the sorted carparks to the final_three_carparks list
    final_three_carparks.extend(closest_three_carparks)
    # for i in final_three_carparks:
    #     print("carparks:", i["carparkName"]["value"], i["distance"])

    return final_three_carparks

# closest_three_carparks = get_top_carparks(live_location, geoquery_nearest_carparks, user_pref, num_cp_to_return=3, min_avail_lots=10, destination=(destination_lat, destination_long))

def find_closest_carpark(carparks_list, live_location, geoquery_nearest_carparks, user_preference, destination, num_cp_return=1, min_avail_lots=0, remove_unsheltered=True, strict_pref=True):
    """Find closest carpark in the event that it rains and originally selected carpark is not sheltered"""
    in_list = False
    for carpark in carparks_list:
        if carpark["sheltered"]["value"] == True:
            in_list = True
            return carpark
        
    
    if in_list == False:
        sheltered_carpark = get_top_carparks(live_location, geoquery_nearest_carparks, user_preference, num_cp_return, min_avail_lots=min_avail_lots, remove_unsheltered=remove_unsheltered, strict_pref=strict_pref, destination=destination)
    
        return sheltered_carpark
    

def format_time_and_rate(h, mins, rate):
    if rate == "$0.00":
        return "Free"
    
    time_string = ""
    if h > 0:
        time_string += f"{h} h "
    if mins > 0:
        time_string += f"{mins} mins"
    
    return f"{rate} per {time_string.strip()}" if time_string.strip() else rate


def convert_to_hours(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    return hours, minutes


def is_time_in_range(start_time, end_time, current_time):
    start = datetime.strptime(start_time, "%H%M").time()
    end = datetime.strptime(end_time, "%H%M").time()
    
    if start <= end:
        return start <= current_time <= end
    else:
        return current_time >= start or current_time <= end


def find_rate_based_on_time(carpark, vehicle_type, current_time, today):
    time_slots = carpark['pricing']['value'][vehicle_type]['TimeSlots']

    if 0 <= today <= 4:
        rate_type = "WeekdayRate"
    elif today == 5:
        rate_type = "SaturdayRate"
    else:
        rate_type = "SundayPHRate"

    for time_slot in time_slots:
        rate_info = time_slot[rate_type]
        start_time = rate_info["startTime"]
        end_time = rate_info["endTime"]

        if start_time and end_time and is_time_in_range(start_time, end_time, current_time):
            return rate_info
        
    return None


def aggregate_message(closest_three_carparks, selected_preference, live_location_lat, live_location_long):
    num_carparks = len(closest_three_carparks)

    if (num_carparks == 0):
        return "😭 Oh no, it seems there are no carparks currently available near your destination..."

    carparks_message = f"🚗 *The {num_carparks} possible carparks near your destination are:*\n\n"

    today = datetime.today().weekday()
    current_time = datetime.now().time()

    price_dict = {}
    duration_list = []

    for count, carpark in enumerate(closest_three_carparks, 1):
        carpark_name = carpark['carparkName']['value'].title()
        if 'pricing' in carpark and 'Car' in carpark['pricing']["value"]:
            dest_lat = carpark['location']['value']['coordinates'][1]
            dest_long = carpark['location']['value']['coordinates'][0]
            duration = get_route_duration(live_location_lat, live_location_long, dest_lat, dest_long, travel_mode="driving")
            duration_list.append(duration)
            carparks_message += (
                f"*{count}. {carpark_name}*\n"
                f"🅿️ *Available Lots:* {carpark['parkingAvailability']['value']}\n"
                f"🚶 *Walk to Destination* {round(carpark['walking_time'])} mins\n"
                f"☂️ *Sheltered:* {'Yes' if carpark['sheltered']['value'] else 'No'}\n"
                f"⌛ *Drive Duration:* {duration} mins\n"
            )



            if 0 <= today <= 4:  # Monday to Friday (Weekday)
                rate_info = find_rate_based_on_time(carpark, "Car", current_time, today)

                if rate_info:
                    price = rate_info['weekdayRate']
                    price_dict[carpark_name] = price

                    minutes = int(rate_info['weekdayMin'].split(" ")[0])
                    h, mins = convert_to_hours(minutes)
                    day_type = "Weekday"
                    rate_display = format_time_and_rate(h, mins, rate_info['weekdayRate'])
                    carparks_message += (
                    f"🏷️ *{day_type} Rate:* {rate_display}\n"
                    f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n\n")
                else:
                    carparks_message += "🏷️ *Price Information:* Not Available\n\n"

            elif today == 5:  # Saturday      
                rate_info = find_rate_based_on_time(carpark, "Car", current_time, today)

                if rate_info:
                    price = rate_info['satdayRate']
                    price_dict[carpark_name] = price
                    minutes = int(rate_info['satdayMin'].split(" ")[0])
                    h, mins = convert_to_hours(minutes)
                    day_type = "Saturday"
                    rate_display = format_time_and_rate(h, mins, rate_info['satdayRate'])
                    carparks_message += (
                    f"🏷️ *{day_type} Rate:* {rate_display}\n"
                    f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n\n")
                else:
                    carparks_message += "🏷️ *Price Information:* Not Available\n\n"

            else:  # Sunday/Public Holiday (today == 6)
                rate_info = find_rate_based_on_time(carpark, "Car", current_time, today)

                if rate_info:
                    price = rate_info['sunPHRate']
                    price_dict[carpark_name] = price
                    minutes = int(rate_info['sunPHMin'].split(" ")[0])
                    h, mins = convert_to_hours(minutes)
                    day_type = "Sunday/Public Holiday"
                    rate_display = format_time_and_rate(h, mins, rate_info['sunPHRate'])
                    carparks_message += (
                    f"🏷️ *{day_type} Rate:* {rate_display}\n"
                    f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n\n")
                else:
                    carparks_message += "🏷️ *Price Information:* Not Available\n\n"
    
        else:
            carparks_message += "🏷️ *Price Information:* Not Available\n\n"
    
    # Process Preference message
    if selected_preference == "cheapest":
        # find out if all prices are the same
        price_list = list(price_dict.values())
        if len(set(price_list))==1:
            cheapest_carpark_message = f"💸 *All carparks have the same price at {price_list[0]} per 30 mins* \n\n"
            final_message = cheapest_carpark_message + carparks_message
            return final_message
        elif len(set(price_list))>1:
            lowest_value_key = min(price_dict, key=price_dict.get)
            lowest_value = price_dict[lowest_value_key]
            # print("Lowest Value:", lowest_value)
            # print("Lowest Value Key:", lowest_value_key)
            cheapest_carpark_message = f"💸 *The cheapest carpark is: {lowest_value_key} at {lowest_value} per 30 mins* \n\n"
            final_message = cheapest_carpark_message + carparks_message 
            return final_message
            
    elif selected_preference == "fastest":
        # print(duration_list)
        if len(set(duration_list))==1:
            print("8================================D")
            fastest_carpark_message = f"*All carparks have the same duration of {duration_list[0]} mins* \n\n"
            final_message = fastest_carpark_message + carparks_message
            return final_message
        elif len(set(duration_list))>1:
            print("aiyayayyayy")
            print("a================================")
            index_min_duration = duration_list.index(min(duration_list))
            fastest_carpark = closest_three_carparks[index_min_duration]["carparkName"]["value"]
            fastest_carpark_message = f"*The Fastest carpark is: {fastest_carpark} with a travelling time of {duration_list[index_min_duration]} mins* \n\n"
            final_message = fastest_carpark_message + carparks_message
            return final_message

    print("Carpark Message from aggregate_message:", carparks_message)

    return carparks_message


def aggregate_message_new(carparks_list: list, selected_preference: list, ideal_num_carparks: int = 3, num_hrs: int = 2):
    '''
    INPUT PARAMETERS:

    [1] carparks_list: List of carpark entities in this format:
    {
        "id":"urn:ngsi-ld:Carpark:IMMBuilding53",
        "type":"Carpark",
        "CarparkName":{
            "type":"Property",
            "value":"IMM Building"
        },
        "location":{
            "type":"GeoProperty",
            "value":{
                "type":"Point",
                "coordinates":[
                    103.746815,
                    1.334847
                ]
            }
        },
        "ParkingCapacity":{
            "type":"Property",
            "value":"-"
        },
        "Sheltered":{
            "type":"Property",
            "value":false
        },
        "ParkingAvailability":{
            "type":"Property",
            "value":1090
        },
        "pricing":{
            ...
        },
        "@context":[
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        ],
        "walking_time":38.0,    <-- Added key
        "travel_time":47.0,     <-- Added key
        "drive_time":9.0        <-- Added key
    }

    [2] selected_preference: User's selected preference in ordered list (1st item most important) (e.g., ['cheapest', 'fastest', 'shortest_walking_distance', 'sheltered', 'available_lots'])

    [3] ideal_num_carparks: Number of carparks expected to be returned (default is 3)
    '''

    # Suggestions for user if there are not enough carparks
    suggestion_msg = "You may try editing your filters in settings to expand your search range."

    # Check if there are no carparks
    if (len(carparks_list) == 0):
        return f"😭 Oh no, it seems there are no carparks currently available near your destination. {suggestion_msg}"

    # INITIALIZE VARIABLES ========================================

    # Fill selected_preference with all needed values
    for pref in ['cheapest', 'fastest', 'shortest_walking_distance', 'sheltered', 'available_lots']:
        if pref not in selected_preference:
            selected_preference.append(pref)

    # Initialize preference message map with empty strings
    pref_msg_map = {}

    # Go through each carpark and fill in the preference message map
    for cp in carparks_list:
        cp_id = cp['id']

        # Initialize preference message map for this carpark
        pref_msg_map[cp_id] = {
            'cheapest': "",
            'fastest': "",
            'shortest_walking_distance': "",
            'sheltered': "",
            'available_lots': ""
        }

        # (1) Fill price info (cheapest)
        pref_msg_map[cp_id]['cheapest'] = get_price_str(cp, num_hrs=num_hrs)

        # (2) Fill travel time info (fastest)
        pref_msg_map[cp_id]['fastest'] = f"🏎️ *Drive:* {get_time_string(cp['drive_time'])}\n"

        # (3) Fill walking time info (shortest_walking_distance)
        pref_msg_map[cp_id]['shortest_walking_distance'] = f"🚶 *Walk to Destination:* {get_time_string(cp['walking_time'])}\n"

        # (4) Fill sheltered info (sheltered)
        if ('sheltered' in cp):
            pref_msg_map[cp_id]['sheltered'] = f"☂️ *Sheltered:* {'Yes' if cp['sheltered']['value'] else 'No'}\n"
        else:
            pref_msg_map[cp_id]['sheltered'] = "☂️ *Sheltered:* Information not available\n"

        # (5) Fill available lots info (available_lots)
        if ('parkingAvailability' in cp):
            pref_msg_map[cp_id]['available_lots'] = f"🅿️ *Available Lots:* {cp['parkingAvailability']['value']}\n"
        else:
            pref_msg_map[cp_id]['available_lots'] = "🅿️ *Available Lots:* Information not available\n"

    
    res_msg = f"🚗 *The {len(carparks_list)} possible carparks near your destination are:*\n\n"

    # Go through each carpark and aggregate the message
    for idx, cp in enumerate(carparks_list):
        cp_id = cp['id']
        cp_name = cp['carparkName']['value']

        res_msg += f"*{idx+1}. {cp_name}*\n"

        for pref in selected_preference:
            res_msg += pref_msg_map[cp_id][pref]

        res_msg += "\n"
    
    # If there are not enough carparks, add a message to inform the user
    if len(carparks_list) < ideal_num_carparks:
        res_msg += f"\nℹ️ Only {len(carparks_list)} carparks were found near your destination. {suggestion_msg}"
    
    return res_msg


def find_next_best_carpark(carparks, current_carpark):
    """Find the next best carpark with more than 10 available lots."""
    best_carpark = None
    min_distance = float('inf')

    for carpark in carparks:
        if carpark == current_carpark:
            continue
        
        available_lots = carpark['parkingAvailability']['value']
        if available_lots > 10:
            distance = carpark['distance']  # Assuming you already calculated distances

            if distance < min_distance:
                min_distance = distance
                best_carpark = carpark

    return best_carpark


def get_top_carparks(live_location: Union[list, tuple], carparks: list, user_preferences: dict, num_cp_to_return: int, min_avail_lots: int=10, num_hrs: int=2, remove_unsheltered: bool=False, strict_pref: bool=False, destination: Union[list, tuple]=None, remove_missing_price: bool=False, remove_missing_lots: bool=False):
    '''
        Function to get the top N carparks based on user preferences using Z-Score Normalization and Weighted Scoring.
        
        INPUT PARAMETERS SPECIFICATIONS ===============================================================
        [1] live_location: Tuple of latitude and longitude of the user's live location in this format: (1.332549, 103.739453)

        [2] carparks: List of carpark entities in this format:
            [
                {
                    'id': 'urn:ngsi-ld:Carpark:BEDOKSOUTHROADB0069',
                    'type': 'Carpark',
                    'CarparkName': {'type': 'Property', 'value': 'BEDOK SOUTH ROAD '},
                    'location': {'type': 'GeoProperty', 'value': {'type': 'Point',
                    'coordinates': [103.939938, 1.320495]}},
                    'ParkingCapacity': {'type': 'Property', 'value': 8},
                    'Sheltered': {'type': 'Property', 'value': False},
                    'ParkingAvailability': {'type': 'Property', 'value': 0},
                    'pricing': {
                        'type': 'Property',
                        'value': {
                            'Car': {'TimeSlots': []},
                            'Motorcycle': {'TimeSlots': []},
                            'Heavy Vehicle': {'TimeSlots': [{'WeekdayRate': {'startTime': '0700', 'endTime': '1700', 'weekdayMin': '30 mins', 'weekdayRate': '$1.20'}, 'SaturdayRate': {'startTime': '0700', 'endTime': '1700', 'satdayMin': '30 mins', 'satdayRate': '$1.20'}, 'SundayPHRate': {'startTime': '0700', 'endTime': '1700', 'sunPHMin': '30 mins', 'sunPHRate': '$1.20'}}, {'WeekdayRate': {'startTime': '1700', 'endTime': '1900', 'weekdayMin': '30 mins', 'weekdayRate': '$1.20'}, 'SaturdayRate': {'startTime': '1700', 'endTime': '1900', 'satdayMin': '30 mins', 'satdayRate': '$1.20'}, 'SundayPHRate': {'startTime': '1700', 'endTime': '1900', 'sunPHMin': '30 mins', 'sunPHRate': '$1.20'}}]}}
                        },
                    '@context': ['https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld']
                },
                ...   
            ]
        
        [3] User preferences: Dictionary of user preferences in this format:
            {
                'price': 0.5,
                'walking_time': 0.2,    # Time to walk from carpark to destination
                'travel_time': 0.1,     # Drive to carpark + Walk to destination (total time)
                'available_lots': 0.2,
                'is_sheltered': 0.1,
            }
        
        [4] num_cp_to_return: Number of top carparks to return (e.g., 3)

        [5] min_avail_lots: Minimum number of available lots required for a carpark to be considered (default is 10)

        [6] num_hrs: Number of hours user intends to park for (default is 2 hours)

        [7] remove_unsheltered: Boolean to remove unsheltered carparks (default is False)

        [8] strict_pref: Boolean to enforce strict preference (default is False)
            - If True, only carparks that meet all user preferences (ie. min_avail_lots & remove_unsheltered) will be considered
            - If False, carparks that do not meet all user preferences will be considered but with lower scores
        
        [9] destination: Tuple of latitude and longitude of the user's destination in this format: (1.332549, 103.739453)
            - If destination is provided, the function will calculate the walking time from the carpark to the destination
            - If destination is not provided, the function will default walking time to 0.0

        [10] remove_missing_price: Boolean to remove carparks with missing price information (default is False)

        [11] remove_missing_lots: Boolean to remove carparks with missing available lots information (default is False)

        OUTPUT PARAMETERS SPECIFICATIONS ===============================================================
        Returns: List of top N carpark dictionaries in the same format as the input carparks. (First item in the list is the best carpark)

            Added keys in each carpark dictionary:
            - 'walking_time': Time to walk from live location to carpark
            - 'drive_time': Time to drive to carpark
            - 'travel_time': Time to drive to carpark + Time to walk from carpark to destination
    '''

    # Check if there are no carparks
    if len(carparks) == 0:
        return []

    # Filter out carparks that do not meet the minimum requirements
    new_carparks = []
    rotten_carparks = []

    for cp in carparks:
        cp = cp.to_dict()

        if remove_missing_lots and ('parkingAvailability' not in cp):
            continue

        # SKIP IF PRICE INFORMATION IS MISSING [DONT INCLUDE IN ROTTEN CARPARKS]
        if remove_missing_price and find_price_per_hr(cp, num_hrs, 'Car') == -1:
            continue
        
        if ('parkingAvailability' in cp) and int(cp['parkingAvailability']['value']) < min_avail_lots:
            rotten_carparks.append(cp)
            continue

        if ('sheltered' in cp) and remove_unsheltered and not cp['sheltered']['value']:
            rotten_carparks.append(cp)
            continue

        new_carparks.append(cp)
    
    carparks = new_carparks

    # If insufficient carparks meet the requirements, recurse with the rotten carparks to combine at the end of function
    if len(carparks) < num_cp_to_return:
        sorted_rotten_carparks = []

        if len(rotten_carparks) > 0  and (not strict_pref):
            sorted_rotten_carparks = get_top_carparks(live_location, rotten_carparks, user_preferences, num_cp_to_return - len(carparks), min_avail_lots=0, num_hrs=num_hrs, remove_unsheltered=False, strict_pref=False, destination=destination)

    # If there are no carparks meeting minimum criteria, return the rotten carparks
    if len(carparks) == 0:
        if (not strict_pref):
            return sorted_rotten_carparks
        else:
            return []

    # Convert carpark data into a NumPy array
    carparks_list = []

    for cp in carparks:
        # [A] PRICE PER HOUR =================================================
        # Extract the values from the carpark dictionary
        price = find_price_per_hr(cp, num_hrs, 'Car') # Note: -1 value indicates price information is not available
        
        # [B] AVAILABLE LOTS =================================================
        available_lots = -1 # Default value for missing information
        
        if ('parkingAvailability' in cp):
            available_lots = int(cp['parkingAvailability']['value'])

        # [C] WALKING TIME & TRAVEL TIME =====================================
        if (destination):
            walk_time = get_route_duration(cp['location']['value']['coordinates'][1], cp['location']['value']['coordinates'][0], destination[0], destination[1], travel_mode="walking")
        else:
            walk_time = 0.0
        
        drive_time = get_route_duration(live_location[0], live_location[1], cp['location']['value']['coordinates'][1], cp['location']['value']['coordinates'][0], travel_mode="driving")

        # If no available lots, assume 15min wait
        if available_lots == 0:
            drive_time += 15

        travel_time = walk_time + drive_time

        # [D] SHELTERED STATUS ==============================================
        is_sheltered = False # Default value for missing information

        if ('sheltered' in cp):
            is_sheltered = bool(cp['sheltered']['value'])
         
        # Append the data as a list to the carparks_list
        carparks_list.append([price, walk_time, travel_time, available_lots, is_sheltered])

    # Convert the list of lists into a NumPy array
    carparks_np = np.array(carparks_list)

    # Convert the user preferences data into a NumPy array
    user_preferences_np = np.array([
        user_preferences['price'],
        user_preferences['walking_time'],
        user_preferences['travel_time'],
        user_preferences['available_lots'],
        user_preferences['is_sheltered']
    ])

    # Z-SCORE NORMALIZATION =================================================
    # Calculate the mean and standard deviation of each feature
    mean = np.mean(carparks_np, axis=0)
    std = np.std(carparks_np, axis=0)

    # Handle division by zero (i.e., std == 0)
    std[std == 0] = 1  # To avoid division by zero, set any 0 std to 1 (no scaling will occur)

    # Penalty for missing price information: If price is missing, price = average price * (1 + penalty)
    missing_price_penalty = 0.05
    missing_lots_penalty = 0.05

    # Replace missing prices and lots (indicated by -1) with the mean price + penalty
    for i in range(len(carparks_np)):
        if carparks_np[i][0] == -1:
            carparks_np[i][0] = mean[0] * (1 + missing_price_penalty)
        if carparks_np[i][3] == -1:
            carparks_np[i][3] = mean[3] * (1 + missing_lots_penalty)

    # Apply Z-Score normalization: (x - mean) / std
    normalized_carparks = (carparks_np - mean) / std

    # Invert Z-scores for price, walking_time, travel_time (we want lower values to result in higher scores)
    normalized_carparks[:, 0] *= -1  # Invert price scores
    normalized_carparks[:, 1] *= -1  # Invert walking time scores
    normalized_carparks[:, 2] *= -1  # Invert travel time scores

    # Sheltered status does not need Z-score normalization as it is binary (0 or 1)
    normalized_carparks[:, 4] = carparks_np[:, 4]  # Keep the sheltered status unchanged

    # WEIGHTED SCORING ======================================================
    # Apply weights
    weighted_scores = normalized_carparks * user_preferences_np

    # Sum up weighted scores for each carpark
    total_scores = np.sum(weighted_scores, axis=1)


    # RETURN TOP N CARPARKS =================================================
    # Sort the carparks by their total scores (descending order)
    sorted_indices = np.argsort(-total_scores)

    '''
    [DEBUGGING] PRINT EACH CARPARK WITH SCORES AND VALUES (From carparks_np) ============================
    for i in sorted_indices:
        print(f"\n\nCarpark: {carparks[i]['carparkName']['value']} ======================")
        print(f"Score: {total_scores[i]}")
        print(f"\nOriginal Price: {find_price_per_hr(carparks[i], num_hrs, 'Car')}")
        print(f"Scored Price: {carparks_np[i][0]} | Normalised: {normalized_carparks[i][0]}")
        print(f"\nWalk Time: {carparks_np[i][1]} | Normalised: {normalized_carparks[i][1]}")
        print(f"Travel Time: {carparks_np[i][2]} | Normalised: {normalized_carparks[i][2]}")
        print(f"Available Lots: {carparks_np[i][3]} | Normalised: {normalized_carparks[i][3]}")
        print(f"Sheltered: {carparks_np[i][4]} | Normalised: {normalized_carparks[i][4]}")
    '''

    # Create the list of top N carparks and include walking_time, travel_time, and drive_time
    top_N_carparks = []

    for i in sorted_indices[:num_cp_to_return]:
        carpark_dict = carparks[i]  # Convert to dictionary
        carpark_dict['walking_time'] = float(carparks_np[i][1])  # Add walking time
        carpark_dict['travel_time'] = float(carparks_np[i][2])   # Add travel time
        carpark_dict['drive_time'] = float(carparks_np[i][2] - carparks_np[i][1])  # Add drive time
        top_N_carparks.append(carpark_dict)
    
    # Combine the top N carparks with the rotten carparks
    if len(carparks) < num_cp_to_return:
        top_N_carparks.extend(sorted_rotten_carparks)

    # Return
    return top_N_carparks

def find_price_per_hr(carpark, num_hrs, vehicle_type='Car'):
    '''
    To be implemented: Figure out price per hour based on input params

    INPUT PARAMETERS:
    [1] carpark: Entire NGSI-LD carpark entity
    [2] num_hrs: Number of hours user intends to park for
    [3] vehicle_type: Type of vehicle ('Car', 'Motorcycle', 'Heavy Vehicle')

    RETURNS:
    float value >= 0.0 IF price information is available
    -1.0 IF price information is not available
    '''

    # Check if price information is available
    if 'pricing' not in carpark:
        return -1.0

    today = datetime.today().weekday()
    current_time = datetime.now().time()
    
    # If the carpark is a Commercial carpark
    if not is_ura_carpark(carpark):
        # (1) Format the current time to the same format found in the entity - e.g. 15:00
        current_time = current_time.strftime("%H:%M")

        # (2) Format the current day to either 'weekday', 'saturday', or 'sundayPublicHoliday'
        if 0 <= today <= 4:
            day_type = "weekday"
        elif today == 5:
            day_type = "saturday"
        else:
            day_type = "sundayPublicHoliday"
        
        day_price_info = carpark['pricing']['value']['rates'][day_type]

        # (3) Find the entry_fee based on the current time and day (entry_fee_price)
        entry_fee_price = None

        if ('flatEntryFee' in day_price_info):
            entry_fee = day_price_info['flatEntryFee']
            entry_fee_start_time = entry_fee['startTime']
            entry_fee_end_time = entry_fee['endTime']

            if entry_fee_start_time <= current_time <= entry_fee_end_time:
                entry_fee_price = entry_fee['fee']
        
        # (4) Find out if there's a first hour rate present (first_hour_rate)
        first_hour_rate_price = None

        if ('firstHourRate' in day_price_info):
            first_hour_rate_price = day_price_info['firstHourRate']
        
        # (5) Find out the usual rate per hour (rate_per_hour)
        rate_per_hour = None

        if ('timeBased' in day_price_info):
            time_based = day_price_info['timeBased']

            for time_slot in time_based:
                start_time = convert_time_to_int(time_slot['startTime'])
                end_time = convert_time_to_int(time_slot['endTime'])

                if start_time <= convert_time_to_int(current_time) <= end_time:
                    rate_per_hour = time_slot['ratePerHour']
                    break

        # (6) Find out if there's a max_daily_fee (max_daily_fee)
        max_daily_fee = None

        if ('maxDailyFee' in day_price_info):
            max_daily_fee = day_price_info['maxDailyFee']

        # (7) Calculate the total price based on the number of hours
        if entry_fee_price != None:
            total_price = entry_fee_price
        else:
            total_price = 0.0

        if first_hour_rate_price != None:
            total_price += first_hour_rate_price
        else:
            total_price += 0.0

        if rate_per_hour != None:
            if first_hour_rate_price != None:
                total_price += rate_per_hour * (num_hrs-1)
            else:
                total_price += rate_per_hour * num_hrs
        else:
            total_price += 0.0
        
        if max_daily_fee != None:
            if total_price > max_daily_fee:
                total_price = max_daily_fee

        if total_price == 0.0:
            return -1.0
        else:
            rate = total_price / num_hrs
        
        return rate

    # If the carpark is a URA carpark
    else:
        # (1) Format the current time to the same format found in the entity - e.g. 1500
        current_time = current_time.strftime("%H%M")

        # (2) Format the current day to either 'weekday', 'saturday', or 'sundayPublicHoliday'
        if 0 <= today <= 4:
            day_type = "WeekdayRate"
        elif today == 5:
            day_type = "SaturdayRate"
        else:
            day_type = "SundayPHRate"

        # Set mapping
        day_map = {
            "WeekdayRate": "weekday",
            "SaturdayRate": "satday",
            "SundayPHRate": "sunPH"
        }

        # (3) Find the correct rate data based on time and day    
        all_timeslots = carpark['pricing']['value'][vehicle_type]['TimeSlots']

        # Loop through the time slots and find the correct time range
        for e_timeslot in all_timeslots:
            # Check if current_time is between start and end time
            start_time = e_timeslot[day_type]['startTime']  # e.g. 0700
            end_time = e_timeslot[day_type]['endTime']      # e.g. 1700

            if int(start_time) <= int(current_time) <= int(end_time):
                # Found the correct time slot
                rate = float(e_timeslot[day_type][day_map[day_type] + 'Rate'][1:])                      # e.g. 1.20
                time_interval_mins = int(e_timeslot[day_type][day_map[day_type] + 'Min'].split(" ")[0]) # e.g. 30

                # If time interval is 0, assume it is per entry
                if time_interval_mins == 0:
                    return rate / num_hrs
                
                # Calculate the total price for 1hr. Note: If time_interval_mins is more than 60, assume entire rate must be charged for the hr
                if time_interval_mins > 60:
                    return rate
                else:
                    num_intervals_per_hr = 60 / time_interval_mins
                    return rate * num_intervals_per_hr
        
        # If no rate is found, return -1.0
        return -1.0

def convert_time_to_int(time_str):
    '''
    time_str input possibilities: "hh:mm", "hh:mm AM", "hh:mm PM"
    '''

    if (len(time_str) == 5):
        return int(time_str[:2] + time_str[3:])
    
    time_str = time_str.split(" ")

    if (time_str[1] == "AM"):
        return int(time_str[0][:2] + time_str[0][3:])
    else:
        return int(time_str[0][:2] + time_str[0][3:]) + 1200
    

def get_price_str(carpark, vehicle_type='Car', num_hrs=2):
    '''
    Returns the pricing info of carpark as a string
    '''

    no_price_info = "💵 *Rate:* Information not available\n"

    # Handle no pricing info
    if 'pricing' not in carpark:
        return no_price_info

    today = datetime.today().weekday()
    current_time = datetime.now().time()

    if not is_ura_carpark(carpark):
        # Handle Commercial carpark

        # (1) Format the current day to either 'weekday', 'saturday', or 'sundayPublicHoliday'
        today = datetime.today().weekday()

        pricing_info = carpark['pricing']['value']
        wd_str = None
        sat_str = None
        sun_str = None

        rate_str = None

        if 'weekdayStr' in pricing_info:
            wd_str = pricing_info['weekdayStr']
        if 'saturdayStr' in pricing_info:
            sat_str = pricing_info['saturdayStr']
        if 'sundayPHStr' in pricing_info:
            sun_str = pricing_info['sundayPHStr']
        
        # (2) Find the correct rate data based on the current day
        if (0 <= today <= 4) and (wd_str):
            rate_str = wd_str

        elif today == 5 and (sat_str):
            rate_str = sat_str

            if rate_str == "Same as wkdays":
                rate_str = wd_str

        elif today == 6 and (sun_str):
            rate_str = sun_str

            if rate_str == "Same as wkdays":
                rate_str = wd_str
                
            elif rate_str == "Same as Saturday":
                rate_str = sat_str

        if rate_str == None:
            price_per_hr = find_price_per_hr(carpark, num_hrs, vehicle_type)

            if (price_per_hr >= 0):
                rate_str = f"${price_per_hr:.2f} per hour"

        if rate_str == None:
            return no_price_info
        
        return f"💵 *Rate: *{rate_str}\n"
        
    else:
        # Handle URA carpark
        # (1) Format the current time to the same format found in the entity - e.g. 1500
        current_time = current_time.strftime("%H%M")

        # (2) Format the current day to either 'weekday', 'saturday', or 'sundayPublicHoliday'
        if 0 <= today <= 4:
            day_type = "WeekdayRate"
        elif today == 5:
            day_type = "SaturdayRate"
        else:
            day_type = "SundayPHRate"

        # Set mapping
        day_map = {
            "WeekdayRate": "weekday",
            "SaturdayRate": "satday",
            "SundayPHRate": "sunPH"
        }

        # (3) Find the correct rate data based on time and day    
        all_timeslots = carpark['pricing']['value'][vehicle_type]['TimeSlots']

        # Loop through the time slots and find the correct time range
        for e_timeslot in all_timeslots:
            # Check if current_time is between start and end time
            start_time = e_timeslot[day_type]['startTime']  # e.g. 0700
            end_time = e_timeslot[day_type]['endTime']      # e.g. 1700

            if int(start_time) <= int(current_time) <= int(end_time):
                # Found the correct time slot
                rate_str = e_timeslot[day_type][day_map[day_type] + 'Rate']                 # e.g. $1.20
                time_interval_mins_str = e_timeslot[day_type][day_map[day_type] + 'Min']    # e.g. 30 Min

                res = f"💵 *{day_type}:* {rate_str}/{time_interval_mins_str}\n🕙 *Rate Time:* {start_time} - {end_time}\n"
                return res
        
        # If no rate is found, return -1.0
        return "💵 No pricing info available for current time\n"
        

def is_word_present(sentence, word):
    """ Function that returns true if the word is found """
    sentence = sentence.upper()
    # splitting the sentence to list
    lis = sentence.split()
    # checking if word is present
    if(lis.count(word) > 0):
        return True
    else:
        return False
    
def remove_selected_button(query):
    """Remove the button that the user has selected"""
    keyboard = query.message.reply_markup.inline_keyboard
    new_keyboard = []
    for row in keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data != query.data:
                new_row.append(btn)
        if new_row:  # Only add non-empty rows
            new_keyboard.append(new_row)
    return new_keyboard

def is_ura_carpark(carpark) -> bool:
    '''
    Check if the carpark is a URA carpark or Commercial carpark
    '''
    
    # If pricing.value has a Car key, it is a URA carpark
    if 'Car' in carpark['pricing']['value']:
        return True

    # If pricing.value has a rates key, it is a Commercial carpark
    if 'rates' in carpark['pricing']['value']:
        return False

def get_time_string(duration_mins: float):
    '''
    Function to convert duration in minutes to a human-readable string
    '''

    if duration_mins < 60:
        return f"{int(duration_mins)} mins"
    else:
        hours = int(duration_mins // 60)
        mins = int(duration_mins % 60)

        if mins == 0:
            return f"{hours} hr"
        else:
            return f"{hours} hr {mins} mins"

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the session and provide a restart button."""

    if context.user_data.get('live_location_message_id'):
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['live_location_message_id']
        )

    if context.user_data.get("google_route_id"):
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["google_route_id"],
            reply_markup=None
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👋 *Goodbye!* I look forward to assisting you again.\n\nTo start a new session, please enter /start or press the menu button on the left.", parse_mode="Markdown",
        reply_markup=None,
    )
            
    return ConversationHandler.END

def repeated_function_calls(function, timer: int, stop_event: threading.Event):
    """Repeatedly call the provided function every `timer` seconds."""
    while not stop_event.is_set():
        try:
            print("running", function.__name__)
            # Call the provided function
            function()
        except Exception as e:
            print(f"Error running the function: {e}")
        
        # Wait for the specified interval before running the function again
        stop_event.wait(timer)

async def update_context_broker():
    """Update the context broker with the API data at API update frequency.
    
    URA Carpark ParkingAvailability Update Frequency: Every 5 mins / 300 seconds

    Weather Data Update Frequency: Every 2 hours / 7200 seconds

    TrafficAdvisories Update Frequency: Every 2 minutes / 120 seconds
    """
    stop_event = threading.Event()

    try:
        print("Updating context broker...")
        # Create threads for each repeated function call
        carpark_thread = threading.Thread(target=repeated_function_calls, args=(import_Carpark_entity, 300, stop_event)) 
        weather_thread = threading.Thread(target=repeated_function_calls, args=(import_WeatherForecast_entity, 7200, stop_event)) 
        traffic_thread = threading.Thread(target=repeated_function_calls, args=(import_TrafficAdvisories_entity, 120, stop_event)) 

        # Start the threads
        carpark_thread.start()
        weather_thread.start()
        traffic_thread.start()

        # Join the threads to ensure they run concurrently
        carpark_thread.join()
        weather_thread.join()
        traffic_thread.join()
        print("Context broker updated successfully.")
    except Exception as e:
        print(f"Error updating context broker: {e}")
    finally:
        stop_event.set()