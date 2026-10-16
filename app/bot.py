
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from ai_service import generate_social_post
from database import (
    init_db,
    create_post,
    get_post,
    get_latest_draft,
    get_recent_posts,
    update_status,
    start_publishing,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
ADMIN_ID_VALUE = os.getenv("TELEGRAM_ADMIN_ID", "").strip()

try:
    ADMIN_ID = int(ADMIN_ID_VALUE) if ADMIN_ID_VALUE else None
except ValueError:
    ADMIN_ID = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# ADMIN ACCESS
# --------------------------------------------------

async def is_admin(update: Update) -> bool:
    user = update.effective_user
    return (
        user is not None
        and ADMIN_ID is not None
        and user.id == ADMIN_ID
    )


async def deny_access(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text(
            "⛔ You are not authorized to use this bot."
        )


# --------------------------------------------------
# DRAFT APPROVAL BUTTONS
# --------------------------------------------------

def approval_keyboard(post_id: int):
    keyboard = [[
        InlineKeyboardButton(
            "✅ Approve & Publish",
            callback_data=f"approve:{post_id}",
        ),
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject:{post_id}",
        ),
    ]]
    return InlineKeyboardMarkup(keyboard)


async def show_post(update: Update, post_id: int, content: str):
    await update.effective_message.reply_text(
        f"📝 POST #{post_id}\n\n"
        f"{content}\n\n"
        "Review your draft before publishing.",
        reply_markup=approval_keyboard(post_id),
    )


# --------------------------------------------------
# START AND HELP
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    await update.effective_message.reply_text(
        "👋 Welcome to SocialPilot AI!\n\n"
        "COMMANDS\n\n"
        "/generate <topic> - Generate an AI post\n"
        "/draft <text> - Save a manual draft\n"
        "/preview - Preview the latest draft\n"
        "/publish - Publish the latest draft\n"
        "/posts - View recent posts and statuses\n"
        "/cancel - Discard the latest draft\n"
        "/myid - Show your Telegram user ID\n"
        "/start - Show this menu\n\n"
        "Your posts are now saved in SQLite, even when "
        "you restart the bot."
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        await update.effective_message.reply_text(
            f"Your Telegram user ID is: {user.id}"
        )


# --------------------------------------------------
# CREATE A MANUAL DRAFT
# --------------------------------------------------

async def draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    content = " ".join(context.args).strip()

    if not content:
        await update.effective_message.reply_text(
            "Provide the post text.\n\n"
            "Example:\n"
            "/draft Enjoy a peaceful weekend at our resort!"
        )
        return

    post_id = create_post(
        update.effective_user.id,
        content,
    )

    await show_post(update, post_id, content)


# --------------------------------------------------
# GENERATE A POST WITH GEMINI
# --------------------------------------------------

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    topic = " ".join(context.args).strip()

    if not topic:
        await update.effective_message.reply_text(
            "Tell me what post to create.\n\n"
            "Example:\n"
            "/generate Create a friendly weekend post for our resort"
        )
        return

    await update.effective_message.reply_text(
        "🤖 Generating your post. Please wait..."
    )

    try:
        content = await asyncio.to_thread(
            generate_social_post,
            topic,
        )
        content = (content or "").strip()

        if not content:
            raise ValueError("Gemini returned an empty response.")

        post_id = create_post(
            update.effective_user.id,
            content,
        )

        await update.effective_message.reply_text(
            "✨ AI draft saved successfully."
        )
        await show_post(update, post_id, content)

    except Exception:
        logger.exception("AI post generation failed")
        await update.effective_message.reply_text(
            "❌ Could not generate the post. "
            "Check the terminal for the error."
        )


# --------------------------------------------------
# PREVIEW THE LATEST DRAFT
# --------------------------------------------------

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    post = get_latest_draft(update.effective_user.id)

    if not post:
        await update.effective_message.reply_text(
            "You have no saved drafts.\n"
            "Use /generate or /draft to create one."
        )
        return

    await show_post(update, post["id"], post["content"])


# --------------------------------------------------
# PUBLISH A SAVED POST
# --------------------------------------------------

async def publish_post(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    post_id: int,
):
    # Reserve the draft before sending it to reduce duplicate
    # publications caused by repeated button clicks.
    if not start_publishing(post_id, user_id):
        return (
            False,
            "⚠️ This post is no longer an available draft. "
            "Use /posts to check its status.",
        )

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=get_post(post_id, user_id)["content"],
        )

        update_status(
            post_id,
            user_id,
            "published",
            str(CHANNEL_ID),
        )

        logger.info("Published post #%s", post_id)

        return True, f"✅ Post #{post_id} published successfully!"

    except Exception:
        logger.exception("Publishing post #%s failed", post_id)

        # Return it to draft status so the administrator can retry.
        update_status(post_id, user_id, "draft")

        return (
            False,
            "❌ Publishing failed. The post was kept as a draft. "
            "Check the terminal for details.",
        )


async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    if not CHANNEL_ID:
        await update.effective_message.reply_text(
            "TELEGRAM_CHANNEL_ID is missing from .env."
        )
        return

    post = get_latest_draft(update.effective_user.id)

    if not post:
        await update.effective_message.reply_text(
            "No draft is available to publish."
        )
        return

    await update.effective_message.reply_text(
        f"📤 Publishing post #{post['id']}..."
    )

    _, message = await publish_post(
        context,
        update.effective_user.id,
        post["id"],
    )

    await update.effective_message.reply_text(message)


# --------------------------------------------------
# APPROVE OR REJECT BUTTON
# --------------------------------------------------

async def handle_approval(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not await is_admin(update):
        await query.answer(
            "You are not authorized to do this.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        action, post_id_text = query.data.split(":", 1)
        post_id = int(post_id_text)
    except (ValueError, AttributeError):
        await query.edit_message_text("Invalid button action.")
        return

    user_id = update.effective_user.id
    post = get_post(post_id, user_id)

    if not post or post["status"] != "draft":
        await query.edit_message_text(
            "⚠️ This post is no longer a draft. "
            "Use /posts to check its status."
        )
        return

    if action == "reject":
        update_status(post_id, user_id, "rejected")
        await query.edit_message_text(
            f"❌ Post #{post_id} rejected and saved in history."
        )
        return

    if action == "approve":
        if not CHANNEL_ID:
            await query.edit_message_text(
                "TELEGRAM_CHANNEL_ID is missing from .env."
            )
            return

        await query.edit_message_text(
            f"📤 Publishing approved post #{post_id}..."
        )

        _, message = await publish_post(
            context,
            user_id,
            post_id,
        )

        await query.edit_message_text(message)
        return

    await query.edit_message_text("Unknown action.")


# --------------------------------------------------
# SHOW RECENT POSTS AND THEIR STATUS
# --------------------------------------------------

async def posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    saved_posts = get_recent_posts(update.effective_user.id)

    if not saved_posts:
        await update.effective_message.reply_text(
            "No posts saved yet. Try /generate."
        )
        return

    lines = ["📚 YOUR RECENT POSTS\n"]

    for post in saved_posts:
        excerpt = post["content"].replace("\n", " ")
        if len(excerpt) > 75:
            excerpt = excerpt[:72] + "..."

        lines.append(
            f"#{post['id']} | {post['status'].upper()}\n"
            f"{excerpt}\n"
            f"Created: {post['created_at']}\n"
        )

    await update.effective_message.reply_text("\n".join(lines))


# --------------------------------------------------
# CANCEL THE LATEST DRAFT
# --------------------------------------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await deny_access(update)
        return

    post = get_latest_draft(update.effective_user.id)

    if not post:
        await update.effective_message.reply_text(
            "There is no draft to cancel."
        )
        return

    update_status(
        post["id"],
        update.effective_user.id,
        "cancelled",
    )

    await update.effective_message.reply_text(
        f"🗑️ Draft #{post['id']} cancelled. "
        "It remains in your history."
    )


# --------------------------------------------------
# LOG UNEXPECTED ERRORS
# --------------------------------------------------

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Unexpected error while processing an update",
        exc_info=context.error,
    )


# --------------------------------------------------
# START THE APPLICATION
# --------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from .env.")

    if not CHANNEL_ID:
        raise RuntimeError("TELEGRAM_CHANNEL_ID is missing from .env.")

    if ADMIN_ID is None:
        raise RuntimeError(
            "TELEGRAM_ADMIN_ID is missing or invalid in .env."
        )

    # Create the database and table if they do not exist.
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("draft", draft))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("publish", publish))
    application.add_handler(CommandHandler("posts", posts))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(
        CallbackQueryHandler(
            handle_approval,
            pattern=r"^(approve|reject):\d+$",
        )
    )

    application.add_error_handler(error_handler)

    logger.info("Starting SocialPilot AI...")
    application.run_polling()


if __name__ == "__main__":
    main()
