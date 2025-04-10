from telebot import TeleBot, types
import json
import os

bot = TeleBot("7740611922:AAHcawCFoYGgHgd5ZjeyuZuxVGaog2l2qBk", parse_mode="Markdown")

admin_id = 7712850427
users_file = "users.json"
seen_vip_file = "seen_vip_users.json"
msg_map_file = "msg_map.json"

# Ensure required files exist
for f in [users_file, seen_vip_file, msg_map_file]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({}, file) if "msg_map" in f else json.dump([], file)

def save_user(user_id):
    with open(users_file, "r") as f:
        users = json.load(f)
    if str(user_id) not in users:
        users.append(str(user_id))
        with open(users_file, "w") as f:
            json.dump(users, f)

def has_seen_vip(uid):
    with open(seen_vip_file, "r") as f:
        seen = json.load(f)
    return str(uid) in seen

def mark_seen_vip(uid):
    with open(seen_vip_file, "r") as f:
        seen = json.load(f)
    if str(uid) not in seen:
        seen.append(str(uid))
        with open(seen_vip_file, "w") as f:
            json.dump(seen, f)

def log_message_link(forwarded_msg_id, user_id):
    with open(msg_map_file, "r") as f:
        msg_map = json.load(f)
    msg_map[str(forwarded_msg_id)] = user_id
    with open(msg_map_file, "w") as f:
        json.dump(msg_map, f)

def get_original_user(reply_msg_id):
    with open(msg_map_file, "r") as f:
        msg_map = json.load(f)
    return msg_map.get(str(reply_msg_id))

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != admin_id:
        return
    try:
        text = message.text.split(" ", 1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Please provide a message to send.\nUsage: `/broadcast Your message here`", parse_mode="Markdown")
        return
    with open(users_file, "r") as f:
        users = json.load(f)
    sent_count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 *Broadcast Message:*\n\n{text}", parse_mode="Markdown")
            sent_count += 1
        except:
            continue
    bot.reply_to(message, f"✅ Broadcast sent to {sent_count} users.")

@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in ['magkano', 'vip', 'pano bumili', 'buy vip']))
def send_vip_offer(message):
    uid = message.from_user.id
    if has_seen_vip(uid):
        return
    mark_seen_vip(uid)
    caption = "🔥 Buy PINAY ATABS VIP access for only ₱499!\n\n🖼️ Exclusive TG channel content, full set access 👀"
    markup = types.InlineKeyboardMarkup()
    gcash_btn = types.InlineKeyboardButton("🟡 GCash via Scan2Pay", url="https://t.me/Scan2PayBot?startapp=UQApinayatabsVIP499")
    ton_btn = types.InlineKeyboardButton("🔵 Pay via TON", url="https://app.tonkeeper.com/transfer/UQAwroBrBTSzzVYx_IXpR-R_KJ_mZQgmT7uNsUZdJ5MM68ep")
    markup.add(gcash_btn)
    markup.add(ton_btn)
    with open("499.png", 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup)

@bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id == admin_id)
def handle_admin_reply(message):
    reply_msg_id = message.reply_to_message.message_id
    target_user = get_original_user(reply_msg_id)
    if target_user:
        try:
            bot.send_message(target_user, message.text)
            bot.reply_to(message, "✅ Sent to user.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send: {e}")
    else:
        bot.reply_to(message, "⚠️ Cannot find the original user for this reply.")

@bot.message_handler(func=lambda message: True)
def track_users(message):
    save_user(message.from_user.id)

    if message.from_user.id != admin_id:
        forwarded = bot.forward_message(admin_id, message.chat.id, message.message_id)
        log_message_link(forwarded.message_id, message.from_user.id)

        # Optional logging
        with open("log.json", "a", encoding="utf-8") as log_file:
            log_file.write(f"{message.from_user.id} - {message.text}\n")

bot.polling()
