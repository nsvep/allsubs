from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import requests

TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'
ADMIN_CHAT_ID = 50274860

WAITING_FOR_USER_ID, WAITING_FOR_RESPONSE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = "https://miniapp-nsvep.amvera.io/"
    keyboard = [
        [InlineKeyboardButton("Open", web_app=WebAppInfo(url=url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Open", reply_markup=reply_markup)


async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    url = f'https://miniapp-nsvep.amvera.io/get_user_subscriptions_for_bot/{telegram_id}'
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

async def manual_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_CHAT_ID:  # Проверка, что команду отправил администратор
        url = 'https://miniapp-nsvep.amvera.io/trigger_manual_update'
        print(f"Sending request to: {url}")  # Отладочное сообщение

        try:
            response = requests.post(url)
            print(f"Response status code: {response.status_code}")  # Отладочное сообщение
            print(f"Response content: {response.text}")  # Отладочное сообщение

            if response.status_code == 200:
                message = "Ручное обновление платежей запущено. Проверьте логи сервера для деталей."
            else:
                message = f"Произошла ошибка при запуске обновления. Код ответа: {response.status_code}"
        except Exception as e:
            message = f"Произошла ошибка при отправке запроса: {str(e)}"

        await update.message.reply_text(message)
    else:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")

async def otvet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return ConversationHandler.END
    
    await update.message.reply_text("Пожалуйста, отправьте Telegram ID пользователя.")
    return WAITING_FOR_USER_ID

async def receive_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.text
    if not user_id.isdigit():
        await update.message.reply_text("Пожалуйста, отправьте корректный Telegram ID (только цифры).")
        return WAITING_FOR_USER_ID
    
    context.user_data['reply_to_user_id'] = int(user_id)
    await update.message.reply_text("Теперь отправьте ваш ответ пользователю.")
    return WAITING_FOR_RESPONSE

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response_text = update.message.text
    user_id = context.user_data['reply_to_user_id']
    
    try:
        message = (
            "*📬 Ответ от службы поддержки*\n\n"
            f"{response_text}\n\n"
            "_Спасибо, что пользуетесь нашим сервисом! "
            "Если у вас есть дополнительные вопросы, не стесняйтесь обращаться._"
        )
        
        await context.bot.send_message(
            chat_id=user_id, 
            text=message,
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"✅ Ответ успешно отправлен пользователю с ID {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка при отправке сообщения: {str(e)}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("otvet", otvet)],
        states={
            WAITING_FOR_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id)],
            WAITING_FOR_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_response)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_subs", my_subs))
    application.add_handler(CommandHandler("update_payments", manual_update))

    application.run_polling()

if __name__ == '__main__':
    main()