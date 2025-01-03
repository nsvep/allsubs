from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, date, timedelta, time
from calendar import monthrange
from sqlalchemy.sql import func, extract
import pytz
from dateutil.relativedelta import relativedelta
from flask_cors import CORS
import logging
import requests
from sqlalchemy import or_
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import typefmt

TELEGRAM_BOT_TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'
ADMIN_CHAT_ID = 50274860  # Здесь нужно указать chat_id администратора
FEEDBACK_GROUP_ID = -1002264720815

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub?options=-c%20timezone=Europe/Moscow'
app.config['SECRET_KEY'] = 'aboba_sin_sobaki'
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    is_premium = db.Column(db.Boolean, default=False)
    premium_expired = db.Column(db.DateTime, nullable=True)
    runapp = db.Column(db.Integer, default=0)
    telegram_theme = db.Column(db.String(10), default='light')


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    next_payment_date = db.Column(db.Date)
    billing_cycle = db.Column(db.String(10), nullable=False, default='monthly')
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    bank = db.Column(db.String(50))
    card_last_4 = db.Column(db.String(4))
    send_notifications = db.Column(db.Boolean, default=False)
    total_spent = db.Column(db.Float, default=0)
    last_payment_date = db.Column(db.Date)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))

    category = db.relationship('Category', backref=db.backref('subscriptions', lazy=True))
    payments = db.relationship('Payment', backref='subscription', lazy=True, cascade="all, delete-orphan")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, user_id, subscription_id, payment_date, amount):
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.payment_date = payment_date
        self.amount = amount

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __str__(self):
        return self.name

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('services', lazy=True))
    is_custom = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'category_id': self.category_id, 'is_custom': self.is_custom}
    
class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(3), nullable=False, unique=True)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

###АДМИНКА
def date_format(view, value):
    return value.strftime('%d.%m.%Y %H:%M:%S')

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        # Здесь вы можете добавить проверку аутентификации
        return True  # Замените на вашу логику аутентификации

class BaseModelView(ModelView):
    page_size = 50  # Количество элементов на странице
    can_export = True  # Разрешить экспорт данных
    can_view_details = True  # Добавить страницу с деталями
    column_default_sort = ('id', True)  # Сортировка по умолчанию

    column_type_formatters = {
        datetime: date_format
    }

# Создаем пользовательские представления для моделей
class UserView(BaseModelView):
    column_exclude_list = ['created_at']
    column_searchable_list = ['telegram_id', 'first_name', 'last_name', 'username']
    column_filters = ['created_at', 'telegram_id', 'is_premium']
    column_labels = {
        'id': 'ID',
        'telegram_id': 'Telegram ID',
        'first_name': 'Имя',
        'last_name': 'Фамилия',
        'username': 'Имя пользователя',
        'created_at': 'Дата создания',
        'is_premium': 'Премиум статус'
    }
    column_list = ['id', 'telegram_id', 'first_name', 'last_name', 'username', 'created_at', 'is_premium']
    column_default_sort = ('id', True)

    form_columns = ('telegram_id', 'first_name', 'last_name', 'username', 'is_premium')

    def _telegram_id_formatter(view, context, model, name):
        return f"{model.telegram_id}"

    column_formatters = {
        'telegram_id': _telegram_id_formatter
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_at = datetime.now(pytz.timezone('Europe/Moscow'))

class SubscriptionView(BaseModelView):
    column_exclude_list = ['created_at']
    column_searchable_list = ['service_name', 'user.telegram_id', 'category.name']
    column_filters = ['start_date', 'next_payment_date', 'amount', 'is_archived', 'user.telegram_id', 'category.name']
    column_labels = {
        'user.id': 'ID пользователя',
        'user.telegram_id': 'Telegram ID',
        'service_name': 'Сервис',
        'category.name': 'Категория',
        'start_date': 'Дата начала',
        'next_payment_date': 'Следующая оплата',
        'amount': 'Сумма',
        'currency': 'Валюта',
        'is_archived': 'Архивирован'
    }
    column_list = ['id', 'user.id', 'user.telegram_id', 'service_name', 'category.name', 'start_date', 'next_payment_date', 'amount', 'currency', 'is_archived']

    def _user_formatter(view, context, model, name):
        if model.user:
            return f"{model.user.id} (Telegram ID: {model.user.telegram_id})"
        return ""

    column_formatters = {
        'user.id': _user_formatter,
        'category.name': lambda v, c, m, p: m.category.name if m.category else ""
    }

class CategoryView(BaseModelView):
    column_searchable_list = ['name']
    column_labels = {'name': 'Название категории'}

class ServiceView(BaseModelView):
    column_searchable_list = ['name', 'category.name']
    column_filters = ['category.name', 'is_custom']
    column_labels = {
        'name': 'Название сервиса',
        'category.name': 'Категория',
        'is_custom': 'Пользовательский'
    }
    column_list = ['id', 'name', 'category.name', 'is_custom']

    column_formatters = {
        'category.name': lambda v, c, m, p: m.category.name if m.category else ""
    }

class PaymentView(BaseModelView):
    column_searchable_list = ['subscription_id', 'payment_date']
    column_filters = ['payment_date', 'amount']
    column_labels = {
        'user': 'Пользователь',
        'subscription': 'Подписка',
        'payment_date': 'Дата оплаты',
        'amount': 'Сумма'
    }

admin = Admin(app, name='Менеджер подписок', template_mode='bootstrap3')
# Добавляем представления в админку
admin.add_view(UserView(User, db.session, name='Пользователи'))
admin.add_view(SubscriptionView(Subscription, db.session, name='Подписки'))
admin.add_view(CategoryView(Category, db.session, name='Категории'))
admin.add_view(ServiceView(Service, db.session, name='Сервисы'))
admin.add_view(PaymentView(Payment, db.session, name='Платежи'))
admin.add_view(ModelView(Currency, db.session, name='Валюты'))
admin.add_view(ModelView(Bank, db.session, name='Банки'))

###АДМИНКА
def update_subscription_payments():
    import traceback
    stack = traceback.extract_stack()
    send_admin_message(f"update_subscription_payments called from: {stack[-2][0]}:{stack[-2][1]}")
    with app.app_context():
        tz = pytz.timezone('Europe/Moscow')
        today = datetime.now(tz).date()
        start_message = f"update_subscription_payments started for date: {today}"
        send_admin_message(start_message)

        try:
            subscriptions = Subscription.query.filter_by(is_archived=False).all()
            send_admin_message(f"Total active subscriptions found: {len(subscriptions)}")

            for subscription in subscriptions:
                try:
                    send_admin_message(f"Processing subscription ID: {subscription.id}")

                    # Проверяем и сбрасываем last_payment_date, если она в будущем
                    if subscription.last_payment_date and subscription.last_payment_date > today:
                        send_admin_message(f"  Resetting future last_payment_date from {subscription.last_payment_date} to None")
                        subscription.last_payment_date = None

                    # Устанавливаем next_payment_date, если она не установлена
                    if not subscription.next_payment_date:
                        subscription.next_payment_date = subscription.start_date
                        send_admin_message(f"  Setting initial next_payment_date to: {subscription.next_payment_date}")

                    # Создаем платежи для всех прошедших дат до сегодняшнего дня
                    while subscription.next_payment_date and subscription.next_payment_date <= today:
                        existing_payment = Payment.query.filter_by(
                            subscription_id=subscription.id,
                            payment_date=subscription.next_payment_date
                        ).first()

                        if not existing_payment:
                            payment = Payment(
                                user_id=subscription.user_id,
                                subscription_id=subscription.id,
                                payment_date=subscription.next_payment_date,
                                amount=subscription.amount
                            )
                            db.session.add(payment)
                            subscription.total_spent += subscription.amount
                            send_admin_message(f"  Created payment for date: {subscription.next_payment_date}")

                        subscription.last_payment_date = subscription.next_payment_date

                        # Обновляем next_payment_date
                        if subscription.billing_cycle == 'monthly':
                            subscription.next_payment_date += relativedelta(months=1)
                        else:  # yearly
                            subscription.next_payment_date += relativedelta(years=1)

                    db.session.commit()
                    send_admin_message(f"Subscription ID: {subscription.id} processed successfully")

                except Exception as e:
                    error_message = f"Error processing subscription {subscription.id}: {str(e)}"
                    send_admin_message(error_message)
                    app.logger.error(error_message)
                    db.session.rollback()

        except Exception as e:
            error_message = f"Error in update_subscription_payments: {str(e)}"
            send_admin_message(error_message)
            app.logger.error(error_message)

        end_time = datetime.now(tz)
        end_message = f"update_subscription_payments finished at {end_time}"
        send_admin_message(end_message)
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manual_update_payments', methods=['POST'])
def manual_update_payments():
    update_subscription_payments()
    return jsonify({"message": "Manual update completed. Check server logs for details."})


@app.route('/reset_last_payment_date/<int:subscription_id>', methods=['POST'])
def reset_last_payment_date(subscription_id):
    with app.app_context():
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({"error": "Subscription not found"}), 404

        old_date = subscription.last_payment_date
        subscription.last_payment_date = None
        db.session.commit()

        return jsonify({
            "message": "Last payment date reset successfully",
            "old_date": old_date.isoformat() if old_date else None,
            "new_date": None
        })

@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    data = request.json
    if not data or 'user' not in data or 'theme' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    user_data = data['user']
    theme = data['theme']
    user = User.query.filter_by(telegram_id=user_data['id']).first()

    if user:
        user.runapp += 1
        user.telegram_theme = theme  # Обновляем тему
    else:
        user = User(
            telegram_id=user_data['id'],
            first_name=user_data['first_name'],
            last_name=user_data.get('last_name', ''),
            username=user_data.get('username', ''),
            runapp=1,
            telegram_theme=theme  # Устанавливаем тему для нового пользователя
        )
        db.session.add(user)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'user_id': user.id,
        'runapp': user.runapp,
        'telegram_theme': user.telegram_theme
    })


@app.route('/get_subscriptions/<int:user_id>')
def get_subscriptions(user_id):
    subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=False).all()
    result = [{
        'id': sub.id,
        'service_name': sub.service_name,
        'category_name': sub.category.name,
        'start_date': sub.start_date.strftime('%Y-%m-%d'),
        'billing_cycle': sub.billing_cycle,
        'amount': sub.amount,
        'currency': sub.currency,
        'bank': sub.bank,
        'card_last_4': sub.card_last_4,
        'next_payment_date': sub.next_payment_date.strftime('%Y-%m-%d') if sub.next_payment_date else None,
        'last_payment_date': sub.last_payment_date.strftime('%Y-%m-%d') if sub.last_payment_date else None,
        'total_spent': sub.total_spent,
        'send_notifications': sub.send_notifications
    } for sub in subscriptions]

    # Сортировка по дате следующего платежа
    result.sort(key=lambda x: x['next_payment_date'] or '9999-12-31')

    app.logger.info(f"Active subscriptions data for user {user_id}: {result}")
    return jsonify(result)


@app.route('/get_subscription/<int:subscription_id>')
def get_subscription(subscription_id):
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"status": "error", "message": "Подписка не найдена"}), 404

    return jsonify({
        'id': subscription.id,
        'service_name': subscription.service_name,
        'start_date': subscription.start_date.strftime('%Y-%m-%d'),
        'amount': subscription.amount,
        'currency': subscription.currency,
        'bank': subscription.bank,
        'card_last_4': subscription.card_last_4, 
        'billing_cycle': subscription.billing_cycle
    })


@app.route('/get_categories')
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])


@app.route('/get_services')
def get_services():
    services = Service.query.filter_by(is_custom=False).all()
    return jsonify([service.to_dict() for service in services])


@app.route('/add_custom_service', methods=['POST'])
def add_custom_service():
    data = request.json
    new_service = Service(
        name=data['service_name'],
        category_id=data['category_id'],
        is_custom=True
    )
    db.session.add(new_service)
    db.session.commit()
    return jsonify(new_service.to_dict())


@app.route('/add_subscription', methods=['POST'])
def add_subscription():
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")

        required_fields = ['user_id', 'service_name', 'next_payment_date', 'amount', 'currency']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Проверка даты следующего платежа
        start_date = datetime.strptime(data['next_payment_date'], '%Y-%m-%d').date()
        if start_date < date.today():
            return jsonify({"status": "error", "message": "Дата следующего платежа не может быть в прошлом"}), 400

        user = User.query.get(int(data['user_id']))
        if not user:
            raise ValueError(f"User with id {data['user_id']} does not exist")

        service_name = data['service_name']
        category_id = data.get('category_id')

        if service_name.isdigit():
            service = Service.query.get(int(service_name))
        else:
            service = Service.query.filter_by(name=service_name).first()

        if service:
            service_name = service.name
            category_id = service.category_id
        else:
            if category_id is None:
                other_category = Category.query.filter_by(name="Другое").first()
                if not other_category:
                    other_category = Category(name="Другое")
                    db.session.add(other_category)
                    db.session.commit()
                category_id = other_category.id

            new_service = Service(name=service_name, category_id=category_id, is_custom=True)
            db.session.add(new_service)
            db.session.commit()

        new_sub = Subscription(
            user_id=user.id,
            service_name=service_name,
            category_id=category_id,
            start_date=start_date,
            billing_cycle=data['billing_cycle'],
            amount=float(data['amount']),
            total_spent=0,
            currency=data['currency'],
            bank=data.get('bank'),
            card_last_4=data.get('card_last_4'),
            send_notifications=data.get('send_notifications', False),
            next_payment_date=start_date,
            last_payment_date=None
        )

        db.session.add(new_sub)
        db.session.commit()

        return jsonify({"status": "success", "id": new_sub.id})

    except Exception as e:
        app.logger.error(f"Error in add_subscription: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_subscription/<int:subscription_id>', methods=['DELETE'])
def delete_subscription(subscription_id):
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"status": "error", "message": "Подписка не найдена"}), 404

    db.session.delete(subscription)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/get_subscription_dates/<int:user_id>/<int:year>/<int:month>')
def get_subscription_dates(user_id, year, month):
    print(f"get_subscription_dates called with user_id={user_id}, year={year}, month={month}")
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    subscriptions = Subscription.query.filter(
        Subscription.user_id == user_id,
        Subscription.start_date >= start_date,
        Subscription.start_date <= end_date
    ).all()

    dates = {}
    for sub in subscriptions:
        day = sub.start_date.day
        if day not in dates:
            dates[day] = []
        dates[day].append({
            'id': sub.id,
            'service_name': sub.service_name,
            'amount': sub.amount,
            'currency': sub.currency
        })
    print(f"Returning dates: {dates}")
    return jsonify(dates)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/get_payment_history/<int:subscription_id>')
def get_payment_history(subscription_id):
    payments = Payment.query.filter_by(subscription_id=subscription_id).order_by(Payment.payment_date.desc()).all()
    return jsonify([{
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'amount': payment.amount
    } for payment in payments])

@app.route('/archive_subscription/<int:subscription_id>', methods=['POST'])
def archive_subscription(subscription_id):
    with app.app_context():
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({"error": "Subscription not found"}), 404

        subscription.is_archived = True
        subscription.last_payment_date = datetime.now().date()
        db.session.commit()

        return jsonify({
            "message": "Subscription archived successfully",
            "subscription_id": subscription.id,
            "last_payment_date": subscription.last_payment_date.isoformat()
        })

@app.route('/update_subscription/<int:subscription_id>', methods=['POST'])
def update_subscription(subscription_id):
    data = request.json
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"error": "Subscription not found"}), 404

    subscription.service_name = data['service_name']
    subscription.category_id = Category.query.filter_by(name=data['category_name']).first().id
    subscription.amount = data['amount']
    subscription.currency = data['currency']

    db.session.commit()

    app.logger.info(f"Updated subscription: {subscription.id}, {subscription.service_name}")
    return jsonify({"message": "Subscription updated successfully"})


@app.route('/get_user_subscriptions_for_bot/<int:telegram_id>')
def get_user_subscriptions_for_bot(telegram_id):
    app.logger.info(f"Received request for telegram_id: {telegram_id}")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        app.logger.warning(f"User not found for telegram_id: {telegram_id}")
        return jsonify([])

    subscriptions = Subscription.query.filter_by(user_id=user.id, is_archived=False).all()
    app.logger.info(f"Found {len(subscriptions)} subscriptions for user {user.id}")

    result = [{
        'service_name': sub.service_name,
        'amount': sub.amount,
        'currency': sub.currency,
        'billing_cycle': sub.billing_cycle
    } for sub in subscriptions]

    app.logger.info(f"Returning result: {result}")
    return jsonify(result)

@app.route('/profile')
def profile():
    return render_template('index.html')

@app.route('/api/calendar-events')
def calendar_events():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        user_id = int(user_id)
        today = datetime.now().date()

        # Получаем прошлые платежи из таблицы Payment
        past_payments = Payment.query.filter_by(user_id=user_id).filter(Payment.payment_date <= today).all()

        # Получаем будущие платежи из таблицы Subscription
        future_subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=False).filter(Subscription.next_payment_date > today).all()

        events = []

        # Добавляем прошлые платежи
        for payment in past_payments:
            events.append({
                'id': payment.subscription_id,
                'service': payment.subscription.service_name,
                'amount': payment.amount,
                'currency': payment.subscription.currency,
                'date': payment.payment_date.strftime('%Y-%m-%d'),
                'isPast': True
            })

        # Добавляем будущие платежи
        for sub in future_subscriptions:
            events.append({
                'id': sub.id,
                'service': sub.service_name,
                'amount': sub.amount,
                'currency': sub.currency,
                'date': sub.next_payment_date.strftime('%Y-%m-%d'),
                'isPast': False
            })

        # Сортируем события по дате
        events.sort(key=lambda x: x['date'])

        app.logger.info(f"Calendar events for user {user_id}: {events}")
        return jsonify(events)
    except Exception as e:
        app.logger.error(f"Error in calendar_events: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/send_debug_log', methods=['POST'])
def send_debug_log():
    try:
        user_id = request.json.get('user_id')
        debug_log = request.json.get('debug_log')

        # Проверяем, является ли пользователь администратором
        user = User.query.get(user_id)
        if not user or user.id != 1:  # Предполагаем, что админ имеет id 1
            return jsonify({"error": "Unauthorized"}), 403

        # Если ADMIN_CHAT_ID не установлен, получаем его из базы данных
        global ADMIN_CHAT_ID
        if ADMIN_CHAT_ID is None:
            admin_user = User.query.get(1)
            if admin_user:
                ADMIN_CHAT_ID = admin_user.telegram_id
            else:
                return jsonify({"error": "Admin user not found"}), 500

        # Отправляем сообщение через Telegram API
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": f"Debug Log:\n\n{debug_log}"
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Failed to send message"}), 500

    except Exception as e:
        app.logger.error(f"Error in send_debug_log: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def send_admin_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send admin message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending admin message: {str(e)}")

@app.route('/trigger_manual_update', methods=['POST'])
def trigger_manual_update():
    update_subscription_payments()
    return jsonify({"message": "Manual update completed. Check server logs for details."})

@app.route('/get_currencies')
def get_currencies():
    currencies = Currency.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'code': c.code} for c in currencies])

@app.route('/get_banks')
def get_banks():
    banks = Bank.query.all()
    return jsonify([{'id': b.id, 'name': b.name} for b in banks])

@app.route('/api/analytics/<int:user_id>')
def get_analytics(user_id):
    today = datetime.now(pytz.timezone('Europe/Moscow')).date()
    current_month_start = today.replace(day=1)
    current_year_end = today.replace(month=12, day=31)

    # Получаем все уникальные валюты пользователя
    user_currencies = db.session.query(Subscription.currency).filter(
        Subscription.user_id == user_id
    ).distinct().all()
    user_currencies = [currency[0] for currency in user_currencies]

    analytics_data = {}

    for currency in user_currencies:
        # Траты за текущий месяц
        current_month_expenses = db.session.query(func.sum(Payment.amount)).join(Subscription).filter(
            Payment.user_id == user_id,
            Payment.payment_date >= current_month_start,
            Payment.payment_date <= today,
            Subscription.currency == currency
        ).scalar() or 0

        # Все траты за всё время
        total_expenses = db.session.query(func.sum(Subscription.total_spent)).filter(
            Subscription.user_id == user_id,
            Subscription.currency == currency
        ).scalar() or 0

        # Прогноз трат до конца года
        active_subscriptions = Subscription.query.filter(
            Subscription.user_id == user_id,
            Subscription.is_archived == False,
            Subscription.currency == currency
        ).all()

        future_expenses = 0
        for sub in active_subscriptions:
            next_payment = sub.next_payment_date or sub.start_date
            while next_payment <= current_year_end:
                if next_payment > today:
                    future_expenses += sub.amount
                if sub.billing_cycle == 'monthly':
                    next_payment += relativedelta(months=1)
                elif sub.billing_cycle == 'yearly':
                    next_payment += relativedelta(years=1)

        analytics_data[currency] = {
            'current_month_expenses': round(current_month_expenses, 2),
            'total_expenses': round(total_expenses, 2),
            'future_expenses': round(future_expenses, 2)
        }

    return jsonify(analytics_data)

@app.route('/not_in_telegram')
def not_in_telegram():
    return render_template('not_in_telegram.html')

@app.route('/get_user_profile/<int:user_id>')
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    active_subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=False).count()
    archived_subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=True).count()

    return jsonify({
        "first_name": user.first_name,
        "active_subscriptions": active_subscriptions,
        "archived_subscriptions": archived_subscriptions,
        "is_premium": user.is_premium,
        "premium_expired": user.premium_expired.isoformat() if user.premium_expired else None
    })

@app.route('/get_archived_subscriptions/<int:user_id>')
def get_archived_subscriptions(user_id):
    archived_subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=True).all()
    return jsonify([{
        'id': sub.id,
        'service': sub.service_name,  # Изменено с sub.service на sub.service_name
        'amount': sub.amount,
        'currency': sub.currency
    } for sub in archived_subscriptions])

@app.route('/unarchive_subscription/<int:subscription_id>', methods=['POST'])
def unarchive_subscription(subscription_id):
    data = request.json
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"error": "Subscription not found"}), 404

    try:
        next_payment_date = datetime.strptime(data['next_payment_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    today = datetime.now(pytz.timezone('Europe/Moscow')).date()
    if next_payment_date < today:
        return jsonify({"error": "Next payment date cannot be in the past"}), 400

    # Разархивируем подписку
    subscription.is_archived = False
    subscription.next_payment_date = next_payment_date

    db.session.commit()

    return jsonify({
        "message": "Subscription unarchived successfully",
        "subscription_id": subscription.id,
        "next_payment_date": subscription.next_payment_date.isoformat()
    })

def send_group_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": FEEDBACK_GROUP_ID,
            "text": message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send group message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending group message: {str(e)}")

@app.route('/send_feedback', methods=['POST'])
def send_feedback():
    try:
        data = request.json
        feedback_type = data['type']
        feedback_text = data['text']
        user_id = request.headers.get('X-Telegram-User-Id')

        user = User.query.filter_by(telegram_id=user_id).first()

        if user:
            hashtag = "#проблема" if feedback_type == "problem" else "#сотрудничество"
            username = f"@{user.username}" if user.username else "Нет username"
            message = f"{hashtag}\n\nОт: {user.telegram_id} ({username})\n\nСообщение:\n{feedback_text}"
            
            send_group_message(message)

            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        app.logger.error(f"Error in send_feedback: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    
@app.route('/update_premium_status', methods=['POST'])
def update_premium_status():
    data = request.json
    user_id = data['user_id']
    duration = data['duration']  # в месяцах
    
    user = User.query.filter_by(telegram_id=user_id).first()
    if user:
        user.is_premium = True
        user.premium_expired = datetime.now() + timedelta(days=30*int(duration))
        db.session.commit()
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
def check_and_update_premium_status():
    with app.app_context():
        try:
            current_time = datetime.now(pytz.timezone('Europe/Moscow'))
            send_admin_message(f"Starting premium status check at {current_time}")

            expired_users = User.query.filter(User.is_premium == True, User.premium_expired <= current_time).all()
            
            update_count = 0
            for user in expired_users:
                user.is_premium = False
                user.premium_expired = None
                update_count += 1
            
            db.session.commit()
            
            message = f"Premium status check completed.\n"
            message += f"Updated premium status for {update_count} users.\n"
            message += f"Total premium users: {User.query.filter_by(is_premium=True).count()}"
            
            send_admin_message(message)
            app.logger.info(message)

        except Exception as e:
            error_message = f"Error in premium status check: {str(e)}"
            send_admin_message(error_message)
            app.logger.error(error_message)

@app.route('/api/get_all_users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([{'telegram_id': user.telegram_id} for user in users])

scheduler.add_job(
    id='update_subscription_payments_job',
    func=update_subscription_payments,
    trigger='cron',
    hour=12,
    minute=00,
    timezone='Europe/Moscow'
)

scheduler.add_job(
    id='check_and_update_premium_status_job',
    func=check_and_update_premium_status,
    trigger='interval',
    hours=1,
    next_run_time=datetime.now() + timedelta(seconds=10),  # Запуск через 10 секунд после старта приложения
    timezone='Europe/Moscow'
)

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("Flask application stopped by user")