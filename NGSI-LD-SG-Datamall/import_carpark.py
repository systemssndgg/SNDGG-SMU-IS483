from mylibs.ura_parking import get_ura_token, get_carpark, get_season_carpark
from mylibs.trafficflow import get_trafficflow_url, get_trafficflow
from mylibs.trafficadvisories import get_traffic_advisories
import mylibs.ngsi_ld_parking as ngsi_parking

token = get_ura_token()['Result']

carpark_list = get_carpark(token)
trafficflow_list = get_trafficflow()
traffic_advisories = get_traffic_advisories()

ngsi_parking.create_entities_in_broker(carpark_list)
ngsi_parking.create_entities_in_broker(trafficflow_list)
ngsi_parking.create_entities_in_broker(traffic_advisories)

retrieved_carparks = ngsi_parking.retrieve_ngsi_type("Carpark")
retrieved_trafficflow = ngsi_parking.retrieve_ngsi_type("TrafficFlow")
retrieved_trafficadvisories = ngsi_parking.retrieve_ngsi_type("TrafficAdvisories")


print ("Num entities retrieved" , len(retrieved_carparks))
# for i in range(len(retrieved_carparks)):
#     retrieved_carparks[i].pprint()
#     print("\n\n\n\n\n")

print ("Num entities retrieved" , len(retrieved_trafficflow))
# for i in range(len(retrieved_trafficflow)):
#     retrieved_trafficflow[i].pprint()
#     print("\n\n\n\n\n")

print ("Num entities retrieved" , len(retrieved_trafficadvisories))
# for i in range(len(retrieved_trafficadvisories)):
#     retrieved_trafficadvisories[i].pprint()
#     print("\n\n\n\n\n")