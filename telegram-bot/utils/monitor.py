from geopy.distance import geodesic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import asyncio
import logging
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

from utils.helper_functions import find_next_best_carpark, find_closest_carpark, is_word_present, end
from import_entities import import_Carpark_entity, import_TrafficAdvisories_entity, import_WeatherForecast_entity
from utils.context_broker import retrieve_entity_entry, retrieve_ngsi_type

async def monitor_carpark_availability(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_carpark):
    """Monitor the user's proximity to the selected carpark and alert if availability is low."""
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    approaching_message_sent = False

    destination_lat = context.user_data.get('destination_lat')
    destination_long = context.user_data.get('destination_long')

    sent_new = False
    # Begin monitoring the user's proximity
    while True:
        selected_carpark_updated = retrieve_entity_entry(context.user_data['selected_carpark_id'])

        # Continuously get updated live location
        live_location = context.user_data.get('live_location')

        # Debugging: print current lat/lng for testing
        print(Fore.GREEN + f"Monitoring live location: Latitude {live_location[0]}, Longitude {live_location[1]}")

        # Check if live location is still available
        if not live_location:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Error: Couldn't retrieve your live location.")
            break
        
        carpark_lat = context.user_data.get('selected_carpark_lat')
        carpark_long = context.user_data.get('selected_carpark_long')
        distance_to_carpark = geodesic(live_location, (carpark_lat, carpark_long)).km
        distance_to_destination = geodesic(live_location, (destination_lat, destination_long)).km

        # Debugging: print distance calculation
        print(Fore.RED + f"Distance from carpark: {distance_to_carpark:.2f} km")
        print(Fore.RED + f"Distance from destination: {distance_to_destination:.2f} km")

        # Check if the user has reached the destination
        if distance_to_carpark <= 0.1:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🚗 You have reached the carpark! 🏁 Ending the session now. Safe travels!",
                parse_mode='Markdown'
            )
            await end(update, context)
            break

        # Trigger warning if within 2km and less than 10 parking spots
        carpark_name = context.user_data.get('selected_carpark_name')
        available_lots = selected_carpark_updated['ParkingAvailability']['value']
        
        if distance_to_carpark <= 2.0 and not approaching_message_sent:
            if available_lots < 10:
                next_best_carpark = find_next_best_carpark(context.user_data['closest_carparks'], selected_carpark)

                if next_best_carpark:
                    next_carpark_name = next_best_carpark['CarparkName']['value'].title()
                    next_carpark_lat = next_best_carpark['location']['value']['coordinates'][1]
                    next_carpark_long = next_best_carpark['location']['value']['coordinates'][0]

                    google_maps_link = (
                        f"https://www.google.com/maps/dir/?api=1&origin={live_location[0]},{live_location[1]}"
                        f"&waypoints={next_carpark_lat},{next_carpark_long}"
                        f"&destination={context.user_data.get('destination_lat')},{context.user_data.get('destination_long')}&travelmode=driving"
                    )

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🚗 You are approaching your destination, but ⚠️ warning! The carpark '{carpark_name}' "
                            f"has less than 10 available lots left. We suggest using the next closest carpark '{next_carpark_name}' instead.\n\n"
                            f"[Click here to view the route]({google_maps_link})"
                        ),
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                else:
                    await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚗 You are approaching your destination, but ⚠️ warning! The carpark '{carpark_name}' has less than 10 available lots left. Drive carefully!",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚗 You are approaching your destination, and the carpark '{carpark_name}' currently has {available_lots} available lots. Drive carefully!",
                    parse_mode='Markdown'
                )

            approaching_message_sent = True
        
        # Sleep for 5 seconds before checking again    
        await asyncio.sleep(10)
        if sent_new == True:
            break


async def monitor_traffic_advisories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor traffic advisories along the route."""
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    # traffic_advisories = [
    # {
    #     "id": "urn:ngsi-ld:TrafficAdvisories:EVMS_RS10",
    #     "type": "TrafficAdvisories",
    #     "Message": {
    #         "type": "Property",
    #         "value": "DRIVE SAFELY,SPEED CAMERAS,IN TUNNEL"
    #     },
    #     "Location": {
    #         "type": "GeoProperty",
    #         "value": {
    #             "type": "Point",
    #             "coordinates": [
    #                 103.892766,
    #                 1.334989
    #             ]
    #         }
    #     }
    # },
    # {
    #     "id": "urn:ngsi-ld:TrafficAdvisories:VMS_0008",
    #     "type": "TrafficAdvisories",
    #     "Message": {
    #         "type": "Property",
    #         "value": "ACCIDENT IN LANE,"
    #     },
    #     "Location": {
    #         "type": "GeoProperty",
    #         "value": {
    #             "type": "Point",
    #             "coordinates": [
    #                 103.874857,
    #                 1.314717
    #             ]
    #         }
    #     }
    # }
    # ]
    
    traffic_advisories = retrieve_ngsi_type(
        input_type="TrafficAdvisories")
    # print("traffic advisories:", traffic_advisories)
    keywords = ["ACCIDENT", "CLOSURE", "CONSTRUCTION", "JAM"]
    sent_advisories = context.user_data.setdefault('sent_advisories', set())

    while True:    
        live_location = context.user_data.get('live_location')

        for advisory in traffic_advisories:  
            advisory_id = advisory['id']
            if advisory_id not in sent_advisories:
                advisory_message = advisory['Message']['value']
                advisory_coordinates = advisory['Location']['value']['coordinates']
                advisory_lat = advisory_coordinates[1]
                advisory_long = advisory_coordinates[0]
                distance_to_advisory = geodesic(live_location, (advisory_lat, advisory_long)).km

                print(Fore.RED + f"Distance to advisory: {distance_to_advisory:.2f} km")        
                
                for word in keywords:
                    if is_word_present(advisory_message, word):
                        if distance_to_advisory <= 2.0:
                            advisory_message = advisory['Message']['value']
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"🚧 Traffic advisory: {advisory_message}",
                                parse_mode='Markdown'
                            )
                            sent_advisories.add(advisory_id)
                        break

        await asyncio.sleep(5)


async def monitor_live_location_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continuously check for updates in the live location."""
    
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    
    previous_location = context.user_data.get('live_location')
    
    while True:
        current_location = context.user_data.get('live_location')
        
        if current_location != previous_location:
            previous_location = current_location
            print(Fore.GREEN + f"Live location updated: Latitude {current_location[0]}, Longitude {current_location[1]}")

        else:
            print(Fore.YELLOW + "Live location has not changed.")
        
        await asyncio.sleep(2)

# def find_closest_carpark(carparks_list, live_location, geoquery_nearest_carparks, user_preference, destination, num_cp_return=1, min_avail_lots=0, remove_unsheltered=True, strict_pref=True):

async def monitor_weather(update: Update, context: ContextTypes.DEFAULT_TYPE, current_carpark, closest_three_carparks, user_address, destination_address, geoquery_nearest_carparks, live_location, user_preference, destination):
    rain_values = ["Light Rain" , "Moderate Rain" , "Heavy Rain" , "Passing Showers" , "Light Showers" , "Showers", "Heavy Showers", "Thundery Showers", "Heavy Thundery Showers", "Heavy Thundery Showers with Gusty Winds"]

    # weather = [
    #     {
    #         "id": "urn:ngsi-ld:WeatherForecast:Bedok-WeatherForecast-2024-10-08T12:23:56_2024-10-08T14:23:56",
    #         "type": "WeatherForecast",
    #         "Area": {
    #             "type": "Property",
    #             "value": "Bedok"
    #         },
    #         "forecast": {
    #             "type": "Property",
    #             "value": "Heavy Rain"
    #         },
    #         "location": {
    #             "type": "GeoProperty",
    #             "value": {
    #                 "type": "Point",
    #                 "coordinates": [
    #                     103.924,
    #                     1.321
    #                 ]
    #             }
    #         }
    #     }
    #     ]
    
    weather = retrieve_ngsi_type(
        input_type="WeatherForecast")
    # print("weather:", weather)


    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    carpark_location = current_carpark['location']['value']['coordinates']
    sent_new = False
    query = update.callback_query
    await query.answer()

    while True:
        live_location = context.user_data.get('live_location')
        for area in weather:
            carpark_coordinates = (carpark_location[1], carpark_location[0])
            forecast_coordinates= (area["location"]["value"]["coordinates"][1], area["location"]["value"]["coordinates"][0])

            distance = geodesic(carpark_coordinates, forecast_coordinates).km
            rain_value = area["forecast"]["value"]
            check_distance_list = [0.5, 1.0, 1.5, 2.0]
            new_carpark = None
            for check_distance in check_distance_list: 
                if distance < check_distance and area["forecast"]["value"] in rain_values:
                    rain_value = area["forecast"]["value"]
                    print("rain_value:", rain_value)
            if current_carpark["Sheltered"]["value"] == False:    
                live_location = (context.user_data.get('live_location')[0], context.user_data.get('live_location')[1]) 
                destination = (context.user_data.get('destination_lat'), context.user_data.get('destination_long'))
                user_preference = context.user_data.get('user_preference')

                new_carpark = find_closest_carpark(closest_three_carparks, live_location,geoquery_nearest_carparks, user_preference , destination, num_cp_return=1, min_avail_lots=0, remove_unsheltered=True, strict_pref=True)
                    
                
                if new_carpark == []:
                    rain_value = area["forecast"]["value"]
                    await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=f"🌦️ *Weather Update:* There is an ongoing {rain_value} happening around your destination. Drive safely and remember to grab an umbrella!", 
                    parse_mode='Markdown')
                    sent_new = True
                    print("No sheltered carpark found")
                    break

                lat = new_carpark["location"]["value"]["coordinates"][1] 
                long = new_carpark["location"]["value"]["coordinates"][0]
                google_maps_link = (
                    f"https://www.google.com/maps/dir/?api=1&origin={live_location[0]},{live_location[1]}"
                    f"&waypoints={lat},{long}"
                    f"&destination={context.user_data.get('destination_lat')},{context.user_data.get('destination_long')}&travelmode=driving"
                )

                await asyncio.sleep(6)

                context.user_data['selected_carpark_lat'] = new_carpark['location']['value']['coordinates'][1]
                context.user_data['selected_carpark_long'] = new_carpark['location']['value']['coordinates'][0]
                context.user_data['selected_carpark'] = new_carpark
                context.user_data['selected_carpark_name'] = new_carpark['CarparkName']['value'].title()
                context.user_data['selected_carpark_available_lots'] = new_carpark['ParkingAvailability']['value']

                google_route_id = context.user_data.get('google_route_id')

                if google_route_id:
                    try:
                        await context.bot.edit_message_reply_markup(
                            chat_id=update.effective_chat.id,
                            message_id=google_route_id,
                            reply_markup=None
                        )
                    except BadRequest as e:
                        logger.error(f"Failed to delete Google Maps route message: {e}")

                keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.reply_text(
                    f"🌧️ *RAIN ALERT: TAP TO REROUTE TO SHELTERED CARPARK*\n\n"
                    f"🛣️ *Here is a new route to a sheltered carpark:*\n\n"
                    f"📍 Start: {user_address}\n"
                    f"🅿️ Stop: {new_carpark['CarparkName']['value'].title()} (Carpark)\n"
                    f"🏁 End: {destination_address}\n\n"
                    f"[Click here to view the route]({google_maps_link})", 
                    parse_mode='Markdown', 
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
                print("new_carpark:", new_carpark)

                sent_new = True
                break
            else:
                rain_value = area["forecast"]["value"]
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=f"🌦️ *Weather Update:* There is an ongoing {rain_value} happening around your destination. Drive safely and remember to grab an umbrella!", 
                    parse_mode='Markdown')
                sent_new = True
                break

        # Sleep for 5 seconds before checking again    
        await asyncio.sleep(5)
        if sent_new == True:
            break


async def monitor_all(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_carpark, closest_three_carparks, destination_details, user_address, destination_address, geoquery_nearest_carparks, live_location, user_preference, destination):
    """Run all monitoring tasks concurrently."""
    print(Fore.CYAN + "Starting monitoring tasks...")
    try:
        await asyncio.gather(
            monitor_carpark_availability(update, context, selected_carpark),
            monitor_traffic_advisories(update, context),
            monitor_weather(update, context, selected_carpark, closest_three_carparks, user_address, destination_address, geoquery_nearest_carparks, live_location, user_preference, destination),
            monitor_live_location_changes(update, context),
        )
    except BadRequest as e:
        logging.error(f"BadRequest error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")