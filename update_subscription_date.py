from app import app, db, Subscription
from datetime import datetime


def update_subscription_start_date(subscription_id, new_start_date):
    with app.app_context():
        subscription = Subscription.query.get(subscription_id)
        if subscription:
            old_start_date = subscription.start_date
            subscription.start_date = new_start_date
            db.session.commit()
            print(f"Subscription {subscription_id} updated:")
            print(f"Old start date: {old_start_date}")
            print(f"New start date: {new_start_date}")
        else:
            print(f"Subscription with ID {subscription_id} not found.")


if __name__ == "__main__":
    subscription_id = 2  # ID подписки, которую мы хотим изменить

    # Запрашиваем у пользователя новую дату
    date_input = input("Enter new start date (YYYY-MM-DD): ")
    try:
        new_start_date = datetime.strptime(date_input, "%Y-%m-%d").date()
        update_subscription_start_date(subscription_id, new_start_date)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")