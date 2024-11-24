from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy.sql import func
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dateutil.relativedelta import relativedelta
from flask_cors import CORS
import logging
import requests

TELEGRAM_BOT_TOKEN = '7567530655:AAFF43H1MTmfcdTTnFEAUh37tYOmgHAaThI'
ADMIN_CHAT_ID = 50274860  # Здесь нужно указать chat_id администратора

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub'
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    next_payment_date = db.Column(db.Date)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    discount = db.Column(db.Float)
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
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, subscription_id, payment_date, amount):
        self.subscription_id = subscription_id
        self.payment_date = payment_date
        self.amount = amount

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

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


def update_subscription_payments():
    with app.app_context():
        tz = pytz.timezone('Europe/Moscow')
        today = datetime.now(tz).date()
        print(f"Running update_subscription_payments for date: {today}")

        subscriptions = Subscription.query.filter_by(is_archived=False).all()
        print(f"Total active subscriptions found: {len(subscriptions)}")

        for subscription in subscriptions:
            try:
                print(f"Processing subscription ID: {subscription.id}")

                # Проверяем и сбрасываем last_payment_date, если она в будущем
                if subscription.last_payment_date and subscription.last_payment_date > today:
                    print(f"  Resetting future last_payment_date from {subscription.last_payment_date} to None")
                    subscription.last_payment_date = None

                # Устанавливаем next_payment_date, если она не установлена
                if not subscription.next_payment_date:
                    subscription.next_payment_date = subscription.start_date
                    print(f"  Setting initial next_payment_date to: {subscription.next_payment_date}")

                # Создаем платежи для всех прошедших дат до сегодняшнего дня
                while subscription.next_payment_date and subscription.next_payment_date <= today:
                    existing_payment = Payment.query.filter_by(
                        subscription_id=subscription.id,
                        payment_date=subscription.next_payment_date
                    ).first()

                    if not existing_payment:
                        payment = Payment(subscription_id=subscription.id,
                                          payment_date=subscription.next_payment_date,
                                          amount=subscription.amount)
                        db.session.add(payment)
                        subscription.total_spent += subscription.amount
                        print(f"  Created payment for date: {subscription.next_payment_date}")

                    subscription.last_payment_date = subscription.next_payment_date

                    # Обновляем next_payment_date
                    subscription.next_payment_date += relativedelta(months=1)
                    print(f"  Next payment date set to: {subscription.next_payment_date}")

                db.session.commit()
                print(f"  Subscription {subscription.id} processed successfully")
            except Exception as e:
                print(f"Error processing subscription {subscription.id}: {e}")
                db.session.rollback()

        print("Update subscription payments completed")

# Настройка планировщика
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
scheduler.add_job(
    func=update_subscription_payments,
    trigger=CronTrigger(hour=0, minute=1),
    id='update_subscription_payments_job',
    name='Update subscription payments every day at 00:01',
    replace_existing=True)

# Запуск планировщика
scheduler.start()

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
    user_data = data['user']

    user = User.query.filter_by(telegram_id=user_data['id']).first()
    if not user:
        user = User(
            telegram_id=user_data['id'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),  # Используем get() с пустой строкой по умолчанию
            username=user_data.get('username', '')
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Обновляем данные пользователя, если он уже существует
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)  # Используем get() с текущим значением по умолчанию
        user.username = user_data.get('username', user.username)
        db.session.commit()

    return jsonify({"status": "success", "user_id": user.id})


@app.route('/get_subscriptions/<int:user_id>')
def get_subscriptions(user_id):
    subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=False).all()
    result = [{
        'id': sub.id,
        'service_name': sub.service_name,
        'category_name': sub.category.name,
        'start_date': sub.start_date.strftime('%Y-%m-%d'),
        'amount': sub.amount,
        'currency': sub.currency,
        'discount': sub.discount,
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
        'discount': subscription.discount,
        'bank': subscription.bank,
        'card_last_4': subscription.card_last_4
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

@app.route('/unarchive_subscription/<int:subscription_id>', methods=['POST'])
def unarchive_subscription(subscription_id):
    with app.app_context():
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({"error": "Subscription not found"}), 404

        subscription.is_archived = False
        db.session.commit()

        return jsonify({
            "message": "Subscription unarchived successfully",
            "subscription_id": subscription.id
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
        'currency': sub.currency
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

        # Изменяем запрос, чтобы получить только неархивные подписки
        subscriptions = Subscription.query.filter_by(user_id=user_id, is_archived=False).all()

        events = [{
            'id': sub.id,
            'service': sub.service_name,
            'amount': sub.amount,
            'currency': sub.currency,
            'nextPaymentDate': sub.start_date.strftime('%Y-%m-%d') if sub.start_date else None
        } for sub in subscriptions]

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

import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")

        try:
            update_subscription_payments()
        except KeyboardInterrupt:
            print("Update subscription payments interrupted by user")
        except Exception as e:
            print(f"Error in update_subscription_payments: {e}")

    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("Flask application stopped by user")