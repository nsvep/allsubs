from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Подключение к базе данных
db_uri = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub'
engine = create_engine(db_uri)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

# Создание базового класса для моделей
Base = declarative_base()

# Удаление всех таблиц
Base.metadata.reflect(engine)
Base.metadata.drop_all(engine)

print("Все таблицы удалены")

# Закрытие сессии
session.close()