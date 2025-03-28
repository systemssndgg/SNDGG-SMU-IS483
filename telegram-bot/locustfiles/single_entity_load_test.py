from locust import HttpUser, task, between
import os
import random

class CarparkUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("BROKER_URL", "http://localhost:9090")

    headers = {
        "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.8.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"',
        "Accept": "application/ld+json",
        "NGSILD-Tenant": "openiot"
    }

    # @task(1)
    # def query_available_lots(self):
    #     """Fetch Carparks where parkingAvailability < 100."""
    #     response = self.client.get(
    #         "/ngsi-ld/v1/entities?type=Carpark&q=parkingAvailability<100",
    #         headers=self.headers,
    #         name="Query Available Lots < 100"  # This name appears in Locust's UI
    #     )
    #     if response.status_code != 200:
    #         print(f"Failed to fetch available carparks: {response.status_code}")

    def random_carpark_location(self):
        """Generate random carpark locations for geoquery testing."""
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
        """Perform Geoquery for Carparks within 800m."""
        coords = self.random_carpark_location()
        params = {
            "type": "Carpark",
            "georel": "near;maxDistance==800",
            "coordinates": str(coords),
            "geometry": "Point",
            "options": "keyValues",
        }
        response = self.client.get(
            "/ngsi-ld/v1/entities",
            params=params,
            headers=self.headers,
            name="Geoquery near Coordinates"  # This name appears in Locust's UI
        )
        if response.status_code != 200:
            print(f"Geoquery failed: {response.status_code}")