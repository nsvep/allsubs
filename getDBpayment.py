import psycopg2
from psycopg2 import sql

db_params = {
    'dbname': 'vsesub',
    'user': 'admin',
    'password': 'aboba',
    'host': 'dbvsesub-nsvep.db-msk0.amvera.tech',
}

def check_payment_table():
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Проверяем количество записей в таблице
        cur.execute("SELECT COUNT(*) FROM payment")
        count = cur.fetchone()[0]
        print(f"Количество записей в таблице payment: {count}")

        # Получаем все ID из таблицы
        cur.execute("SELECT id FROM payment ORDER BY id")
        ids = cur.fetchall()
        print(f"Существующие ID в таблице payment: {[id[0] for id in ids]}")

        # Получаем последние 5 записей
        cur.execute("SELECT * FROM payment ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        if rows:
            column_names = [desc[0] for desc in cur.description]
            print("\nПоследние 5 записей:")
            for row in rows:
                payment_info = dict(zip(column_names, row))
                print(payment_info)
        else:
            print("В таблице нет данных.")

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
    finally:
        if conn:
            cur.close()
            conn.close()

# Запускаем проверку
check_payment_table()