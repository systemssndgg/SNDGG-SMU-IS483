import sys
print(sys.version)

import constants

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

# import functions
from utils.telegram_handlers import start, get_destination, destination_selected, user_preference, store_preference, confirm_destination, preference, live_location, carpark_selected, info, settings, handle_settings, handle_filter, confirm_filter, end

# State definitions
DESTINATION, CHECK_USER_PREFERENCE, USER_PREFERENCE, STORE_PREFERENCE, PREFERENCE, CONFIRM_DESTINATION, LIVE_LOCATION, INFO, SETTINGS, FILTER, CONFIRM_FILTER = range(11)

def main() -> None:
    """Run the bot."""
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
                CallbackQueryHandler(handle_filter, pattern="^(missing_carpark_prices|missing_carpark_avail|end)$"),
            ],
            CONFIRM_FILTER: [
                CallbackQueryHandler(confirm_filter, pattern="^(include|exclude|end)$"),
            ],
        },
        fallbacks=[CommandHandler('end', end),
        CallbackQueryHandler(end, pattern='^end$'),
        CallbackQueryHandler(preference, pattern='^preference$'),
        ],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()