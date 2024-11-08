import mylibs.constants  as constants
import mylibs.ngsi_ld_parking as ngsi_parking
import mylibs.onemap as onemap

from landtransportsg import Traffic
import requests
import urllib.parse

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime

from geopy.distance import geodesic

