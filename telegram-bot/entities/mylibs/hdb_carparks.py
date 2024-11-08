import mylibs.constants as constants 
from landtransportsg import Traffic
import requests
from openai import OpenAI
import openpyxl
import os
import re

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import pandas as pd

API_KEY = constants.LTA_API_KEY
ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant


# (1) Fetch carpark availability from the data.gov.sg API
def fetch_carpark_availabilities():
    '''
    Inputs: None
    
    \nOutput: entity_dict (dict) A dictionary of carpark entities with the CarParkID as the key

    \nDescription: Fetches the 40 carpark availabilities under LTA and returns a dictionary of carpark entities with the CarParkID as the key.
    '''
    url = "https://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2"
    commerical_ids = []

    # make a request to the url and retrieve the response
    response = requests.get(url, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "AccountKey": "iGUugKJzSkGPCPBbLAhyhA=="
    })
    
    # check if the response is successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch carpark availabilities: {response.status_code}")
    else:
        print("Successfully fetched carpark availabilities")
        response = response.json()
    
        # the response returns a JSON object with 'value' as a key, this in turns points to the list of carpark dictionaries.
        # iterate through the list of dictionaries
        entity_dict = {}
        for i in range(0, len(response['value'])):
            agency = response['value'][i]['Agency']
            if agency == 'HDB':
                entity = response['value'][i]
                entity_dict[entity['CarParkID']] = entity
        
        return entity_dict
    
# print(fetch_carpark_availabilities())

# (2) Convert the carpark availability data to NGSI-LD format
def create_hdb_carparks():
    '''
    Inputs: None
    
    \nOutput: entity_list (list) A list of carpark entities in NGSI-LD format

    \nDescription: Converts the carpark availability data to NGSI-LD format and returns a list of carpark entities.
    '''
    entity_dict = fetch_carpark_availabilities()
    entity_list = []
    for key, value in entity_dict.items():
        entity = Entity("Carpark", value['CarParkID'], ctx=ctx)
        for key, value in value.items():
            if key == "Development":
                entity.prop("carparkName", value)
            elif key == "Location":
                coordinates = value.split(" ")
                entity.gprop("location", (float(coordinates[0]), float(coordinates[1])))
            elif key == "AvailableLots":
                entity.prop("parkingAvailability", value)
            
        # Fill in the empty properties
        entity.prop("sheltered", True)
        entity_list.append(entity)  # Add entity to list
    return entity_list

# print(create_hdb_carparks())