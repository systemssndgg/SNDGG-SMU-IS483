# Context: https://raw.githubusercontent.com/dexter-lau-pmo/NGSI-LD-SG-Datamall/main/context/custom_context.json?token=GHSAT0AAAAAACVEQXNKVWJNBF533JCYV6GQZU6FTSA

from landtransportsg import PublicTransport
import mylibs.constants as constants
import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime


API_KEY = constants.DATAMALL_API_KEY


ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant


lta_client = PublicTransport(API_KEY)
taxi_list = lta_client.taxi_availability()
print("Number of Taxis is: ", len(taxi_list))


print("Taxi list")
print(taxi_list)

entity = Entity("TaxiFleet", "AvaliableTaxiFleet", ctx=ctx)  # Entity type, id

# tprop() sets a TemporalProperty
# entity.tprop("dateObserved", datetime.now())

# gprop() sets a GeoProperty : Point, Polygon, ...
# entity.gprop("location", (bus_stop['Latitude'], bus_stop['Longitude']))
# no Gprop

entity.prop("FleetType", "Taxi")
entity.prop("FleetLocationList", taxi_list)
entity.prop("FleetSize", len(taxi_list))

print("NGSI entity")
entity.pprint()

print("\n\n\n\n\n\n_______________________________________\n\n\n")


print("Attempt to upload to broker")


# with Client(hostname=broker_url, port=broker_port, tenant=broker_tenant, port_temporal=temporal_port ) as client:
with Client(hostname=broker_url, port=broker_port, tenant=broker_tenant) as client:

    print("\nupload to broker")
    try:
        ret = client.upsert(entity)
        print("Entity created:", ret)
    except (RequestException, HTTPError) as e:
        print(f"Failed to create entity: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

    print("\nPull from broker")
    # Try retrieving the entity
    try:
        ret_entity = client.get("urn:ngsi-ld:TaxiFleet:AvaliableTaxiFleet")
        print("Entity retrieved:", ret_entity)
    except (RequestException, HTTPError) as e:
        print(f"Failed to retrieve entity: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")
