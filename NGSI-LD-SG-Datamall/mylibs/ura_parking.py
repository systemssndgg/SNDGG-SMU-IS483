import mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import mylibs.SVY21 as SVY21

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

def get_carpark(ura_token):
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
        iter_counter = 0

        for carpark in carpark_list["Result"]:
            remove_spaced_name = carpark["ppName"].replace(" ", "")
            id = remove_spaced_name + str(carpark["ppCode"])

            # Check if carpark name is unique, if yes, create a new entity
            if carpark["ppName"].strip() not in unique_carparkNames:
                unique_carparkNames.append(carpark["ppName"].strip())
                entity = Entity("Carpark", id, ctx=ctx)
                
                for key, value in carpark.items():
                    if key=="ppName":
                        entity.prop("CarparkName", value.strip())
                    if key == "geometries":
                        svy21_geocoordinates = value[0]["coordinates"].split(",")
                        latlon_geocoordinates = svy21_converter.computeLatLon(float(svy21_geocoordinates[1]), float(svy21_geocoordinates[0]))
                        if (len(latlon_geocoordinates) > 1):
                            entity.gprop("location", (float(latlon_geocoordinates[0]), float(latlon_geocoordinates[1])))
                    elif key == "parkCapacity":
                        entity.prop("ParkingCapacity", value)

                for carpark_availability in carpark_availability_list["Result"]:
                    if carpark["ppCode"] == carpark_availability["carparkNo"] and carpark_availability["lotType"] == "C":
                        entity.prop("ParkingAvailability", int(carpark_availability["lotsAvailable"]))
                        break
                    else:
                        entity.prop("ParkingAvailability", 0)
                
                price_dictionary = {
                    "Car" :{
                            "WeekdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "weekdayMin" : None,
                                "weekdayRate" : None
                            },
                            "SaturdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "satdayMin" : None,
                                "satdayRate" : None
                            },
                            "SundayPHRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "sunPHMin" : None,
                                "sunPHRate" : None
                            },
                    },
                    "Motorcycle" :{
                            "WeekdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "weekdayMin" : None,
                                "weekdayRate" : None
                            },
                            "SaturdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "satdayMin" : None,
                                "satdayRate" : None
                            },
                            "SundayPHRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "sunPHMin" : None,
                                "sunPHRate" : None
                            },
                    },
                    "Heavy Vehicle" :{
                            "WeekdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "weekdayMin" : None,
                                "weekdayRate" : None
                            },
                            "SaturdayRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "satdayMin" : None,
                                "satdayRate" : None
                            },
                            "SundayPHRate" : {
                                "startTime" : None,
                                "endTime" : None,
                                "sunPHMin" : None,
                                "sunPHRate" : None
                            },
                    }
                }
                entity.prop("Pricing", price_dictionary)
                entity_list.append(entity)
                count += 1
                if count == 10:
                    break

        for carpark in carpark_list["Result"]:            
            for entity in entity_list:
                vehicle_type = carpark["vehCat"]
                if entity["CarparkName"]["value"].strip() == carpark["ppName"].strip():
                    if carpark["weekdayRate"] != "$0.00":
                        entity["Pricing"]["value"][vehicle_type]["WeekdayRate"]["weekdayMin"] = carpark["weekdayMin"]
                        entity["Pricing"]["value"][vehicle_type]["WeekdayRate"]["weekdayRate"] = carpark["weekdayRate"]
                        entity["Pricing"]["value"][vehicle_type]["WeekdayRate"]["startTime"] = convert_to_24hr(carpark["startTime"])
                        entity["Pricing"]["value"][vehicle_type]["WeekdayRate"]["endTime"] = convert_to_24hr(carpark["endTime"])
                    if carpark["satdayRate"] != "$0.00":
                        entity["Pricing"]["value"][vehicle_type]["SaturdayRate"]["satdayMin"] = carpark["satdayMin"]
                        entity["Pricing"]["value"][vehicle_type]["SaturdayRate"]["satdayRate"] = carpark["satdayRate"]
                        entity["Pricing"]["value"][vehicle_type]["SaturdayRate"]["startTime"] = convert_to_24hr(carpark["startTime"])
                        entity["Pricing"]["value"][vehicle_type]["SaturdayRate"]["endTime"] = convert_to_24hr(carpark["endTime"])
                    if carpark["sunPHRate"] != "$0.00":
                        entity["Pricing"]["value"][vehicle_type]["SundayPHRate"]["sunPHMin"] = carpark["sunPHMin"]
                        entity["Pricing"]["value"][vehicle_type]["SundayPHRate"]["sunPHRate"] = carpark["sunPHRate"]
                        entity["Pricing"]["value"][vehicle_type]["SundayPHRate"]["startTime"] = convert_to_24hr(carpark["startTime"])
                        entity["Pricing"]["value"][vehicle_type]["SundayPHRate"]["endTime"] = convert_to_24hr(carpark["endTime"])

        print("Total number of carparks: ", len(carpark_list["Result"]))
        print("Total entities created: ", len(entity_list))

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
    return datetime.strptime(time, "%I.%M %p").strftime("%H%M")