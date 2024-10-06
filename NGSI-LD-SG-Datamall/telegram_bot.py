import sys
print(sys.version)

import mylibs.constants as constants
import mylibs.ngsi_ld as ngsi_parking
import time

from landtransportsg import PublicTransport

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime

import logging
from geopy.distance import geodesic
from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import mylibs.google_maps as google_maps
import asyncio

import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def ngsi_test_fn():
    ret = ngsi_parking.geoquery_ngsi_point(input_type="Carpark", maxDistance=5000, lat=103.83359, long=1.3071)
    print(len(ret))

# State definitions
DESTINATION, CONFIRM_DESTINATION, LIVE_LOCATION = range(3)

# Store user data
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and ask for user's destination."""
    await update.message.reply_text(
        "👋 *Welcome!* Where would you like to go today?\n\n"
        "Please type your destination.",
        parse_mode='Markdown'
        )
    return DESTINATION

async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle destination input and return a list of suggestions"""
    if update.message and update.message.text:
        user_input = update.message.text
        suggestions = google_maps.get_autocomplete_place(user_input)

        if suggestions:
            # Create a list of buttons with suggestions for the user to choose from
            keyboard = [[InlineKeyboardButton(suggestion['description'], callback_data=suggestion['place_id'])]
            for suggestion in suggestions]

            # Add a 'Search another destination' button at the bottom
            keyboard.append([InlineKeyboardButton("🔍 Search another destination", callback_data="search_again")])

            # Add a "Cancel" button at the bottom
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("🌐 *Please select your destination from the suggestions below:*", reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text('🚫 No suggestions found. Please try again.')
        
        return DESTINATION
    else:
        await update.message.reply_text('✏️ Please type your destination.')
        return DESTINATION

async def destination_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selected destination, search another destination, or cancel"""
    context.user_data['carpark_list_sent'] = False

    query = update.callback_query
    await query.answer()

    destination_id = query.data

    # Debug print statements to check callback data
    print(f"Callback data received: {destination_id}")

    # Check if the destination_id matches any special cases
    if destination_id in ["confirm_yes", "confirm_no"]:
        print("Yes/No was selected")
        return DESTINATION

    if destination_id == "search_again":
        await query.edit_message_text("🔄 Let's try again. Where would you like to go?")
        return DESTINATION

    if destination_id == "cancel":
        await query.edit_message_text("❌ Operation cancelled. Bye!")
        return ConversationHandler.END

    # Debugging to check if place details are fetched
    print(f"Destination selected. Fetching details for place ID: {destination_id}")

    # Fetch destination details using the Google Maps API
    destination_details = google_maps.get_details_place(destination_id)

    if destination_details:
        lat = destination_details['geometry']['location']['lat']
        lng = destination_details['geometry']['location']['lng']
        place_name = destination_details.get('name', 'Unknown location')
        address = destination_details.get('formatted_address', 'No address available')

        context.user_data['destination_lat'] = lat
        context.user_data['destination_long'] = lng
        context.user_data['destination_address'] = place_name + " " + address

        # Display the destination details to the user
        await query.edit_message_text(
            f"📍 *{place_name} {address}*\n\n",
            parse_mode="Markdown"
            )

        # Generate static map URL and send the map to the user
        static_map_url = google_maps.generate_static_map_url(lat, lng)
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=static_map_url)

        # Debugging: Check if the photo is being sent
        print("Static map photo sent")

        # Create a keyboard with Yes/No options for the user to confirm
        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data="confirm_yes"), InlineKeyboardButton("❌ No", callback_data="confirm_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the confirmation message
        await query.message.reply_text("💬 *Is this the correct destination?*", reply_markup=reply_markup, parse_mode="Markdown")

        return CONFIRM_DESTINATION
    else:
        await query.edit_message_text("❌ An error occurred. Please try again.")
        return DESTINATION

async def confirm_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm the destination and ask for live location."""
    query = update.callback_query
    await query.answer()

    print(f"User selected: {query.data}")

    if query.data == "confirm_yes":
        print("User confirmed the location. Asking for live location.")
        await query.message.reply_text("🛰️ *Great!* Now, please share your live location so I can find the best route.", parse_mode="Markdown")
        return LIVE_LOCATION 
    
    elif query.data == "confirm_no":
        print("User rejected the location. Asking for a new destination.")
        await query.message.reply_text("🔄 Let's search again. Where would you like to go?")
        return DESTINATION
    
    return ConversationHandler.END

async def live_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the live location input and find nearest carpark based on destination"""
    
    # Handle both regular and live location updates
    if update.message and update.message.location:
        live_location = (update.message.location.latitude, update.message.location.longitude)
        context.user_data['live_location'] = live_location
        print(Fore.BLUE + f"Received initial live location: Latitude {live_location[0]}, Longitude {live_location[1]}")
    elif update.edited_message and update.edited_message.location:
        live_location = (update.edited_message.location.latitude, update.edited_message.location.longitude)
        context.user_data['live_location'] = live_location
        print(Fore.RED + f"Received updated live location: Latitude {live_location[0]}, Longitude {live_location[1]}")
    else:
        await update.message.reply_text("⚠️ Please share your live location to proceed.")
        return LIVE_LOCATION

    if context.user_data.get('carpark_list_sent'):
        logger.info("Carpark list has already been sent. Skipping...")
        return LIVE_LOCATION

    destination_lat = context.user_data.get('destination_lat')
    destination_long = context.user_data.get('destination_long')
    
    if destination_lat and destination_long:
        nearest_carparks = ngsi_parking.geoquery_ngsi_point(
            input_type="Carpark",
            maxDistance=100000,
            lat=destination_lat,
            long=destination_long
        )

        if len(nearest_carparks) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="🚫 Sorry! No nearby carparks found.")
        else:
            closest_three_carparks = find_closest_three_carparks(
                nearest_carparks_list=nearest_carparks,
                dest_lat=destination_lat,
                dest_long=destination_long
            )
            
            closest_carparks_message = "🚗 *The closest 3 carparks to your destination are:*\n\n"

            today = datetime.today().weekday()
            
            for count, carpark in enumerate(closest_three_carparks, 1):
                carpark_name = carpark['CarparkName']['value'].title()

                closest_carparks_message += (
                    f"*{count}. {carpark_name}*\n"
                    f"🅿️ *Available Lots:* {carpark['ParkingAvailability']['value']}\n"
                    f"📏 *Distance:* {carpark['distance']:.2f} km\n"
                )
            
                if 'Pricing' in carpark and 'Car' in carpark['Pricing']["value"]:
                    if 0 <= today <= 4:  # Monday to Friday (Weekday)
                        rate_info = carpark['Pricing']['value']['Car']['WeekdayRate']
                        day_type = "Weekday"
                        closest_carparks_message += (
                        f"🏷️ *{day_type} Rate:* {rate_info['weekdayRate']}\n"
                        f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n"
                        f"⏳ *Duration:* {rate_info['weekdayMin']}\n\n"
                    )
                    elif today == 5:  # Saturday
                        rate_info = carpark['Pricing']['value']['Car']['SaturdayRate']
                        day_type = "Saturday"
                        closest_carparks_message += (
                        f"🏷️ *{day_type} Rate:* {rate_info['satdayRate']}\n"
                        f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n"
                        f"⏳ *Duration:* {rate_info['satdayMin']}\n\n"
                    )
                    else:  # Sunday/Public Holiday (today == 6)
                        rate_info = carpark['Pricing']['value']['Car']['SundayPHRate']
                        day_type = "Sunday/Public Holiday"
                        closest_carparks_message += (
                        f"🏷️ *{day_type} Rate:* {rate_info['sunPHRate']}\n"
                        f"⏰ *Time:* {rate_info['startTime']} - {rate_info['endTime']}\n"
                        f"⏳ *Duration:* {rate_info['sunPHMin']}\n\n"
                    )

                else:
                    closest_carparks_message += "🏷️ *Price Information:* Not Available\n\n"

            await context.bot.send_message(chat_id=update.effective_chat.id, text=closest_carparks_message, parse_mode='Markdown')

            context.user_data['closest_carparks'] = closest_three_carparks

            keyboard = [
                [InlineKeyboardButton(carpark['CarparkName']['value'].title(), callback_data=f"carpark_{count}")]
                for count, carpark in enumerate(closest_three_carparks)
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please select a carpark:", reply_markup=reply_markup)

            context.user_data['carpark_list_sent'] = True

            return LIVE_LOCATION
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No destination set. Please set your destination first.")
        return LIVE_LOCATION

async def monitor_carpark_availability(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_carpark):
    """Monitor the user's proximity to the selected carpark and alert if availability is low."""
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    
    # Begin monitoring the user's proximity
    while True:
        # Continuously get updated live location
        live_location = context.user_data.get('live_location')

        # Debugging: print current lat/lng for testing
        print(Fore.GREEN + f"Monitoring live location: Latitude {live_location[0]}, Longitude {live_location[1]}")

        # Check if live location is still available
        if not live_location:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Error: Couldn't retrieve your live location.")
            break

        carpark_lat = selected_carpark['location']['value']['coordinates'][1]
        carpark_long = selected_carpark['location']['value']['coordinates'][0]
        distance = geodesic(live_location, (carpark_lat, carpark_long)).km

        # Debugging: print distance calculation
        print(f"Distance from carpark: {distance:.2f} km")

        # Trigger warning if within 4km and less than 10 parking spots
        if distance <= 4.0:
            available_lots = selected_carpark['ParkingAvailability']['value']

            if available_lots < 10:
                carpark_name = selected_carpark['CarparkName']['value'].title()
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ *Warning!* The carpark '{carpark_name}' has less than 10 available lots left. Drive carefully!",
                    parse_mode='Markdown'
                )
                break

        # Sleep for 5 seconds before checking again    
        await asyncio.sleep(5)

async def carpark_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selected carpark and return a Google Maps route."""
    query = update.callback_query
    await query.answer()

    selected_carpark_index = int(query.data.split("_")[1])
    closest_three_carparks = context.user_data['closest_carparks']
    selected_carpark = closest_three_carparks[selected_carpark_index]

    live_location = context.user_data.get('live_location')
    if not live_location:
        await query.message.reply_text("⚠️ Error: Couldn't retrieve your live location.")
        return ConversationHandler.END
    
    user_address = google_maps.get_address_from_coordinates(live_location[0], live_location[1])
    destination_address = context.user_data.get('destination_address')
    
    carpark_lat = selected_carpark['location']['value']['coordinates'][1]
    carpark_long = selected_carpark['location']['value']['coordinates'][0]
    destination_lat = context.user_data.get('destination_lat')
    destination_long = context.user_data.get('destination_long')

    google_maps_link = (
        f"https://www.google.com/maps/dir/?api=1&origin={live_location[0]},{live_location[1]}"
        f"&waypoints={carpark_lat},{carpark_long}"
        f"&destination={destination_lat},{destination_long}&travelmode=driving"
    )

    await query.message.reply_text(
        f"🛣️ *Here is your route:*\n\n"
        f"📍 Start: {user_address}\n"
        f"🅿️ Stop: {selected_carpark['CarparkName']['value'].title()} (Carpark)\n"
        f"🏁 End: {destination_address}\n\n"
        f"[Click here to view the route]({google_maps_link})", 
        parse_mode='Markdown', 
        disable_web_page_preview=True
    )

    asyncio.create_task(monitor_carpark_availability(update, context, selected_carpark))

    return LIVE_LOCATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    if update.message:
        await update.message.reply_text('👋 Goodbye! I look forward to assisting you again.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def find_closest_three_carparks(nearest_carparks_list, dest_lat, dest_long):
    closest_three_carparks = []
    for carpark in nearest_carparks_list:
        carpark_dict = carpark.to_dict()
        lat = carpark_dict["location"]["value"]["coordinates"][1]
        long = carpark_dict["location"]["value"]["coordinates"][0]
        distance = geodesic((dest_lat, dest_long), (lat, long)).km
        carpark_dict["distance"] = distance
        
        if "Car" in carpark_dict["Pricing"]["value"] and carpark_dict["ParkingAvailability"]["value"] > 0:
            if len(closest_three_carparks) < 3:
                closest_three_carparks.append(carpark_dict)
            else:
                farthest_carpark = max(closest_three_carparks, key=lambda x: x["distance"])
                if farthest_carpark["distance"] > carpark_dict["distance"]:
                    closest_three_carparks.remove(farthest_carpark)
                    closest_three_carparks.append(carpark_dict)
    return closest_three_carparks

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESTINATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, get_destination),
                CallbackQueryHandler(destination_selected)
            ],
            CONFIRM_DESTINATION: [
                CallbackQueryHandler(confirm_destination)
            ],
            LIVE_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, live_location),
                CallbackQueryHandler(carpark_selected)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
