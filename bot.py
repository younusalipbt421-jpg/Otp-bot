import logging
import os
import json
import random
import time
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, CHANNELS, OTP_GROUP_LINK, SUPPORT_USERS

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DATA_FOLDER = "numbers_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

COUNTRIES_FILE = "countries.json"
USERS_FILE = "users.json"
TAKEN_NUMBERS_FILE = "taken_numbers.json"
SETTINGS_FILE = "settings.json"

FLAGS = {
    "Bangladesh": "🇧🇩", "India": "🇮🇳", "USA": "🇺🇸", "UK": "🇬🇧", "Canada": "🇨🇦",
    "Australia": "🇦🇺", "Germany": "🇩🇪", "France": "🇫🇷", "Italy": "🇮🇹", "Spain": "🇪🇸",
    "Brazil": "🇧🇷", "Mexico": "🇲🇽", "Indonesia": "🇮🇩", "Malaysia": "🇲🇾", "Singapore": "🇸🇬",
    "Thailand": "🇹🇭", "Vietnam": "🇻🇳", "Philippines": "🇵🇭", "Pakistan": "🇵🇰", "Nepal": "🇳🇵",
    "Sri Lanka": "🇱🇰", "Russia": "🇷🇺", "China": "🇨🇳", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Turkey": "🇹🇷", "UAE": "🇦🇪", "Saudi Arabia": "🇸🇦", "Egypt": "🇪🇬", "Nigeria": "🇳🇬", "South Africa": "🇿🇦"
}

SERVICES = ["WhatsApp", "Facebook", "Telegram", "TikTok", "Instagram"]
SERVICE_ICONS = {"WhatsApp": "📱", "Facebook": "📘", "Telegram": "✈️", "TikTok": "🎵", "Instagram": "📷"}

def get_flag(country_name):
    for name, flag in FLAGS.items():
        if name.lower() == country_name.lower():
            return flag
    return "🌍"

def load_countries():
    if os.path.exists(COUNTRIES_FILE):
        with open(COUNTRIES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_countries(countries):
    with open(COUNTRIES_FILE, 'w') as f:
        json.dump(countries, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_taken_numbers():
    if os.path.exists(TAKEN_NUMBERS_FILE):
        with open(TAKEN_NUMBERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_taken_numbers(taken):
    with open(TAKEN_NUMBERS_FILE, 'w') as f:
        json.dump(taken, f, indent=4)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            if "visible_services" not in data:
                data["visible_services"] = {s: True for s in SERVICES}
            return data
    return {"unique_number_mode": True, "visible_services": {s: True for s in SERVICES}}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

countries = load_countries()
users = load_users()
taken_numbers = load_taken_numbers()
settings = load_settings()

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def is_joined_all(application, user_id):
    if not CHANNELS:
        return True
    for channel in CHANNELS:
        try:
            member = await application.bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

WELCOME_TEXT = (
    "🎀 *⋆⁺₊☾ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐍𝐔𝐌𝐁𝐄𝐑 𝐁𝐎𝐓 ☽₊⁺⋆* 🎀\n\n"
    "💎 *─────────────* 💎\n"
    "✨ *𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐐𝐮𝐚𝐥𝐢𝐭𝐲 𝐍𝐮𝐦𝐛𝐞𝐫𝐬* ✨\n"
    "🔥 *𝟐𝟒/𝟕 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞* 🔥\n"
    "💎 *─────────────* 💎\n\n"
    "👇 *𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐨𝐩𝐭𝐢𝐨𝐧 𝐛𝐞𝐥𝐨𝐰:*"
)

BTN_GET_NUMBER = "📞 𝐆𝐄𝐓 𝐍𝐔𝐌𝐁𝐄𝐑"
BTN_SUPPORT = "🆘 𝐒𝐔𝐏𝐏𝐎𝐑𝐓"
BTN_ADMIN = "⚙️ 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋"
BTN_MENU = "◀️ 𝐌𝐄𝐍𝐔"
BTN_BACK = "◀️ 𝐁𝐀𝐂𝐊"
BTN_CHANGE = "🔄 𝐂𝐇𝐀𝐍𝐆𝐄"
BTN_OTP = "🔑 𝐎𝐓𝐏"
BTN_VERIFY = "✅ 𝐕𝐄𝐑𝐈𝐅𝐘"
BTN_JOIN = "📢 𝐉𝐎𝐈𝐍"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in users:
        user_info = update.effective_user
        users[str(user_id)] = {"name": user_info.full_name, "username": user_info.username, "joined_date": str(update.message.date)}
        save_users(users)
    joined = await is_joined_all(context.application, user_id)
    if not joined and CHANNELS:
        keyboard = []
        for ch in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"{BTN_JOIN} {ch['username'].upper()}", url=ch["link"])])
        keyboard.append([InlineKeyboardButton(BTN_VERIFY, callback_data="verify")])
        await update.message.reply_text(
            "🔒 *𝐀𝐂𝐂𝐄𝐒𝐒 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃*\n\n👇 *𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐛𝐞𝐥𝐨𝐰:*\n\n✅ *𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐕𝐄𝐑𝐈𝐅𝐘.*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await show_main_menu(update, context)

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    joined = await is_joined_all(context.application, user_id)
    if joined:
        await query.edit_message_text("✅ *𝐕𝐄𝐑𝐈𝐅𝐈𝐄𝐃!*\n\n🎉 *𝐘𝐨𝐮 𝐜𝐚𝐧 𝐧𝐨𝐰 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐛𝐨𝐭.*", parse_mode="Markdown")
        await show_main_menu(update, context, from_callback=True)
    else:
        keyboard = []
        for ch in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"{BTN_JOIN} {ch['username'].upper()}", url=ch["link"])])
        keyboard.append([InlineKeyboardButton(BTN_VERIFY, callback_data="verify")])
        await query.edit_message_text(
            "❌ *𝐕𝐄𝐑𝐈𝐅𝐈𝐂𝐀𝐓𝐈𝐎𝐍 𝐅𝐀𝐈𝐋𝐄𝐃*\n\n⚠️ *𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐚𝐧𝐝 𝐭𝐫𝐲 𝐚𝐠𝐚𝐢𝐧.*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    keyboard = [
        [InlineKeyboardButton(BTN_GET_NUMBER, callback_data="get_number")],
        [InlineKeyboardButton(BTN_SUPPORT, callback_data="support")]
    ]
    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(BTN_ADMIN, callback_data="admin_panel")])
    if from_callback:
        await update.callback_query.message.edit_text(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_services_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    visible = settings.get("visible_services", {})
    visible_services = [s for s in SERVICES if visible.get(s, True)]
    if not visible_services:
        await query.edit_message_text("❌ No services available at the moment.", parse_mode="Markdown")
        return
    keyboard = []
    row = []
    for i, service in enumerate(visible_services):
        icon = SERVICE_ICONS.get(service, "📌")
        row.append(InlineKeyboardButton(f"{icon} {service}", callback_data=f"service_{service}"))
        if len(row) == 2 or i == len(visible_services)-1:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton(BTN_MENU, callback_data="main_menu")])
    await query.edit_message_text(
        "🔧 *SELECT SERVICE*\n\nChoose a service to get numbers:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_countries_for_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data.replace("service_", "")
    context.user_data['selected_service'] = service
    country_data = []
    for cname, svcs in countries.items():
        if service in svcs and svcs[service]:
            num_count = len(svcs[service])
            country_data.append((cname, num_count))
    if not country_data:
        await query.edit_message_text(f"❌ No numbers available for {service} yet.", parse_mode="Markdown")
        return
    keyboard = []
    for country, cnt in country_data:
        flag = get_flag(country)
        badge = f" ({cnt})" if cnt > 1 else ""
        keyboard.append([InlineKeyboardButton(f"{flag} {country}{badge}", callback_data=f"country_{country}")])
    keyboard.append([InlineKeyboardButton(BTN_BACK, callback_data="get_number")])
    await query.edit_message_text(f"{SERVICE_ICONS.get(service, '📌')} *{service}*\n\n🌍 *Select a country:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_numbers_for_service_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country_name = query.data.replace("country_", "")
    service = context.user_data.get('selected_service')
    if not service:
        await query.edit_message_text("❌ Please select a service first.", parse_mode="Markdown")
        return
    numbers_list = countries.get(country_name, {}).get(service, [])
    if not numbers_list:
        await query.edit_message_text(f"❌ No numbers available for {service} in {country_name}.", parse_mode="Markdown")
        return
    context.user_data['current_country'] = country_name
    context.user_data['current_service'] = service
    unique_mode = settings.get("unique_number_mode", True)
    taken_key = f"{country_name}|{service}"
    if unique_mode:
        taken = taken_numbers.get(taken_key, [])
        avail = [n for n in numbers_list if n not in taken]
    else:
        avail = numbers_list.copy()
    if not avail:
        await query.edit_message_text("⚠️ No more numbers available! Contact admin.", parse_mode="Markdown")
        return
    random.shuffle(avail)
    show = avail[:4]
    context.user_data['current_display_numbers'] = show
    flag = get_flag(country_name)
    numbers_text = ""
    for num in show:
        if not num.startswith('+'):
            num = '+' + num
        numbers_text += f"{flag} 📞 `{num}`\n"
    keyboard = [
        [InlineKeyboardButton(BTN_CHANGE, callback_data="change_number")],
        [InlineKeyboardButton(BTN_OTP, url=OTP_GROUP_LINK)],
        [InlineKeyboardButton(BTN_BACK, callback_data="get_number")]
    ]
    total_numbers = len(numbers_list)
    left = len(avail)
    text = f"{flag} *{country_name}* | {SERVICE_ICONS.get(service, '📌')} *{service}*\n\n📊 *Total:* {total_numbers}\n✅ *Left:* {left}\n\n👇 *Click any number to copy:*\n\n{numbers_text}\n⏰ *OTP will arrive soon.*"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def change_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country = context.user_data.get('current_country')
    service = context.user_data.get('current_service')
    if not country or not service:
        await query.edit_message_text("❌ Please select a country and service first.", parse_mode="Markdown")
        return
    numbers_list = countries.get(country, {}).get(service, [])
    if not numbers_list:
        await query.edit_message_text("❌ No numbers available.", parse_mode="Markdown")
        return
    unique_mode = settings.get("unique_number_mode", True)
    taken_key = f"{country}|{service}"
    if unique_mode:
        taken = taken_numbers.get(taken_key, [])
        avail = [n for n in numbers_list if n not in taken]
    else:
        avail = numbers_list.copy()
    if not avail:
        await query.edit_message_text("⚠️ No more numbers available! Contact admin.", parse_mode="Markdown")
        return
    random.shuffle(avail)
    show = avail[:4]
    context.user_data['current_display_numbers'] = show
    flag = get_flag(country)
    numbers_text = ""
    for num in show:
        if not num.startswith('+'):
            num = '+' + num
        numbers_text += f"{flag} 📞 `{num}`\n"
    keyboard = [
        [InlineKeyboardButton(BTN_CHANGE, callback_data="change_number")],
        [InlineKeyboardButton(BTN_OTP, url=OTP_GROUP_LINK)],
        [InlineKeyboardButton(BTN_BACK, callback_data="get_number")]
    ]
    total_numbers = len(numbers_list)
    left = len(avail)
    text = f"{flag} *{country}* | {SERVICE_ICONS.get(service, '📌')} *{service}*\n\n📊 *Total:* {total_numbers}\n✅ *Left:* {left}\n\n👇 *Click any number to copy:*\n\n{numbers_text}\n⏰ *OTP will arrive soon.*"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_copy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    number = query.data.replace("copy_", "")
    unique = settings.get("unique_number_mode", True)
    country = context.user_data.get('current_country')
    service = context.user_data.get('current_service')
    if unique and country and service:
        taken_key = f"{country}|{service}"
        if taken_key not in taken_numbers:
            taken_numbers[taken_key] = []
        if number not in taken_numbers[taken_key]:
            taken_numbers[taken_key].append(number)
            save_taken_numbers(taken_numbers)
    await query.answer(f"📋 Copied: {number}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ *𝐀𝐂𝐂𝐄𝐒𝐒 𝐃𝐄𝐍𝐈𝐄𝐃*", parse_mode="Markdown")
        return
    mode = "🟢 𝐄𝐍𝐀𝐁𝐋𝐄𝐃" if settings.get("unique_number_mode", True) else "🔴 𝐃𝐈𝐒𝐀𝐁𝐋𝐄𝐃"
    buttons = [
        ("📁 𝐀𝐃𝐃 𝐂𝐎𝐔𝐍𝐓𝐑𝐘", "add_country"),
        ("🗑 𝐃𝐄𝐋𝐄𝐓𝐄 𝐂𝐎𝐔𝐍𝐓𝐑𝐘", "del_country"),
        ("📜 𝐕𝐈𝐄𝐖 𝐂𝐎𝐔𝐍𝐓𝐑𝐈𝐄𝐒", "view_countries"),
        ("👥 𝐕𝐈𝐄𝐖 𝐔𝐒𝐄𝐑𝐒", "view_users"),
        ("📢 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓", "broadcast"),
        (f"🎯 𝐔𝐍𝐈𝐐𝐔𝐄 𝐌𝐎𝐃𝐄: {mode}", "toggle_unique_mode"),
        ("🔄 𝐑𝐄𝐒𝐄𝐓 𝐍𝐔𝐌𝐁𝐄𝐑𝐒", "reset_taken_numbers"),
        (BTN_MENU, "main_menu")
    ]
    keyboard = []
    for i in range(0, len(buttons), 2):
        row = []
        row.append(InlineKeyboardButton(buttons[i][0], callback_data=buttons[i][1]))
        if i+1 < len(buttons):
            row.append(InlineKeyboardButton(buttons[i+1][0], callback_data=buttons[i+1][1]))
        keyboard.append(row)
    await query.edit_message_text(
        f"🔧 *𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋*\n\n📌 *Unique Mode: {mode}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_country_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data['waiting_country'] = True
    await query.edit_message_text(
        "📁 *ADD COUNTRY/SERVICE*\n\nSend a .txt file with numbers.\n\n📌 *Filename format:* `Country_Service.txt`\nExample: `Bangladesh_WhatsApp.txt`\n\n📞 One number per line.\n\nSend the file now:",
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_country'):
        return
    if not is_admin(update.effective_user.id):
        return
    doc = update.message.document
    if not doc.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file", parse_mode="Markdown")
        return
    base = doc.file_name.replace('.txt', '')
    parts = base.split('_')
    if len(parts) != 2:
        await update.message.reply_text("❌ Invalid filename. Use format: `Country_Service.txt`", parse_mode="Markdown")
        return
    country_name = parts[0]
    service = parts[1]
    if service not in SERVICES:
        await update.message.reply_text(f"❌ Invalid service. Allowed: {', '.join(SERVICES)}", parse_mode="Markdown")
        return
    file = await doc.get_file()
    file_path = os.path.join(DATA_FOLDER, doc.file_name)
    await file.download_to_drive(file_path)
    with open(file_path, 'r') as f:
        new_numbers = [line.strip() for line in f if line.strip()]
    if not new_numbers:
        await update.message.reply_text("❌ No numbers found in file.", parse_mode="Markdown")
        return
    if country_name not in countries:
        countries[country_name] = {}
    if service not in countries[country_name]:
        countries[country_name][service] = []
    countries[country_name][service].extend(new_numbers)
    save_countries(countries)
    flag = get_flag(country_name)
    icon = SERVICE_ICONS.get(service, "📌")
    total = len(countries[country_name][service])
    await update.message.reply_text(
        f"✅ *ADDED!*\n\n{flag} {country_name} | {icon} {service}\n📞 Total numbers: {total} (+{len(new_numbers)})",
        parse_mode="Markdown"
    )
    context.user_data['waiting_country'] = False

async def delete_country_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    if not countries:
        await query.edit_message_text("📭 No countries to delete.", parse_mode="Markdown")
        return
    keyboard = []
    for country_name in countries.keys():
        flag = get_flag(country_name)
        keyboard.append([InlineKeyboardButton(f"🗑 {flag} {country_name}", callback_data=f"del_{country_name}")])
    keyboard.append([InlineKeyboardButton(BTN_BACK, callback_data="admin_panel")])
    await query.edit_message_text(
        "🗑 *DELETE COUNTRY*\n\nSelect a country to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def delete_country_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    country_name = query.data.replace("del_", "")
    if country_name in countries:
        del countries[country_name]
        save_countries(countries)
        await query.edit_message_text(f"✅ *{country_name} deleted successfully.*", parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ Country not found.", parse_mode="Markdown")
    await admin_panel(update, context)

async def view_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    if not countries:
        await query.edit_message_text("📭 No countries added yet.", parse_mode="Markdown")
        return
    text = "📜 *AVAILABLE COUNTRIES & SERVICES*\n\n"
    for country, services in countries.items():
        flag = get_flag(country)
        text += f"{flag} *{country}*\n"
        for serv, nums in services.items():
            icon = SERVICE_ICONS.get(serv, "📌")
            text += f"   {icon} {serv}: {len(nums)} numbers\n"
        text += "\n"
    keyboard = [[InlineKeyboardButton(BTN_BACK, callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    if not users:
        await query.edit_message_text("📭 No users found.", parse_mode="Markdown")
        return
    text = f"👥 *TOTAL USERS:* {len(users)}\n\n"
    for i, (uid, data) in enumerate(list(users.items())[:20]):
        text += f"{i+1}. {data.get('name', 'Unknown')}\n   🆔 `{uid}`\n"
        if data.get('username'):
            text += f"   @{data['username']}\n"
        text += "\n"
    keyboard = [[InlineKeyboardButton(BTN_BACK, callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data['waiting_broadcast'] = True
    await query.edit_message_text("📢 *BROADCAST*\n\nSend me the message to broadcast.", parse_mode="Markdown")

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_broadcast'):
        return
    if not is_admin(update.effective_user.id):
        return
    users_list = load_users()
    if not users_list:
        await update.message.reply_text("❌ No users found!", parse_mode="Markdown")
        context.user_data['waiting_broadcast'] = False
        return
    success, fail = 0, 0
    for uid in users_list:
        try:
            await context.bot.send_message(chat_id=int(uid), text=update.message.text)
            success += 1
        except:
            fail += 1
    await update.message.reply_text(f"✅ *BROADCAST COMPLETED*\n\n📨 Sent: {success}\n❌ Failed: {fail}", parse_mode="Markdown")
    context.user_data['waiting_broadcast'] = False

async def toggle_unique_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    settings["unique_number_mode"] = not settings.get("unique_number_mode", True)
    save_settings(settings)
    await admin_panel(update, context)

async def reset_taken_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    global taken_numbers
    taken_numbers = {}
    save_taken_numbers(taken_numbers)
    await query.edit_message_text("✅ *All taken numbers reset!*", parse_mode="Markdown")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👨‍💻 𝐀𝐃𝐌𝐈𝐍 𝟏", url="https://t.me/fib_helpe")],
        [InlineKeyboardButton("👨‍💻 𝐀𝐃𝐌𝐈𝐍 𝟐", url="https://t.me/mashrafitech")],
        [InlineKeyboardButton(BTN_MENU, callback_data="main_menu")],
    ]
    await query.edit_message_text("🆘 *SUPPORT*\n\n📌 Click to contact admin:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    if d == "verify":
        await verify(update, context)
    elif d == "get_number":
        await show_services_list(update, context)
    elif d.startswith("service_"):
        await show_countries_for_service(update, context)
    elif d.startswith("country_"):
        await show_numbers_for_service_country(update, context)
    elif d == "change_number":
        await change_number(update, context)
    elif d.startswith("copy_"):
        await handle_copy(update, context)
    elif d == "support":
        await support(update, context)
    elif d == "admin_panel":
        await admin_panel(update, context)
    elif d == "add_country":
        await add_country_start(update, context)
    elif d == "del_country":
        await delete_country_start(update, context)
    elif d.startswith("del_"):
        await delete_country_confirm(update, context)
    elif d == "view_countries":
        await view_countries(update, context)
    elif d == "view_users":
        await view_users(update, context)
    elif d == "broadcast":
        await broadcast_start(update, context)
    elif d == "toggle_unique_mode":
        await toggle_unique_mode(update, context)
    elif d == "reset_taken_numbers":
        await reset_taken_numbers(update, context)
    elif d == "main_menu":
        await show_main_menu(update, context, from_callback=True)
    else:
        await q.edit_message_text("❌ Not available", parse_mode="Markdown")

def main():
    print("🤖 Bot starting...")
    app = Application.builder().token(BOT_TOKEN).connect_timeout(30).read_timeout(30).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast))
    app.run_polling()

if __name__ == "__main__":
    main()