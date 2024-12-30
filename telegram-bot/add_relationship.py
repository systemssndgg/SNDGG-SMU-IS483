import requests
import json

# Orion-LD Context Broker URL
ORION_LD_URL = "http://localhost:9090/ngsi-ld/v1/entities"

# Define Carpark Entity
def create_carpark_entity():
    carpark_entity = {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld",
        "id": "urn:ngsi-ld:Carpark:66",
        "type": "Carpark",
        "carparkName": {
            "type": "Property",
            "value": "Funan Mall"
        },
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [
                    103.8502,
                    1.2911
                ]
            }
        },
        "sheltered": {
            "type": "Property",
            "value": True
        },
        "parkingAvailability": {
            "type": "Relationship",
            "object": "urn:ngsi-ld:ParkingAvailability:66",
            "objectType": "ParkingAvailability"
        },
        "pricing": {
            "type": "Property",
            "value": {
                "rates": {
                    "weekday": {
                        "timeBased": [
                            {
                                "startTime": "00:00",
                                "endTime": "17:59",
                                "ratePerHour": 2.14
                            }
                        ],
                        "flatEntryFee": {
                            "startTime": "18:00",
                            "endTime": "21:59",
                            "fee": 2.14
                        },
                        "firstHourRate": 2.14
                    },
                    "saturday": {
                        "timeBased": [
                            {
                                "startTime": "00:00",
                                "endTime": "23:59",
                                "ratePerHour": 2.14
                            }
                        ],
                        "firstHourRate": 2.14
                    },
                    "sundayPublicHoliday": {
                        "timeBased": [
                            {
                                "startTime": "00:00",
                                "endTime": "23:59",
                                "ratePerHour": 2.14
                            }
                        ],
                        "firstHourRate": 2.14
                    }
                },
                "weekdayStr": "12am-5.59pm: $2.14 for 1st hr; $0.54 for sub. 15mins; 6pm-9.59pm: $2.14 per entry",
                "saturdayStr": "Same as wkdays",
                "sundayPHStr": "Same as wkdays"
            }
        }
    }
    response = requests.post(ORION_LD_URL, json=carpark_entity, headers={"Content-Type": "application/ld+json", "NGSILD-Tenant": "openiot"})
    print(f"Carpark Entity Creation Status: {response.status_code}, Response: {response.text}")

# Define Parking Availability Entity
def create_parking_availability_entity():
    parking_availability_entity = {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld",
        "id": "urn:ngsi-ld:ParkingAvailability:66",
        "type": "ParkingAvailability",
        "availableLots": {
            "type": "Property",
            "value": 131
        }
    }
    response = requests.post(ORION_LD_URL, json=parking_availability_entity, headers={"Content-Type": "application/ld+json", "NGSILD-Tenant": "openiot"})
    print(f"Parking Availability Entity Creation Status: {response.status_code}, Response: {response.text}")

# Main Execution
if __name__ == "__main__":
    create_carpark_entity()
    create_parking_availability_entity()
