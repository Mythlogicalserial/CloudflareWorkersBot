import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = '7795554263:AAE7yje0MLNqiruDXWYjHx-xkgtqZGt5ByM'  # Replace with your actual token

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Format UTC datetime string to readable format
def format_time(utc_str):
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt = dt.astimezone()  # local timezone
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return "Unknown Time"

# 📍 /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to InstaStory Bot!*\n\n"
        "📥 Use `/story <username>` to download Instagram stories.\n"
        "📥 Or just send any Instagram post/reel link to get media.\n\n"
        "🔍 Example: `/story natgeo`",
        parse_mode="Markdown"
    )

# 📍 /story command
async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text(
            "⚠️ Please provide exactly *one* Instagram username.\n\n"
            "✅ Example: `/story virat.kohli`",
            parse_mode="Markdown"
        )
        return

    username = context.args[0].strip().lower()
    api_url = f"https://api.yabes-desu.workers.dev/download/instagram/stories?username={username}"

    try:
        response = requests.get(api_url)
        data = response.json()
        logger.info("📦 Story Response: %s", data)

        if not data.get("success"):
            await update.message.reply_text(f"❌ Failed to fetch stories: {data.get('message', 'Unknown error.')}")
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
            f"🕒 *Account Created:* {format_time(user.get('created_at'))}\n"
            f"🔄 *Last Updated:* {format_time(user.get('updated_at'))}"
        )
        await update.message.reply_text(profile_text, parse_mode="Markdown", disable_web_page_preview=True)

        if not stories:
            await update.message.reply_text(f"ℹ️ No active stories found for @{username}.")
            return

        for i, story in enumerate(stories, 1):
            media_url = story.get("download")
            media_type = story.get("type")
            try:
                if media_type == "video":
                    await update.message.reply_video(video=media_url)
                elif media_type == "photo":
                    await update.message.reply_photo(photo=media_url)
                else:
                    await update.message.reply_text(f"📎 Story {i} (Unknown Type): {media_url}")
            except Exception as e:
                logger.warning("⚠️ Failed to send media. Sending link instead: %s", str(e))
                await update.message.reply_text(f"📎 Link to Story {i}: {media_url}")

    except Exception as e:
        logger.error("❌ Error fetching story: %s", str(e))
        await update.message.reply_text("❌ Error occurred while fetching story. Try again later.")

# 📥 Handle Reels/Posts automatically
async def handle_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text(f"❌ Failed to fetch post: {data.get('message', 'Unknown error.')}")
            return

        d = data["data"]
        media_urls = d.get("url", [])
        caption = d.get("caption", "No caption.")
        username = d.get("username", "Unknown")
        is_video = d.get("isVideo", False)

        text_info = (
            f"🔗 *Original Post:* [Open on Instagram]({post_url})\n"
            f"👤 *Posted by:* {username}\n"
            f"🕒 *Posted on:* {d.get('created_at', 'Unknown Time')}\n\n"
            f"🎬 *Caption:*\n```\n{caption}\n```"
        )
        await update.message.reply_text(text_info, parse_mode="Markdown", disable_web_page_preview=True)

        for media_url in media_urls:
            try:
                if is_video:
                    await update.message.reply_video(video=media_url)
                else:
                    await update.message.reply_photo(photo=media_url)
            except:
                await update.message.reply_text(f"📎 Media: {media_url}")

    except Exception as e:
        logger.error("❌ Error fetching reel/post: %s", str(e))
        await update.message.reply_text("❌ Error occurred while fetching post.")

# 🚀 Main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_reel))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
