from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub'
db = SQLAlchemy(app)

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(3), nullable=False, unique=True)
    is_custom = db.Column(db.Boolean, default=False)
    # Убираем ссылку на user_id
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_custom = db.Column(db.Boolean, default=False)
    # Убираем ссылку на user_id
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

def add_initial_data():
    # Добавление стандартных валют
    currencies = [
        Currency(code='RUB', name='Рубль', is_custom=False),
        Currency(code='USD', name='Доллар', is_custom=False),
        Currency(code='EUR', name='Евро', is_custom=False),
        Currency(code='AED', name='Дирхам ОАЭ', is_custom=False),
        Currency(code='KZT', name='Тенге', is_custom=False),
        Currency(code='TRY', name='Турецкая лира', is_custom=False),
        Currency(code='BYN', name='Белорусский рубль', is_custom=False),
        Currency(code='UAH', name='Украинская Гривна', is_custom=False),
        Currency(code='CNY', name='Юань', is_custom=False),
        Currency(code='GBP', name='Фунт стерлингов', is_custom=False),
        Currency(code='JPY', name='Японская иена', is_custom=False),
        Currency(code='CHF', name='Швейцарский франк', is_custom=False),
        Currency(code='INR', name='Индийская рупия', is_custom=False),
    ]

    # Добавление стандартных банков
    banks = [
        Bank(name='Сбер', is_custom=False),
        Bank(name='Т-Банк', is_custom=False),
        Bank(name='Альфа-Банк', is_custom=False),
        Bank(name='ВТБ', is_custom=False),
        Bank(name='МТС-Банк', is_custom=False),
        Bank(name='Газпромбанк', is_custom=False),
        Bank(name='Райффайзенбанк', is_custom=False),
        Bank(name='Росбанк', is_custom=False),
        Bank(name='Совкомбанк', is_custom=False),
        Bank(name='Промсвязьбанк', is_custom=False),
    ]

    # Удаляем существующие записи (опционально)
    Currency.query.delete()
    Bank.query.delete()

    # Добавляем новые записи
    db.session.add_all(currencies)
    db.session.add_all(banks)
    
    # Сохраняем изменения
    db.session.commit()

    print("Начальные данные успешно добавлены в базу данных.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы, если они еще не существуют
        add_initial_data()