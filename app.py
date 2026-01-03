from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Настройка подключения к PostgreSQL
# Формат: postgresql://логин:пароль@localhost/имя_базы
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ttrpg_user:ttrpg_password@localhost/ttrpg_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- МОДЕЛИ ДАННЫХ ---

class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    
    # Атрибуты
    body = db.Column(db.Integer, default=4)
    mind = db.Column(db.Integer, default=4)
    spirit = db.Column(db.Integer, default=4)

    # Навыки Тела
    dexterity = db.Column(db.Integer, default=4) # Ловкость
    accuracy = db.Column(db.Integer, default=4)  # Меткость
    agility = db.Column(db.Integer, default=4)   # Проворство
    strength = db.Column(db.Integer, default=4)  # Сила
    endurance = db.Column(db.Integer, default=4) # Стойкость

    # Навыки Разума
    perception = db.Column(db.Integer, default=4) # Внимательность
    knowledge = db.Column(db.Integer, default=4)  # Знание
    insight = db.Column(db.Integer, default=4)    # Проницательность
    reason = db.Column(db.Integer, default=4)     # Рассудок
    wit = db.Column(db.Integer, default=4)        # Смекалка

    # Навыки Духа
    eloquence = db.Column(db.Integer, default=4)  # Красноречие
    leadership = db.Column(db.Integer, default=4) # Лидерство
    charm = db.Column(db.Integer, default=4)      # Обаяние
    deception = db.Column(db.Integer, default=4)  # Притворство
    composure = db.Column(db.Integer, default=4)  # Хладнокровие

    # Связи (один ко многим)
    advantages = db.relationship('Advantage', backref='character', lazy=True)
    miracles = db.relationship('Miracle', backref='character', lazy=True)

class Advantage(db.Model):
    __tablename__ = 'advantages'
    id = db.Column(db.Integer, primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    name = db.Column(db.String(100))
    value = db.Column(db.Integer, default=1)

class Miracle(db.Model):
    __tablename__ = 'miracles'
    id = db.Column(db.Integer, primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    rank = db.Column(db.Integer, default=1)
    level = db.Column(db.Integer, default=1)

@app.route('/')
def index():
    return "<h1>Character Editor: Database Connected!</h1>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Автоматически создает таблицы при запуске
    app.run(debug=True, host='0.0.0.0')
