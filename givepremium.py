import psycopg2

# Параметры подключения к базе данных
db_uri = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub'

def give_premium(user_id):
    conn = None
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(db_uri)
        cur = conn.cursor()

        # SQL запрос для обновления is_premium
        update_query = """
        UPDATE "user"
        SET is_premium = TRUE
        WHERE id = %s
        """

        # Выполнение запроса
        cur.execute(update_query, (user_id,))
        
        # Проверка, был ли обновлен пользователь
        if cur.rowcount == 0:
            print(f"Пользователь с ID {user_id} не найден.")
        else:
            print(f"Премиум статус успешно установлен для пользователя с ID {user_id}.")

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
        user_input = input("Введите ID пользователя (или 'q' для выхода): ")
        
        if user_input.lower() == 'q':
            print("Выход из программы.")
            break
        
        try:
            user_id = int(user_input)
            give_premium(user_id)
        except ValueError:
            print("Ошибка: ID пользователя должно быть целым числом.")