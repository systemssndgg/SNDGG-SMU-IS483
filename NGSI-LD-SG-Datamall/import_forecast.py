from mylibs.weather_forecast import get_two_hour_weather
import mylibs.ngsi_ld_parking as ngsi_parking

# token = get_ura_token()['Result']

weather_list = get_two_hour_weather()

ngsi_parking.create_entities_in_broker(weather_list)

retrieved_forecast = ngsi_parking.retrieve_ngsi_type("WeatherForecast")

print(retrieved_forecast)
print("Num entities retrieved", len(retrieved_forecast))
for i in range(len(retrieved_forecast)):
    retrieved_forecast[i].pprint()
    print("\n\n\n\n\n")
