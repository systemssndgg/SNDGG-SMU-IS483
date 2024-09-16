from libs.ura_parking import get_ura_token, get_carpark, get_season_carpark
import libs.ngsi_ld_parking as ngsi_parking

token = get_ura_token()['Result']

carpark_list = get_carpark(token)

ngsi_parking.create_entities_in_broker(carpark_list)

retrieved_carparks = ngsi_parking.retrieve_ngsi_type("Carpark")

print(retrieved_carparks)
print ("Num entities retrieved" , len(retrieved_carparks))
for i in range(len(retrieved_carparks)):
    retrieved_carparks[i].pprint()
    print("\n\n\n\n\n")