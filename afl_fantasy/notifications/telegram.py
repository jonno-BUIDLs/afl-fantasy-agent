"""Telegram notification and approval workflow."""
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from loguru import logger
from afl_fantasy.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def send_message(text: str, parse_mode: str = "Markdown") -> int:
    """Send a message and return the message_id."""
    msg = await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=parse_mode,
    )
    return msg.message_id


async def send_draft_post(tweet_text: str, post_type: str, post_id: int) -> int:
    """
    Send a draft tweet for approval with Approve/Reject buttons.
    Returns the Telegram message_id.
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{post_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{post_id}"),
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit:{post_id}"),
        ]
    ])
    text = (
        f"*Draft {post_type.replace('_', ' ').title()} Post*\n\n"
        f"```\n{tweet_text}\n```\n\n"
        f"_{len(tweet_text)}/280 chars_"
    )
    msg = await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return msg.message_id


async def send_strategy_brief(brief: str, round_name: str) -> None:
    """Send the full strategy brief (for your eyes only, not for posting)."""
    header = f"*AFL Fantasy Strategy Brief — {round_name}*\n\n"
    # Telegram messages max at 4096 chars; split if needed
    full = header + brief
    chunk_size = 4000
    for i in range(0, len(full), chunk_size):
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=full[i:i+chunk_size],
            parse_mode="Markdown",
        )


def send_sync(coro) -> None:
    """Run an async telegram call from sync context."""
    asyncio.run(coro)


# ── Approval handler (run as part of the bot polling loop) ───────────────────

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle approve/reject button presses."""
    from afl_fantasy.db.store import get_client
    query = update.callback_query
    await query.answer()

    action, post_id = query.data.split(":")
    post_id = int(post_id)

    supabase = get_client()

    if action == "approve":
        supabase.table("posts").update({"status": "approved"}).eq("id", post_id).execute()
        await query.edit_message_reply_markup(None)
        await query.message.reply_text(f"✅ Post #{post_id} approved and queued for posting.")
    elif action == "reject":
        supabase.table("posts").update({"status": "rejected"}).eq("id", post_id).execute()
        await query.edit_message_reply_markup(None)
        await query.message.reply_text(f"❌ Post #{post_id} rejected.")
    elif action == "edit":
        supabase.table("posts").update({"status": "editing"}).eq("id", post_id).execute()
        await query.message.reply_text(
            f"✏️ Reply to this message with your edited text for post #{post_id}."
        )


def build_bot_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_approval))
    return app
