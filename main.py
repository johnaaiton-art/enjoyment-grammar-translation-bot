import os
import random
import re
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
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
REMINDER_CHAT_ID = os.getenv("REMINDER_CHAT_ID")

# --- TARGET CHATS CONFIGURATION ---
TARGET_CHATS = []

env_chat_config = os.getenv("TARGET_CHAT_CONFIG", "")
if env_chat_config:
    try:
        for entry in env_chat_config.split(","):
            if ":" in entry:
                chat_id_str, langs_str = entry.split(":", 1)
                chat_id = int(chat_id_str.strip())
                langs = [l.strip() for l in langs_str.split("+")]
                TARGET_CHATS.append((chat_id, f"Student_{len(TARGET_CHATS)+1}", langs))
    except (ValueError, TypeError) as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error parsing TARGET_CHAT_CONFIG: {e}")

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

# --- Grammar Structures ---
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

# --- Topics as NOUN PHRASES (not gerunds) — lets the model vary syntax ---
TOPIC_CATEGORIES = [
    # Food & Cooking
    ["pancakes", "homemade bread", "borscht", "sushi", "shashlik",
     "dumplings", "strawberry jam", "pizza delivery", "a watermelon", "pickled cucumbers"],
    # Nature & Outdoors
    ["a sunset", "pigeons in the park", "wild mushrooms", "forest berries", "tomato seedlings",
     "rain", "the first snow", "a thunderstorm", "a hedgehog", "the river bank"],
    # Home & Daily Life
    ["new furniture", "a leaky tap", "a freshly painted wall", "lost keys", "new curtains",
     "the balcony", "a broken lightbulb", "old photos", "an old letter", "a messy wardrobe"],
    # People & Relationships
    ["grandmother", "the neighbour", "a classmate", "an older brother",
     "an old friend", "a pen pal", "a colleague", "a lost tourist",
     "a nephew", "a sad friend"],
    # Travel & Transport
    ["the last bus", "the wrong train", "the airport", "an unfamiliar city",
     "a cheap hostel", "a bicycle", "a hitchhiking trip", "a night train", "a lost passport",
     "a new neighbourhood"],
    # Hobbies & Entertainment
    ["knitting", "a chess game", "an old film", "a concert", "pottery class",
     "juggling", "a detective novel", "a jigsaw puzzle", "origami", "the museum"],
    # Health & Sport
    ["jogging", "the gym", "a pulled muscle", "drinking water", "swimming lessons",
     "yoga", "a steep hill", "table tennis", "a bad cold", "a long walk"],
    # Work & Study
    ["a deadline", "overtime at work", "a presentation", "a new program",
     "an online course", "a difficult essay", "a failed exam", "a promotion", "a new job",
     "an internship"],
    # Technology & Modern Life
    ["a phone charger", "a forgotten password", "a new laptop", "a video call",
     "short videos", "a new phone", "old files", "a software update",
     "a TV series", "the printer"],
    # Seasons & Celebrations
    ["the New Year tree", "flowers for 8 March", "fireworks", "the dacha",
     "a snowman", "a Christmas tree", "a birthday picnic", "the ice rink",
     "graduation", "a school play"],
]

# --- Syntactic frames to force structural variety ---
SYNTACTIC_FRAMES = [
    "Start with a time adverbial (Вчера, Обычно, На прошлой неделе, etc.)",
    "Start with the subject (я, мы, ты, он, она, они)",
    "Start with a subordinate clause (Когда..., Если..., Хотя...)",
    "Use an impersonal construction (Было, Можно, Нужно, Стоит...)",
    "Start with a place adverbial (В парке, На кухне, У бабушки...)",
    "Start with an object or complement (Этот фильм..., Такую погоду...)",
    "Use a question form",
    "Start with a participle or adverbial participle (Проснувшись..., Сидя...)",
]

recent_topics_used = []
MAX_RECENT = 30


def get_unique_topics(n: int) -> list:
    """Pick N topics that haven't been used recently, preferring different categories."""
    # Try to draw one from each category first for maximum variety
    available_by_cat = [
        [t for t in cat if t not in recent_topics_used]
        for cat in TOPIC_CATEGORIES
    ]
    # Drop empty categories
    available_by_cat = [cat for cat in available_by_cat if cat]

    picked = []
    random.shuffle(available_by_cat)
    for cat in available_by_cat:
        if len(picked) >= n:
            break
        picked.append(random.choice(cat))

    # If we still need more, draw from the general pool
    if len(picked) < n:
        all_available = [t for cat in TOPIC_CATEGORIES for t in cat
                         if t not in recent_topics_used and t not in picked]
        if len(all_available) < (n - len(picked)):
            recent_topics_used.clear()
            all_available = [t for cat in TOPIC_CATEGORIES for t in cat if t not in picked]
        picked.extend(random.sample(all_available, n - len(picked)))

    for t in picked:
        recent_topics_used.append(t)
    while len(recent_topics_used) > MAX_RECENT:
        recent_topics_used.pop(0)

    return picked


# --- BATCHED generation: all 6 sentences in ONE API call ---
def generate_russian_sentences_batch(structures: list) -> list:
    """Generate N Russian sentences in a single call with strong anti-repetition framing."""
    n = len(structures)
    topics = get_unique_topics(n)
    frames = random.sample(SYNTACTIC_FRAMES, min(n, len(SYNTACTIC_FRAMES)))
    if len(frames) < n:
        frames += random.choices(SYNTACTIC_FRAMES, k=n - len(frames))

    numbered_tasks = "\n".join(
        f"{i+1}. Grammar structure: {s}\n   Topic: {topics[i]}\n   Syntactic frame: {frames[i]}"
        for i, s in enumerate(structures)
    )

    prompt = f"""You are a Russian language teacher creating example sentences for an English-speaking student (A2-B1 level).

Write {n} Russian sentences. Each one demonstrates a different English grammar structure (translated into natural Russian).

{numbered_tasks}

CRITICAL VARIETY RULES — read carefully:
- Each sentence MUST start with a DIFFERENT word. No two sentences may share their first word.
- Follow the syntactic frame given for each sentence.
- Vary grammatical subjects across the set: mix "я", "мы", "ты", "они", "он", "она", impersonal forms, and noun subjects.
- Do NOT use the same sentence skeleton twice. If sentence 1 is "Вчера я X", sentence 2 must not be "Вчера я Y".
- Simple, everyday A2-B1 vocabulary only.
- Natural-sounding Russian, not word-for-word translation from English.

OUTPUT FORMAT — follow exactly:
1. <Russian sentence>
2. <Russian sentence>
3. <Russian sentence>
...

No explanations, no English, no quotation marks. Just numbered Russian sentences."""

    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            # Using the full yandexgpt model (not lite) — much better at variety
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.9,
                "maxTokens": 600
            },
            "messages": [
                {"role": "user", "text": prompt}
            ]
        }

        logger.info(f"Calling YandexGPT (batch of {n}) | Topics: {topics}")
        res = requests.post(url, headers=headers, json=payload, timeout=40)

        if res.status_code != 200:
            logger.error(f"YandexGPT error: {res.status_code} - {res.text}")
            raise Exception(f"YandexGPT returned {res.status_code}")

        response_data = res.json()
        raw = response_data['result']['alternatives'][0]['message']['text'].strip()
        logger.info(f"Raw batch output:\n{raw}")

        # Parse numbered lines: "1. sentence", "2. sentence", ...
        sentences = []
        for line in raw.split('\n'):
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^\s*\d+[.)]\s*(.+)$', line)
            if m:
                s = m.group(1).strip()
                for bad in ['"', '«', '»', '*', '_']:
                    s = s.replace(bad, '')
                sentences.append(s.strip())

        if len(sentences) < n:
            logger.warning(f"Got only {len(sentences)}/{n} sentences, falling back for missing ones")
            while len(sentences) < n:
                sentences.append(random.choice(FALLBACK_SENTENCES))

        return sentences[:n]

    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        return [random.choice(FALLBACK_SENTENCES) for _ in range(n)]


FALLBACK_SENTENCES = [
    "Если бы я позвонил бабушке вчера, она была бы рада.",
    "Я собираюсь навестить друга в больнице завтра.",
    "Этот телефон намного удобнее, чем мой старый.",
    "Эта книга не такая интересная, как та.",
    "Если пойдёт снег, мы слепим снеговика.",
    "Ты когда-нибудь пробовал узбекскую кухню?",
    "На прошлой неделе нам покрасили стены в квартире.",
    "Жаль, что я не взял зонт сегодня утром.",
    "Вчера в парке кормили уток целый час.",
    "Хотя шёл дождь, мы всё равно пошли гулять."
]


def translate_sentence(text: str, target_lang: str) -> str:
    """Translate Russian sentence to target language using YandexGPT."""
    lang_names = {
        "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "ar": "Arabic", "he": "Hebrew"
    }
    lang_name = lang_names.get(target_lang, target_lang.upper())

    prompt = f"""Translate this Russian sentence to {lang_name}.
Use simple, everyday vocabulary (A2-B1 level).
Output ONLY the translated sentence, nothing else.

Russian: {text}"""

    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 150
            },
            "messages": [{"role": "user", "text": prompt}]
        }

        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code != 200:
            logger.error(f"Translation error: {res.status_code} - {res.text}")
            raise Exception(f"YandexGPT returned {res.status_code}")

        response_data = res.json()
        translation = response_data['result']['alternatives'][0]['message']['text'].strip()
        for bad in ['"', '«', '»', '\n']:
            translation = translation.replace(bad, '')

        logger.info(f"Translated to {lang_name}: {translation}")
        return translation

    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"[Translation to {lang_name} failed]"


active_quizzes = {}


async def cleanup_quiz(chat_id: int, delay: int = 30):
    await asyncio.sleep(delay)
    if chat_id in active_quizzes:
        del active_quizzes[chat_id]
        logger.info(f"Quiz expired for chat {chat_id}")


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
            "Пожалуйста, настройте TARGET_CHATS в коде или TARGET_CHAT_CONFIG в .env"
        )
        return

    chat_descriptions = []
    for _, name, langs in TARGET_CHATS:
        lang_str = "+".join(langs).upper()
        chat_descriptions.append(f"{name} ({lang_str})")

    chat_list = ", ".join(chat_descriptions)
    await update.message.reply_text(f"⏳ Генерирую предложения для: {chat_list}...")

    prompts = random.sample(GRAMMAR_STRUCTURES, 6)
    # ONE call for all 6 sentences instead of 6 separate calls
    sentences = generate_russian_sentences_batch(prompts)

    active_quizzes[chat_id] = {
        'sentences': sentences,
        'sent_count': 0,
        'message_id': None
    }

    buttons = []
    for i, sent in enumerate(sentences):
        buttons.append([InlineKeyboardButton(f"📝 {sent}", callback_data=f"send_{i}")])
    buttons.append([InlineKeyboardButton("✅ Готово", callback_data="finish")])

    message = await update.message.reply_text(
        f"🎯 **Выбери предложения для отправки ({len(TARGET_CHATS)} чатов):**\n\n"
        "• Нажми на предложение чтобы отправить его\n"
        "• Кнопки активны 30 секунд\n"
        "• Нажми '✅ Готово' когда закончишь",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    active_quizzes[chat_id]['message_id'] = message.message_id
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
            russian_sentence = sentences[idx]
            sent_to = []
            failed = []

            for target_id, student_name, langs in TARGET_CHATS:
                try:
                    for lang_code in langs:
                        if lang_code == "ru":
                            await context.bot.send_message(chat_id=target_id, text=russian_sentence)
                        else:
                            translated = translate_sentence(russian_sentence, lang_code)
                            await context.bot.send_message(chat_id=target_id, text=translated)
                        if len(langs) > 1:
                            await asyncio.sleep(0.5)

                    lang_str = "+".join(langs).upper()
                    sent_to.append(f"{student_name} ({lang_str})")
                    logger.info(f"Sentence {idx} sent to {student_name} ({target_id}) in {langs}")
                except Exception as e:
                    failed.append(student_name)
                    logger.error(f"Failed to send to {student_name} ({target_id}): {e}")

            quiz_data['sent_count'] += 1
            sent_count = quiz_data['sent_count']

            status_parts = []
            if sent_to:
                status_parts.append(f"✅ {', '.join(sent_to)}")
            if failed:
                status_parts.append(f"❌ {', '.join(failed)}")
            status_info = f" ({' | '.join(status_parts)})" if status_parts else ""

            await query.edit_message_text(
                f"🎯 **Отправлено: {sent_count}/6{status_info}**\n\n"
                "• Нажми на предложение чтобы отправить его\n"
                "• Кнопки активны 30 секунд\n"
                "• Нажми '✅ Готово' когда закончишь",
                reply_markup=query.message.reply_markup
            )

            confirmation = f"✅ Отправлено в {len(sent_to)} чатов"
            if failed:
                confirmation += f" (не удалось: {len(failed)})"
            confirmation += f": _{russian_sentence}_"

            await context.bot.send_message(chat_id=chat_id, text=confirmation, parse_mode="Markdown")
        else:
            await query.answer("❌ Предложение не найдено", show_alert=True)

    except Exception as e:
        logger.error(f"Send error: {e}")
        await query.answer("❌ Ошибка при отправке", show_alert=True)


# --- Hebrew Reminder Messages (A2 Level) ---
REMINDER_MESSAGES = [
    ("Have you sent the sentences to Elena yet?", "האם שלחת את המשפטים לאלנה עדיין?", "Ha'im shalakhta et ha'mishpatim le'Elena adayin?"),
    ("Has Elena received her grammar practice?", "האם אלנה קיבלה את תרגול הדקדוק שלה?", "Ha'im Elena kibla et targil ha'dikduk shelah?"),
    ("Did you choose sentences for Elena today?", "האם בחרת משפטים לאלנה היום?", "Ha'im bakhart mishpatim le'Elena hayom?"),
    ("Does Elena have material for today?", "האם יש לאלנה חומר להיום?", "Ha'im yesh le'Elena khamer le'hayom?"),
    ("Have you checked if Elena practiced?", "האם בדקת אם אלנה התאמנה?", "Ha'im badakhta im Elena hit'amna?"),
    ("Did you send Hebrew reminders today?", "האם שלחת תזכורות בעברית היום?", "Ha'im shalakhta tizkorot be'Ivrit hayom?"),
    ("Is Elena's grammar practice ready?", "האם תרגול הדקדוק של אלנה מוכן?", "Ha'im targil ha'dikduk shel Elena mukhan?"),
    ("Have you reviewed Elena's progress?", "האם סקרת את ההתקדמות של אלנה?", "Ha'im sakarta et ha'hitkadmut shel Elena?"),
    ("Did you prepare new sentences today?", "האם הכנת משפטים חדשים היום?", "Ha'im hekhanta mishpatim khadashim hayom?"),
    ("Has today's practice been sent?", "האם תרגול היום נשלח?", "Ha'im targil ha'yom nishlakh?"),
    ("Are you helping Elena with grammar?", "האם אתה עוזר לאלנה עם דקדוק?", "Ha'im ata ozer le'Elena im dikduk?"),
    ("Did you remember to send the quiz?", "האם זכרת לשלוח את החידון?", "Ha'im zakhrta lishlakh et ha'khidon?")
]


def send_reminder():
    if not REMINDER_CHAT_ID:
        return
    en, he, trans = random.choice(REMINDER_MESSAGES)
    text = f"{en}\n*{he}*\n_{trans}_"
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def send_async():
            bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build().bot
            await bot.send_message(chat_id=REMINDER_CHAT_ID, text=text, parse_mode="Markdown")

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


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CallbackQueryHandler(send_sentence))
    start_scheduler()
    logger.info("🤖 Starting bot with polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
