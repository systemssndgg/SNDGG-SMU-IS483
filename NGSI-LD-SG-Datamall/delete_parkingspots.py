import mylibs.constants  as constants
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
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant

ngsi_parking.delete_all_type("Carpark")