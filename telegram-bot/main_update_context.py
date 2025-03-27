import sys
print(sys.version)
#import threading
from flask import Flask
import os
import constants
import time

#import fns
from import_entities import import_WeatherForecast_entity,import_TrafficAdvisories_entity, import_Carpark_entity #Added to import fns


#Set paths
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def main() -> None:
    loop_count = 0
    while (True):
        if loop_count % 3 ==0: #update every 3 mins
            import_Carpark_entity()
        if loop_count % 3 ==0: #update every 3 mins
            import_TrafficAdvisories_entity()
        if loop_count % 60 ==0: #update weather every hour
            import_WeatherForecast_entity()
        
        time.sleep(60)
        loop_count = loop_count + 1

        if loop_count > 120:
            loop_count = 1
        
if __name__ == '__main__':
    main()