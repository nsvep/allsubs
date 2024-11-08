from app import app, db, Category, Service


def add_categories_and_services():
    with app.app_context():
        # Добавление категорий
        categories = [
            "Развлечения",
            "Музыка",
            "Видео",
            "Образование",
            "Облачные хранилища",
            "Программное обеспечение",
            "Игры",
            "Новости",
            "Спорт",
            "Другое"
        ]

        for category_name in categories:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)

        db.session.commit()

        # Словарь сервисов по категориям
        services = {
            "Развлечения": ["Netflix", "Disney+", "HBO Max", "Amazon Prime Video"],
            "Музыка": ["Spotify", "Apple Music", "Tidal", "YouTube Music"],
            "Видео": ["YouTube Premium", "Vimeo", "Twitch"],
            "Образование": ["Coursera", "Udemy", "Skillshare", "MasterClass"],
            "Облачные хранилища": ["Dropbox", "Google One", "iCloud", "OneDrive"],
            "Программное обеспечение": ["Adobe Creative Cloud", "Microsoft 365", "Notion", "Evernote"],
            "Игры": ["PlayStation Plus", "Xbox Game Pass", "Nintendo Switch Online"],
            "Новости": ["The New York Times", "The Wall Street Journal", "The Economist"],
            "Спорт": ["ESPN+", "DAZN", "NBA League Pass"],
        }

        # Добавление сервисов
        for category_name, service_list in services.items():
            category = Category.query.filter_by(name=category_name).first()
            for service_name in service_list:
                service = Service.query.filter_by(name=service_name).first()
                if not service:
                    service = Service(name=service_name, category_id=category.id, is_custom=False)
                    db.session.add(service)

        db.session.commit()

        print("Категории и сервисы успешно добавлены в базу данных.")


if __name__ == "__main__":
    add_categories_and_services()