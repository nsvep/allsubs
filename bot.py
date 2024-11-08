from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = "https://7ae3-95-25-19-47.ngrok-free.app"
    keyboard = [
        [InlineKeyboardButton("Open", web_app=WebAppInfo(url=url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Open", reply_markup=reply_markup)


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.run_polling()

if __name__ == '__main__':
    main()