import mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime

TWO_HOUR_WEATHER_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
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