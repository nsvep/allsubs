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
            "Банк",
            "Кино",
            "Музыка",
            "Книги",
            "Другое",
            "Софт",
            "Игры",
            "Образование"
        ]

        for category_name in categories:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)

        db.session.commit()

        # Словарь сервисов по категориям
        services = {
            "Мульти": ["Яндекс Плюс", "СберПрайм", "OZON Premium", "Telegram Premium", "WB Клуб", "МТС Premium", "Пакет X5"],
            "Банк": ["Tinkoff Pro", "Альфа‑Смарт", "Tinkoff Premium", "Халва. Десятка", "Привилегии Плюс", "Газпром Бонус", "Всё Своё. Продвинутый"],
            "Кино": ["ИВИ", "PREMIER", "Okko", "Start", "More.tv", "KION", "Apple TV", "Netflix"],
            "Музыка": ["VK Музыка", "Spotify", "Apple Music", "МТС Музыка", "СберЗвук"],
            "Книги": ["Яндекс Книги", "Строки", "ЛитРес", "MyBook", "Литнет", "Патефон"],
            "Другое": ["Мобильная связь", "Интернет", "Карта Тройка", "hh PRO", "VPN", "Благотворительность"],
            "Софт": ["Яндекс Диск", "Облако Mail.ru", "Microsoft 365", "Microsoft OneDrive", "Adobe Creative Cloud", "Photoshop", "iCloud+", "Яндекс 360+", "Kaspersky", "Dr.Web", "Docker", "Figma"],
            "Игры": ["Dota Plus", "Discord Nitro", "Xbox Game Pass", "PlayStation Plus", "Apple Arcade"],
            "Образование": ["Duolingo", "Учи.ру", "Skayeng", "Arzamas", "Правое полушарие Интроверта"]
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