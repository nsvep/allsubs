import psycopg2
from datetime import datetime

# Параметры подключения к базе данных
db_params = {
    'dbname': 'vsesub',
    'user': 'admin',
    'password': 'aboba',
    'host': 'dbvsesub-nsvep.db-msk0.amvera.tech',
}

try:
    # Подключение к базе данных
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    print("Успешное подключение к базе данных.")

    # Запрос id подписки у пользователя
    subscription_id = input("Введите id подписки для изменения: ")

    # Запрос новой даты следующего платежа у пользователя
    new_next_payment_date = input("Введите новую дату следующего платежа (формат YYYY-MM-DD): ")

    # Проверка формата даты
    try:
        datetime.strptime(new_next_payment_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Неправильный формат даты. Используйте YYYY-MM-DD")

    # SQL-запрос для обновления даты следующего платежа
    update_query = """
    UPDATE "subscription"
    SET next_payment_date = %s
    WHERE id = %s
    """

    # Выполнение запроса
    cursor.execute(update_query, (new_next_payment_date, subscription_id))
    conn.commit()

    print(f"Дата следующего платежа для подписки с id {subscription_id} успешно обновлена.")

except (Exception, psycopg2.Error) as error:
    print("Ошибка при работе с PostgreSQL:", error)

finally:
    # Закрытие соединения
    if conn:
        cursor.close()
        conn.close()
        print("Соединение с PostgreSQL закрыто.")