from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = "https://d643-95-25-22-90.ngrok-free.app"
    keyboard = [
        [InlineKeyboardButton("Open", web_app=WebAppInfo(url=url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Open", reply_markup=reply_markup)


async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    url = f'https://d643-95-25-22-90.ngrok-free.app/get_user_subscriptions_for_bot/{telegram_id}'
    print(f"Sending request to: {url}")  # Отладочное сообщение

    try:
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")  # Отладочное сообщение
        print(f"Response content: {response.text}")  # Отладочное сообщение

        if response.status_code == 200:
            subscriptions = response.json()
            if subscriptions:
                message = "Ваши подписки:\n\n"
                for sub in subscriptions:
                    message += f"- {sub['service_name']}: {sub['amount']} {sub['currency']}\n"
            else:
                message = "У вас пока нет активных подписок."
        else:
            message = f"Извините, не удалось получить информацию о подписках. Код ответа: {response.status_code}"
    except Exception as e:
        message = f"Произошла ошибка при получении подписок: {str(e)}"

    await update.message.reply_text(message)

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_subs", my_subs))

    application.run_polling()

if __name__ == '__main__':
    main()