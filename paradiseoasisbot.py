from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import uuid

TOKEN = "8389709391:AAHaDABvO7ggEEeE2zsrBdyE7Q0sv1tBFl4"
ADMIN_CHAT_ID = -1003510243073

# ================= STORAGE =================
ORDERS = {}
USER_TO_ORDER = {}
ADMIN_ACTIVE = {}
LIFETIME_SALES = 0.0

# ================= ENTRY =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "🌴 Paradise Oasis Concierge 🌴\n\n"
        "Travel smarter. Not harder.\n"
        "Premium routes. Better prices. Same providers.\n\n"
        "👇 Tap a service to get started 👇"
    )
    keyboard = [
        [InlineKeyboardButton("✈️ Flights", callback_data="svc_flights")],
        [InlineKeyboardButton("🏨 Hotels", callback_data="svc_hotels")],
        [InlineKeyboardButton("🏡 Airbnb", callback_data="svc_airbnb")],
        [InlineKeyboardButton("🚗 Car Rentals", callback_data="svc_cars")],
        [InlineKeyboardButton("🚆 Amtrak", callback_data="svc_amtrak")],
        [InlineKeyboardButton("🎢 Theme Parks", callback_data="svc_parks")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= SERVICE SELECT =================
async def service_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    service = q.data.replace("svc_", "")
    context.user_data["service"] = service

    if service == "flights":
        await flights_start(q, context)
    elif service == "hotels":
        await hotels_start(q, context)
    elif service == "airbnb":
        await airbnb_start(q, context)
    elif service == "cars":
        await cars_start(q, context)
    elif service == "amtrak":
        await amtrak_start(q, context)
    elif service == "parks":
        await parks_start(q, context)

# ================= FLIGHTS =================
async def flights_start(q, context):
    context.user_data["step"] = "flight_type"
    text = (
        "✈️ Flights\n\n"
        "• Same airlines, better prices\n"
        "• $300 minimum applies\n"
        "• Discount reflects at checkout\n\n"
        "👇 Choose trip type 👇"
    )
    keyboard = [[
        InlineKeyboardButton("➡️ One-Way", callback_data="flight_oneway"),
        InlineKeyboardButton("🔁 Round-Trip", callback_data="flight_roundtrip"),
    ]]
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def flight_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["trip_type"] = q.data
    context.user_data["step"] = "passengers"
    keyboard = [[
        InlineKeyboardButton("1", callback_data="pax_1"),
        InlineKeyboardButton("2", callback_data="pax_2"),
        InlineKeyboardButton("3", callback_data="pax_3"),
        InlineKeyboardButton("4+", callback_data="pax_4"),
    ]]
    await q.message.reply_text("👥 Number of passengers:", reply_markup=InlineKeyboardMarkup(keyboard))

async def passenger_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["passengers"] = q.data.replace("pax_", "")
    context.user_data["step"] = "depart_city"
    await q.message.reply_text("🛫 Departure city:")

# ================= OTHER SERVICES =================
async def hotels_start(q, context):
    context.user_data["step"] = "hotel_info"
    await q.message.reply_text(
        "🏨 Hotels\n\n"
        "• Major hotels worldwide\n"
        "• $300 minimum applies\n"
        "• Discount reflects at checkout\n\n"
        "📍 Send hotel name, dates, or screenshot."
    )

async def airbnb_start(q, context):
    context.user_data["step"] = "airbnb_info"
    await q.message.reply_text(
        "🏡 Airbnb\n\n"
        "• $500 minimum applies\n"
        "• Discount reflects at checkout\n\n"
        "📸 Send listing link or screenshot."
    )

async def cars_start(q, context):
    context.user_data["step"] = "car_provider"
    keyboard = [[
        InlineKeyboardButton("🚗 Turo", callback_data="car_turo"),
        InlineKeyboardButton("🚘 Budget", callback_data="car_budget"),
        InlineKeyboardButton("🚙 Avis", callback_data="car_avis"),
    ]]
    await q.message.reply_text(
        "🚗 Car Rentals\n\n"
        "• $500 minimum applies\n"
        "• Discount reflects at checkout\n"
        "• Budget/Avis require your card for deposit\n\n"
        "👇 Choose provider 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def car_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["provider"] = q.data
    context.user_data["step"] = "car_details"
    await q.message.reply_text("📍 Send rental details or screenshot.")

async def amtrak_start(q, context):
    context.user_data["step"] = "amtrak_info"
    await q.message.reply_text("🚆 Amtrak\n\n📍 Send route and dates.")

async def parks_start(q, context):
    context.user_data["step"] = "parks_info"
    await q.message.reply_text("🎢 Theme Parks\n\n📍 Send park name and visit date.")

# ================= TEXT ROUTER =================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    # ADMIN CHAT
    if uid in ADMIN_ACTIVE:
        oid = ADMIN_ACTIVE[uid]
        order = ORDERS.get(oid)
        if order and order["status"] == "OPEN":
            await context.bot.send_message(order["user_id"], f"💬 Agent: {text}")
        return

    # CUSTOMER CHAT
    if uid in USER_TO_ORDER:
        oid = USER_TO_ORDER[uid]
        order = ORDERS.get(oid)
        if order and order["status"] == "OPEN" and order["admin"]:
            await context.bot.send_message(order["admin"], f"💬 Customer: {text}")
        return

    step = context.user_data.get("step")

    if step in ["hotel_info","airbnb_info","car_details","amtrak_info","parks_info","passenger_info"]:
        context.user_data["details"] = text
        await finalize_order(update, context)
        return

# ================= PHOTO ROUTER =================
async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    photo = update.message.photo[-1]

    # ADMIN SENDING
    if uid in ADMIN_ACTIVE:
        oid = ADMIN_ACTIVE[uid]
        order = ORDERS.get(oid)
        if order and order["status"] == "OPEN":
            await context.bot.send_photo(order["user_id"], photo.file_id)
        return

    # CUSTOMER SENDING (THIS FIXES SCREENSHOT ISSUE)
    if uid in USER_TO_ORDER:
        oid = USER_TO_ORDER[uid]
        order = ORDERS.get(oid)
        if order and order["status"] == "OPEN" and order["admin"]:
            await context.bot.send_photo(order["admin"], photo.file_id)
        return

    # If no active order → create one
    step = context.user_data.get("step")
    if step in ["hotel_info","airbnb_info","car_details","amtrak_info","parks_info"]:
        context.user_data["details"] = "Screenshot attached"
        await finalize_order(update, context)

# ================= FINALIZE =================
async def finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oid = str(uuid.uuid4())[:8]

    ORDERS[oid] = {
        "user_id": update.message.from_user.id,
        "admin": None,
        "status": "OPEN",
        "price": 0.0,
    }

    USER_TO_ORDER[update.message.from_user.id] = oid

    keyboard = [
        [InlineKeyboardButton("👤 Claim", callback_data=f"claim_{oid}")],
        [
            InlineKeyboardButton("✅ Paid", callback_data=f"paid_{oid}"),
            InlineKeyboardButton("❌ Unpaid", callback_data=f"unpaid_{oid}"),
            InlineKeyboardButton("🔒 Close", callback_data=f"close_{oid}")
        ]
    ]

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"🆕 NEW ORDER #{oid}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Connecting you to an agent…")
    context.user_data.clear()

# ================= ADMIN ACTIONS =================
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, oid = q.data.split("_")
    order = ORDERS.get(oid)
    if not order:
        return

    if action == "claim":
        order["admin"] = q.from_user.id
        ADMIN_ACTIVE[q.from_user.id] = oid
        await context.bot.send_message(order["user_id"], "👤 An agent has joined the chat.")

    elif action == "close":
        order["status"] = "CLOSED"

        # CLEANUP FIX
        USER_TO_ORDER.pop(order["user_id"], None)
        ADMIN_ACTIVE.pop(order["admin"], None)

        await context.bot.send_message(order["user_id"], "🔒 Order closed.")
        await q.message.reply_text(f"🔒 Order {oid} closed")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(service_select, pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(flight_type, pattern="^flight_(oneway|roundtrip)$"))
    app.add_handler(CallbackQueryHandler(passenger_count, pattern="^pax_"))
    app.add_handler(CallbackQueryHandler(car_provider, pattern="^car_"))
    app.add_handler(CallbackQueryHandler(admin_actions))
    app.add_handler(MessageHandler(filters.PHOTO, photo_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("✅ Paradise Oasis Concierge running")
    app.run_polling()

if __name__ == "__main__":
    main()
