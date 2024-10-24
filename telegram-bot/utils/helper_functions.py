from geopy.distance import geodesic
from datetime import datetime
import numpy as np
import random
import logging

from utils.google_maps import get_route_duration
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def find_closest_three_carparks(nearest_carparks_list, dest_lat, dest_long, selected_preference):
    closest_three_carparks = []
    distance_dict = {}
    final_three_carparks = []

    for carpark in nearest_carparks_list:
        carpark_dict = carpark.to_dict()
        lat = carpark_dict["location"]["value"]["coordinates"][1]
        long = carpark_dict["location"]["value"]["coordinates"][0]
        distance = geodesic((dest_lat, dest_long), (lat, long)).km #distance from carpark to user's final destination
        distance_dict[carpark_dict["CarparkName"]["value"]] = distance
        carpark_dict["distance"] = distance
        if "Car" in carpark_dict["Pricing"]["value"] and carpark_dict["ParkingAvailability"]["value"] > 0:
            if selected_preference == "sheltered":
                if carpark["Sheltered"]["value"] == True:
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
    closest_three_carparks.sort(key=lambda x: distance_dict[x["CarparkName"]["value"]])

    # Add the sorted carparks to the final_three_carparks list
    final_three_carparks.extend(closest_three_carparks)
    # for i in final_three_carparks:
    #     print("carparks:", i["CarparkName"]["value"], i["distance"])

    return final_three_carparks


def find_closest_carpark(carparks_list, dest_lat, dest_long):
    """Find closest carpark in the event that it rains and originally selected carpark is not sheltered"""
    in_list = False
    for carpark in carparks_list:
        if carpark["Sheltered"]["value"] == True:
            in_list = True
            return carpark
    
    if in_list == False:
        distance_dict = {}
        selected_carpark = []
        
        lat = carpark["location"]["value"]["coordinates"][1]
        long = carpark["location"]["value"]["coordinates"][0]

        for carpark in nearest_carparks:
            distance = geodesic((dest_lat, dest_long), (lat, long)).km
            distance_dict[carpark["CarparkName"]["value"]] = distance
            
        distance_dict.sort(key=lambda x: distance_dict[x["CarparkName"]["value"]])

        # Add the sorted carparks to the final_three_carparks list
        selected_carpark.extend(closest_three_carparks)
        # print("selected_carpark:", selected_carpark[0])
        return selected_carpark[0]
    

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
    time_slots = carpark['Pricing']['value'][vehicle_type]['TimeSlots']

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
    carparks_message = "🚗 *The 3 possible carparks near your destination are:*\n\n"

    today = datetime.today().weekday()
    current_time = datetime.now().time()

    price_dict = {}
    duration_list = []

    for count, carpark in enumerate(closest_three_carparks, 1):
        carpark_name = carpark['CarparkName']['value'].title()
        if 'Pricing' in carpark and 'Car' in carpark['Pricing']["value"]:
            dest_lat = carpark['location']['value']['coordinates'][1]
            dest_long = carpark['location']['value']['coordinates'][0]
            duration = get_route_duration(live_location_lat, live_location_long, dest_lat, dest_long, travel_mode="driving")
            duration_list.append(duration)
            carparks_message += (
                f"*{count}. {carpark_name}*\n"
                f"🅿️ *Available Lots:* {carpark['ParkingAvailability']['value']}\n"
                f"🚶 *Walk to Destination* {round(carpark['walking_time'])} mins\n"
                f"☂️ *Sheltered:* {'Yes' if carpark['Sheltered']['value'] else 'No'}\n"
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
            fastest_carpark = closest_three_carparks[index_min_duration]["CarparkName"]["value"]
            fastest_carpark_message = f"*The Fastest carpark is: {fastest_carpark} with a travelling time of {duration_list[index_min_duration]} mins* \n\n"
            final_message = fastest_carpark_message + carparks_message
            return final_message

    print("Carpark Message from aggregate_message:", carparks_message)

    return carparks_message


def find_next_best_carpark(carparks, current_carpark):
    """Find the next best carpark with more than 10 available lots."""
    best_carpark = None
    min_distance = float('inf')

    for carpark in carparks:
        if carpark == current_carpark:
            continue
        
        available_lots = carpark['ParkingAvailability']['value']
        if available_lots > 10:
            distance = carpark['distance']  # Assuming you already calculated distances

            if distance < min_distance:
                min_distance = distance
                best_carpark = carpark

    return best_carpark


def get_top_carparks(live_location, carparks, user_preferences, num_cp_to_return, min_avail_lots=10, num_hrs=2, remove_unsheltered=False):
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
                    'Pricing': {
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

        OUTPUT PARAMETERS SPECIFICATIONS ===============================================================
        Returns: List of top N carpark dictionaries in the same format as the input carparks. (First item in the list is the best carpark)

            Added keys in each carpark dictionary:
            - 'walking_time': Time to walk from live location to carpark
            - 'drive_time': Time to drive to carpark
            - 'travel_time': Time to drive to carpark + Time to walk from carpark to destination
    '''

    # Filter out carparks that do not meet the minimum requirements
    new_carparks = []

    for cp in carparks:
        if int(cp['ParkingAvailability']['value']) < min_avail_lots:
            continue

        if remove_unsheltered and not cp['Sheltered']['value']:
            continue

        new_carparks.append(cp)
    
    carparks = new_carparks

    # Convert carpark data into a NumPy array
    carparks_list = []

    for cp in carparks:
        # Extract the values from the carpark dictionary
        price = find_price_per_hr(cp, num_hrs, 'Car')   # Need to change this later to fetch
        walk_time = get_route_duration(live_location[0], live_location[1], cp['location']['value']['coordinates'][1], cp['location']['value']['coordinates'][0], travel_mode="walking")
        drive_time = get_route_duration(live_location[0], live_location[1], cp['location']['value']['coordinates'][1], cp['location']['value']['coordinates'][0], travel_mode="driving")
        travel_time = walk_time + drive_time
        available_lots = int(cp['ParkingAvailability']['value'])
        is_sheltered = bool(cp['Sheltered']['value'])
         
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
        print(f"\n\nCarpark: {carparks[i]['CarparkName']['value']}")
        print(f"Score: {total_scores[i]}")
        print(f"\nPrice: {carparks_np[i][0]} | Normalised: {normalized_carparks[i][0]}")
        print(f"Walk Time: {carparks_np[i][1]} | Normalised: {normalized_carparks[i][1]}")
        print(f"Travel Time: {carparks_np[i][2]} | Normalised: {normalized_carparks[i][2]}")
        print(f"Available Lots: {carparks_np[i][3]} | Normalised: {normalized_carparks[i][3]}")
        print(f"Sheltered: {carparks_np[i][4]} | Normalised: {normalized_carparks[i][4]}")
    '''

    # Create the list of top N carparks and include walking_time and travel_time
    top_N_carparks = []

    for i in sorted_indices[:num_cp_to_return]:
        carpark_dict = carparks[i].to_dict()  # Convert to dictionary
        carpark_dict['walking_time'] = carparks_np[i][1]  # Add walking time
        carpark_dict['travel_time'] = carparks_np[i][2]   # Add travel time
        carpark_dict['drive_time'] = carparks_np[i][2] - carparks_np[i][1]  # Add drive time
        top_N_carparks.append(carpark_dict)

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

    # TO IMPLEMENT LATER: FIGURE OUT HOW TO CALCULATE PRICE PER HOUR
    today = datetime.today().weekday()
    current_time = datetime.now().time()

    price_info = find_rate_based_on_time(carpark=carpark, vehicle_type=vehicle_type, current_time=current_time, today=today)

    # Placeholder: Returns random float value between 0 and 5
    return round(random.uniform(0, 5), 2)

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