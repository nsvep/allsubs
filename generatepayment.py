import sys
import psycopg2
from datetime import datetime, timedelta

# Настройки подключения к базе данных
DATABASE_URL = "postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub"


def generate_test_payments(subscription_id):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Получаем информацию о подписке
        cur.execute("SELECT user_id, amount FROM subscription WHERE id = %s", (subscription_id,))
        subscription = cur.fetchone()

        if not subscription:
            print(f"Подписка с ID {subscription_id} не найдена.")
            return

        user_id, amount = subscription

        start_date = datetime(2024, 1, 26)  # Дата начала подписки
        today = datetime(2024, 11, 25)  # Сегодняшняя дата для теста
        current_date = start_date

        while current_date <= today:
            # Вставляем платеж
            cur.execute("""
                INSERT INTO payment (user_id, subscription_id, amount, payment_date)
                VALUES (%s, %s, %s, %s)
            """, (user_id, subscription_id, amount, current_date.date()))

            # Переходим к следующей дате платежа (предполагаем ежемесячные платежи)
            current_date += timedelta(days=30)

        conn.commit()
        print(f"Созданы тестовые платежи для подписки {subscription_id}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            subscription_id = int(sys.argv[1])
            generate_test_payments(subscription_id)
        except ValueError:
            print("Ошибка: ID подписки должно быть целым числом.")
    else:
        print("Пожалуйста, укажите ID подписки в качестве аргумента.")
        print("Пример использования: python generatepayment.py 1")