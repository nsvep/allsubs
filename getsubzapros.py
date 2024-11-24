import psycopg2
from psycopg2 import sql

db_params = {
    'dbname': 'vsesub',
    'user': 'admin',
    'password': 'aboba',
    'host': 'dbvsesub-nsvep.db-msk0.amvera.tech',
}

def check_subscription_table():
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Проверяем количество записей в таблице
        cur.execute("SELECT COUNT(*) FROM subscription")
        count = cur.fetchone()[0]
        print(f"Количество записей в таблице subscription: {count}")

        # Получаем все ID из таблицы
        cur.execute("SELECT id FROM subscription ORDER BY id")
        ids = cur.fetchall()
        print(f"Существующие ID в таблице subscription: {[id[0] for id in ids]}")

        # Получаем первые 5 записей для примера
        cur.execute("SELECT * FROM subscription ORDER BY id LIMIT 5")
        rows = cur.fetchall()
        if rows:
            column_names = [desc[0] for desc in cur.description]
            print("\nПример данных (первые 5 записей):")
            for row in rows:
                subscription_info = dict(zip(column_names, row))
                print(subscription_info)
        else:
            print("В таблице нет данных.")

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
    finally:
        if conn:
            cur.close()
            conn.close()

# Запускаем проверку
check_subscription_table()