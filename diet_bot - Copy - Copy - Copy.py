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

# Enable logging to see errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the conversation
GOAL, WEIGHT, HEIGHT = range(3)

# --- Conversation Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the user's goal."""
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
    """Stores the selected goal and asks for weight."""
    user_choice = update.message.text
    context.user_data['goal'] = user_choice
    
    response_text = ""
    if user_choice == "لاغری":
        response_text = "آفرین! هدف لاغری داری 🔥 نگران نباش، با هم یه برنامه سبک و موثر برات آماده می‌کنیم که هم سالم باشه هم خوشمزه! 🥗🍲"
    elif user_choice == "افزایش وزن":
        response_text = "به به! هدف افزایش وزن داری 💪 آماده‌ای با هم یه برنامه پرانرژی و خوشمزه بچینیم تا به هدفت برسی؟ 🍛🍳"
    elif user_choice == "حفظ وزن":
        response_text = "تبریک! هدفت حفظ وزن هست 😎 بیاید یه برنامه متعادل و سالم بسازیم که بدنت تو فرم بمونه! 🥑🍎"
    elif user_choice == "رژیم ورزشی":
        response_text = "عالیه! 🏋️‍♂️ هدف تو ترکیب رژیم و ورزش هست. با هم یه برنامه غذایی و تمرینی قدرتمند آماده می‌کنیم تا هم انرژی کافی داشته باشی هم عضلاتت رشد کنه! 💪🥗"

    await update.message.reply_text(
        f"{response_text}\n\n"
        "حالا که هدف رو مشخص کردیم، وقتشه وزن خودت رو (به کیلوگرم) بهم بگی تا برنامه دقیق و شخصی برات آماده کنم! 💪",
        reply_markup=ReplyKeyboardRemove(),
    )
    return WEIGHT

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the weight and asks for height."""
    user_weight = update.message.text
    context.user_data['weight'] = user_weight
    logger.info(f"Weight of {update.effective_user.first_name}: {user_weight}")
    
    await update.message.reply_text("عالی! قدت چند سانتی‌متره؟ 📏")
    
    return HEIGHT

# --- AI Integration Function (for OpenRouter) ---
async def generate_diet_suggestion(info: dict) -> str:
    """Sends user info to the OpenRouter AI and gets a diet suggestion."""
    
    client = openai.AsyncOpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key="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", # !!! کلید API خود را که از سایت OpenRouter گرفته‌اید، اینجا قرار دهید !!!
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
          messages=[
            {
              "role": "user",
              "content": prompt,
            },
          ],
          # --- این خط با شناسه مدل جدید به‌روزرسانی شد ---
          model="x-ai/grok-4-fast:free",
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"--- DETAILED OPENROUTER ERROR: {e} ---")
        logger.error(f"Error calling OpenRouter AI API: {e}")
        return "متاسفانه در حال حاضر ارتباط با سرویس هوش مصنوعی OpenRouter ممکن نیست. لطفاً بعداً تلاش کنید."

# --- Modified height function to call the AI ---
async def height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the height, calls the AI, and shows the suggestion."""
    user_height = update.message.text
    context.user_data['height'] = user_height
    logger.info(f"Height of {update.effective_user.first_name}: {user_height}")
    
    await update.message.reply_text("عالی! اطلاعاتت ثبت شد. لطفاً چند لحظه صبر کن تا یک برنامه غذایی هوشمند برایت آماده کنم...")
    
    ai_suggestion = await generate_diet_suggestion(context.user_data)
    
    await update.message.reply_text(
        f"{ai_suggestion}\n\n"
        "این فقط یک شروع است! در آینده برنامه‌های کامل‌تری دریافت خواهی کرد. 💪",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "باشه، هر وقت آماده بودی من اینجام. برای شروع دوباره /start رو بزن.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    timezone = pytz.utc
    job_queue = JobQueue()
    job_queue.scheduler.configure(timezone=timezone)

    # !!! توکن ربات تلگرام خود را در اینجا جایگزین کنید !!!
    application = (
        Application.builder()
        .token("8228747943:AAGtBrH0UcgubwFLLYGtiXBT1ZR1MxG-nX4")
        .job_queue(job_queue)
        .build()
    )

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