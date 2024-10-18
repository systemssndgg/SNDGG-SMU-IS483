from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram.error import BadRequest
from utils.google_maps import get_autocomplete_place

# State definitions
DESTINATION, CONFIRM_DESTINATION, LIVE_LOCATION, RESTART, USER_PREFERENCE = range(5)

# Store user data
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and ask for user's destination."""
    keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message: 
        message = await update.message.reply_text(
         "👋 *Welcome!* Where would you like to go today?\n\n"
         "Please type your destination.",
         parse_mode='Markdown',
         reply_markup=reply_markup
    )

        context.user_data['message_id'] = message.message_id

    elif update.callback_query:
        await update.callback_query.edit_message_text(
           "👋 *Welcome!* Where would you like to go today?\n\n""Please type your destination.",
           parse_mode='Markdown',
           reply_markup=reply_markup
    ) 

    return DESTINATION

async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle destination input and return a list of suggestions"""
    if update.message and update.message.text:
        user_input = update.message.text
        loading_message = await update.message.reply_text("🔄 Fetching suggestions for your destination...")
        suggestions = get_autocomplete_place(user_input)

        keyboard = [[InlineKeyboardButton(suggestion['description'], callback_data=suggestion['place_id'][:64])]
        for suggestion in suggestions]

        keyboard.append([InlineKeyboardButton("🔍 Search another destination", callback_data="search_again")])

        keyboard.append([InlineKeyboardButton("🛑 End Session", callback_data="end")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id,
            text="🌐 *Please select your destination below:*", 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        return DESTINATION

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the session and provide a restart button."""
    message_id = context.user_data.get('message_id')

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text="👋 *Goodbye!* I look forward to assisting you again.",
            parse_mode='Markdown',
            reply_markup=None)
    except BadRequest as e:
        await update.callback_query.message.reply_text(
            # TODO: Add error message instead 
            "👋 *Goodbye!* I look forward to assisting you again.", parse_mode='Markdown',
            reply_markup=None
    )
    
    return ConversationHandler.END