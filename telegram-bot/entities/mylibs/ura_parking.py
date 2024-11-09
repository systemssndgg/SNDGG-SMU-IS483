import entities.mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import entities.mylibs.SVY21 as SVY21


import colorama
from colorama import Fore, Back, Style
import traceback
colorama.init(autoreset=True)

ACCESS_KEY = constants.URA_ACCESS_KEY
TOKEN_URL = "https://www.ura.gov.sg/uraDataService/insertNewToken.action"
CARPARK_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Details"
SEASON_CARPARK_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Season_Car_Park_Details"
CARPARK_AVAILABILITY_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Availability"

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant

# Initialise the SVY21 class
svy21_converter = SVY21.SVY21()

# Retrieve API token for the day
def get_ura_token():
    response = requests.get(TOKEN_URL, headers={
    'Content-Type': 'application/json',
    'AccessKey': ACCESS_KEY,
    'User-Agent': 'Mozilla/5.0'
})

    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None

def get_ura_carparks(ura_token):
    # retrieve carpark availabilities
    carpark_availability_response = requests.get(CARPARK_AVAILABILITY_URL, headers={
        "Content-Type": "application/json",
        "AccessKey": ACCESS_KEY,
        "Token": ura_token,
        "User-Agent": "Mozilla/5.0"
    })

    if carpark_availability_response.status_code == 200:
        carpark_availability_list = json.loads(carpark_availability_response.content.decode("utf-8"))
    else:
        print(f"Failed to retrieve URA carparks , {carpark_availability_response.status_code}")
        return None

    # retrieve carpark details
    carpark_details_response = requests.get(CARPARK_URL, headers={
        "Content-Type": "application/json",
        "AccessKey": ACCESS_KEY,
        "Token": ura_token,
        "User-Agent": "Mozilla/5.0"
    })

    if carpark_details_response.status_code == 200:
        count = 0
        entity_list = []
        unique_carparkNames = []
        carpark_list = json.loads(carpark_details_response.content.decode("utf-8"))

        for carpark in carpark_list["Result"]:
            remove_spaced_name = carpark["ppName"].replace(" ", "")
            id = remove_spaced_name + str(carpark["ppCode"])

            # Check if carpark name is unique, if yes, create a new entity
            if carpark["ppName"].strip() not in unique_carparkNames:
                unique_carparkNames.append(carpark["ppName"].strip())
                
                # Set entity properties
                entity = Entity("Carpark", id, ctx=ctx)

                # Set carpark name
                entity.prop("carparkName", carpark["ppName"])
                
                # Set location using coordinates
                if carpark["geometries"]:
                    svy21_geocoordinates = carpark["geometries"][0]["coordinates"].split(",")
                    latlon_geocoordinates = svy21_converter.computeLatLon(float(svy21_geocoordinates[1]), float(svy21_geocoordinates[0]))
                    if len(latlon_geocoordinates) > 1:
                        entity.gprop("location", (float(latlon_geocoordinates[0]), float(latlon_geocoordinates[1])))
                
                # Parking capcacity
                if carpark["parkCapacity"]:
                    if carpark["parkCapacity"] != "0":
                        entity.prop("parkingCapacity", int(carpark["parkCapacity"]))

                # Mock sheltered status
                entity.prop("sheltered", False)
                # entity.prop("Sheltered", False if count % 2 == 0 else True)
                # count += 1


                # Parking availability
                for carpark_availability in carpark_availability_list["Result"]:
                    if carpark["ppCode"] == carpark_availability["carparkNo"] and carpark_availability["lotType"] == "C":
                        entity.prop("parkingAvailability", int(carpark_availability["lotsAvailable"]))
                        break
                
                # Append to entity_list
                entity_list.append(entity)

        # Update entity pricing based on carpark data
        # Loop through each created entity, then loop through each carpark in the carpark list
        # Everytime the carpark name matches, update the pricing dictionary
        # If it's the first time the carpark name matches, create a new pricing dictionary
        for entity in entity_list:
            pricing = {}
            pricing["rates"] = {}
            for carpark in carpark_list["Result"]:
                if entity["carparkName"]["value"].strip() == carpark["ppName"].strip():
                    try:
                        if "weekdayRate" in carpark and "weekdayMin" in carpark:
                            weekdayRateFloat = float(carpark["weekdayRate"].replace("$", ""))
                            weekdayMinFloat = float(carpark["weekdayMin"].replace(" mins", " "))
                        if "satdayRate" in carpark and "satdayMin" in carpark:
                            satdayRateFloat = float(carpark["satdayRate"].replace("$", ""))
                            satdayMinFloat = float(carpark["satdayMin"].replace(" mins", " "))
                        if "sunPHRate" in carpark and "sunPHMin" in carpark:
                            sunPHRateFloat = float(carpark["sunPHRate"].replace("$", ""))
                            sunPHMinFloat = float(carpark["sunPHMin"].replace(" mins", " "))
                        
                        # Can't divide by 0 in Python, changing it to 1 has the same effect.
                        if weekdayMinFloat == 0:
                            weekdayMinFloat = 1
                        if satdayMinFloat == 0:
                            satdayMinFloat = 1
                        if sunPHMinFloat == 0:
                            sunPHMinFloat = 1

                        # If the rate is 0, the rate per hour is 0
                        if weekdayRateFloat == 0:
                            weekdayRatePerHour = 0
                        else:
                            weekdayRatePerHour = weekdayRateFloat / weekdayMinFloat * 60
                        if satdayRateFloat == 0:
                            satdayRatePerHour = 0
                        else:
                            satdayRatePerHour = satdayRateFloat / satdayMinFloat * 60
                        if sunPHRateFloat == 0:
                            sunPHRatePerHour = 0
                        else:
                            sunPHRatePerHour = sunPHRateFloat / sunPHMinFloat * 60

                        # Convert startTime and endTime to a 24-hour format
                        startTime = convert_to_24hr(carpark["startTime"])
                        endTime = convert_to_24hr(carpark["endTime"])

                        # Check if then entity already has a populated pricing dictionary
                        if not pricing["rates"]:
                            pricing["rates"]["weekday"] = {
                                'timeBased': [
                                    {
                                    'startTime': startTime,
                                    'endTime': endTime,
                                    'ratePerHour': weekdayRatePerHour
                                    }
                                ]
                            }
                            pricing["rates"]["saturday"] = {
                                'timeBased': [
                                    {
                                    'startTime': startTime,
                                    'endTime': endTime,
                                    'ratePerHour': satdayRatePerHour
                                    }
                                ]
                            }
                            pricing["rates"]["sundayPublicHoliday"] = {
                                'timeBased': [
                                    {
                                    'startTime': startTime,
                                    'endTime': endTime,
                                    'ratePerHour': sunPHRatePerHour
                                    }
                                ]
                            }
                        else:
                            pricing["rates"]["weekday"]["timeBased"].append({
                                'startTime': startTime,
                                'endTime': endTime,
                                'ratePerHour': weekdayRatePerHour
                            })
                            pricing["rates"]["saturday"]["timeBased"].append({
                                'startTime': startTime,
                                'endTime': endTime,
                                'ratePerHour': satdayRatePerHour
                            })
                            pricing["rates"]["sundayPublicHoliday"]["timeBased"].append({
                                'startTime': startTime,
                                'endTime': endTime,
                                'ratePerHour': sunPHRatePerHour
                            })
                    except Exception as e:
                        print(f"Error processing carpark {carpark['ppName']}: {e}")
                        traceback.print_exc()
                        continue
            entity.prop('pricing', pricing)    

        print("Total number of carparks: ", len(carpark_list["Result"]))
        print("Total entities created: ", len(entity_list), "\n")
        
        return entity_list 
    else:
        return None

def get_season_carpark(ura_token):
    response = requests.get(SEASON_CARPARK_URL, headers={
        "Content-Type": "application/json",
        "AccessKey": ACCESS_KEY,
        "Token": ura_token,
        "User-Agent": "Mozilla/5.0"
    })

    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None

def convert_to_24hr(time):
    return datetime.strptime(time, "%I.%M %p").strftime("%H:%M")

