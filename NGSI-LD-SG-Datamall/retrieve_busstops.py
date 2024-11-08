import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime
import mylibs.constants  as constants

ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant


with Client(hostname=broker_url, port=broker_port, tenant=broker_tenant, port_temporal=temporal_port ) as client:
    
    bus_stop_entities = client.query(type="BusStop", ctx=ctx)
    
    print("Bus stops retrieved: ", len(bus_stop_entities))
    for bus_stop in bus_stop_entities:
        print(bus_stop.id)
        







