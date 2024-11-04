from mylibs.hdb_carparks import create_hdb_carparks
import mylibs.ngsi_ld as ngsi_ld

# (1) Fetch carpark availability from the data.gov.sg API
entities = create_hdb_carparks()

# (2) Convert the carpark availability data to NGSI-LD format
ngsi_ld.create_entities_in_broker(entities)



