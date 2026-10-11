
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))


async def is_admin(update: Update) -> bool:
    """Allow commands only from the configured Telegram user."""
    user = update.effective_user

    if user is None or user.id != ADMIN_ID or ADMIN_ID == 0:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Access denied. Configure the correct admin ID."
            )
        return False

    return True


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "Welcome to SocialPilot AI!\n\n"
        "Commands:\n"
        "/draft Your post text - create a draft\n"
        "/preview - preview your draft\n"
        "/publish - publish to your test channel\n"
        "/cancel - discard your draft"
    )


async def create_draft(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update):
        return

    post_text = update.effective_message.text.partition(" ")[2].strip()

    if not post_text:
        await update.effective_message.reply_text(
            "Usage:\n/draft Write your social media post here"
        )
        return

    user_id = update.effective_user.id
    context.application.bot_data.setdefault("drafts", {})[user_id] = post_text

    await update.effective_message.reply_text(
        "Draft saved in memory.\n\n"
        f"{post_text}\n\n"
        "Use /preview to review it or /publish to publish it."
    )


async def preview(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update):
        return

    drafts = context.application.bot_data.get("drafts", {})
    post_text = drafts.get(update.effective_user.id)

    if not post_text:
        await update.effective_message.reply_text(
            "No draft found. Create one with /draft."
        )
        return

    await update.effective_message.reply_text(
        f"POST PREVIEW\n\n{post_text}\n\n"
        "Use /publish to publish or /cancel to discard."
    )


async def publish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update):
        return

    if not CHANNEL_ID:
        await update.effective_message.reply_text(
            "Configure TELEGRAM_CHANNEL_ID in .env first."
        )
        return

    drafts = context.application.bot_data.get("drafts", {})
    user_id = update.effective_user.id
    post_text = drafts.get(user_id)

    if not post_text:
        await update.effective_message.reply_text(
            "No draft found. Create one with /draft."
        )
        return

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_text,
        )
    except Exception:
        await update.effective_message.reply_text(
            "Publishing failed. Check the channel ID, bot permissions, "
            "and Telegram error logs, then try again."
        )
        raise

    del drafts[user_id]

    await update.effective_message.reply_text(
        "Post published successfully to your configured channel."
    )


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update):
        return

    drafts = context.application.bot_data.get("drafts", {})
    drafts.pop(update.effective_user.id, None)

    await update.effective_message.reply_text("Draft discarded.")

async def myid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    await update.effective_message.reply_text(
        f"Your Telegram user ID is: {user.id}"
    )
    
def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in .env")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draft", create_draft))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("publish", publish))
    application.add_handler(CommandHandler("cancel", cancel))

    print("SocialPilot AI bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
