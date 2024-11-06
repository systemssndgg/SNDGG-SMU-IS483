from datetime import datetime
from ngsildclient import Client, Entity, SmartDataModels

ctx = "test"
exampleCarparkEntity = Entity("Carpark", "test", ctx=ctx)

# 'Bugis+': {'rates': {'weekday': {'time_based': [{'start_time': '08:00', 'end_time': '17:00', 'rate_per_hour': 1.07}, {'start_time': '17:00', 'end_time': '23:59', 'rate_per_hour': 2.5}], 'flat_entry_fee': None, 'first_hour_rate': 1.07, 'max_daily_fee': None}, 'saturday': {'time_based': [{'start_time': '00:00', 'end_time': '23:59', 'rate_per_hour': 2.5}], 'flat_entry_fee': None, 'first_hour_rate': 2.5, 'max_daily_fee': None}, 'sundayPublicHoliday': {'time_based': [{'start_time': '00:00', 'end_time': '23:59', 'rate_per_hour': 2.5}], 'flat_entry_fee': None, 'first_hour_rate': 2.5, 'max_daily_fee': None}}}

def find_price_per_hr(carpark, num_hrs, vehicle_type='Car'):
    '''
    To be implemented: Figure out price per hour based on input params

    INPUT PARAMETERS:
    [1] carpark: Entire NGSI-LD carpark entity
    [2] num_hrs: Number of hours user intends to park for
    [3] vehicle_type: Type of vehicle ('Car', 'Motorcycle', 'Heavy Vehicle')

    RETURNS:
    float value >= 0.0 IF price information is available
    -1.0 IF price information is not available
    '''

    # TO IMPLEMENT LATER: FIGURE OUT HOW TO CALCULATE PRICE PER HOUR
    today = datetime.today().weekday()
    current_time = datetime.now().time()
    
    # (1) Format the current time to the same format found in the entity - e.g. 15:00
    current_time = current_time.strftime("%H:%M")

    # (2) Format the current day to either 'weekday', 'saturday', or 'sundayPublicHoliday'
    if 0 <= today <= 4:
        day_type = "weekday"
    elif today == 5:
        day_type = "saturday"
    else:
        day_type = "sundayPublicHoliday"
    
    # (3) Find the entry_fee based on the current time and day
    entry_fee = carpark['pricing']['value']['rates'][day_type]['flatEntryFee']
    if entry_fee != '-' or entry_fee != None:
        entry_fee_start_time = entry_fee['startTime']
        entry_fee_end_time = entry_fee['endTime']
        if entry_fee_start_time <= current_time <= entry_fee_end_time:
            entry_fee_price = entry_fee['price']
        else:
            entry_fee_price = None
    
    # (4) Find out if there's a first hour rate present
    first_hour_rate = carpark['pricing']['value']['rates'][day_type]['firstHourRate']
    if first_hour_rate != '-' or first_hour_rate != None:
        first_hour_rate_start_time = first_hour_rate['startTime']
        first_hour_rate_end_time = first_hour_rate['endTime']
        if first_hour_rate_start_time <= current_time <= first_hour_rate_end_time:
            first_hour_rate_price = first_hour_rate['price']
        else:
            first_hour_rate_price = None
    
    # (5) Find out the usual rate per hour
    time_based = carpark['pricing']['value']['rates'][day_type]['timeBased']
    if time_based != '-' or time_based != None:
        for time_slot in time_based:
            if time_slot['startTime'] <= current_time <= time_slot['endTime']:
                rate_per_hour = time_slot['ratePerHour']
            else:
                rate_per_hour = None

    # (6) Find out if there's a max_daily_fee
    max_daily_fee = carpark['pricing']['value']['rates'][day_type]['maxDailyFee']

    # (7) Calculate the total price based on the number of hours
    if entry_fee_price != None:
        total_price = entry_fee_price
    else:
        total_price = 0.0

    if first_hour_rate_price != None:
        total_price += first_hour_rate_price
    else:
        total_price += 0.0

    if rate_per_hour != None:
        total_price += rate_per_hour * num_hrs
    else:
        total_price += 0.0
    
    if max_daily_fee != None:
        if total_price > max_daily_fee:
            total_price = max_daily_fee
    
    return total_price