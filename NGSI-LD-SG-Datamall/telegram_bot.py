import sys
print(sys.version)

import mylibs.constants as constants
import mylibs.ngsi_ld_parking as ngsi_parking
import time

from landtransportsg import PublicTransport

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime

import logging
from geopy.distance import geodesic
from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def ngsi_test_fn():
    ret = ngsi_parking.geoquery_ngsi_point(input_type="Carpark", maxDistance=5000, lat=103.83359, long=1.3071)
    print(len(ret))

# State definitions
DESTINATION, LIVE_LOCATION = range(2)

# Store user data
user_data = {}

def find_closest_three_carparks(nearest_carparks_list, dest_lat, dest_long):
    closest_three_carparks = []
    for carpark in nearest_carparks_list:
        carpark_dict = carpark.to_dict()
        lat = carpark_dict["location"]["value"]["coordinates"][1]
        long = carpark_dict["location"]["value"]["coordinates"][0]
        distance = geodesic((dest_lat, dest_long), (lat, long)).km
        carpark_dict["distance"] = distance
        
        if carpark_dict["LotType"]["value"] == "C" and carpark_dict["ParkingAvalibility"]["value"] > 0:
            if len(closest_three_carparks) < 3:
                closest_three_carparks.append(carpark_dict)
            else:
                farthest_carpark = max(closest_three_carparks, key=lambda x: x["distance"])
                if farthest_carpark["distance"] > carpark_dict["distance"]:
                    closest_three_carparks.remove(farthest_carpark)
                    closest_three_carparks.append(carpark_dict)
    return closest_three_carparks

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for destination location."""
    if update.message:
        await update.message.reply_text('Hi! Please share your destination location.')
    return DESTINATION

async def destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the destination location and ask for live location."""
    if update.message and update.message.location:
        user = update.message.from_user
        destination_location = update.message.location
        user_data[user.id] = {
            'destination': (destination_location.latitude, destination_location.longitude)
        }

        nearest_carparks = ngsi_parking.geoquery_ngsi_point(input_type="Carpark", maxDistance=1000, lat=destination_location.latitude, long=destination_location.longitude)

        if len(nearest_carparks) == 0:
            await update.message.reply_text("No Nearby carparks")
        else:
            closest_three_carparks = find_closest_three_carparks(nearest_carparks_list=nearest_carparks, dest_lat=destination_location.latitude, dest_long=destination_location.longitude)

            closest_carparks_message = "The closest 3 carparks to your destination are:\n"
            for count, carpark in enumerate(closest_three_carparks, 1):
                closest_carparks_message += (
                    f"{count}: \nArea: {carpark['DevelopmentName']['value']} \nLots: {carpark['ParkingAvalibility']['value']} \n"
                    f"Distance from destination: {carpark['distance']} km\n"
                )

            await update.message.reply_text(closest_carparks_message)

        await update.message.reply_text('Got your destination. Now please share your live location continuously.')
        return LIVE_LOCATION
    else:
        await update.message.reply_text('Please send your destination location by using the location sharing feature in Telegram.')
        return DESTINATION

async def live_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Check if the user is within 5km of the destination."""
    if update.message and update.message.location:
        user = update.message.from_user
        live_location = update.message.location

        destination = user_data.get(user.id, {}).get('destination')
        print(destination)
        if destination:
            distance = geodesic((destination[0] , destination[1]), (live_location.latitude, live_location.longitude)).km

            if distance <= 5:
                await update.message.reply_text('You are within 5km of your destination!')
                
                nearest_carparks = ngsi_parking.geoquery_ngsi_point(input_type="Carpark", maxDistance=1000, lat=destination[0], long=destination[1])
                if len(nearest_carparks) == 0:
                    await update.message.reply_text("No Nearby carparks")
                else:
                    closest_three_carparks = find_closest_three_carparks(nearest_carparks_list=nearest_carparks, dest_lat=destination[0], dest_long=destination[1])

                    closest_carparks_message = "The current closest 3 carparks to your destination with available lots are:\n"
                    for count, carpark in enumerate(closest_three_carparks, 1):
                        closest_carparks_message += (
                            f"{count}: \nArea: {carpark['DevelopmentName']['value']} \nLots: {carpark['ParkingAvalibility']['value']} \n"
                            f"Distance from destination: {carpark['distance']} km\n"
                        )
                    await update.message.reply_text(closest_carparks_message)
            else:
                await update.message.reply_text("You are not within 5km of your destination yet.")
             
        return LIVE_LOCATION
    else:
        if update.message:
            await update.message.reply_text('Please share your live location by using the location sharing feature in Telegram.')
        return LIVE_LOCATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    if update.message:
        await update.message.reply_text('Bye! Hope to talk to you again soon.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESTINATION: [MessageHandler(filters.LOCATION | filters.TEXT, destination)],
            LIVE_LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT, live_location)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
