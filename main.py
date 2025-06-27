import os
from telebot import TeleBot, types
import json
import logging

# Security: Use environment variables for sensitive data
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")
if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID environment variable is required!")

# Initialize bot
bot = TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
USERS_FILE = "users.json"
SEEN_VIP_FILE = "seen_vip_users.json"
MSG_MAP_FILE = "msg_map.json"
LOG_FILE = "bot_log.txt"

def ensure_files_exist():
    """Ensure all required JSON files exist with proper structure"""
    files_config = {
        USERS_FILE: [],
        SEEN_VIP_FILE: [],
        MSG_MAP_FILE: {}
    }
    
    for filepath, default_content in files_config.items():
        if not os.path.exists(filepath):
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, indent=2)
                logger.info(f"Created {filepath}")
            except Exception as e:
                logger.error(f"Failed to create {filepath}: {e}")

def safe_json_operation(filepath, operation, default_value=None):
    """Safely perform JSON file operations with error handling"""
    try:
        if operation == "read":
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        elif operation == "write":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_value, f, indent=2, ensure_ascii=False)
            return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"JSON operation failed for {filepath}: {e}")
        return [] if filepath != MSG_MAP_FILE else {}
    except Exception as e:
        logger.error(f"Unexpected error with {filepath}: {e}")
        return [] if filepath != MSG_MAP_FILE else {}

def save_user(user_id):
    """Save user ID to users list"""
    users = safe_json_operation(USERS_FILE, "read") or []
    user_str = str(user_id)
    
    if user_str not in users:
        users.append(user_str)
        safe_json_operation(USERS_FILE, "write", users)
        logger.info(f"New user saved: {user_id}")

def has_seen_vip(user_id):
    """Check if user has already seen VIP offer"""
    seen_users = safe_json_operation(SEEN_VIP_FILE, "read") or []
    return str(user_id) in seen_users

def mark_seen_vip(user_id):
    """Mark user as having seen VIP offer"""
    seen_users = safe_json_operation(SEEN_VIP_FILE, "read") or []
    user_str = str(user_id)
    
    if user_str not in seen_users:
        seen_users.append(user_str)
        safe_json_operation(SEEN_VIP_FILE, "write", seen_users)

def log_message_link(forwarded_msg_id, user_id):
    """Link forwarded message ID to original user"""
    msg_map = safe_json_operation(MSG_MAP_FILE, "read") or {}
    msg_map[str(forwarded_msg_id)] = user_id
    safe_json_operation(MSG_MAP_FILE, "write", msg_map)

def get_original_user(reply_msg_id):
    """Get original user ID from forwarded message ID"""
    msg_map = safe_json_operation(MSG_MAP_FILE, "read") or {}
    return msg_map.get(str(reply_msg_id))

def log_user_activity(user_id, content):
    """Log user activity to file"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id} - {content}\n")
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    welcome_text = """
🌟 *Welcome to PINAY ATABS Bot!* 🌟

😘 For *content selling only*, no random chats or chika pls! 😌💋

📱 Type keywords like 'VIP', 'magkano', or 'pano bumili' to get pricing info!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """Handle broadcast command - Admin only"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    try:
        # Extract message text after command
        text = message.text.split(" ", 1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Please provide a message to broadcast.\n\n*Usage:* `/broadcast Your message here`")
        return
    
    users = safe_json_operation(USERS_FILE, "read") or []
    sent_count = 0
    failed_count = 0
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 *Broadcast Message:*\n\n{text}")
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to send broadcast to {user_id}: {e}")
    
    result_msg = f"✅ Broadcast Results:\n• Sent: {sent_count} users\n• Failed: {failed_count} users"
    bot.reply_to(message, result_msg)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Show bot statistics - Admin only"""
    if message.from_user.id != ADMIN_ID:
        return
    
    users = safe_json_operation(USERS_FILE, "read") or []
    seen_vip = safe_json_operation(SEEN_VIP_FILE, "read") or []
    
    stats_text = f"""
📊 *Bot Statistics:*

👥 Total Users: {len(users)}
👀 Seen VIP Offer: {len(seen_vip)}
🆕 New Potential: {len(users) - len(seen_vip)}
    """
    bot.reply_to(message, stats_text)

@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in ['magkano', 'vip', 'pano bumili', 'buy vip', 'price', 'presyo']))
def send_vip_offer(message):
    """Send VIP offer when triggered by keywords"""
    user_id = message.from_user.id
    
    # Check if user already saw VIP offer
    if has_seen_vip(user_id):
        bot.reply_to(message, "You've already received our VIP offer! Check your previous messages. 😊")
        return
    
    # Mark user as having seen VIP offer
    mark_seen_vip(user_id)
    
    # VIP offer message
    caption = """
🔥 *Buy PINAY ATABS VIP Access for only ₱499!*

🖼️ *What you get:*
• Exclusive TG channel content
• Full set access 👀
• Premium quality content
• Instant access after payment

💰 *Choose your payment method:*
    """
    
    # Create payment buttons
    markup = types.InlineKeyboardMarkup(row_width=1)
    gcash_btn = types.InlineKeyboardButton(
        "🟡 GCash / Maya Payment", 
        url="https://t.me/PhScan2Pabot?startapp=Gcash_Maya"
    )
    crypto_btn = types.InlineKeyboardButton(
        "🔵 Crypto Payment", 
        url="https://t.me/Cryptopayphbot?startapp=Crypto"
    )
    markup.add(gcash_btn, crypto_btn)
    
    # Try to send with photo, fallback to text if no photo
    try:
        if os.path.exists("vip_offer.png"):
            with open("vip_offer.png", 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        logger.error(f"Failed to send VIP offer: {e}")
        bot.send_message(message.chat.id, caption, reply_markup=markup)

@bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id == ADMIN_ID)
def handle_admin_reply(message):
    """Handle admin replies to forwarded messages"""
    reply_msg_id = message.reply_to_message.message_id
    target_user = get_original_user(reply_msg_id)
    
    if not target_user:
        bot.reply_to(message, "⚠️ Cannot find the original user for this reply.")
        return
    
    try:
        # Handle different message types
        if message.text:
            bot.send_message(target_user, message.text)
        elif message.photo:
            bot.send_photo(target_user, message.photo[-1].file_id, caption=message.caption)
        elif message.video:
            bot.send_video(target_user, message.video.file_id, caption=message.caption)
        elif message.voice:
            bot.send_voice(target_user, message.voice.file_id)
        elif message.document:
            bot.send_document(target_user, message.document.file_id, caption=message.caption)
        elif message.sticker:
            bot.send_sticker(target_user, message.sticker.file_id)
        elif message.animation:
            bot.send_animation(target_user, message.animation.file_id, caption=message.caption)
        elif message.video_note:
            bot.send_video_note(target_user, message.video_note.file_id)
        else:
            bot.reply_to(message, "⚠️ Unsupported media type.")
            return
        
        bot.reply_to(message, "✅ Message sent successfully!")
        
    except Exception as e:
        error_msg = f"❌ Failed to send message: {str(e)}"
        bot.reply_to(message, error_msg)
        logger.error(f"Admin reply failed: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages - track users and forward to admin"""
    user_id = message.from_user.id
    
    # Save user to database
    save_user(user_id)
    
    # Don't forward admin's own messages
    if user_id == ADMIN_ID:
        return
    
    # Forward message to admin
    try:
        forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        log_message_link(forwarded.message_id, user_id)
    except Exception as e:
        logger.error(f"Failed to forward message from {user_id}: {e}")
    
    # Log user activity
    if message.text:
        log_content = message.text[:100] + "..." if len(message.text) > 100 else message.text
    elif message.photo:
        log_content = "[PHOTO]"
    elif message.video:
        log_content = "[VIDEO]"
    elif message.voice:
        log_content = "[VOICE]"
    elif message.document:
        log_content = "[DOCUMENT]"
    elif message.sticker:
        log_content = "[STICKER]"
    elif message.animation:
        log_content = "[GIF]"
    elif message.video_note:
        log_content = "[VIDEO NOTE]"
    else:
        log_content = "[UNKNOWN MEDIA]"
    
    log_user_activity(user_id, log_content)

def main():
    """Main function to start the bot"""
    ensure_files_exist()
    logger.info("Bot starting...")
    
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")

if __name__ == "__main__":
    main()
