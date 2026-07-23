
import base64
import io
import sqlite3
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8578569041:AAEdl6RdKaD-yMawFegDCT57dSntfBuLlLo"
SD_API_URL = "http://host.docker.internal:7860/sdapi/v1/txt2img"

# ==================== ЦЕНЗУРА ====================
NSFW_WORDS = [
    "nude", "naked", "sex", "porn", "porno", "explicit", "erotic",
    "hentai", "nsfw", "xxx", "cum", "orgasm", "penis", "vagina",
    "cunt", "clit", "breast", "boobs", "dick", "dik", "dic",
    "cock", "cawk", "pussy", "tits", "tit", "fuck", "fuk", "fucc",
    "fck", "anal", "oral", "blow", "bdsm", "bondage", "slut", "whore",
    "milf", "teen", "twink", "gay", "gey", "lesbian", "lesb", "queer",
    "incest", "taboo", "rape", "abuse", "forced", "bad", "nonconsensual", "sperm", "sprm", "spem",
]

AGE_WORDS = [
    "child", "children", "kid", "kids", "little", "young",
    "teen", "teenager", "girl", "boy", "toddler", "baby", "minor",
]

PEOPLE_WORDS = [
    "men", "man", "women", "woman", "girl", "boy", "people", "person",
    "human", "model", "fashion", "body", "figure", "face", "portrait",
]

# ==================== БАЗА ДАННЫХ ====================
DB_PATH = "data/users.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 5))
        conn.commit()
        conn.close()
        return 5

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def is_gibberish(text):
    if len(text) < 4:
        return True
    if not re.search(r'[a-zA-Z]', text):
        return True
    return False

# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼️ Сгенерировать", callback_data="gen")],
        [InlineKeyboardButton("💳 Купить 10 генераций", callback_data="buy_10")],
        [InlineKeyboardButton("📊 Мой баланс", callback_data="balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я твой AI-генератор. \n\n"
        "Напиши промпт на английском, чтобы создать картинку.\n"
        "Или воспользуйся кнопками ниже:",
        reply_markup=reply_markup
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("100₽ — 20 генераций", callback_data="pay_20")],
        [InlineKeyboardButton("200₽ — 50 генераций", callback_data="pay_50")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💳 Выбери тариф для пополнения баланса (демо-режим):",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "gen":
        await query.message.reply_text(
            "🤖 Напиши промпт на английском, чтобы я сгенерировал картинку. Например: 'a photorealistic portrait of a young woman with flowing hair, soft cinematic lighting, 8k, masterpiece, highly detailed.'"
        )
    elif query.data == "buy_10":
        update_balance(user_id, 10)
        new_balance = get_balance(user_id)
        await query.edit_message_text(f"✅ Баланс пополнен! Теперь у тебя {new_balance} генераций.")
    elif query.data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(f"📊 Твой текущий баланс: {balance} генераций.")
    elif query.data == "pay_20":
        update_balance(user_id, 20)
        await query.edit_message_text("✅ Демо-оплата прошла! Начислено 20 генераций.")
    elif query.data == "pay_50":
        update_balance(user_id, 50)
        await query.edit_message_text("✅ Демо-оплата прошла! Начислено 50 генераций.")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    if balance <= 0:
        await update.message.reply_text("❌ У тебя закончились бесплатные генерации! Нажми /start или кнопку 'Купить'.")
        return
    prompt = update.message.text

    if is_gibberish(prompt):
        await update.message.reply_text("❌ Слишком короткий или бессмысленный промпт. Напиши что-то вроде: 'a futuristic city, 8k'.")
        return

    lower = prompt.lower()
    if any(w in lower for w in NSFW_WORDS):
        await update.message.reply_text("❌ Ваш запрос содержит запрещённые слова. Переформулируйте промпт.")
        return

    if any(a in lower for a in AGE_WORDS) and any(n in lower for n in NSFW_WORDS):
        await update.message.reply_text("❌ Недопустимая комбинация. Переформулируйте промпт.")
        return

    if any(p in lower for p in PEOPLE_WORDS):
        safe_prompt = f"{prompt}, wearing clothes, fully dressed, casual outfit, strict clothing, no nudity"
        negative = "worst quality, low quality, deformed, blurry, text, watermark, nude, naked, erotic, explicit, lingerie, bikini, undressed, revealing clothes, low cut, cleavage, showing skin, bare, without clothes, semi-nude"
    else:
        safe_prompt = prompt
        negative = "worst quality, low quality, deformed, blurry, text, watermark"

    wait_msg = await update.message.reply_text(f"🎨 Генерирую...")

    try:
        payload = {
            "prompt": safe_prompt,
            "negative_prompt": negative,
            "steps": 25,
            "sampler_name": "DPM++ 2M Karras",
            "cfg_scale": 7,
            "width": 512,
            "height": 512,
            "batch_size": 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(SD_API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_data = base64.b64decode(data['images'][0])
                    await wait_msg.delete()
                    await update.message.reply_photo(photo=io.BytesIO(img_data))
                    update_balance(user_id, -1)
                    new_balance = get_balance(user_id)
                    await update.message.reply_text(f"Осталось: {new_balance} генераций")
                else:
                    await wait_msg.edit_text(f"❌ Ошибка WebUI: {resp.status}. Ведутся технические работы.")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка: {e}. Ведутся технические работы.")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), generate_image))
    print("✅ Бот запущен и ждет команд...")
    app.run_polling()