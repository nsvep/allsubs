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

    # Запрос новой даты начала у пользователя
    new_start_date = input("Введите новую дату начала (формат YYYY-MM-DD): ")

    # Проверка формата даты
    try:
        datetime.strptime(new_start_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Неправильный формат даты. Используйте YYYY-MM-DD")

    # SQL-запрос для обновления даты начала
    update_query = """
    UPDATE "subscription"
    SET start_date = %s
    WHERE id = %s
    """

    # Выполнение запроса
    cursor.execute(update_query, (new_start_date, subscription_id))
    conn.commit()

    print(f"Дата начала для подписки с id {subscription_id} успешно обновлена.")

except (Exception, psycopg2.Error) as error:
    print("Ошибка при работе с PostgreSQL:", error)

finally:
    # Закрытие соединения
    if conn:
        cursor.close()
        conn.close()
        print("Соединение с PostgreSQL закрыто.")