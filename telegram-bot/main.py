import constants
from handlers.telegram_handlers import start, get_destination, end

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# State definitions
DESTINATION, CONFIRM_DESTINATION, LIVE_LOCATION, RESTART, USER_PREFERENCE = range(5)

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(constants.TELEGRAM_BOT_KEY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESTINATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, get_destination),
                # CallbackQueryHandler(destination_selected),
            ],
            # USER_PREFERENCE: [
                # CallbackQueryHandler(user_preference),
            # ],
            # CONFIRM_DESTINATION: [
                # CallbackQueryHandler(confirm_destination),
            # ],
            # LIVE_LOCATION: [
                # MessageHandler(filters.LOCATION | filters.TEXT, live_location),
                # CallbackQueryHandler(carpark_selected),
            # ],
            # RESTART: [
            #     CallbackQueryHandler(restart, pattern='^start$'),
            # ]
        },
        fallbacks=[CommandHandler('end', end),
        CallbackQueryHandler(end, pattern='^end$'),
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()