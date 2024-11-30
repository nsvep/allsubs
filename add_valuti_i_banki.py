from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Создаем подключение к базе данных
DATABASE_URI = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub?options=-c%20timezone=Europe/Moscow'
engine = create_engine(DATABASE_URI)

# Создаем базовый класс для моделей
Base = declarative_base()

# Определяем модели
class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    code = Column(String(3), nullable=False, unique=True)

class Bank(Base):
    __tablename__ = 'bank'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

# Создаем таблицы
Base.metadata.create_all(engine)

# Создаем сессию
Session = sessionmaker(bind=engine)
session = Session()

def add_initial_data():
    # Добавление валют
    currencies = [
        Currency(code='RUB', name='Рубль'),
        Currency(code='USD', name='Доллар'),
        Currency(code='EUR', name='Евро'),
        Currency(code='AED', name='Дирхам ОАЭ'),
        Currency(code='KZT', name='Тенге'),
        Currency(code='TRY', name='Турецкая лира'),
        Currency(code='BYN', name='Белорусский рубль'),
        Currency(code='UAH', name='Украинская Гривна'),
        Currency(code='CNY', name='Юань'),
        Currency(code='GBP', name='Фунт стерлингов'),
        Currency(code='JPY', name='Японская иена'),
        Currency(code='CHF', name='Швейцарский франк'),
        Currency(code='INR', name='Индийская рупия'),
    ]

    # Добавление банков
    banks = [
        Bank(name='Сбер'),
        Bank(name='Т-Банк'),
        Bank(name='Альфа-Банк'),
        Bank(name='ВТБ'),
        Bank(name='МТС-Банк'),
        Bank(name='Газпромбанк'),
        Bank(name='Райффайзенбанк'),
        Bank(name='Росбанк'),
        Bank(name='Совкомбанк'),
        Bank(name='Промсвязьбанк'),
    ]

    # Удаляем существующие записи (опционально)
    session.query(Currency).delete()
    session.query(Bank).delete()

    # Добавляем новые записи
    session.add_all(currencies)
    session.add_all(banks)
    
    # Сохраняем изменения
    session.commit()

    print("Начальные данные успешно добавлены в базу данных.")

if __name__ == "__main__":
    add_initial_data()