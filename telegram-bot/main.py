import sys
print(sys.version)

import constants

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

# import functions
from utils.telegram_handlers import start, get_destination, destination_selected, user_preference, store_preference, confirm_destination, preference, live_location, carpark_selected, info, end

# State definitions
DESTINATION, CHECK_USER_PREFERENCE, USER_PREFERENCE, STORE_PREFERENCE, PREFERENCE, CONFIRM_DESTINATION, LIVE_LOCATION, INFO, = range(8)

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).write_timeout(120).read_timeout(120).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('preference', preference), CommandHandler('info', info)], 
        states={
            DESTINATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination),
                CallbackQueryHandler(destination_selected),
                CommandHandler("info", info),
                CommandHandler("preference", preference),
            ],
            USER_PREFERENCE: [
                CallbackQueryHandler(user_preference),
               CommandHandler("info", info),
                CommandHandler("preference", preference),

            ],
            CONFIRM_DESTINATION: [
                CallbackQueryHandler(confirm_destination),
                CommandHandler("info", info),
                CommandHandler("preference", preference),
            ],
            STORE_PREFERENCE: [
                CallbackQueryHandler(store_preference),
                CommandHandler("info", info),
                CommandHandler("preference", preference),
            ],
            PREFERENCE: [
                CallbackQueryHandler(preference),
                CommandHandler("info", info),
                CommandHandler("preference", preference),
            ],
            LIVE_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, live_location),
                CallbackQueryHandler(carpark_selected),
                CommandHandler("info", info),
                CommandHandler("preference", preference),
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