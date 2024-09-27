from mylibs.weather_observed import get_weather_observed_data, create_entities_in_broker

# Code to run ==================================================
list_entities = get_weather_observed_data()

print("Entities created: ", len(list_entities))
print("\nPushing to broker...")

create_entities_in_broker(list_entities)