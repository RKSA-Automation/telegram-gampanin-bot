from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import time
import pymysql

# 🔐 Configuration
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "suguan_bot")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "password")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "249351514"))

# ⏳ Wait for DB to be ready
for _ in range(10):
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        conn.close()
        print("✅ Database connection established.")
        break
    except pymysql.err.OperationalError:
        print("⏳ Waiting for DB to be ready...")
        time.sleep(3)

# 🧱 DB setup
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

# 👥 Models
class AuthorizedUser(Base):
    __tablename__ = "authorized_users"
    user_id = Column(BigInteger, primary_key=True)
    full_name = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)
    entries = relationship("SuguanEntry", back_populates="user")

class SuguanEntry(Base):
    __tablename__ = "suguan_entries"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    day = Column(String(20))
    time = Column(String(20))
    lokal = Column(String(100))
    gampanin = Column(String(100))
    language = Column(String(50))
    user_id = Column(BigInteger, ForeignKey("authorized_users.user_id"))
    user = relationship("AuthorizedUser", back_populates="entries")

Base.metadata.create_all(engine)

# 🔐 Authorization helper
def is_authorized(user_id: int) -> bool:
    session = SessionLocal()
    authorized = session.query(AuthorizedUser).filter_by(user_id=user_id).first()
    session.close()
    return authorized is not None

# 🔔 Send approval request to admin
async def send_access_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "🚫 You are not authorized to use this bot.\n"
        "⏳ Please wait for admin approval."
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user.id}:{user.full_name}")
    ]])
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 User requesting access:\nName: {user.full_name}\nID: `{user.id}`",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# 📌 /sendsuguan command
async def sendsuguan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_access_request(update, context)
        return
    await update.message.reply_text(
        "Please send your *suguan po* (one at a time po):\n"
        "Format: `Day, Time, Lokal, Gampanin, Language`\n\n"
        "*Example:* `Thu, 5:45AM, Green Condo, R1, Tag`\n\n"
        "Thanks po 🙏🏻.",
        parse_mode="Markdown"
    )

# 📥 Handle entries
async def handle_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await send_access_request(update, context)
        return

    text = update.message.text.strip()
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 5:
        await update.message.reply_text(
            "❌ Invalid format. Please use:\n"
            "`Day, Time, Lokal, Gampanin, Language`\n\n"
            "*Example:*\n`Thu, 5:45AM, Green Condo, R1, Tag`",
            parse_mode="Markdown"
        )
        return

    day, time_str, lokal, gampanin, language = parts
    session = SessionLocal()
    try:
        entry = SuguanEntry(
            day=day,
            time=time_str,
            lokal=lokal,
            gampanin=gampanin,
            language=language,
            user_id=user_id
        )
        session.add(entry)
        session.commit()
        await update.message.reply_text("✅ Salamat! Naitala na ang suguan mo.")
    except Exception as e:
        session.rollback()
        print(f"❌ DB error: {e}")
        await update.message.reply_text("⚠️ May problema sa pag-save sa database. Paki-ulit po mamaya.")
    finally:
        session.close()

# ☑️ Callback handler (approve via button)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("⛔ Only the admin can approve access.", show_alert=True)
        return

    data = query.data
    if data.startswith("approve:"):
        _, target_user_id, full_name = data.split(":", 2)
        session = SessionLocal()
        exists = session.query(AuthorizedUser).filter_by(user_id=int(target_user_id)).first()
        if not exists:
            session.add(AuthorizedUser(user_id=int(target_user_id), full_name=full_name))
            session.commit()
            await query.edit_message_text(f"✅ Approved access for {full_name} ({target_user_id}).")
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text="✅ You are now approved to use this bot."
                )
            except Exception as e:
                print(f"⚠️ Cannot notify user: {e}")
        else:
            await query.edit_message_text(f"✅ {full_name} is already approved.")
        session.close()

# 🔧 /approve and /revoke
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    session = SessionLocal()
    session.add(AuthorizedUser(user_id=user_id, full_name=f"User {user_id}"))
    session.commit()
    session.close()
    await update.message.reply_text(f"✅ Approved user {user_id}.")
    await context.bot.send_message(chat_id=user_id, text="✅ You are now approved to use this bot.")

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /revoke <user_id>")
        return

    user_id = int(context.args[0])
    session = SessionLocal()
    deleted = session.query(AuthorizedUser).filter_by(user_id=user_id).delete()
    session.commit()
    session.close()
    await update.message.reply_text(f"🚫 Revoked user {user_id}.")
    if deleted:
        try:
            await context.bot.send_message(chat_id=user_id, text="🚫 Your access has been revoked.")
        except:
            pass

# 🚀 Bot launcher
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("sendsuguan", sendsuguan))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("revoke", revoke_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_entry))
    print("🤖 Telegram Sugúan Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
