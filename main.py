import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
REMINDER_CHAT_ID = os.getenv("REMINDER_CHAT_ID")

# Convert chat IDs to integers
try:
    if TARGET_CHAT_ID:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    if REMINDER_CHAT_ID:
        REMINDER_CHAT_ID = int(REMINDER_CHAT_ID)
except (ValueError, TypeError):
    pass  # Handle None values gracefully

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Grammar Structures (from your PDF) ---
GRAMMAR_STRUCTURES = [
    # A2
    "Used to (past habit): I used to smoke.",
    "Be going to (future plan): I'm going to visit my parents.",
    "Comparatives: much more expensive, a bit smaller than.",
    "Not as... as: This car is not as fast as that one.",
    "First conditional: If it rains, I'll stay home.",
    "Present Perfect (ever): Have you ever seen this film?",
    "Present Perfect Continuous (duration): How long have you been studying English?",
    "Passive (present simple): Where is this food sold?",
    "Need + -ing: My car needs fixing.",
    
    # B1
    "Second conditional: If I knew French, I would watch French films.",
    "Third conditional: If I had studied, I would have passed.",
    "Mixed conditional: If I had eaten, I wouldn't be hungry now.",
    "Wish (present regret): I wish I had more time.",
    "Passive (continuous & future): The house is being painted. The car will be fixed.",
    "Should have + past participle: You should have studied harder.",
    "Might have / can't have + past participle: He might have missed the bus.",
    "Future continuous: This time tomorrow I'll be flying to Dubai.",
    "Get used to + -ing: I can't get used to living alone.",
    "Be used to + -ing: I'm used to waking up early.",
    "Not quite as...: This restaurant isn't quite as good as the old one.",
    "The more... the more...: The more you read, the more you learn.",
    "Despite + noun: Despite the rain, we went out.",
    "Whereas: I like sports, whereas she prefers books.",
    "Stop doing vs. stop to do: He stopped smoking. He stopped to tie his shoes.",
    "Remember doing vs. remember to do: I remember meeting her. Remember to lock the door.",
    "Try doing vs. try to do: Try adding salt. I'll try to finish.",
    "Regret doing vs. regret to do: I regret telling him. I regret to inform you.",
    "Verb + object + infinitive: She told me to wait.",
    "Verb + object + -ing: I caught him stealing.",
    
    # B2
    "Must have + past participle: He must have been lying.",
    "Will have + past participle: By 2025, I will have graduated.",
    "Far more difficult: This exam was far more difficult than the last.",
    "From what I've heard...: From what I've heard, the new manager is strict.",
    "I wish I had + past participle: I wish I had gone to the party.",
    "It is said that...: It is said that the castle is haunted.",
    "Prefer + -ing / would rather + infinitive: I prefer reading. I'd rather stay home.",
    "Famous for + -ing: She's famous for singing jazz.",
    "Worth + -ing: It's worth visiting this museum."
]

# --- Hebrew Reminder Messages (A2 Level) ---
REMINDER_MESSAGES = [
    (
        "Have you sent the sentences to Elena yet?",
        "האם שלחת את המשפטים לאלנה עדיין?",
        "Ha'im shalakhta et ha'mishpatim le'Elena adayin?"
    ),
    (
        "Has Elena received her grammar practice?",
        "האם אלנה קיבלה את תרגול הדקדוק שלה?",
        "Ha'im Elena kibla et targil ha'dikduk shelah?"
    ),
    (
        "Did you choose sentences for Elena today?",
        "האם בחרת משפטים לאלנה היום?",
        "Ha'im bakhart mishpatim le'Elena hayom?"
    ),
    (
        "Does Elena have material for today?",
        "האם יש לאלנה חומר להיום?",
        "Ha'im yesh le'Elena khamer le'hayom?"
    ),
    (
        "Have you checked if Elena practiced?",
        "האם בדקת אם אלנה התאמנה?",
        "Ha'im badakhta im Elena hit'amna?"
    ),
    (
        "Did you send Hebrew reminders today?",
        "האם שלחת תזכורות בעברית היום?",
        "Ha'im shalakhta tizkorot be'Ivrit hayom?"
    ),
    (
        "Is Elena's grammar practice ready?",
        "האם תרגול הדקדוק של אלנה מוכן?",
        "Ha'im targil ha'dikduk shel Elena mukhan?"
    ),
    (
        "Have you reviewed Elena's progress?",
        "האם סקרת את ההתקדמות של אלנה?",
        "Ha'im sakarta et ha'hitkadmut shel Elena?"
    ),
    (
        "Did you prepare new sentences today?",
        "האם הכנת משפטים חדשים היום?",
        "Ha'im hekhanta mishpatim khadashim hayom?"
    ),
    (
        "Has today's practice been sent?",
        "האם תרגול היום נשלח?",
        "Ha'im targil ha'yom nishlakh?"
    ),
    (
        "Are you helping Elena with grammar?",
        "האם אתה עוזר לאלנה עם דקדוק?",
        "Ha'im ata ozer le'Elena im dikduk?"
    ),
    (
        "Did you remember to send the quiz?",
        "האם זכרת לשלוח את החידון?",
        "Ha'im zakhrta lishlakh et ha'khidon?"
    )
]

# --- DeepSeek: Generate simple Russian sentence ---
def generate_russian_sentence(desc: str) -> str:
    prompt = f"""
    You are an English teacher creating grammar practice.
    Generate ONE clear Russian sentence that demonstrates this grammar structure.
    Rules:
    - Use ONLY simple, everyday A2-B1 Russian vocabulary (no rare/advanced words).
    - Include context like 'вчера', 'завтра', 'когда я был ребёнком' if needed.
    - DO NOT include English, labels, or explanations.
    - Output ONLY the Russian sentence, nothing else.

    Grammar: {desc}
    """
    try:
        res = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": 55
            },
            timeout=15
        )
        sentence = res.json()['choices'][0]['message']['content'].strip()
        for bad in ['"', '«', '»']:
            sentence = sentence.replace(bad, '')
        return sentence
    except Exception as e:
        logger.error(f"DeepSeek error: {e}")
        return random.choice([
            "Если бы я знал об этом вчера, я бы пришёл.",
            "Я собираюсь навестить родителей завтра.",
            "Этот телефон намного дороже, чем тот.",
            "Эта машина не такая быстрая, как моя старая.",
            "Если пойдёт дождь, я останусь дома.",
            "Ты когда-нибудь был в Лондоне?"
        ])

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start command from user {update.effective_user.id}")
    await update.message.reply_text(
        "Привет! Напиши /quiz здесь (в личном чате), чтобы выбрать предложения для отправки в группу."
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Quiz command from user {user_id}")
    
    if not TARGET_CHAT_ID:
        await update.message.reply_text("❌ TARGET_CHAT_ID не настроен.")
        return
    
    await update.message.reply_text("⏳ Генерирую предложения...")
    
    prompts = random.sample(GRAMMAR_STRUCTURES, 6)
    sentences = [generate_russian_sentence(p) for p in prompts]
    context.user_data["sentences"] = sentences

    buttons = []
    for i, sent in enumerate(sentences):
        label = (sent[:22] + "…") if len(sent) > 22 else sent
        buttons.append([InlineKeyboardButton(label, callback_data=f"send_{i}")])

    await update.message.reply_text(
        "Выбери, что отправить в группу:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def send_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        idx = int(query.data.split("_")[1])
        sentences = context.user_data.get("sentences", [])
        if 0 <= idx < len(sentences):
            await context.bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=sentences[idx]
            )
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.reply_text("✅ Отправлено в группу!")
            logger.info(f"Sentence sent to group {TARGET_CHAT_ID}")
        else:
            await query.message.edit_text("❌ Предложение не найдено.")
    except Exception as e:
        logger.error(f"Send error: {e}")
        await query.message.edit_text("❌ Ошибка при отправке.")

# --- Reminder Scheduler ---
def send_reminder():
    if not REMINDER_CHAT_ID:
        return
    
    en, he, trans = random.choice(REMINDER_MESSAGES)
    text = f"{en}\n*{he}*\n_{trans}_"
    
    try:
        # Create new event loop for each reminder
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_async():
            bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build().bot
            await bot.send_message(
                chat_id=REMINDER_CHAT_ID, 
                text=text, 
                parse_mode="Markdown"
            )
        
        loop.run_until_complete(send_async())
        loop.close()
        logger.info("✅ Reminder sent")
    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")

def start_scheduler():
    if not REMINDER_CHAT_ID:
        logger.info("No REMINDER_CHAT_ID — scheduler not started.")
        return
    
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(send_reminder, CronTrigger(hour=10, minute=0, timezone=pytz.utc))
    scheduler.add_job(send_reminder, CronTrigger(hour=16, minute=0, timezone=pytz.utc))
    scheduler.start()
    logger.info("⏰ Reminder scheduler started")

# --- Main Bot Setup ---
def main():
    """Start the bot with polling"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CallbackQueryHandler(send_sentence))
    
    # Start scheduler
    start_scheduler()
    
    # Start polling
    logger.info("🤖 Starting bot with polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
