from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)
import os
from datetime import datetime
import time
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, AuthorizedUser, SuguanEntry, TaskAssignment

# 🔐 Config
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "suguan_bot")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "password")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "249351514"))

# ⏳ Wait for DB
for _ in range(10):
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        conn.close()
        print("✅ Database connection established.")
        break
    except pymysql.err.OperationalError:
        print("⏳ Waiting for DB to be ready...")
        time.sleep(3)

# SQLAlchemy Setup
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# 🔐 Auth helper
def is_authorized(user_id: int) -> bool:
    session = SessionLocal()
    result = session.query(AuthorizedUser).filter_by(user_id=user_id).first()
    session.close()
    return result is not None

# 🔔 Approval request
async def send_access_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("🚫 You are not authorized.\n⏳ Wait for admin approval.")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user.id}:{user.full_name}")]
    ])
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 Access request:\nName: {user.full_name}\nID: `{user.id}`",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# 📝 Suguan
async def sendsuguan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_access_request(update, context)
        return
    await update.message.reply_text(
        "Please send your *suguan po*:\n"
        "`Day, Time, Lokal, Gampanin, Language`\n"
        "*Example:* `Thu, 5:45AM, Green Condo, R1, Tag`",
        parse_mode="Markdown"
    )

async def handle_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await send_access_request(update, context)
        return
    parts = [p.strip() for p in update.message.text.split(",")]
    if len(parts) != 5:
        await update.message.reply_text(
            "❌ Invalid format.\nExample: `Thu, 5:45AM, Green Condo, R1, Tag`",
            parse_mode="Markdown"
        )
        return
    session = SessionLocal()
    try:
        entry = SuguanEntry(day=parts[0], time=parts[1], lokal=parts[2],
                            gampanin=parts[3], language=parts[4], user_id=user_id)
        session.add(entry)
        session.commit()
        await update.message.reply_text("✅ Suguan saved.")
    except Exception as e:
        session.rollback()
        await update.message.reply_text("⚠️ Failed to save. Please try again.")
        print(f"❌ DB error: {e}")
    finally:
        session.close()

# ✅ Button callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ Only admin allowed.", show_alert=True)
        return
    data = query.data
    if data.startswith("approve:"):
        _, uid, full_name = data.split(":", 2)
        session = SessionLocal()
        if not session.query(AuthorizedUser).filter_by(user_id=int(uid)).first():
            session.add(AuthorizedUser(user_id=int(uid), full_name=full_name))
            session.commit()
            await context.bot.send_message(chat_id=int(uid), text="✅ You are now approved to use this bot.")
        await query.edit_message_text(f"✅ Approved: {full_name}")
        session.close()

# 🔧 Approve & Revoke
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args) != 1:
        return await update.message.reply_text("Usage: /approve <user_id>")
    session = SessionLocal()
    user_id = int(context.args[0])
    session.add(AuthorizedUser(user_id=user_id, full_name=f"User {user_id}"))
    session.commit()
    session.close()
    await update.message.reply_text(f"✅ Approved user {user_id}")
    await context.bot.send_message(chat_id=user_id, text="✅ You are now approved to use this bot.")

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args) != 1:
        return await update.message.reply_text("Usage: /revoke <user_id>")
    user_id = int(context.args[0])
    session = SessionLocal()
    try:
        user = session.query(AuthorizedUser).get(user_id)
        if user:
            session.delete(user)
            session.commit()
            await update.message.reply_text(f"🚫 Revoked user {user_id}")
            await context.bot.send_message(chat_id=user_id, text="🚫 Your access has been revoked.")
        else:
            await update.message.reply_text("⚠️ User not found.")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ Error revoking: {e}")
    finally:
        session.close()

# 🆕 /assigntask
async def assigntask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args) < 2:
        return await update.message.reply_text("Usage: /assigntask <user_id> <task>")
    try:
        target_user_id = int(context.args[0])
        task_text = " ".join(context.args[1:])
        session = SessionLocal()
        task = TaskAssignment(user_id=target_user_id, task=task_text)
        session.add(task)
        session.commit()
        await context.bot.send_message(chat_id=target_user_id, text=f"📝 New Task:\n{task_text}")
        await update.message.reply_text(f"✅ Task assigned to {target_user_id}")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ Failed to assign task: {e}")
    finally:
        session.close()

# 🆕 /mytasks
async def mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await send_access_request(update, context)
        return
    session = SessionLocal()
    tasks = session.query(TaskAssignment).filter_by(user_id=user_id).all()
    if tasks:
        msg = "📋 Your Tasks:\n" + "\n".join([f"• {t.task}" for t in tasks])
    else:
        msg = "📭 You have no tasks assigned."
    await update.message.reply_text(msg)
    session.close()

# 🆕 /listusers
async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ You are not authorized to use this command.")

    session = SessionLocal()
    users = session.query(AuthorizedUser).all()
    if not users:
        msg = "📭 No authorized users found."
    else:
        msg = "👥 *Authorized Users:*\n"
        msg += "\n".join([f"• {u.full_name} - `{u.user_id}`" for u in users])
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🚀 Start Bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("sendsuguan", sendsuguan))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("revoke", revoke_command))
    app.add_handler(CommandHandler("assigntask", assigntask))
    app.add_handler(CommandHandler("mytasks", mytasks))
    app.add_handler(CommandHandler("listusers", listusers))  # ✅ Added here
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_entry))
    print("🤖 Telegram Sugúan Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
