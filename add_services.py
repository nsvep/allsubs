from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:aboba@dbvsesub-nsvep.db-msk0.amvera.tech/vsesub'
db = SQLAlchemy(app)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_custom = db.Column(db.Boolean, default=False)

def add_categories_and_services():
    with app.app_context():
        # Добавление категорий
        categories = [
            "Мульти",
            "Музыка",
            "Кино",
            "Книги",
            "Программное обеспечение",
            "Игры",
            "Банковские услуги",
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
            "Мульти": ["Telegram Premium", "OZON Premium", "WB Клуб", "МТС Premium", "Пакет X5", "СберПрайм","Яндекс Плюс"],
            "Музыка": ["Apple Music", "Spotify", "VK Музыка", "МТС Музыка"],
            "Кино": ["Netflix", "Apple TV", "KION", "More.tv", "Okko", "PREMIER", "Start", "ИВИ"],
            "Книги": ["MyBook", "ЛитРес", "Литнет", "Патефон", "Строки", "Яндекс Книги"],
            "Программное обеспечение": ["Adobe Creative Cloud", "Microsoft 365", "Photoshop"],
            "Игры": ["Apple Arcade", "PlayStation Plus", "Xbox Game Pass"],
            "Банковские услуги": ["Tinkoff Pro", "Альфа‑Смарт (Альфа-Банк)", "Всё Своё. Продвинутый (Россельхозбанк)", "Газпром Бонус", "Привилегии Плюс (ВТБ)", "Халва. Десятка"],
            "Другое": ["VPN", "Интернет", "Мобильная связь", "Пожертвования"],
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