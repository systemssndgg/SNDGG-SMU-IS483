import sys
print(sys.version)

import constants

import time

from landtransportsg import PublicTransport

import json
from requests.exceptions import RequestException, HTTPError
from ngsildclient import Client, Entity, SmartDataModels
from datetime import datetime

import logging

from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram.error import BadRequest

import asyncio

import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

# import functions
from utils.telegram_handlers import start, get_destination, destination_selected, user_preference, confirm_destination, live_location, carpark_selected, restart_session ,end


# State definitions
DESTINATION, USER_PREFERENCE, CONFIRM_DESTINATION, LIVE_LOCATION, RESTART, = range(5)

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).read_timeout(60).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESTINATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, get_destination),
                CallbackQueryHandler(destination_selected),
            ],
            USER_PREFERENCE: [
                CallbackQueryHandler(user_preference),
            ],
            CONFIRM_DESTINATION: [
                CallbackQueryHandler(confirm_destination, pattern="^submit$"),
            ],
            LIVE_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, live_location),
                CallbackQueryHandler(carpark_selected),
            ],
            RESTART: [
                CallbackQueryHandler(restart_session, pattern='^start$'),
            ]
        },
        fallbacks=[CommandHandler('end', end),
        CallbackQueryHandler(end, pattern='^end$'),
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()