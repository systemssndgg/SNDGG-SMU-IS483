import mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime, timedelta
import mylibs.SVY21 as SVY21

TWO_HOUR_WEATHER_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
TEMPREATURE_URL = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
RAINFALL_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
WIND_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-direction"
UVI_URL = "https://api-open.data.gov.sg/v2/real-time/api/uv"
PM25_URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25"

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant

# Initialise the SVY21 class
svy21_converter = SVY21.SVY21()

# Convert to NGSI-LD
"""
Weather Forecast
- id - from SDM
- validFrom - From SDM
- validTo - From SDM
- weatherType - From SDM 
- validity - From SDM 



Example NEA data return:
            "area": "Tampines",
            "forecast": "Partly Cloudy (Night)"

"""

def get_two_hour_weather():
    response = requests.get(
        TWO_HOUR_WEATHER_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code == 200:
        count = 0
        entity_list = []
        # Get current date and time
        now = datetime.now()
        # Get date and time 2 hours later
        two_hours_later = now + timedelta(hours=2)

        # Format date and time
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        two_hours_later_str = two_hours_later.strftime("%Y-%m-%dT%H:%M:%S")

        forecast_list = json.loads(response.content.decode("utf-8"))

        for area in forecast_list["data"]["area_metadata"]:
            remove_spaced_name = area["name"].replace(" ", "")
            id = f"{remove_spaced_name}-WeatherForecast-{now_str}_{two_hours_later_str}"
            entity = Entity("WeatherForecast", id, ctx=ctx)

            for key, value in area.items():
                if key == "name":
                    entity.prop("Area", value)
                    for forecast in forecast_list["data"]["items"][0]["forecasts"]:
                        if value == forecast["area"]:
                            entity.prop("forecast", forecast["forecast"])
                if key == "label_location":
                    lat = float(area["label_location"]["latitude"])
                    long = float(area["label_location"]["longitude"])
                    entity.gprop("location", (lat, long))
            entity_list.append(entity)

        print(
            "Total number of forecasts: ",
            len(forecast_list["data"]["items"][0]["forecasts"]),
        )
        print("Total entities created: ", len(entity_list), "\n")

        return entity_list
    else:
        return None