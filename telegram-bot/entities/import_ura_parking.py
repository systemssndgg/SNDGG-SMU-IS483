from mylibs.ura_parking import get_ura_token, get_ura_carparks, get_season_carpark
from mylibs.traffic_flow import get_trafficflow_url, get_trafficflow
from mylibs.traffic_advisories import get_traffic_advisories
from mylibs.ngsi_ld import create_entities_in_broker

token = get_ura_token()['Result']
print("Token ", token)

# Code to run ==================================================
carpark_list = get_ura_carparks(token)
# print("carpark_list" , carpark_list)
trafficflow_list = get_trafficflow()
trafficadvisories_list = get_traffic_advisories()

print("\nPushing to broker...")
create_entities_in_broker(carpark_list)

# print("\nPushing to broker...")
# create_entities_in_broker(trafficflow_list)

print("\nPushing to broker...")
create_entities_in_broker(trafficadvisories_list)
