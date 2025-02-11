from locust import HttpUser, task, between, SequentialTaskSet
import os
import random
import json




class CarparkQueryTest(SequentialTaskSet):
    wait_time = between(1, 3)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/ld+json"
    }

    def on_start(self):
        """Setup before tasks run."""
        self.carpark_availability_ids = []

    @task(1)
    def query_available_lots(self):
        """Step 1: Fetch CarparkAvailability where availableLots < 100."""
        response = self.client.get(
            "/ngsi-ld/v1/entities?type=CarparkAvailability&q=availableLots<100",
            headers=self.headers,
            name="Query Available Lots < 100"  # Name shown in Locust report
        )

        if response.status_code == 200:
            availability_data = response.json()
            self.carpark_availability_ids = [entity["id"] for entity in availability_data]
        else:
            self.carpark_availability_ids = []

    @task(1)
    def query_matching_carparks(self):
        """Step 2: Fetch Carpark entities matching the found CarparkAvailability IDs."""
        if not self.carpark_availability_ids:
            return  # Skip if no availability data found

        for availability_id in self.carpark_availability_ids:
            response = self.client.get(
                f"/ngsi-ld/v1/entities?type=Carpark&q=parkingAvailability=={availability_id}",
                headers=self.headers,
                name="Fetch Matching Carparks"  # Name shown in Locust report
            )

            # Only log failed requests to reduce clutter
            if response.status_code != 200:
                print(f"Failed to fetch Carpark for {availability_id}: {response.status_code}")


class CarparkUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("BROKER_URL", "http://localhost:9090")
    # tasks = [CarparkQueryTest]
    headers = {
        "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.8.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"',
        "Accept": "application/ld+json",
        "NGSILD-Tenant": "openiot"
    }


    def random_carpark_location(self):
        carpark_locations = [
            [103.851959, 1.290270],  # Marina Bay
            [103.819836, 1.352083],  # Central Area
            [103.902042, 1.352476],  # Tampines
            [103.835243, 1.300804],  # Orchard
            [103.695054, 1.344439],  # Jurong West
        ]

        return random.choice(carpark_locations)



    @task(1)
    def geo_query_carparks(self):
        coords = self.random_carpark_location()
        params = {
            "type": "Carpark",
            "georel": "near;maxDistance==800",
            "coordinates": str(coords),
            "geometry": "Point",
            "options": "keyValues",
             "join": "inline",
            "joinLevel": "3",
        }
        response = self.client.get(
            "/ngsi-ld/v1/entities",
            params=params,
            headers=self.headers,
            name="Geoquery near Coordinates",
        )

                # Parse the response as JSON
        try:
            response_json = response.json()
            if response_json:
                first_item = response_json[0]  # Get the first item in the response
                print(first_item, "FIRST ITEM IN RESPONSE")
            else:
                print("Response is empty")
        except ValueError:
            print("Response is not in JSON format")

