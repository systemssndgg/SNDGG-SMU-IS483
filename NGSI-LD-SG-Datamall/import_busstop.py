import sys 
print(sys.version)

#LTA

import mylibs.constants  as constants
from landtransportsg import PublicTransport

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime


API_KEY = constants.LTA_API_KEY

lta_client = PublicTransport(API_KEY)
bus_stop_list = lta_client.bus_stops()
print("Number of Bus stops is: " , len(bus_stop_list))
print("Example bus stop: " , bus_stop_list[0])


#NGSI-LD



# No context provided => defaults to NGSI-LD Core Context
#ctx = "http://34.126.76.13/context.jsonld"
ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant


#Context: https://schema.org/BusStop
#API: https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf
#JSOn-LD visualiser: https://json-ld.org/playground/

#import data from LTA

print("\n\n\nGet bus stops from LTA\n")
count = 0
for bus_stop in bus_stop_list:
    print("BusStopCode is: " , bus_stop['BusStopCode'])
    id = "BusStop" + bus_stop['BusStopCode'] #Create NGSI-LD ID from the BusStopCode. All other params can be directly loaded
    bus_stop['id'] = id
    print("Calculated NGSI-LD ID should be: " , bus_stop['id'])

    #Create Geoproperty dictionary
    d = {}
    d['location'] = {}
    d['location']['type'] = "GeoProperty"
    d['location']['value'] = {}
    d['location']['value']['type'] = "Point"
    d['location']['value']['coordinates'] = [ bus_stop['Longitude'] , bus_stop['Latitude'] ]
    bus_stop['location'] = d['location'] # Add Geoproperty to dict
    
    
    print("Calculated NGSI-LD Geolocation should be: " , bus_stop['location'])

    count+=1
    if count == 5:
        break #Only run through first bus stop, remove break for all bus stops
print(bus_stop_list[0])






print("\n\n\n\n\n\n_______________________________________\n\n\n")

print("Format data in NGSI-LD")

#Create entity locally only



entity_list = []
count = 0

for bus_stop in bus_stop_list:
    print(bus_stop.keys())
    print(bus_stop['id'])
    entity = Entity("BusStop", bus_stop['id'], ctx=ctx) #Entity type, id
    
    # Once we've created our entity by calling the Entity() constructor 
    # We can add properties thanks to primitives
    
    # tprop() sets a TemporalProperty
    #entity.tprop("dateObserved", datetime(2018, 8, 7, 12))

    # gprop() sets a GeoProperty : Point, Polygon, ...
    entity.gprop("location", (bus_stop['Latitude'], bus_stop['Longitude']))

    for key, value in bus_stop.items():
        if key!='location' and key!='id':
            entity.prop(key, value)
    
    entity_list.append(entity) #Add to list
    # rel() sets a Relationship Property
    #entity.rel("refPointOfInterest", "PointOfInterest:RZ:MainSquare")
    
    count+=1
    if count == 5:
        break #Only run through first bus stop, remove break for all bus stops
    
entity.pprint()

print("\n\n\n\n\n\n_______________________________________\n\n\n")




print("Attempt to upload to broker")

#Put entity in broker

def get_json_or_text(response):
    try:
        return response.json()
    except ValueError:
        return response.text


with Client(hostname=broker_url, port=broker_port, tenant=broker_tenant, port_temporal=temporal_port ) as client:

    # Try creating the entity
    #print(client.list_types())
    upload_success_count = 0
    for ngsi_entity in entity_list:
        print("\nupload to broker")
        try:
            ret = client.upsert(ngsi_entity)
            print("Entity created:", ret)
            upload_success_count+=1
        except (RequestException, HTTPError) as e:
            print(f"Failed to create entity: {e}")
    print("\nEntities Successfuly Created: ",upload_success_count)
        
       
    # Try retrieving the entity
    pull_success_count = 0
    for ngsi_entity in entity_list:
        print("\nPull from broker")
        try:
            ret_entity = client.get(ngsi_entity) #Can use urn ID string also
            print("Entity retrieved:", ret_entity)
            pull_success_count+=1
        except (RequestException, HTTPError) as e:
            print(f"Failed to retrieve entity: {e}")
    print("\nEntities Successfuly Created: ",upload_success_count)
    print("\nEntities Successfuly Pulled: ",pull_success_count)
    

