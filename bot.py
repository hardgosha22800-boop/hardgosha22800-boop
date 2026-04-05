import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ==========================================================
# 🔐 ТВОИ КЛЮЧИ
# ==========================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Чтение системного промпта из файла
with open("prompt.txt", "r", encoding="utf-8") as f:
    PROMT = f.read()
# ==========================================================



client = Groq(api_key=GROQ_API_KEY)

# Модель (бесплатно и быстро)
MODEL = "llama-3.1-8b-instant"

logging.basicConfig(level=logging.INFO)
history_storage = {}

async def start(update, context):
    await update.message.reply_text("👋 Привет! Я бот на Groq. Пиши мне!")

async def clear_history(update, context):
    user_id = update.effective_user.id
    history_storage[user_id] = []
    await update.message.reply_text("🧹 История очищена!")

async def handle_message(update, context):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        history = history_storage.get(user_id, [])
        messages = [{"role": "system", "content": PROMT}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_text})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content

        if user_id not in history_storage:
            history_storage[user_id] = []
        history_storage[user_id].append({"role": "user", "content": user_text})
        history_storage[user_id].append({"role": "assistant", "content": reply})
        
        if len(history_storage[user_id]) > 20:
            history_storage[user_id] = history_storage[user_id][-20:]

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка. Попробуй /clear. ({str(e)[:50]})")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот на Groq запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()