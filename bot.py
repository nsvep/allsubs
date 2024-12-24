from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice, Invoice, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, PreCheckoutQueryHandler
import requests

# Constants
TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'
ADMIN_CHAT_ID = 50274860
PAYMENT_PROVIDER_TOKEN = ''  # Замените на ваш токен платежного провайдера
FEEDBACK_GROUP_ID = -1002264720815

WAITING_FOR_USER_ID, WAITING_FOR_RESPONSE = range(2)

PREMIUM_PLANS = {
    '1': {'duration': '1 месяц', 'price': 1, 'emoji': '🚀'},
    '6': {'duration': '6 месяцев', 'price': 445, 'emoji': '🌟'},
    '12': {'duration': '1 год', 'price': 890, 'emoji': '💎'},
    '24': {'duration': '2 года', 'price': 1558, 'emoji': '👑'}
}

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = "https://miniapp-nsvep.amvera.io/"
    keyboard = [
        [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Добро пожаловать в менеджер подписок!\n\n"
        "🔹 Отслеживайте свои подписки\n"
        "🔹 Анализируйте расходы\n"
        "🔹 Получайте уведомления\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=reply_markup
    )

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    url = f'https://miniapp-nsvep.amvera.io/get_user_subscriptions_for_bot/{telegram_id}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            subscriptions = response.json()
            if subscriptions:
                message = "📊 *Ваши активные подписки:*\n\n"
                for sub in subscriptions:
                    message += f"🔸 *{sub['service_name']}*: {sub['amount']} {sub['currency']}\n"
            else:
                message = "🔍 У вас пока нет активных подписок."
        else:
            message = f"😕 Извините, не удалось получить информацию о подписках. Попробуйте позже."
    except Exception as e:
        message = f"❌ Произошла ошибка при получении подписок: {str(e)}"

    await update.message.reply_text(message, parse_mode='Markdown')

async def manual_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_CHAT_ID:
        url = 'https://miniapp-nsvep.amvera.io/trigger_manual_update'
        try:
            response = requests.post(url)
            if response.status_code == 200:
                message = "✅ Ручное обновление платежей запущено. Проверьте логи сервера для деталей."
            else:
                message = f"❌ Произошла ошибка при запуске обновления. Код ответа: {response.status_code}"
        except Exception as e:
            message = f"❌ Произошла ошибка при отправке запроса: {str(e)}"
    else:
        message = "🚫 У вас нет прав для выполнения этой команды."

    await update.message.reply_text(message)

async def otvet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("🚫 У вас нет прав для выполнения этой команды.")
        return ConversationHandler.END
    
    await update.message.reply_text("📝 Пожалуйста, отправьте Telegram ID пользователя. Для отмены введите /cancel")
    return WAITING_FOR_USER_ID

async def receive_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.text
    context.user_data['reply_to_user_id'] = user_id
    await update.message.reply_text(f"👤 ID пользователя: {user_id}\n\n📩 Теперь отправьте ваш ответ пользователю:")
    return WAITING_FOR_RESPONSE

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response_text = update.message.text
    user_id = context.user_data['reply_to_user_id']
    
    try:
        message = (
            "*📬 Ответ от службы поддержки*\n\n"
            f"{response_text}\n\n"
            "_Спасибо, что пользуетесь нашим сервисом! "
            "Если у вас есть дополнительные вопросы, повторно воспользуйтесь формой обратной связи._"
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
    await update.message.reply_text("🚫 Операция отменена.")
    return ConversationHandler.END

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for duration, plan in PREMIUM_PLANS.items():
        button_text = f"{plan['emoji']} {plan['duration']} - {plan['price']} Telegram Stars"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"premium_{duration}_{plan['price']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🌟 *Выберите план Premium подписки* 🌟\n\n"
        "Премиум доступ открывает для вас:\n"
        "✅ Неограниченное количество подписок\n"
        "✅ Приоритетная поддержка\n"
        "✅ Эксклюзивные функции\n\n"
        "Выберите подходящий вам план:"
    )
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    duration, amount = query.data.split('_')[1:]
    plan = PREMIUM_PLANS[duration]
    
    title = f"Премиум подписка на {plan['duration']}"
    description = (
        f"🚀 Активируйте премиум доступ на {plan['duration']} и откройте для себя "
        f"мир неограниченных возможностей управления подписками!"
    )
    payload = f"premium_{duration}_{amount}"
    currency = "XTR"
    prices = [LabeledPrice("Премиум подписка", int(plan['price']))]
    
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
        start_parameter="premium-subscription"
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("premium_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Что-то пошло не так, попробуйте еще раз.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment_info = update.message.successful_payment
    duration = payment_info.invoice_payload.split('_')[1]
    user_id = update.effective_user.id
    plan = PREMIUM_PLANS[duration]
    
    # Отправляем запрос на обновление премиум статуса
    response = requests.post('https://miniapp-nsvep.amvera.io/update_premium_status', json={
        'user_id': user_id,
        'duration': int(duration)
    })
    
    if response.status_code == 200:
        await update.message.reply_text(
            f"🎉 Поздравляем! Ваша премиум подписка на {plan['duration']} успешно активирована.\n"
            f"Сумма оплаты: {payment_info.total_amount} Telegram Stars ⭐\n"
            "Наслаждайтесь расширенными возможностями!"
        )
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при активации премиум статуса. Пожалуйста, свяжитесь с поддержкой."
        )

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_subs", my_subs))
    application.add_handler(CommandHandler("manual_update", manual_update))
    application.add_handler(CommandHandler("premium", premium_command))

    # Обработчик для ответа пользователю
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("otvet", otvet)],
        states={
            WAITING_FOR_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_id)],
            WAITING_FOR_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_response)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Обработчики для премиум подписки
    application.add_handler(CallbackQueryHandler(premium_callback, pattern="^premium_"))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    application.run_polling()

if __name__ == '__main__':
    main()