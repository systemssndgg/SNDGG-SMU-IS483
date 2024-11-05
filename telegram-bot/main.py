import sys
print(sys.version)
import threading
from flask import Flask
import asyncio

import constants

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

# import functions
from utils.telegram_handlers import start, get_destination, destination_selected, user_preference, store_preference, confirm_destination, preference, live_location, carpark_selected, info, settings, handle_settings, handle_filter, confirm_filter, handle_numeric_input, end
from utils.helper_functions import update_context_broker

# State definitions
DESTINATION, CHECK_USER_PREFERENCE, USER_PREFERENCE, STORE_PREFERENCE, PREFERENCE, CONFIRM_DESTINATION, LIVE_LOCATION, INFO, SETTINGS, FILTER, CONFIRM_FILTER, NUMERIC_INPUT = range(12)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def run_update_context_broker():
    asyncio.run(update_context_broker())

def main() -> None:
    """Run the Telegram bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).write_timeout(120).read_timeout(120).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('info', info), CommandHandler('settings', settings)], 
        states={
            DESTINATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination),
                CallbackQueryHandler(destination_selected),
                CommandHandler("info", info),
                CommandHandler("settings", settings),
            ],
            USER_PREFERENCE: [
                CallbackQueryHandler(user_preference),
                CommandHandler("info", info),
                CommandHandler("settings", settings),

            ],
            CONFIRM_DESTINATION: [
                CallbackQueryHandler(confirm_destination),
                CommandHandler("info", info),
                CommandHandler("settings", settings),
            ],
            STORE_PREFERENCE: [
                CallbackQueryHandler(store_preference),
                CommandHandler("info", info),
                CommandHandler("settings", settings),
            ],
            PREFERENCE: [
                CallbackQueryHandler(preference),
                CommandHandler("info", info),
                CommandHandler("settings", settings),
            ],
            LIVE_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, live_location),
                CallbackQueryHandler(carpark_selected),
                CommandHandler("info", info),
                CommandHandler("settings", settings),
            ],
            SETTINGS: [
                CallbackQueryHandler(handle_settings, pattern="^(preference|filter|end)$"),
            ],
            FILTER: [
                CallbackQueryHandler(handle_filter, pattern="^(missing_carpark_prices|missing_carpark_avail|minimum_carpark_avail|number_carpark_options|end)$"),
            ],
            CONFIRM_FILTER: [
                CallbackQueryHandler(confirm_filter, pattern="^(include|exclude|end)$"),
            ],
            NUMERIC_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_numeric_input),
            ],
        },
        fallbacks=[CommandHandler('end', end),
        CallbackQueryHandler(end, pattern='^end$'),
        CallbackQueryHandler(preference, pattern='^preference$'),
        ],
        per_message=False
    )

    application.add_handler(conv_handler)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    update_thread = threading.Thread(target=run_update_context_broker)
    update_thread.start()

    application.run_polling()

if __name__ == '__main__':
    main()