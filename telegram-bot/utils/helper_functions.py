
def find_closest_three_carparks(nearest_carparks_list, dest_lat, dest_long, selected_preference):
    closest_three_carparks = []
    distance_dict = {}
    final_three_carparks = []

    for carpark in nearest_carparks_list:
        carpark_dict = carpark.to_dict()
        lat = carpark_dict["location"]["value"]["coordinates"][1]
        long = carpark_dict["location"]["value"]["coordinates"][0]
        distance = geodesic((dest_lat, dest_long), (lat, long)).km
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
        print("selected_carpark:", selected_carpark[0])
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


def aggregate_message(closest_three_carparks, selected_preference):
    carparks_message = "🚗 *The 3 possible carparks near your destination are:*\n\n"

    today = datetime.today().weekday()
    current_time = datetime.now().time()

    price_dict = {}

    for count, carpark in enumerate(closest_three_carparks, 1):
        carpark_name = carpark['CarparkName']['value'].title()
        if 'Pricing' in carpark and 'Car' in carpark['Pricing']["value"]:
        
            carparks_message += (
                    f"*{count}. {carpark_name}*\n"
                    f"🅿️ *Available Lots:* {carpark['ParkingAvailability']['value']}\n"
                    f"📏 *Distance:* {carpark['distance']:.2f} km\n"
                    f"☂️ *Sheltered:* {'Yes' if carpark['Sheltered']['value'] else 'No'}\n"
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
        print(price_list)

        if len(set(price_list))==1:
            cheapest_carpark_message = f"💸 *All carparks have the same price at {price_list[0]} per 30 mins* \n\n"
            final_message = cheapest_carpark_message + carparks_message
            return final_message
        else:
            lowest_value_key = min(price_dict, key=price_dict.get)
            lowest_value = price_dict[lowest_value_key]
            print("Lowest Value:", lowest_value)
            print("Lowest Value Key:", lowest_value_key)
        cheapest_carpark_message = f"💸 *The cheapest carpark is: {lowest_value_key} at {lowest_value} per 30 mins* \n\n"
        final_message = cheapest_carpark_message + carparks_message 
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