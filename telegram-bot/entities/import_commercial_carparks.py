from mylibs.commercial_carparks import create_commercial_carparks
import mylibs.ngsi_ld as ngsi_ld

entities = create_commercial_carparks()
print("\nPushing to broker...")
ngsi_ld.create_entities_in_broker(entities)