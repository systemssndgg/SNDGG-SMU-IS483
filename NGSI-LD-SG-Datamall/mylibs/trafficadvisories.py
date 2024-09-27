import mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import mylibs.SVY21 as SVY21

TRAFFICADVISORIES = "https://datamall2.mytransport.sg/ltaodataservice/VMS"
ACCESS_KEY = constants.DATAMALL_ACCESS_KEY

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant

# Initialise the SVY21 class
svy21_converter = SVY21.SVY21()

def get_traffic_advisories():
    response = requests.get(TRAFFICADVISORIES, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "AccountKey": ACCESS_KEY
    })

    if response.status_code == 200:
        traffic_advisories = json.loads(response.content.decode("utf-8"))["value"]
        entity_list = []

        for advisories in traffic_advisories:
            entity = Entity("TrafficAdvisories", advisories["EquipmentID"], ctx=ctx)
            location = []
            for key, value in advisories.items():
                if key == "Message":
                    entity.prop("Message", value.strip())
                elif key == "Latitude":
                    location.append(float(value))
                elif key == "Longitude":
                    location.append(float(value))
            entity.gprop("Location", tuple(location))
            
            entity_list.append(entity)
        print("Total number of Traffic Advisories: ", len(traffic_advisories))
        print("Total entities created: ", len(entity_list))
    
        return entity_list
    else:
        return None
