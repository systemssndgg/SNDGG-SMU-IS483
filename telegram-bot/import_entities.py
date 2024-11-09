from entities.mylibs.ura_parking import get_ura_token, get_ura_carparks, get_season_carpark
from entities.mylibs.traffic_advisories import get_traffic_advisories
from entities.mylibs.ngsi_ld import create_entities_in_broker
from entities.mylibs.weather import get_two_hour_weather, get_weather_observed
from entities.mylibs.commercial_carparks import create_commercial_carparks
from entities.mylibs.hdb_carparks import create_hdb_carparks

from colorama import Fore


def import_Carpark_entity():
    token = get_ura_token()['Result']

    # URA Carparks
    print(Fore.MAGENTA + "\nPushing URA carparks to broker...")
    carpark_list = get_ura_carparks(token)
    create_entities_in_broker(carpark_list)

    # Commercial Carparks
    print(Fore.MAGENTA + "\nPushing commerical carparks to broker...")
    comm_carparks = create_commercial_carparks()
    create_entities_in_broker(comm_carparks)

    # HDB Carparks
    print(Fore.MAGENTA + "\nPushing HDB carparks to broker...")
    hdb_carparks = create_hdb_carparks()
    create_entities_in_broker(hdb_carparks)



def import_TrafficAdvisories_entity():
    traffic_advisories_list = get_traffic_advisories()
    print(Fore.MAGENTA + "\nPushing TrafficAdvisories to broker...")
    create_entities_in_broker(traffic_advisories_list)


def import_WeatherForecast_entity():
    forecast_list = get_two_hour_weather()
    observed_list = get_weather_observed()
    print(Fore.MAGENTA + "\nPushing WeatherForecast to broker...", "\n")
    create_entities_in_broker(forecast_list)
    create_entities_in_broker(observed_list)


if __name__ == "__main__":
    try:
        import_WeatherForecast_entity()
        import_TrafficAdvisories_entity()
        import_Carpark_entity()
        print(Fore.MAGENTA + "\nCompleted importing entities.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nFailed to import entities.")