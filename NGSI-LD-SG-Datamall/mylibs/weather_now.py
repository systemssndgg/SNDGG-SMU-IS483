import libs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import libs.SVY21 as SVY21

# ACCESS_KEY = constants.URA_ACCESS_KEY
# TOKEN_URL = "https://www.ura.gov.sg/uraDataService/insertNewToken.action"
# CARPARK_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Details"
# SEASON_CARPARK_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Season_Car_Park_Details"

PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
TEMPREATURE_URL = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
RAINFALL_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
WIND_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-speed"
UVI_URL = "https://api-open.data.gov.sg/v2/real-time/api/uv"
PM25_URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25"


ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant

#Convert to NGSI-LD
'''
Weather 
- Temperature - 
- Humidity -
- PM2.5 -
- Rainfall -
- Wind Speed -
- Ultraviolet Index (UVI) -
- Pollutant Standards Index (PSI) -




Example NEA data return:
            "CarParkID": "1",
            "Area": "Marina",
            "Development": "Suntec City",
            "Location": "1.29375 103.85718",
            "AvailableLots": 442,
            "LotType": "C",
            "Agency": "LTA"


Carpark
- id - Core context
- DevelopmentName (From LTA)
- Region (From LTA)
- Location - Gprop
- Price (Pending Terrence)
- ParkingAvalibility - From SDM 
- ParkingChargeType - From SDM (Pending Terrence)
- ParkingMaxAvalibility - From SDM (Info not avaliable)
- DataSource - From SDM
- ParkingSiteOwner (relationship) - From SDM


Example LTA data return:
            "CarParkID": "1",
            "Area": "Marina",
            "Development": "Suntec City",
            "Location": "1.29375 103.85718",
            "AvailableLots": 442,
            "LotType": "C",
            "Agency": "LTA"
'''


def get_two_hour_weather():
    response = requests.get(
        TWO_HOUR_WEATHER_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",


        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_psi():
    response = requests.get(
        PSI_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_temperature():
    response = requests.get(
        TEMPREATURE_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_rainfall():
    response = requests.get(
        RAINFALL_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_wind():
    response = requests.get(
        WIND_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_uvi():
    response = requests.get(
        UVI_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    
def get_pm25():
    response = requests.get(
        PM25_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        return None
    


# def get_carpark(ura_token):
#     response = requests.get(
#         CARPARK_URL,
#         headers={
#             "Content-Type": "application/json",
#             "AccessKey": ACCESS_KEY,
#             "Token": ura_token,
#             "User-Agent": "Mozilla/5.0",
#         },
#     )

#     if response.status_code == 200:
#         count = 0
#         entity_list = []

#         carpark_list = json.loads(response.content.decode("utf-8"))

#         for carpark in carpark_list["Result"]:
#             remove_spaced_name = carpark["ppName"].replace(" ", "")
#             id = remove_spaced_name + str(carpark["ppCode"])

#             entity = Entity("Carpark", id, ctx=ctx)

#             for key, value in carpark.items():
#                 if key == "weekdayMin":
#                     entity.prop("WeekdayMaximumDuration", value)
#                 elif key == "weekdayRate":
#                     entity.prop("WeekdayRate", value)
#                 elif key == "satdayMin":
#                     entity.prop("SaturdayMaximumDuration", value)
#                 elif key == "satDayRate":
#                     entity.prop("SaturdayRate", value)
#                 elif key == "sunPHMin":
#                     entity.prop("SundayPHMaximumDuration", value)
#                 elif key == "sunPHRate":
#                     entity.prop("SundayPHRate", value)
#                 elif key == "ppCode":
#                     entity.prop("CarParkID", value)
#                 elif key == "ppName":
#                     entity.prop("DevelopmentName", value.rstrip())
#                 elif key == "geometries":
#                     svy21_geocoordinates = value[0]["coordinates"].split(",")
#                     latlon_geocoordinates = svy21_converter.computeLatLon(
#                         float(svy21_geocoordinates[0]), float(svy21_geocoordinates[1])
#                     )
#                     if len(latlon_geocoordinates) > 1:
#                         entity.gprop(
#                             "location",
#                             (
#                                 float(latlon_geocoordinates[0]),
#                                 float(latlon_geocoordinates[1]),
#                             ),
#                         )
#                 elif key == "parkCapacity":
#                     entity.prop("ParkingAvailablilty", value)
#                 elif key == "parkingSystem":
#                     entity.prop("LotType", value)
#                 elif key == "startTime":
#                     entity.prop(
#                         "StartTime",
#                         (datetime.strptime(value, "%I.%M %p").strftime("%H%M")),
#                     )
#                 elif key == "endTime":
#                     entity.prop(
#                         "endTime",
#                         (datetime.strptime(value, "%I.%M %p").strftime("%H%M")),
#                     )

#             entity_list.append(entity)

#             count += 1
#             if count == 10:
#                 break

#         print("Total number of carparks: ", len(carpark_list["Result"]))
#         print("Total entities created: ", len(entity_list))

#         return entity_list
#     else:
#         return None


# def get_season_carpark(ura_token):
#     response = requests.get(
#         SEASON_CARPARK_URL,
#         headers={
#             "Content-Type": "application/json",
#             "AccessKey": ACCESS_KEY,
#             "Token": ura_token,
#             "User-Agent": "Mozilla/5.0",
#         },
#     )

#     if response.status_code == 200:
#         return json.loads(response.content.decode("utf-8"))
#     else:
#         return None
