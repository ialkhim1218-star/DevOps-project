import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ttrpg_user:ttrpg_password@localhost/ttrpg_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- СПИСКИ НАВЫКОВ ---
SKILLS_MAP = {
    'Тело': ['dexterity', 'accuracy', 'agility', 'strength', 'endurance'],
    'Разум': ['perception', 'knowledge', 'insight', 'reason', 'wit'],
    'Дух': ['eloquence', 'leadership', 'charm', 'deception', 'composure']
}

# --- МОДЕЛИ ---
class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    body = db.Column(db.Integer, default=4); mind = db.Column(db.Integer, default=4); spirit = db.Column(db.Integer, default=4)
    # Навыки
    dexterity = db.Column(db.Integer, default=4); accuracy = db.Column(db.Integer, default=4)
    agility = db.Column(db.Integer, default=4); strength = db.Column(db.Integer, default=4)
    endurance = db.Column(db.Integer, default=4); perception = db.Column(db.Integer, default=4)
    knowledge = db.Column(db.Integer, default=4); insight = db.Column(db.Integer, default=4)
    reason = db.Column(db.Integer, default=4); wit = db.Column(db.Integer, default=4)
    eloquence = db.Column(db.Integer, default=4); leadership = db.Column(db.Integer, default=4)
    charm = db.Column(db.Integer, default=4); deception = db.Column(db.Integer, default=4)
    composure = db.Column(db.Integer, default=4)

    advantages = db.relationship('Advantage', backref='character', cascade="all, delete-orphan")
    miracles = db.relationship('Miracle', backref='character', cascade="all, delete-orphan")

class Advantage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    name = db.Column(db.String(100))
    value = db.Column(db.Integer, default=1) # Это уровень/сила

class Miracle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    name = db.Column(db.String(100))
    rank = db.Column(db.Integer, default=1)   # Ранг (вводится)
    level = db.Column(db.Integer, default=1)  # Уровень (закупается)

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    return render_template('index.html', characters=Character.query.all())

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        f = request.form
        char_rank = int(f.get('rank', 1))
        
        # 1. Считаем очки за Атрибуты и Навыки
        total_spent = (int(f['body'])-4 + int(f['mind'])-4 + int(f['spirit'])-4) * 10
        for cat in SKILLS_MAP.values():
            for s in cat: total_spent += (int(f.get(s, 4)) - 4) * 5
        
        # 2. Считаем Достоинства (допустим, 5 за уровень)
        adv_names = f.getlist('adv_name[]')
        adv_vals = f.getlist('adv_val[]')
        for v in adv_vals: total_spent += int(v) * 5

        # 3. Считаем Чудеса (Уровень * Ранг)
        mir_names = f.getlist('mir_name[]')
        mir_ranks = f.getlist('mir_rank[]')
        mir_levels = f.getlist('mir_level[]')
        for r, l in zip(mir_ranks, mir_levels):
            total_spent += int(r) * int(l)

        if total_spent > char_rank * 20:
            return f"Перебор! Потрачено {total_spent}, лимит {char_rank*20}"

        # Сохранение
        new_char = Character(name=f['name'], rank=char_rank, body=int(f['body']), mind=int(f['mind']), spirit=int(f['spirit']))
        for cat in SKILLS_MAP.values():
            for s in cat: setattr(new_char, s, int(f.get(s, 4)))
        
        for n, v in zip(adv_names, adv_vals):
            if n: new_char.advantages.append(Advantage(name=n, value=int(v)))
        for n, r, l in zip(mir_names, mir_ranks, mir_levels):
            if n: new_char.miracles.append(Miracle(name=n, rank=int(r), level=int(l)))

        db.session.add(new_char)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html', skills_map=SKILLS_MAP)

@app.route('/upgrade/<int:char_id>', methods=['GET', 'POST'])
def upgrade(char_id):
    char = Character.query.get_or_404(char_id)
    if request.method == 'POST':
        param = request.form.get('param')
        curr = getattr(char, param)
        cost = (curr + 1) * (10 if param in ['body','mind','spirit'] else 5)
        if char.exp >= cost:
            char.exp -= cost
            setattr(char, param, curr + 1)
            db.session.commit()
        return redirect(url_for('upgrade', char_id=char.id))
    return render_template('upgrade.html', char=char, skills_map=SKILLS_MAP, getattr=getattr)

@app.route('/up_adv/<int:id>')
def up_adv(id):
    obj = Advantage.query.get_or_404(id)
    cost = (obj.value + 1) * 5
    if obj.character.exp >= cost:
        obj.character.exp -= cost
        obj.value += 1
        db.session.commit()
    return redirect(url_for('upgrade', char_id=obj.character.id))

@app.route('/up_mir/<int:id>')
def up_mir(id):
    obj = Miracle.query.get_or_404(id)
    # Формула: (Текущий уровень + 1) * Ранг * 2
    cost = (obj.level + 1) * obj.rank * 2
    if obj.character.exp >= cost:
        obj.character.exp -= cost
        obj.level += 1
        db.session.commit()
    return redirect(url_for('upgrade', char_id=obj.character.id))

@app.route('/add_exp/<int:char_id>', methods=['POST'])
def add_exp(char_id):
    char = Character.query.get_or_404(char_id)
    char.exp += int(request.form.get('amount', 0))
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, host='0.0.0.0')
