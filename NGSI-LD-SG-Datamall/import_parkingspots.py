import mylibs.constants as constants
from landtransportsg import Traffic
import requests
import urllib.parse

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import mylibs.ngsi_ld_parking as ngsi_parking
from geopy.distance import geodesic


API_KEY = constants.LTA_API_KEY
ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant


# Convert to NGSI-LD
"""
Carpark
- id - Core context
- DevelopmentName (From LTA)
- Region (From LTA)
- Location - Gprop
- Price (Pending Terrence)
- ParkingAvalibility - From SDM 
- ParkingChargeType - From SDM (Pending Terrence)
- ParkingMaxAvalibility - From SDM (Info not avaliable)
- DataSource - From SDM
- ParkingSiteOwner (relationship) - From SDM


Example LTA data return:
            "CarParkID": "1",
            "Area": "Marina",
            "Development": "Suntec City",
            "Location": "1.29375 103.85718",
            "AvailableLots": 442,
            "LotType": "C",
            "Agency": "LTA"
"""


entity_list = ngsi_parking.get_parking_data()
print("Num entities to upload", len(entity_list))
entity_list[1].pprint()
ngsi_parking.create_entities_in_broker(entity_list)


print("\n\n\n\n\n")
retrieved_carparks = ngsi_parking.retrieve_carparks()
print("Num entities retrieved", len(retrieved_carparks))
retrieved_carparks[0].pprint()

# Delete carparks
"""
print("\n\n\n\n\n")
ngsi_parking.delete_all_type("Carpark")
"""


# Geoquery example
"""
gq = "geometry=Point&georel=near%3BmaxDistance==800&coordinates=%5B103.83359,1.3071%5D"
#retrieved_carparks = geoquery_ngsi_long(input_type = "Carpark" , geoquery = gq)

geoquery_ngsi_point(input_type = "Carpark", maxDistance=10000 , lat = 103.83349, long= 1.3072)

nearest_carparks = ngsi_parking.geoquery_ngsi_point(input_type = "Carpark", maxDistance=1000 , long = 103.83349, lat= 1.3072)

print(nearest_carparks)


closest_three_carparks = []
for carpark in nearest_carparks:
    carpark_dict = carpark.to_dict()
    
    print(carpark_dict["location"])
    print(carpark_dict["location"]["value"]["coordinates"])
    lat = carpark_dict["location"]["value"]["coordinates"][1]
    long = carpark_dict["location"]["value"]["coordinates"][0]
    print(carpark_dict["location"]["value"]["coordinates"][0])
    print(carpark_dict["location"]["value"]["coordinates"][1])
    distance = geodesic((1.3072, 103.83349), (lat, long)).km
    carpark["distance"] = distance
    print(
        "\nArea: " + str(carpark_dict["DevelopmentName"]["value"]) + " \nLots: " + str(carpark_dict["ParkingAvalibility"]["value"]) + "\n Distance from destination is:  " + str(distance) + "km"
    )
    print(carpark_dict["LotType"]["value"])
    
    #Find closest 3 carparks
    if len(closest_three_carparks)<3 and carpark_dict["LotType"]["value"] == "C":
        closest_three_carparks.append(carpark)
    else:
        for closestcarpark in closest_three_carparks :
            if closestcarpark["distance"]>carpark["distance"]: #Carpark is closer than one on list
                closestcarpark = carpark
                break
                
count = 1
closest_carparks = "The closest 3 carparks to your destination are:  \n\n" 
for carpark in closest_three_carparks:
    closest_carparks = closest_carparks + "\n" + str(count) + ": " + "\nArea: " + str(carpark_dict["DevelopmentName"]["value"]) + " \nLots: " + str(carpark_dict["ParkingAvalibility"]["value"]) + "\n Distance from destination is:  " + str(distance) + "\n"
    count += 1

#Send msg to user
print(
    closest_carparks
)
"""
