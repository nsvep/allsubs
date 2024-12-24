import psycopg2
from datetime import datetime
import pytz

# Параметры подключения к базе данных
db_params = {
    'dbname': 'vsesub',
    'user': 'admin',
    'password': 'aboba',
    'host': 'dbvsesub-nsvep.db-msk0.amvera.tech',
    'options': '-c timezone=Europe/Moscow'
}

def set_premium_expiration(user_id, expiration_date):
    conn = None
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # SQL запрос для обновления premium_expired
        update_query = """
        UPDATE "user"
        SET premium_expired = %s
        WHERE id = %s
        """

        # Выполнение запроса
        cur.execute(update_query, (expiration_date, user_id))
        
        # Проверка, был ли обновлен пользователь
        if cur.rowcount == 0:
            print(f"Пользователь с ID {user_id} не найден.")
        else:
            print(f"Дата окончания премиум статуса успешно установлена для пользователя с ID {user_id}.")

        # Подтверждение изменений
        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Соединение с PostgreSQL закрыто.")

if __name__ == "__main__":
    while True:
        user_id = input("Введите ID пользователя (или 'q' для выхода): ")
        
        if user_id.lower() == 'q':
            print("Выход из программы.")
            break
        
        try:
            user_id = int(user_id)
            expiration_date_str = input("Введите дату окончания премиум статуса (YYYY-MM-DD HH:MM:SS): ")
            expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d %H:%M:%S")
            expiration_date = pytz.timezone('Europe/Moscow').localize(expiration_date)
            
            set_premium_expiration(user_id, expiration_date)
        except ValueError:
            print("Ошибка: Неверный формат ID пользователя или даты.")