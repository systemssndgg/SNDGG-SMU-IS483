import entities.mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime, timedelta

# ============================ Weather Forecast ======================

TWO_HOUR_WEATHER_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
TEMPERATURE_URL = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
RAINFALL_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
WIND_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-direction"
UVI_URL = "https://api-open.data.gov.sg/v2/real-time/api/uv"
PM25_URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25"

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant

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

# ============================ Weather Observed ======================

# WindDirectionURL = "https://data.gov.sg/datasets?topics=environment&page=1&query=weather+&resultId=d_534cf203023b51f51f879145ccc56ff9"
# WindSpeedURL = "https://data.gov.sg/datasets?topics=environment&page=1&query=weather+&resultId=d_7677738484067741bf3b56ab5d69c7e9"
# AirTemperatureURL = "https://data.gov.sg/datasets?topics=environment&page=1&query=weather+&resultId=d_66b77726bbae1b33f218db60ff5861f0"
# RelativeHumidityURL = "https://data.gov.sg/datasets?topics=environment&page=1&query=weather+&resultId=d_2d3b0c4da128a9a59efca806441e1429#tag/default/GET/air-temperature"
# RainfallPrecipitationURL = "https://data.gov.sg/datasets?topics=environment&page=1&query=weather+&resultId=d_6580738cdd7db79374ed3152159fbd69#tag/default/GET/air-temperature"


dataURL = "https://api-open.data.gov.sg/v2/real-time/api"
RelativeHumidityURL = dataURL + "/relative-humidity"
RainfallPrecipitationURL = dataURL + "/rainfall"
WindDirectionURL = dataURL + "/wind-direction"
WindSpeedURL = dataURL + "/wind-speed"
AirTemperatureURL = dataURL + "/air-temperature"
UVIndexURL = dataURL + "/uv"

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Example usage
def fetch_relative_humidity_data():
    RelativeHumidityData = fetch_data(RelativeHumidityURL)
    finalData = []
    for i in range(0, len(RelativeHumidityData['data']['stations'])):
        entity = RelativeHumidityData['data']['stations'][i]
        entity['value'] = RelativeHumidityData['data']['readings'][0]['data'][i]['value']
        entity['timestamp'] = RelativeHumidityData['data']['readings'][0]['timestamp']
        finalData.append(entity)
    return finalData

def fetch_rainfall_precipitation_data():
    RainfallPrecipitationData = fetch_data(RainfallPrecipitationURL)
    finalData = []
    for i in range(0, len(RainfallPrecipitationData['data']['stations'])):
        entity = RainfallPrecipitationData['data']['stations'][i]
        entity['value'] = RainfallPrecipitationData['data']['readings'][0]['data'][i]['value']
        entity['timestamp'] = RainfallPrecipitationData['data']['readings'][0]['timestamp']
        finalData.append(entity)
    return finalData

def fetch_wind_direction_data():
    WindDirectionData = fetch_data(WindDirectionURL)
    finalData = []
    for i in range(0, len(WindDirectionData['data']['stations'])):
        entity = WindDirectionData['data']['stations'][i]
        entity['value'] = WindDirectionData['data']['readings'][0]['data'][i]['value']
        entity['timestamp'] = WindDirectionData['data']['readings'][0]['timestamp']
        finalData.append(entity)
    return finalData

def fetch_wind_speed_data():
    WindSpeedData = fetch_data(WindSpeedURL)
    finalData = []
    for i in range(0, len(WindSpeedData['data']['stations'])):
        entity = WindSpeedData['data']['stations'][i]
        entity['value'] = WindSpeedData['data']['readings'][0]['data'][i]['value']
        entity['timestamp'] = WindSpeedData['data']['readings'][0]['timestamp']
        finalData.append(entity)
    return finalData

def fetch_air_temperature_data():
    AirTemperatureData = fetch_data(AirTemperatureURL)
    finalData = []
    for i in range(0, len(AirTemperatureData['data']['stations'])):
        entity = AirTemperatureData['data']['stations'][i]
        entity['value'] = AirTemperatureData['data']['readings'][0]['data'][i]['value']
        entity['timestamp'] = AirTemperatureData['data']['readings'][0]['timestamp']
        finalData.append(entity)
    return finalData

def fetch_uv_index_data():
    UVIndexData = fetch_data(UVIndexURL)
    finalData = {}
    timestamp = UVIndexData['data']['records'][0]['timestamp']
    finalData['timestamp'] = timestamp
    for i in range(0, len(UVIndexData['data']['records'][0]['index'])):
        if UVIndexData['data']['records'][0]['index'][i]['hour'] == timestamp:
            finalData['UVIndex'] = UVIndexData['data']['records'][0]['index'][i]['value']
    return finalData

def get_weather_observed():
    # print("Running get_weather_observed_data()...")
    # Fetches data from each data source and returns a list of WeatherObserved entities
    entity_dict = {}

    # [1] relative_humidity_data
    # print("\nFetching relative humidity data...")
    rhum_data = fetch_relative_humidity_data()
    # print("Fetched ", len(rhum_data), " relative humidity data")

    for e_rhum in rhum_data:
        e_id = check_id(e_rhum, entity_dict)

        entity_dict[e_id].prop("relativeHumidity", e_rhum['value'])

    # [2] rainfall_precipitation_data
    # print("\nFetching rainfall precipitation data...")
    rain_data = fetch_rainfall_precipitation_data()
    # print("Fetched ", len(rain_data), " rainfall precipitation data")

    for e_rain in rain_data:
        e_id = check_id(e_rain, entity_dict)

        entity_dict[e_id].prop("precipitation", e_rain['value'])

    # [3] wind_direction_data
    # print("\nFetching wind direction data...")
    wind_dir_data = fetch_wind_direction_data()
    # print("Fetched ", len(wind_dir_data), " wind direction data")

    for e_wind_dir in wind_dir_data:
        e_id = check_id(e_wind_dir, entity_dict)

        entity_dict[e_id].prop("windDirection", e_wind_dir['value'])

    # [4] wind_speed_data
    # print("\nFetching wind speed data...")
    wind_speed_data = fetch_wind_speed_data()
    # print("Fetched ", len(wind_speed_data), " wind speed data")

    for e_wind_speed in wind_speed_data:
        e_id = check_id(e_wind_speed, entity_dict)

        entity_dict[e_id].prop("windSpeed", e_wind_speed['value'])

    # [5] air_temperature_data
    # print("\nFetching air temperature data...")
    air_temp_data = fetch_air_temperature_data()
    # print("Fetched ", len(air_temp_data), " air temperature data")

    for e_air_temp in air_temp_data:
        e_id = check_id(e_air_temp, entity_dict)

        entity_dict[e_id].prop("temperature", e_air_temp['value'])
    
    # [6] uv_index_data
    # print("\nFetching UV Index data...")
    # Check the current time
    current_time = datetime.now().strftime("%H:%M")
    if current_time < "07:00" or current_time > "20:00":
        # print("Outside of UV Index hours. Setting UV Index data to 0...")
        uv_index_data = {"UVIndex": 0, "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")}

    else:
        uv_index_data = fetch_uv_index_data()
        # print(f"Fetched UV Index data: {uv_index_data['UVIndex']}, for timestamp:, {uv_index_data['timestamp']}")

    # Add UV Index to all entities
    for key in entity_dict.keys():
        entity_dict[key].prop("uvIndex", uv_index_data['UVIndex'])

    limited_entities = list(entity_dict.values())[:10]

    print("Total number of observed: ", len(entity_dict))
    print("Total entities created: ", len(limited_entities), "\n")
    
    return list(entity_dict.values())

# Helper Functions ==================================================

def get_id(json_obj):
    # Takes each json object and figures out how to ID it
    # ID: location_name + timestamp

    return str(json_obj['name']).lower().replace(" ", "-") + "_" + str(json_obj['timestamp'])


def check_id(json_obj, entity_dict):
    # Checks if entity already exists. If not, creates entity in enity_dict. Returns id always
    # IMPORTANT: Assumes json_obj has "location" and "timestamp" keys
    e_id = get_id(json_obj)

    if e_id in entity_dict:
        return e_id
    
    else:
        entity = Entity("WeatherObserved", e_id, ctx=ctx)  # type, id , ctx

        # Add latlong
        geocoordinates = json_obj["location"]
        lat = geocoordinates["latitude"]
        long = geocoordinates["longitude"]
        entity.gprop( "location", (lat, long) )
        
        # Add timestamp
        entity.prop("timestamp", json_obj['timestamp'])

        entity_dict[e_id] = entity
        return e_id

# TESTING
# # [1] relative_humidity_data ==================================
#     # {
#     #   'id': 'S108',
#     #   'deviceId': 'S108',
#     #   'name': 'Marina Gardens Drive',
#     #   'location': {
#     #       'latitude': 1.2799,
#     #       'longitude': 103.8703
#     #   },
#     #   'value': 68.7,
#     #   'timestamp': '2024-09-26T16:58:00+08:00'
#     # }

# print("\nrelative_humidity_data ==================================")
# print(fetch_relative_humidity_data()[0])


# # [2] rainfall_precipitation_data ==================================
#     # {
#     #   'id': 'S218',
#     #   'deviceId': 'S218',
#     #   'name': 'Bukit Batok Street 34',
#     #   'location': {
#     #       'latitude': 1.36491,
#     #       'longitude': 103.75065
#     #   },
#     #   'value': 0,
#     #   'timestamp': '2024-09-26T16:58:00+08:00'
#     # }

# print("\nrainfall_precipitation_data ==================================")
# print(fetch_rainfall_precipitation_data()[0])


# # [3] wind_direction_data ==================================
#     # {
#     #   'id': 'S108',
#     #   'deviceId': 'S108',
#     #   'name': 'Marina Gardens Drive',
#     #   'location': {
#     #       'latitude': 1.2799,
#     #       'longitude': 103.8703
#     #   },
#     #   'value': 225,
#     #   'timestamp': '2024-09-26T16:58:00+08:00'
#     # }

# print("\nwind_direction_data ==================================")
# print(fetch_wind_direction_data()[0])


# # [4] wind_speed_data ==================================
#     # {
#     #   'id': 'S108',
#     #   'deviceId': 'S108',
#     #   'name': 'Marina Gardens Drive',
#     #   'location': {
#     #       'latitude': 1.2799,
#     #       'longitude': 103.8703
#     #   },
#     #   'value': 5.5,
#     #   'timestamp': '2024-09-26T16:58:00+08:00'
#     # }

# print("\nwind_speed_data ==================================")
# print(fetch_wind_speed_data()[0])


# # air_temperature_data
#     # {
#     #   'id': 'S108',
#     #   'deviceId': 'S108',
#     #   'name': 'Marina Gardens Drive',
#     #   'location': {
#     #       'latitude': 1.2799,
#     #       'longitude': 103.8703
#     #   },
#     #   'value': 28.6,
#     #   'timestamp': '2024-09-26T16:58:00+08:00'
#     # }
    
# print("\nair_temperature_data ==================================")
# print(fetch_air_temperature_data()[0])