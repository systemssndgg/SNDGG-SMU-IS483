from mylibs.one_motoring_carparks import create_one_motoring_carparks
import mylibs.ngsi_ld as ngsi_ld

# (1) Get the entities
entities = create_one_motoring_carparks()
print(entities)

# (2) Convert the carpark availability data to NGSI-LD format
ngsi_ld.create_entities_in_broker(entities)
