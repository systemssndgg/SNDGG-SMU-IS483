import entities.mylibs.constants  as constants
import entities.mylibs.ngsi_ld as ngsi_ld

API_KEY = constants.DATAMALL_API_KEY
ctx = constants.ctx
broker_url = constants.broker_url
broker_port = constants.broker_port # default, 80
temporal_port = constants.temporal_port #default 1026
broker_tenant = constants.broker_tenant

ngsi_ld.delete_all_type("Carpark")
ngsi_ld.delete_all_type("TrafficFlow")
ngsi_ld.delete_all_type("TrafficAdvisories")
ngsi_ld.delete_all_type("WeatherForecast")
ngsi_ld.delete_all_type("WeatherObserved")
ngsi_ld.delete_all_type("BusStop")
ngsi_ld.delete_all_type("TaxiFleet")