import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")  # Changed from DEEPSEEK_API_KEY
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")  # Added
REMINDER_CHAT_ID = os.getenv("REMINDER_CHAT_ID")

# --- TARGET CHATS CONFIGURATION ---
# Easy way to add/remove student chats - just edit this list!
# Format: (chat_id, "Student Name") - the name is just for your reference
TARGET_CHATS = [
    # Add your student chats here:
    # (123456789, "Elena"),
    # (-987654321, "Maria"),
    # (111222333, "Dmitry"),
]

# Alternative: Load from environment variable (comma-separated chat IDs)
# This allows you to update without editing code - just change .env file
env_chat_ids = os.getenv("TARGET_CHAT_IDS", "")
if env_chat_ids:
    try:
        # Parse comma-separated IDs: "123456789,-987654321,111222333"
        chat_ids = [int(cid.strip()) for cid in env_chat_ids.split(",") if cid.strip()]
        # Add to TARGET_CHATS if not using the list above
        if not TARGET_CHATS:
            TARGET_CHATS = [(cid, f"Student_{i+1}") for i, cid in enumerate(chat_ids)]
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing TARGET_CHAT_IDS: {e}")

# Convert REMINDER_CHAT_ID
try:
    if REMINDER_CHAT_ID:
        REMINDER_CHAT_ID = int(REMINDER_CHAT_ID)
except (ValueError, TypeError):
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Grammar Structures (Updated) ---
GRAMMAR_STRUCTURES = [
    "Not nearly as... as: This car is not nearly as fast as that one.",
    "Not quite as... as: This car is not quite as fast as that one.",
    "Passive simple past: Where was this food sold?",
    "Passive simple future: Where will this food be sold?",
    "Second conditional: If I knew French, I would watch French films.",
    "Third conditional: If I had studied, I would have passed.",
    "Mixed conditional: If I had eaten, I wouldn't be hungry now.",
    "Wish (present regret): I wish I had more time.",
    "Passive (present continuous): The house is being painted at the moment.",
    "Should have + past participle: You should have studied harder.",
    "I could never get used to + -ing: I could never get used to living alone.",
    "The more... the more...: The more you read, the more you learn.",
    "Must have + past participle: He must have been lying.",
    "I wish I had + past participle: I wish I had gone to the party.",
    "Worth + -ing: It's worth visiting this museum."
]

# Track recently used topics to avoid repetition
recent_topics = []
MAX_RECENT_TOPICS = 20

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

# --- YandexGPT: Generate simple Russian sentence with improved variety ---
def generate_russian_sentence(desc: str) -> str:
    """Generate Russian sentence using YandexGPT"""
    
    # Build context about recently used topics to avoid
    avoid_topics = ""
    if recent_topics:
        avoid_topics = f"\n- AVOID these recently used topics/themes: {', '.join(recent_topics[-10:])}"
    
    prompt = f"""
You are an English teacher creating grammar practice.
Generate ONE clear Russian sentence that demonstrates this grammar structure.

CRITICAL RULES:
- Use ONLY simple, everyday A2-B1 Russian vocabulary (no rare/advanced words).
- MUST use a completely different topic/scenario than common examples.
- Prioritize UNIQUE contexts: daily routines, emotions, technology, nature, health, food, transportation, relationships, entertainment, education, sports, culture, pets, holidays, hobbies, weather, shopping, work, family events, etc.
- Include time markers like 'вчера', 'завтра', 'на прошлой неделе', 'в детстве' when appropriate.
- Be CREATIVE and VARIED - avoid clichés like umbrellas, studying, being late, etc.{avoid_topics}
- DO NOT include English, labels, or explanations.
- Output ONLY the Russian sentence, nothing else.

Grammar structure: {desc}

Example of variety:
- Third conditional about forgetting umbrella ❌ (too common)
- Third conditional about calling grandmother ✅ (more unique)
- Third conditional about buying concert tickets ✅ (creative)
- Third conditional about planting tomatoes ✅ (specific and fresh)
"""
    
    try:
        # YandexGPT API endpoint
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.9,  # High temperature for variety
                "maxTokens": 100
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        logger.info(f"Calling YandexGPT for: {desc[:50]}...")
        
        res = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if res.status_code != 200:
            logger.error(f"YandexGPT error: {res.status_code} - {res.text}")
            raise Exception(f"YandexGPT returned {res.status_code}")
        
        response_data = res.json()
        sentence = response_data['result']['alternatives'][0]['message']['text'].strip()
        
        # Clean up the sentence
        for bad in ['"', '«', '»', '\n']:
            sentence = sentence.replace(bad, '')
        
        # Remove any English text that might have leaked through
        # If the sentence contains English letters, it's probably not pure Russian
        if any(c.isalpha() and ord(c) < 128 for c in sentence[:20]):
            logger.warning(f"YandexGPT returned sentence with English: {sentence}")
            raise Exception("Sentence contains English")
        
        # Extract topic keywords for tracking (simple approach)
        keywords = [word for word in sentence.split() if len(word) > 4][:3]
        if keywords:
            recent_topics.extend(keywords)
            if len(recent_topics) > MAX_RECENT_TOPICS:
                recent_topics[:] = recent_topics[-MAX_RECENT_TOPICS:]
        
        logger.info(f"Generated sentence: {sentence}")
        return sentence
        
    except Exception as e:
        logger.error(f"YandexGPT error: {e}")
        # Fallback sentences if API fails
        return random.choice([
            "Если бы я позвонил бабушке вчера, она была бы рада.",
            "Я собираюсь навестить друга в больнице завтра.",
            "Этот телефон намного удобнее, чем мой старый.",
            "Эта книга не такая интересная, как та.",
            "Если пойдёт снег, мы слепим снеговика.",
            "Ты когда-нибудь пробовал узбекскую кухню?"
        ])

# Store active quizzes with their expiration time
active_quizzes = {}

async def cleanup_quiz(chat_id: int, delay: int = 30):
    """Remove quiz after delay"""
    await asyncio.sleep(delay)
    if chat_id in active_quizzes:
        del active_quizzes[chat_id]
        logger.info(f"Quiz expired for chat {chat_id}")

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start command from user {update.effective_user.id}")
    await update.message.reply_text(
        "Привет! Напиши /quiz здесь (в личном чате), чтобы выбрать предложения для отправки в группу."
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(f"Quiz command from user {user_id}")
    
    if not TARGET_CHATS:
        await update.message.reply_text(
            "❌ Нет настроенных чатов для отправки.\n"
            "Пожалуйста, настройте TARGET_CHATS в коде или TARGET_CHAT_IDS в .env"
        )
        return
    
    # Show which chats will receive sentences
    chat_list = ", ".join([name for _, name in TARGET_CHATS])
    await update.message.reply_text(f"⏳ Генерирую предложения для: {chat_list}...")
    
    prompts = random.sample(GRAMMAR_STRUCTURES, 6)
    sentences = [generate_russian_sentence(p) for p in prompts]
    
    # Store sentences and create buttons
    active_quizzes[chat_id] = {
        'sentences': sentences,
        'sent_count': 0,
        'message_id': None
    }
    
    # Create buttons - each button shows the full sentence
    buttons = []
    for i, sent in enumerate(sentences):
        # Show full sentence in button (Telegram will handle wrapping)
        buttons.append([InlineKeyboardButton(f"📝 {sent}", callback_data=f"send_{i}")])
    
    # Add a "Finish" button
    buttons.append([InlineKeyboardButton("✅ Готово", callback_data="finish")])
    
    message = await update.message.reply_text(
        f"🎯 **Выбери предложения для отправки ({len(TARGET_CHATS)} чатов):**\n\n"
        "• Нажми на предложение чтобы отправить его\n"
        "• Кнопки активны 30 секунд\n"
        "• Нажми '✅ Готово' когда закончишь",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # Store message ID for later editing
    active_quizzes[chat_id]['message_id'] = message.message_id
    
    # Schedule cleanup after 30 seconds
    asyncio.create_task(cleanup_quiz(chat_id))

async def send_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    if chat_id not in active_quizzes:
        await query.edit_message_text("❌ Время вышло! Используй /quiz чтобы начать заново.")
        return
    
    if query.data == "finish":
        sent_count = active_quizzes[chat_id]['sent_count']
        await query.edit_message_text(f"✅ Отправлено предложений: {sent_count}\n\nИспользуй /quiz для нового набора.")
        if chat_id in active_quizzes:
            del active_quizzes[chat_id]
        return
    
    try:
        idx = int(query.data.split("_")[1])
        quiz_data = active_quizzes[chat_id]
        sentences = quiz_data['sentences']
        
        if 0 <= idx < len(sentences):
            # Send to ALL target chats
            sent_to = []
            failed = []
            
            for target_id, student_name in TARGET_CHATS:
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=sentences[idx]
                    )
                    sent_to.append(student_name)
                    logger.info(f"Sentence {idx} sent to {student_name} ({target_id})")
                except Exception as e:
                    failed.append(student_name)
                    logger.error(f"Failed to send to {student_name} ({target_id}): {e}")
            
            # Update counter
            quiz_data['sent_count'] += 1
            sent_count = quiz_data['sent_count']
            
            # Build status message
            status_parts = []
            if sent_to:
                status_parts.append(f"✅ {', '.join(sent_to)}")
            if failed:
                status_parts.append(f"❌ {', '.join(failed)}")
            
            status_info = f" ({' | '.join(status_parts)})" if status_parts else ""
            
            # Update the message to show progress but KEEP THE BUTTONS
            remaining_time = "⏳ ~25 сек"
            await query.edit_message_text(
                f"🎯 **Отправлено: {sent_count}/6{status_info}** • {remaining_time}\n\n"
                "• Нажми на предложение чтобы отправить его\n"
                "• Кнопки активны 30 секунд\n" 
                "• Нажми '✅ Готово' когда закончишь",
                reply_markup=query.message.reply_markup
            )
            
            # Send confirmation separately
            confirmation = f"✅ Отправлено в {len(sent_to)} чатов"
            if failed:
                confirmation += f" (не удалось: {len(failed)})"
            confirmation += f": _{sentences[idx]}_"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=confirmation,
                parse_mode="Markdown"
            )
            
        else:
            await query.answer("❌ Предложение не найдено", show_alert=True)
            
    except Exception as e:
        logger.error(f"Send error: {e}")
        await query.answer("❌ Ошибка при отправке", show_alert=True)

# --- Reminder Scheduler ---
def send_reminder():
    if not REMINDER_CHAT_ID:
        return
    
    en, he, trans = random.choice(REMINDER_MESSAGES)
    text = f"{en}\n*{he}*\n_{trans}_"
    
    try:
        # Create new event loop for each reminder
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