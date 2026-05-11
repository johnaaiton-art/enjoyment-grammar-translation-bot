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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
REMINDER_CHAT_ID = os.getenv("REMINDER_CHAT_ID")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

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

# --- Grammar Structures (narrowed to Elena's current focus) ---
# Conditionals 1/2/3, wish (present + past regret), modals of speculation
# (past + present), comparatives (not quite as / not nearly as),
# "the sooner the better".
GRAMMAR_STRUCTURES = [
    "First conditional: If it rains, we will stay at home.",
    "Second conditional: If I had more time, I would learn Spanish.",
    "Third conditional: If I had studied, I would have passed the exam.",
    "Wish (present regret): I wish I had more time.",
    "Wish (past regret): I wish I had gone to the party yesterday.",
    "Must have + past participle (speculation about past): She must have forgotten.",
    "Might have + past participle (speculation about past): He might have left already.",
    "Must + infinitive (speculation about present): She must be tired.",
    "Might + infinitive (speculation about present): He might be at home.",
    "Not quite as ... as ...: This coffee is not quite as strong as the last one.",
    "Not nearly as ... as ...: My old phone is not nearly as fast as the new one.",
    "The sooner the better: We should book the tickets — the sooner the better.",
]

# --- Topics as NOUN PHRASES — kept simple and everyday for Elena (A2) ---
TOPIC_CATEGORIES = [
    # Food & Cooking — very basic
    ["soup", "tea", "a cake", "breakfast", "an apple",
     "dinner", "coffee", "bread", "ice cream", "pizza"],
    # Nature & Weather — simple
    ["rain", "snow", "the sun", "the wind", "a flower",
     "the sea", "a cat in the yard", "the park", "a dog", "summer"],
    # Home & Daily Life
    ["new shoes", "the keys", "a book", "the TV", "a phone",
     "the bus", "the kitchen", "a chair", "a lamp", "a clock"],
    # People
    ["mum", "dad", "a friend", "the neighbour", "a colleague",
     "my sister", "my brother", "the doctor", "a child", "grandma"],
    # Travel & Transport
    ["the bus", "a taxi", "the train", "the airport", "a holiday",
     "the metro", "a small hotel", "the beach", "the road", "a map"],
    # Work & Study
    ["work", "a meeting", "homework", "an email", "a phone call",
     "the office", "a report", "a course", "a teacher", "a lesson"],
    # Hobbies & Free Time
    ["a walk", "a film", "music", "a book", "a game",
     "a photo", "the radio", "tennis", "yoga", "dancing"],
    # Health
    ["a headache", "vitamins", "water", "sleep", "fresh air",
     "a cold", "running", "the gym", "a long walk", "good food"],
]

recent_topics_used = []
MAX_RECENT = 30


def get_unique_topics(n: int) -> list:
    """Pick N topics that haven't been used recently, preferring different categories."""
    available_by_cat = [
        [t for t in cat if t not in recent_topics_used]
        for cat in TOPIC_CATEGORIES
    ]
    available_by_cat = [cat for cat in available_by_cat if cat]

    picked = []
    random.shuffle(available_by_cat)
    for cat in available_by_cat:
        if len(picked) >= n:
            break
        picked.append(random.choice(cat))

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


def _call_deepseek(prompt: str, temperature: float = 0.8, max_tokens: int = 600) -> str:
    """Call DeepSeek chat completions and return the assistant text."""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    res = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
    if res.status_code != 200:
        logger.error(f"DeepSeek error: {res.status_code} - {res.text}")
        raise Exception(f"DeepSeek returned {res.status_code}")
    data = res.json()
    return data["choices"][0]["message"]["content"].strip()


# --- BATCHED generation: all N sentences in ONE API call ---
def generate_russian_sentences_batch(structures: list) -> list:
    """Generate N Russian sentences in a single call. EASY level for Elena (A2)."""
    n = len(structures)
    topics = get_unique_topics(n)

    numbered_tasks = "\n".join(
        f"{i+1}. TARGET GRAMMAR (must be the main clause): {s}\n"
        f"   Topic (weave in naturally): {topics[i]}"
        for i, s in enumerate(structures)
    )

    prompt = f"""You are writing SHORT, EASY Russian sentences for a real-beginner adult student (A2 level).
The student translates them into English to practise SPECIFIC English grammar.
Recently she said the sentences feel too hard and complicated, so this round must feel FRIENDLY and DOABLE.

TASKS:
{numbered_tasks}

HARD RULES — follow ALL of them:
1. SHORT. Each sentence MUST be 6–12 words. No long sentences. No nested clauses.
2. SIMPLE everyday vocabulary only — words a beginner adult knows (food, family, home, weather, work, transport, hobbies).
3. The TARGET GRAMMAR is the MAIN CLAUSE — never hidden inside a subordinate or reported structure.
4. NO literary, formal, or "tricky" wording. Plain, conversational Russian, like spoken in normal life.
5. No idioms. No proverbs. No rare vocabulary. No abstract topics.
6. Use the right Russian construction for each English grammar:
   - First conditional → "Если + present, будущее" (Если пойдёт дождь, мы останемся дома.)
   - Second conditional → "Если бы + past, past + бы" (Если бы у меня было время, я бы выучила испанский.)
   - Third conditional → "Если бы + past (perfective), past + бы" referring to the past (Если бы я позанималась, я бы сдала экзамен.)
   - Wish (present) → "Жаль, что у меня нет ..." or "Хотела бы я иметь больше времени."
   - Wish (past) → "Жаль, что я не пошла ..." (regret about something that already happened)
   - Must have (past speculation) → "Наверное, она забыла." / "Должно быть, он ушёл."
   - Might have (past speculation) → "Возможно, он уже ушёл." / "Может быть, она забыла."
   - Must (present speculation) → "Наверное, она устала." / "Должно быть, он дома."
   - Might (present speculation) → "Возможно, он дома." / "Может быть, она устала."
   - Not quite as ... as ... → "Этот кофе не такой крепкий, как прошлый." (small difference)
   - Not nearly as ... as ... → "Мой старый телефон совсем не такой быстрый, как новый." (big difference)
   - "The sooner the better" → "Чем раньше, тем лучше."
7. Across the {n} sentences, no two may start with the same word. Mix subjects (я, мы, ты, он, она, они, impersonal).

SELF-CHECK before outputting each sentence:
- Is it 6–12 words? If longer, SHORTEN it.
- Is the target grammar obvious in the main clause? If not, REWRITE.
- Could a real A2 beginner translate this without panicking? If not, SIMPLIFY.

OUTPUT FORMAT (follow exactly, nothing else):
1. <Russian sentence>
2. <Russian sentence>
...

No explanations, no English, no quotation marks, no bold. Just numbered Russian sentences."""

    try:
        logger.info(f"Calling DeepSeek (batch of {n}) | Topics: {topics}")
        raw = _call_deepseek(prompt, temperature=0.8, max_tokens=600)
        logger.info(f"Raw batch output:\n{raw}")

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


# Fallback sentences — short, easy, target Elena's specific grammar list.
FALLBACK_SENTENCES = [
    "Если пойдёт дождь, мы останемся дома.",                        # 1st cond
    "Если бы у меня было время, я бы выучила испанский.",           # 2nd cond
    "Если бы я позанималась, я бы сдала экзамен.",                  # 3rd cond
    "Жаль, что у меня нет больше времени.",                          # wish (present)
    "Жаль, что я не пошла вчера на вечеринку.",                      # wish (past)
    "Наверное, она забыла про встречу.",                             # must have
    "Возможно, он уже ушёл домой.",                                  # might have
    "Должно быть, она устала после работы.",                         # must (present)
    "Может быть, он дома сейчас.",                                   # might (present)
    "Этот кофе не такой крепкий, как прошлый.",                      # not quite as
    "Мой старый телефон совсем не такой быстрый, как новый.",        # not nearly as
    "Чем раньше, тем лучше.",                                        # the sooner the better
]


def translate_sentence(text: str, target_lang: str) -> str:
    """Translate Russian sentence to target language using DeepSeek."""
    lang_names = {
        "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "ar": "Arabic", "he": "Hebrew",
        "en": "English"
    }
    lang_name = lang_names.get(target_lang, target_lang.upper())

    prompt = f"""Translate this Russian sentence to {lang_name}.
Use simple, everyday A2-level vocabulary.
Keep it short and natural.
Output ONLY the translated sentence, nothing else — no quotes, no notes.

Russian: {text}"""

    try:
        translation = _call_deepseek(prompt, temperature=0.3, max_tokens=150)
        for bad in ['"', '«', '»', '\n']:
            translation = translation.replace(bad, '')
        logger.info(f"Translated to {lang_name}: {translation}")
        return translation.strip()

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
