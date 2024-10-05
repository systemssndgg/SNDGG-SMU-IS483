import mylibs.constants as constants
from landtransportsg import Traffic
from ngsildclient import Entity

API_KEY = constants.DATAMALL_API_KEY
ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port  # default, 80
temporal_port = constants.temporal_port  # default 1026
broker_tenant = constants.broker_tenant

def get_parking_data():  # Get parking data in NGSI-LD format
    count = 0
    entity_list = []

    # Import data from LTA
    LTA_client = Traffic(API_KEY)
    carpark_list = LTA_client.carpark_availability()

    print("Example Carpark: ", carpark_list[0])
    print("Number of carparks: ", len(carpark_list))

    for carpark in carpark_list:
        remove_spaced_name = carpark["Development"].replace(
            " ", ""
        )  # remove spaces in development name
        id = remove_spaced_name + str(
            carpark["CarParkID"]
        )  # carparkID would be developmentname plus ID?
        print("ID: ", id)
        entity = Entity("Carpark", id, ctx=ctx)  # type, id , ctx

        for key, value in carpark.items():
            if key == "CarParkID":
                entity.prop("CarParkID", value)
            elif key == "Area":
                entity.prop("Region", value)
            elif key == "Development":
                entity.prop("DevelopmentName", value)
            elif key == "Location":  # Geoproperty
                geocoordinates = value.split()  # lat, long
                if len(geocoordinates) > 1:
                    entity.gprop(
                        "location", (float(geocoordinates[0]), float(geocoordinates[1]))
                    )  # Pass in point
                    print("Lat ", geocoordinates[0], " Long ", geocoordinates[1])
            elif key == "AvailableLots":
                entity.prop("ParkingAvailability", value)
            elif key == "LotType":
                entity.prop("LotType", value)
            elif key == "Agency":
                entity.prop("ParkingSiteOwner", value)

        entity_list.append(entity)  # Add entity to list

        count += 1
        if count == 10:  # Limit number of carparks pulled for now
            break

    return entity_list