import mylibs.constants as constants
import requests
import json
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import mylibs.SVY21 as SVY21

TRAFFICFLOW_URL = "https://datamall2.mytransport.sg/ltaodataservice/TrafficFlow"
ACCESS_KEY = constants.DATAMALL_ACCESS_KEY

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant

# Initialise the SVY21 class
svy21_converter = SVY21.SVY21()


def get_trafficflow_url(ACCESS_KEY):
    response = requests.get(TRAFFICFLOW_URL, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "AccountKey": ACCESS_KEY
    })

    if response.status_code == 200:
        trafficflow_url = json.loads(response.content.decode("utf-8"))["value"][0]["Link"]
        return trafficflow_url
    

def get_trafficflow():
    # response = requests.get(get_trafficflow_url(ACCESS_KEY), headers={
    # "Content-Type": "application/json",
    # "User-Agent": "Mozilla/5.0"
    # })

    # if response.status_code == 200:
    #     trafficflow_dataset = json.loads(response.content.decode("utf-8"))["Value"]
    #     print(trafficflow_dataset)

    # To remove and uncomment from line 34 to 40 & 111 to 112, substitute for exceeding Datamall Traffic Flow API call
    # Change URL to local file path
    with open(r"C:\Users\jiale\OneDrive\Desktop\FYP\SNDGG-SMU-IS483\NGSI-LD-SG-Datamall\mylibs\sample_trafficflow.json") as f:
        trafficflow_dataset = json.load(f)['Value']
        
        # =============== Actual Logic ================= 
        unique_traffic_id = []
        entity_list = []
        count = 0
        
        for traffic_flow in trafficflow_dataset:
            # Dictionaries
            location_dictionary = {
                "start": [],
                "end": []
            }

            date_dictionary = {}

            if traffic_flow["LinkID"] not in unique_traffic_id:
                entity = Entity("TrafficFlow", traffic_flow["LinkID"], ctx=ctx)
                unique_traffic_id.append(traffic_flow["LinkID"])

                for key, value in traffic_flow.items():
                    if key == "RoadName":
                        entity.prop("RoadName", value)
                    elif key == "RoadCat":
                            entity.prop("RoadCat", value)
                    
                    # Location
                    elif key == "StartLat" :
                        location_dictionary["start"].append(float(value))
                    elif key == "StartLon" and len(location_dictionary["start"]) < 2:
                        location_dictionary["start"].append(float(value))
                    elif key == "EndLat":
                        location_dictionary["end"].append(float(value))
                    elif key == "EndLon" and len(location_dictionary["end"]) < 2:
                        location_dictionary["end"].append(float(value))
                
                # Prop Dictionaries
                location_dictionary["start"] = tuple(location_dictionary["start"])
                location_dictionary["end"] = tuple(location_dictionary["end"])
                entity.prop("Location", location_dictionary)
                entity.prop("Date", date_dictionary)
                entity_list.append(entity)

                count += 1
                if count == 10:
                    break
        # print(entity_list)

        # Date
        for traffic_flow in trafficflow_dataset:
            for entity in entity_list:
                entity_id = entity["id"].split(":")[-1]
                if entity_id == traffic_flow["LinkID"]:
                    date_key = traffic_flow["Date"]
                    hour_key = traffic_flow["HourOfDate"]
                    volume_value = traffic_flow["Volume"]

                    if date_key not in entity["Date"]:
                        entity["Date"]["value"][date_key] = {}

                    entity["Date"]["value"][date_key][hour_key] = volume_value

        print("Total number of Traffic Flow: ", len(trafficflow_dataset))
        print("Total entities created: ", len(entity_list))

        return entity_list
    # else:    
        # return None