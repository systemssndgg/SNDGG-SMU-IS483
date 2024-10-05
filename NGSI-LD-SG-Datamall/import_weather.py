from mylibs.weather_forecast import get_two_hour_weather
from mylibs.weather_observed import get_weather_observed
from mylibs.ngsi_ld import create_entities_in_broker

# Code to run ==================================================
forecast_list = get_two_hour_weather()
observed_list = get_weather_observed()

print("\nPushing to broker...")
create_entities_in_broker(forecast_list)

print("\nPushing to broker...")
create_entities_in_broker(observed_list)