import logging
import pytz
import openai
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    JobQueue,
)
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

GOAL, WEIGHT, HEIGHT = range(3)

# --- Conversation Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["لاغری", "افزایش وزن"], ["حفظ وزن", "رژیم ورزشی"]]
    await update.message.reply_text(
        "✨ سلام! خوش اومدی به دستیار رژیمی Mz_Diet 🥗💪\n\n"
        "✨ اول از همه بهم بگو، هدف اصلی تو از رژیم گرفتن چیه؟",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="هدفت چیه؟", resize_keyboard=True
        ),
    )
    return GOAL

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    context.user_data['goal'] = user_choice
    response_text = {
        "لاغری": "آفرین! هدف لاغری داری 🔥 نگران نباش، با هم یه برنامه سبک و موثر برات آماده می‌کنیم که هم سالم باشه هم خوشمزه! 🥗🍲",
        "افزایش وزن": "به به! هدف افزایش وزن داری 💪 آماده‌ای با هم یه برنامه پرانرژی و خوشمزه بچینیم تا به هدفت برسی؟ 🍛🍳",
        "حفظ وزن": "تبریک! هدفت حفظ وزن هست 😎 بیاید یه برنامه متعادل و سالم بسازیم که بدنت تو فرم بمونه! 🥑🍎",
        "رژیم ورزشی": "عالیه! 🏋️‍♂️ هدف تو ترکیب رژیم و ورزش هست. با هم یه برنامه غذایی و تمرینی قدرتمند آماده می‌کنیم تا هم انرژی کافی داشته باشی هم عضلاتت رشد کنه! 💪🥗"
    }.get(user_choice, "")
    
    await update.message.reply_text(
        f"{response_text}\n\nحالا که هدف رو مشخص کردیم، وقتشه وزن خودت رو (به کیلوگرم) بهم بگی تا برنامه دقیق و شخصی برات آماده کنم! 💪",
        reply_markup=ReplyKeyboardRemove(),
    )
    return WEIGHT

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_weight = update.message.text
    context.user_data['weight'] = user_weight
    logger.info(f"Weight of {update.effective_user.first_name}: {user_weight}")
    await update.message.reply_text("عالی! قدت چند سانتی‌متره؟ 📏")
    return HEIGHT

async def generate_diet_suggestion(info: dict) -> str:
    client = openai.AsyncOpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.environ.get("OPENAI_API_KEY"),
    )
    
    prompt = (
        "شما یک متخصص و مربی تغذیه بسیار حرفه‌ای و دقیق به زبان فارسی هستید. "
        "وظیفه شما تهیه یک برنامه غذایی کامل و سالم برای یک روز (شامل صبحانه، ناهار، شام و دو میان‌وعده) "
        f"برای فردی با اطلاعات زیر است:\n\n"
        f"- هدف: {info.get('goal')}\n"
        f"- وزن: {info.get('weight')} کیلوگرم\n"
        f"- قد: {info.get('height')} سانتی‌متر\n\n"
        "قوانین خروجی:\n"
        "- برنامه باید شامل نام غذاها، مواد اصلی تشکیل‌دهنده، و مقدار تقریبی کالری برای هر وعده باشد.\n"
        "- پاسخ باید فقط به زبان فارسی روان و طبیعی باشد.\n"
        "- از هرگونه توضیحات اضافی، مقدمه‌چینی یا نتیجه‌گیری خودداری کن.\n"
        "- پاسخ خود را با '**برنامه غذایی هوشمند شما برای امروز:**' شروع کن."
    )
        
    try:
        completion = await client.chat.completions.create(
          messages=[{"role": "user", "content": prompt}],
          model="x-ai/grok-4-fast:free",
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenRouter AI API: {e}")
        return "متاسفانه در حال حاضر ارتباط با سرویس هوش مصنوعی OpenRouter ممکن نیست. لطفاً بعداً تلاش کنید."

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_height = update.message.text
    context.user_data['height'] = user_height
    logger.info(f"Height of {update.effective_user.first_name}: {user_height}")
    await update.message.reply_text("عالی! اطلاعاتت ثبت شد. لطفاً چند لحظه صبر کن تا یک برنامه غذایی هوشمند برایت آماده کنم...")
    ai_suggestion = await generate_diet_suggestion(context.user_data)
    await update.message.reply_text(f"{ai_suggestion}\n\nاین فقط یک شروع است! در آینده برنامه‌های کامل‌تری دریافت خواهی کرد. 💪", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("باشه، هر وقت آماده بودی من اینجام. برای شروع دوباره /start رو بزن.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    timezone = pytz.utc
    job_queue = JobQueue()
    job_queue.scheduler.configure(timezone=timezone)

    application = Application.builder().token(os.environ.get("TELEGRAM_TOKEN")).job_queue(job_queue).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GOAL: [MessageHandler(filters.Regex("^(لاغری|افزایش وزن|حفظ وزن|رژیم ورزشی)$"), goal)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
