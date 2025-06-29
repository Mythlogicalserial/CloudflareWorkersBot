import logging
import requests
from datetime import datetime
from telegram import Update, Bot, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

BOT_TOKEN = '7795554263:AAE7yje0MLNqiruDXWYjHx-xkgtqZGt5ByM'  # Replace with your actual token

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Format datetime
def format_time(utc_str):
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt = dt.astimezone()
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return "Unknown Time"

# /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 *Welcome to InstaStory Bot!*\n\n"
        "📥 Use `/story <username>` to download Instagram stories.\n"
        "📥 Or send any Instagram post/reel link to get media.\n\n"
        "🔍 Example: `/story natgeo`",
        parse_mode=ParseMode.MARKDOWN
    )

# /story command
def story(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text(
            "⚠️ Please provide exactly *one* Instagram username.\n\n"
            "✅ Example: `/story virat.kohli`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    username = context.args[0].strip().lower()
    api_url = f"https://api.yabes-desu.workers.dev/download/instagram/stories?username={username}"

    try:
        response = requests.get(api_url)
        data = response.json()
        logger.info("📦 Story Response: %s", data)

        if not data.get("success"):
            update.message.reply_text(f"❌ Failed: {data.get('message', 'Unknown error.')}")
            return

        user = data["data"]["user"]
        stories = data["data"].get("stories", [])

        profile_text = (
            f"🔗 *Profile Link:* [Click Here]({user['profile']})\n"
            f"📌 *Bio:* {user.get('bio', 'No bio')}\n"
            f"🖼️ *Posts:* {user.get('posts', 'N/A')}\n"
            f"👥 *Followers:* {user.get('followers')} | *Following:* {user.get('following')}\n"
            f"{'✅ Verified' if user.get('is_verified') else '❌ Not Verified'} | "
            f"{'🔒 Private' if user.get('is_private') else '🌍 Public'}\n"
            f"🕒 *Created:* {format_time(user.get('created_at'))}\n"
            f"🔄 *Updated:* {format_time(user.get('updated_at'))}"
        )
        update.message.reply_text(profile_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        if not stories:
            update.message.reply_text(f"ℹ️ No active stories for @{username}.")
            return

        for i, story in enumerate(stories, 1):
            media_url = story.get("download")
            media_type = story.get("type")
            try:
                if media_type == "video":
                    update.message.reply_video(video=media_url)
                elif media_type == "photo":
                    update.message.reply_photo(photo=media_url)
                else:
                    update.message.reply_text(f"📎 Story {i}: {media_url}")
            except Exception as e:
                logger.warning("⚠️ Media send failed: %s", str(e))
                update.message.reply_text(f"📎 Story {i}: {media_url}")

    except Exception as e:
        logger.error("❌ Error fetching story: %s", str(e))
        update.message.reply_text("❌ Error occurred while fetching story.")

# Handles reels and posts
def handle_reel(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if "instagram.com" not in text or not any(x in text for x in ["/reel/", "/p/", "/tv/"]):
        return

    post_url = text.split("?")[0]
    api_url = f"https://api.yabes-desu.workers.dev/download/instagram/v2?url={post_url}"

    try:
        response = requests.get(api_url)
        data = response.json()
        logger.info("📦 Post Response: %s", data)

        if not data.get("success"):
            update.message.reply_text(f"❌ Failed: {data.get('message', 'Unknown error.')}")
            return

        d = data["data"]
        media_urls = d.get("url", [])
        caption = d.get("caption", "No caption.")
        username = d.get("username", "Unknown")
        is_video = d.get("isVideo", False)

        text_info = (
            f"🔗 *Post:* [Instagram]({post_url})\n"
            f"👤 *By:* {username}\n"
            f"🕒 *Date:* {d.get('created_at', 'Unknown')}\n\n"
            f"🎬 *Caption:*\n```\n{caption}\n```"
        )
        update.message.reply_text(text_info, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        for media_url in media_urls:
            try:
                if is_video:
                    update.message.reply_video(video=media_url)
                else:
                    update.message.reply_photo(photo=media_url)
            except:
                update.message.reply_text(f"📎 Media: {media_url}")

    except Exception as e:
        logger.error("❌ Error: %s", str(e))
        update.message.reply_text("❌ Error while fetching post.")

# Main function
def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("story", story))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_reel))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
