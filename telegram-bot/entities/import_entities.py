from mylibs.ura_parking import get_ura_token, get_ura_carparks, get_season_carpark
from mylibs.traffic_advisories import get_traffic_advisories
from mylibs.ngsi_ld import create_entities_in_broker
from mylibs.weather import get_two_hour_weather, get_weather_observed

from mylibs.ngsi_ld import create_entities_in_broker

# ========== Carpark  ==========
token = get_ura_token()['Result']
print("Token ", token)

carpark_list = get_ura_carparks(token)


def import_Carpark_entity():
    print("\nPushing Carpark and Traffic Advisory to broker...")
    # main() # add creation of commercial carparks function here
    create_entities_in_broker(carpark_list)

# ========== Traffic Advisories  ==========
traffic_advisories_list = get_traffic_advisories()

def import_TrafficAdvisories_entity():
    print("\nPushing Traffic Advisory to broker...")
    create_entities_in_broker(traffic_advisories_list)

# ========== Weather Block ==========
forecast_list = get_two_hour_weather()
observed_list = get_weather_observed()

def import_WeatherForecast_entity():
    print("\nPushing to broker...")
    create_entities_in_broker(forecast_list)
    create_entities_in_broker(observed_list)


if __name__ == "__main__":
    try:
        import_WeatherForecast_entity()
        import_Carpark_entity()
        import_TrafficAdvisories_entity()
        print("\nCompleted importing entities.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nFailed to import entities.")