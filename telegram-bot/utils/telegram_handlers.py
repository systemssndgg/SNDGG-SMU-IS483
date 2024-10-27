import sys
print(sys.version)

import constants as constants
from utils.context_broker import geoquery_ngsi_point

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

# import functions
from utils.monitor import monitor_all
from utils.helper_functions import aggregate_message_new, get_top_carparks, remove_selected_button
from utils.context_broker import geoquery_ngsi_point
from utils.google_maps import get_autocomplete_place, get_details_place, generate_static_map_url, get_address_from_coordinates, get_route_duration
from utils.firestore import check_user_exists, get_user_preference, store_user_preference, edit_user_preference

import asyncio

import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)


# State definitions
DESTINATION, CHECK_USER_PREFERENCE, USER_PREFERENCE, STORE_PREFERENCE, PREFERENCE, CONFIRM_DESTINATION, LIVE_LOCATION, RESTART, = range(8)

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
    
    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    if update.message and update.message.text:
        message_id = context.user_data.get('message_id')
        rejected_destination_id = context.user_data.get('rejected_destination_id')

        if message_id:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=message_id,
                    reply_markup=None
                )
            except BadRequest as e:
                print(f"Failed to delete message: {e}")
        
        if rejected_destination_id:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=rejected_destination_id,
                    reply_markup=None
                )
            except BadRequest as e:
                print(f"Failed to delete message: {e}")
            
        user_input = update.message.text
        loading_message = await update.message.reply_text("🔄 Fetching suggestions for your destination...")
        suggestions = get_autocomplete_place(user_input)

        keyboard = [[InlineKeyboardButton(suggestion['description'], callback_data=suggestion['place_id'][:64])]
        for suggestion in suggestions]

        keyboard.append([InlineKeyboardButton("🔍 Search another destination", callback_data="search_again")])

        keyboard.append([InlineKeyboardButton("🛑 End Session", callback_data="end")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        destinations = await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id,
            text="🌐 *Please select your destination below:*", 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        context.user_data['destinations_id'] = destinations.message_id

        return DESTINATION

async def destination_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selected destination, search another destination, or cancel"""

    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    context.user_data['carpark_list_sent'] = False

    query = update.callback_query
    await query.answer()

    destination_id = query.data

    # Debug print statements to check callback data
    print(f"Callback data received: {destination_id}")

    # Check if the destination_id matches any special cases
    if destination_id == "start":
        return await start(update, context)

    if destination_id == "search_again":
        keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]

        reply_markup = InlineKeyboardMarkup(keyboard)
    
        retry_message = await query.edit_message_text(
            "🔄 *Let's try again.* Where would you like to go?\n\n"
            "Please type your destination.",parse_mode="Markdown",
            reply_markup=reply_markup
        )

        context.user_data['retry_message_id'] = retry_message.message_id
        context.user_data['retry_message_edited_status'] = False

        return DESTINATION
    
    if destination_id == "end":
        return await end(update, context)

    # Debugging to check if place details are fetched
    print(f"Destination selected. Fetching details for place ID: {destination_id}")

    try:
        # Fetch destination details using the Google Maps API
        global destination_details
        destination_details = get_details_place(destination_id)

        if destination_details:
            lat = destination_details['geometry']['location']['lat']
            lng = destination_details['geometry']['location']['lng']
            place_name = destination_details.get('name', 'Unknown location')
            address = destination_details.get('formatted_address', 'No address available')

            context.user_data['destination_lat'] = lat
            context.user_data['destination_long'] = lng
            context.user_data['destination_address'] = place_name + " " + address

            destination_address = await query.edit_message_text(
                f"📍 *{place_name} {address}*\n\n",
                parse_mode="Markdown"
                )
            context.user_data['destination_address_id'] = destination_address.message_id

            # Generate static map URL and send the map to the user
            static_map_url = generate_static_map_url(lat, lng)
            map_message = await context.bot.send_photo(chat_id=query.message.chat_id, photo=static_map_url)
            context.user_data['static_map_message_id'] = map_message.message_id

            # Debugging: Check if the photo is being sent
            print("Static map photo sent")

            # Create a keyboard with Yes/No options for the user to confirm
            keyboard = [
                [InlineKeyboardButton("✅ Yes", callback_data="confirm_yes"), InlineKeyboardButton("❌ No", callback_data="confirm_no")],
                [InlineKeyboardButton("🛑 End Session", callback_data="end")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send the confirmation message
            confirm_destination_message = await query.message.reply_text(
                "💬 *Is this the correct destination?*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
                )
            
            context.user_data['confirm_destination_message'] = confirm_destination_message.message_id

            return USER_PREFERENCE
        else:
            await query.edit_message_text("❌ An error occurred. Please try again.")
            return DESTINATION
    except Exception as e:
        logger.error(f"An error occurred in get_details_place: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")
        return DESTINATION

async def user_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Obtain User's preference for carpark"""
    await context.job_queue.stop()
    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    query = update.callback_query
    print("I'm in user_preference", query)
    await query.answer()
    context.user_data["confirm_destination"] = query.data

    keyboard = [
                [InlineKeyboardButton("🏎️ Fastest", callback_data="fastest")],
                [InlineKeyboardButton("💸 Cheapest", callback_data="cheapest")],
                [InlineKeyboardButton("☂️ Sheltered", callback_data="sheltered")],
                [InlineKeyboardButton("🚶‍♂️ Shortest Walking Distance", callback_data="shortest_walking_distance")],
                [InlineKeyboardButton("🛑 End Session", callback_data="end"), InlineKeyboardButton("🔃 Reset", callback_data="reset")]
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'preference_list' not in context.user_data:
        context.user_data['preference_list'] = []
        context.user_data
    preference_list = context.user_data['preference_list']

    try:
        if query.data == "confirm_no":
            print("User rejected the location. Asking for a new destination.")

            keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            static_map_message_id = context.user_data.get('static_map_message_id')
            if static_map_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=static_map_message_id
                    )
                except BadRequest as e:
                    logger.error(f"Failed to delete static map message: {e}")
            

            rejected_destination = await query.edit_message_text(
                "❌ *Destination rejected.* Let's search again. Where would you like to go?\n\n"
                "Please type your destination.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            context.user_data['rejected_destination_id'] = rejected_destination.message_id

            return DESTINATION
        
        user_id = update.effective_user.id
        if check_user_exists(user_id):
            # Runs if user exists in Firestore
            confirm_destination_message_id = context.user_data.get('confirm_destination_message')
            if confirm_destination_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=confirm_destination_message_id
                    )
                except BadRequest as e:
                    logger.error(f"Failed to delete confirm destination message: {e}")

            stored_preference = get_user_preference(user_id)

            # Set context.user_data['preference_list'] with the stored preference
            context.user_data['preference_list'] = stored_preference

            preference_text = "\n".join(
                        [f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Most Important)" if i == 0 else 
                        f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Least Important)" if i == len(stored_preference) - 1 else 
                        f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)}"
                        for i, pref in enumerate(stored_preference)]
                    )
            await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"Your stored preferences are:\n\n{preference_text}"
                    )
            return await confirm_destination(update, context)
        
        if query.data == "confirm_yes" or query.data == "reset":
            if query.data == "reset":
                context.user_data['preference_list'] = []
                print("Preferences reset")
                preference_message_id = context.user_data.get('preference_message_id')
                first_preference_message_id = context.user_data.get('first_preference_message_id')
                if preference_message_id or first_preference_message_id:
                    if preference_message_id:
                        await context.bot.delete_message(
                            chat_id=query.message.chat_id,
                            message_id=preference_message_id
                        )
                    elif first_preference_message_id:
                        await context.bot.delete_message(
                            chat_id=query.message.chat_id,
                            message_id=first_preference_message_id
                        )
                
            context.user_data["confirm_destination"] = query.data
            print("Asking for User Preference.")
            confirm_destination_message_id = context.user_data.get('confirm_destination_message')
            if confirm_destination_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=confirm_destination_message_id
                    )
                except BadRequest as e:
                    logger.error(f"Failed to delete confirm destination message: {e}")

            first_preference_message = await query.message.reply_text(
                "*Which of the following is most important to you?*\n\n",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            context.user_data['first_preference_message_id'] = first_preference_message.message_id

            return USER_PREFERENCE
        
        elif query.data in ["cheapest", "fastest", "sheltered", "shortest_walking_distance"]:
            # Keep track of user's preference
            if query.data not in preference_list:
                preference_list.append(query.data)
                print("preference list:" , preference_list)

            new_keyboard = remove_selected_button(query)

            if len(new_keyboard) > 2:
                # Update the message with the modified checklist
                preference_message = await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text="*Which of the following is most important to you?*\n\n",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(new_keyboard)
                )
                context.user_data['preference_message_id'] = preference_message.message_id
                
                return USER_PREFERENCE
            
            else:
                # Automatically append the last preference button to the list
                if len(new_keyboard) == 2:
                    last_preference = new_keyboard[0][0].callback_data
                    if last_preference not in preference_list:
                        preference_list.append(last_preference)
                        print("preference list:", preference_list)

                # Send the final preferences summary
                preference_text = "\n".join(
                    [f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Most Important)" if i == 0 else 
                    f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Least Important)" if i == len(preference_list) - 1 else 
                    f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)}"
                    for i, pref in enumerate(preference_list)]
                )
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"You've selected your preferences in the following order:\n\n{preference_text}"
                )
                print("User has chosen their preferences")

                preference_message_id = context.user_data.get('preference_message_id')
                if preference_message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=query.message.chat_id,
                            message_id=preference_message_id
                        )
                    except BadRequest as e:
                        logger.error(f"Failed to delete preference message: {e}")
                return await confirm_preference(update, context)

        elif query.data == "end":
            static_map_message_id = context.user_data.get('static_map_message_id')
            if static_map_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=static_map_message_id
                    )
                except BadRequest as e:
                    logger.error(f"Failed to delete static map message: {e}")
            return await end(update, context)

    except Exception as e:
        logger.error(f"An error occurred in user_preference: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")
        return DESTINATION

async def confirm_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the user's preference in Firestore."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="confirm_preference_yes"), InlineKeyboardButton("❌ No", callback_data="confirm_preference_no")],
        [InlineKeyboardButton("🛑 End Session", callback_data="end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="💡 *Store Your Preference?*\n\nWould you like me to save this preference for future sessions?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return STORE_PREFERENCE

async def store_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the user's preference in Firestore."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_preference_yes":
        user_id = update.effective_user.id
        preference_list = context.user_data.get('preference_list')
        print(f"Storing user preference {preference_list} for user {user_id}")
        store_user_preference(user_id, preference_list)
        await query.edit_message_text("✅ Your preference has been saved.")
    elif query.data == "confirm_preference_no":
        await query.edit_message_text("❌ Your preference has not been saved.")
    return await confirm_destination(update, context)

async def preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user to set their preference."""

    query = update.callback_query

    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("🏎️ Fastest", callback_data="fastest")],
        [InlineKeyboardButton("💸 Cheapest", callback_data="cheapest")],
        [InlineKeyboardButton("☂️ Sheltered", callback_data="sheltered")],
        [InlineKeyboardButton("🚶‍♂️ Shortest Walking Distance", callback_data="shortest_walking_distance")],
        [InlineKeyboardButton("🛑 End Session", callback_data="end"), InlineKeyboardButton("🔃 Reset", callback_data="reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'menu_preference_list' not in context.user_data:
        context.user_data['menu_preference_list'] = []
        context.user_data
    menu_preference_list = context.user_data['menu_preference_list']

    if not query or not query.data or query.data == "confirm_yes" or query.data == "reset":
        if query and query.data == "reset":
            context.user_data['menu_preference_list'] = []
            print("Preferences reset")
            preference_message_id = context.user_data.get('menu_preference_message_id')
            first_preference_message_id = context.user_data.get('menu_first_preference_message_id')
            if preference_message_id or first_preference_message_id:
                if preference_message_id:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=preference_message_id
                    )
                elif first_preference_message_id:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=first_preference_message_id
                    )

        first_preference_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*Which of the following is most important to you?*\n\n",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        context.user_data['menu_first_preference_message_id'] = first_preference_message.message_id

        return PREFERENCE
        
    elif query.data in ["cheapest", "fastest", "sheltered", "shortest_walking_distance"]:
        # Keep track of user's preference
        if query.data not in menu_preference_list:
            menu_preference_list.append(query.data)
            print("preference list:" , menu_preference_list)

        new_keyboard = remove_selected_button(query)

        if len(new_keyboard) > 2:
            # Update the message with the modified checklist
            preference_message = await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="*Which of the following is most important to you?*\n\n",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(new_keyboard)
            )
            context.user_data['menu_preference_message_id'] = preference_message.message_id
            
            return PREFERENCE
            
        else:
            # Automatically append the last preference button to the list
            if len(new_keyboard) == 2:
                last_preference = new_keyboard[0][0].callback_data
                if last_preference not in menu_preference_list:
                    menu_preference_list.append(last_preference)
                    print("preference list:", menu_preference_list)

            # Send the final preferences summary
            preference_text = "\n".join(
                [f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Most Important)" if i == 0 else 
                f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)} (Least Important)" if i == len(menu_preference_list) - 1 else 
                f"{next(button.text for row in keyboard for button in row if button.callback_data == pref)}"
                for i, pref in enumerate(menu_preference_list)]
            )
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"You've selected your preferences in the following order:\n\n{preference_text}"
            )
            print("User has chosen their preferences")

            menu_preference_message_id = context.user_data.get('menu_preference_message_id')
            if menu_preference_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=menu_preference_message_id
                    )
                except BadRequest as e:
                    logger.error(f"Failed to delete preference message: {e}")
            return await edit_preference(update, context)

    elif query.data == "end":
        # ...
        return await end(update, context)

async def edit_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit the user's preference."""
    loading_message = await context.bot.send_message(
        text="*🔄 Updating preference...*",
        chat_id=update.effective_chat.id,
        parse_mode="Markdown"
    )

    user_id = update.effective_user.id
    print(context.user_data.get('menu_preference_list'))
    preference_list = context.user_data.get('menu_preference_list')
    print(f"Editing user preference for user {user_id}")
    
    edit_user_preference(user_id, preference_list)

    await loading_message.edit_text("✅ Your preference has been updated.")

    return ConversationHandler.END

async def confirm_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm the destination and ask for live location."""

    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    await context.job_queue.stop()
    query = update.callback_query
    await query.answer()
    print("I'm in store_destination", query.data)

    preference_list = context.user_data.get('preference_list')

    print("Confirm destination", context.user_data.get("confirm_destination"))
    if context.user_data.get("confirm_destination") == "confirm_yes" or query.data == "confirm_preference_yes" or query.data == "confirm_preference_no":
        print(f"User has chosen his preferences {preference_list}")
        print("Asking for live location.")
        
        keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirm_destination = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Destination confirmed! Please share your live location to help me find the best route.\n\n"
                "*Follow these steps:*\n"
                "📎 Paper Clip > Location > Share Live Location > Select ‘for 1 hour’",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        context.user_data['confirm_destination_message_id'] = confirm_destination.message_id
        context.user_data['confirm_destination_edited_status'] = False

        return LIVE_LOCATION 
    
    elif query.data == "confirm_no":
        print("User rejected the location. Asking for a new destination.")

        keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        static_map_message_id = context.user_data.get('static_map_message_id')
        if static_map_message_id:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=static_map_message_id
            )

        await query.edit_message_text(
            "❌ *Destination rejected.* Let's search again. Where would you like to go?\n\n"
            "Please type your destination.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return DESTINATION
    
    elif query.data == "end":
        static_map_message_id = context.user_data.get('static_map_message_id')
        destination_address_id = context.user_data.get('destination_address_id')
        if static_map_message_id:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=static_map_message_id
            )
        # if destination_address_id:
        #     await context.bot.delete_message(
        #         chat_id=query.message.chat_id,
        #         message_id=destination_address_id
        #     )

        return await end(update, context)

    return ConversationHandler.END

async def live_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the live location input and find nearest carpark based on destination"""
    
    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    confirm_destination_message_id = context.user_data.get('confirm_destination_message_id')

    if context.user_data.get('confirm_destination_edited_status') == False:
        if confirm_destination_message_id:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=confirm_destination_message_id,
            )
            context.user_data['confirm_destination_edited_status'] = True
    
    query = update.callback_query
    if query and query.data == "end":
        static_map_message_id = context.user_data.get('static_map_message_id')
        if static_map_message_id:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=static_map_message_id
            )

        return await end(update, context)
    # Handle both regular and live location updates
    if update.message and update.message.location:
        live_location = (update.message.location.latitude, update.message.location.longitude)
        context.user_data['live_location'] = live_location
        context.user_data['live_location_message_id'] = update.message.message_id
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
        global nearest_carparks
        nearest_carparks = geoquery_ngsi_point(
            input_type="Carpark",
            maxDistance=3000,
            lat=destination_lat,
            long=destination_long
        )

        if len(nearest_carparks) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="🚫 Sorry! No nearby carparks found.")
        else:
            # user_selected_preference is a list of user preferences in order of importance
            # eg.  ['fastest', 'shortest_walking_distance', 'cheapest', 'sheltered']
            user_selected_preference = context.user_data.get("preference_list")[:]

            # Add available_lots to the user preference list as least preference (last item)
            user_selected_preference.append('available_lots')

            user_pref = {}

            var_map = {
                'fastest': 'travel_time',
                'shortest_walking_distance': 'walking_time',
                'cheapest': 'price',
                'sheltered': 'is_sheltered',
                'available_lots': 'available_lots'
            }
           
            scoringWeights = [0.4, 0.25, 0.2, 0.1, 0.05] # In order of importance (1st = most important)

            for i in range(len(user_selected_preference)):
                user_pref_str = user_selected_preference[i]
                attr_name = var_map[user_pref_str]
                attr_weight = scoringWeights[i]

                user_pref[attr_name] = attr_weight
            
            # [END] ========================================================================================================

            global closest_three_carparks
            closest_three_carparks = get_top_carparks(live_location, nearest_carparks, user_pref, num_cp_to_return=3, min_avail_lots=10, destination=(destination_lat, destination_long))
            
            carparks_message = aggregate_message_new(closest_three_carparks, user_selected_preference)

            carpark_options_message_id = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=carparks_message,
                parse_mode='Markdown')

            context.user_data['carpark_options_message_id'] = carpark_options_message_id.message_id

            context.user_data['closest_carparks'] = closest_three_carparks

            keyboard = [
                [InlineKeyboardButton(carpark['CarparkName']['value'].title(), callback_data=f"carpark_{count}")]
                for count, carpark in enumerate(closest_three_carparks)
            ]

            keyboard.append([InlineKeyboardButton("🛑 End Session", callback_data="end")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            carpark_select_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Please select a carpark:", reply_markup=reply_markup)

            context.user_data['carpark_select_message_id'] = carpark_select_message.message_id

            context.user_data['carpark_list_sent'] = True

            return LIVE_LOCATION
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No destination set. Please set your destination first.")
        return LIVE_LOCATION

async def carpark_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selected carpark and return a Google Maps route."""

    # Logging setup
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    query = update.callback_query
    await query.answer()

    if query.data == "start":
        return await start(update, context)

    if query.data == "end":
        static_map_message_id = context.user_data.get('static_map_message_id')
        if static_map_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=static_map_message_id
                )
            except BadRequest as e:
                logger.error(f"Failed to delete static map message: {e}")

        carpark_options_message_id = context.user_data.get('carpark_options_message_id')
        if carpark_options_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=carpark_options_message_id
                )
            except BadRequest as e:
                logger.error(f"Failed to delete carpark options message: {e}")

        return await end(update, context)

    carpark_options_message_id = context.user_data.get('carpark_options_message_id')
    if carpark_options_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=carpark_options_message_id
            )
        except BadRequest as e:
            logger.error(f"Failed to delete carpark options message: {e}")
    
    carpark_select_message_id = context.user_data.get('carpark_select_message_id')
    if carpark_select_message_id:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=carpark_select_message_id
        )

    selected_carpark_index = int(query.data.split("_")[1])
    closest_three_carparks = context.user_data['closest_carparks']
    selected_carpark = closest_three_carparks[selected_carpark_index]

    context.user_data['selected_carpark_lat'] = selected_carpark['location']['value']['coordinates'][1]
    context.user_data['selected_carpark_long'] = selected_carpark['location']['value']['coordinates'][0]
    context.user_data['selected_carpark'] = selected_carpark
    context.user_data['selected_carpark_name'] = selected_carpark['CarparkName']['value'].title()
    context.user_data['selected_carpark_availability'] = selected_carpark['ParkingAvailability']['value']

    selected_carpark_name = selected_carpark['CarparkName']['value'].title()
    await query.message.reply_text(
        f"🅿️ You have selected *{selected_carpark_name}* as your carpark.",
        parse_mode="Markdown"
    )

    live_location = context.user_data.get('live_location')
    if not live_location:
        await query.message.reply_text("⚠️ Error: Couldn't retrieve your live location.")
        return ConversationHandler.END
    
    global user_address
    global destination_address

    user_address = get_address_from_coordinates(live_location[0], live_location[1])
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

    keyboard = [[InlineKeyboardButton("🛑 End Session", callback_data="end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    google_route_id = await query.message.reply_text(
        f"🛣️ *Here is your route:*\n\n"
        f"📍 Start: {user_address}\n"
        f"🅿️ Stop: {selected_carpark['CarparkName']['value'].title()} (Carpark)\n"
        f"🏁 End: {destination_address}\n\n"
        f"[Click here to view the route]({google_maps_link})", 
        parse_mode='Markdown',
        reply_markup=reply_markup, 
        disable_web_page_preview=True
    )

    context.user_data['google_route_id'] = google_route_id.message_id
    
    # global current_carpark
    # current_carpark = selected_carpark

    # asyncio.create_task(monitor_carpark_availability(update, context, selected_carpark))
    asyncio.create_task(monitor_all(update, context, selected_carpark, closest_three_carparks, destination_details, user_address, destination_address))
    
    return LIVE_LOCATION

async def restart_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the bot session when the user clicks 'Start Session'."""
    query = update.callback_query
    await query.answer()

    return await start(update, context)

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the session and provide a restart button."""
    # context.user_data.clear()

    if update.callback_query:
        query = update.callback_query
        try:
            await query.answer()

            if query.message:
                if context.user_data.get('live_location_message_id'):
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=context.user_data['live_location_message_id']
                    )
        
                await query.edit_message_text(
                    "👋 *Goodbye!* I look forward to assisting you again.\n\nTo start a new session, please enter /start or press the menu button on the left.", parse_mode="Markdown", reply_markup=None)

        except BadRequest as e:
            print(f"Failed to delete message: {e}")
            
    
    return ConversationHandler.END