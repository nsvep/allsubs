from locust import HttpUser, task, between, TaskSet, constant_pacing, events
import random
import json
import time
from datetime import datetime, timedelta


class UserBehavior(TaskSet):
    @task(10)
    def view_subscriptions(self):
        self.user.get_subscriptions()

    @task(3)
    def add_and_update_subscription(self):
        self.user.add_subscription()
        self.user.get_subscriptions()
        self.user.update_subscription()

    @task(1)
    def archive_and_unarchive(self):
        self.user.archive_subscription()
        self.user.unarchive_subscription()

    @task(1)
    def view_calendar_and_dates(self):
        self.user.get_calendar_events()
        self.user.get_subscription_dates()


class TelegramBotUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(3, 10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_id = None
        self.user_id = None

    def on_start(self):
        self.telegram_id = random.randint(1000000, 9999999)
        self.user_data = {
            "id": self.telegram_id,
            "first_name": f"User{self.telegram_id}",
            "last_name": "TestUser",
            "username": f"user{self.telegram_id}"
        }
        with self.client.post("/get_user_info", json={"user": self.user_data}, catch_response=True) as response:
            if response.status_code == 200:
                self.user_id = response.json()["user_id"]
            else:
                response.failure(f"Failed to register user. Status code: {response.status_code}")

    @task(3)
    def get_user_subscriptions_for_bot(self):
        with self.client.get(f"/get_user_subscriptions_for_bot/{self.telegram_id}", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get subscriptions for bot. Status code: {response.status_code}")

    @task(2)
    def get_subscriptions(self):
        if self.user_id:
            with self.client.get(f"/get_subscriptions/{self.user_id}", catch_response=True) as response:
                if response.status_code == 200:
                    subscriptions = response.json()
                    if len(subscriptions) == 0:
                        response.failure("No subscriptions found")
                else:
                    response.failure(f"Failed to get subscriptions. Status code: {response.status_code}")

    @task(1)
    def add_subscription(self):
        if self.user_id:
            payload = {
                "user_id": self.user_id,
                "service_name": f"Service {random.randint(1, 100)}",
                "category_id": random.randint(1, 10),
                "next_payment_date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                "amount": random.uniform(5.0, 100.0),
                "currency": random.choice(["RUB", "USD", "EUR"]),
                "bank": random.choice(["Сбербанк", "Тинькофф", "ВТБ"]),
                "card_last_4": str(random.randint(1000, 9999)),
                "send_notifications": random.choice([True, False])
            }
            with self.client.post("/add_subscription", json=payload, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to add subscription. Status code: {response.status_code}")

    @task(1)
    def update_subscription(self):
        if self.user_id:
            with self.client.get(f"/get_subscriptions/{self.user_id}", catch_response=True) as response:
                if response.status_code == 200:
                    subscriptions = response.json()
                    if subscriptions:
                        subscription = random.choice(subscriptions)
                        payload = {
                            "service_name": f"Updated {subscription['service_name']}",
                            "amount": random.uniform(5.0, 100.0),
                            "currency": random.choice(["RUB", "USD", "EUR"])
                        }
                        with self.client.post(f"/update_subscription/{subscription['id']}", json=payload,
                                              catch_response=True) as update_response:
                            if update_response.status_code != 200:
                                update_response.failure(
                                    f"Failed to update subscription. Status code: {update_response.status_code}")
                else:
                    response.failure(f"Failed to get subscriptions for update. Status code: {response.status_code}")

    @task(1)
    def get_subscription_dates(self):
        if self.user_id:
            year = datetime.now().year
            month = random.randint(1, 12)
            with self.client.get(f"/get_subscription_dates/{self.user_id}/{year}/{month}",
                                 catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to get subscription dates. Status code: {response.status_code}")

    @task(1)
    def get_calendar_events(self):
        if self.user_id:
            with self.client.get(f"/api/calendar-events?user_id={self.user_id}", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to get calendar events. Status code: {response.status_code}")

    @task(1)
    def archive_subscription(self):
        if self.user_id:
            with self.client.get(f"/get_subscriptions/{self.user_id}", catch_response=True) as response:
                if response.status_code == 200:
                    subscriptions = response.json()
                    if subscriptions:
                        subscription = random.choice(subscriptions)
                        with self.client.post(f"/archive_subscription/{subscription['id']}",
                                              catch_response=True) as archive_response:
                            if archive_response.status_code != 200:
                                archive_response.failure(
                                    f"Failed to archive subscription. Status code: {archive_response.status_code}")
                else:
                    response.failure(f"Failed to get subscriptions for archiving. Status code: {response.status_code}")

    @task(1)
    def unarchive_subscription(self):
        if self.user_id:
            # Предполагаем, что у нас есть эндпоинт для получения архивированных подписок
            with self.client.get(f"/get_archived_subscriptions/{self.user_id}", catch_response=True) as response:
                if response.status_code == 200:
                    archived_subscriptions = response.json()
                    if archived_subscriptions:
                        subscription = random.choice(archived_subscriptions)
                        with self.client.post(f"/unarchive_subscription/{subscription['id']}",
                                              catch_response=True) as unarchive_response:
                            if unarchive_response.status_code != 200:
                                unarchive_response.failure(
                                    f"Failed to unarchive subscription. Status code: {unarchive_response.status_code}")
                else:
                    response.failure(f"Failed to get archived subscriptions. Status code: {response.status_code}")

        @task(1)
        def simulate_error(self):
            with self.client.get("/non_existent_endpoint", catch_response=True) as response:
                if response.status_code != 404:
                    response.failure(f"Expected 404, got {response.status_code}")
                else:
                    response.success()

        @task(1)
        def add_subscription_with_invalid_data(self):
            if self.user_id:
                payload = {
                    "user_id": self.user_id,
                    "service_name": "",  # Пустое имя сервиса
                    "amount": -100,  # Отрицательная сумма
                }
                with self.client.post("/add_subscription", json=payload, catch_response=True) as response:
                    if response.status_code != 400:
                        response.failure(f"Expected 400 for invalid data, got {response.status_code}")
                    else:
                        response.success()

        @task
        def complete_user_journey(self):
            self.get_subscriptions()
            time.sleep(random.uniform(1, 3))
            self.add_subscription()
            time.sleep(random.uniform(1, 3))
            self.get_subscriptions()
            time.sleep(random.uniform(1, 3))
            self.update_subscription()
            time.sleep(random.uniform(1, 3))
            self.archive_subscription()
            time.sleep(random.uniform(1, 3))
            self.get_calendar_events()

    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        print("A new test is starting")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print("Test finished")