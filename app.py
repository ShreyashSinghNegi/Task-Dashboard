from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    todos = db.relationship('TodoItem', backref='user', lazy=True)

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@login_required
def home():
    todos = TodoItem.query.filter_by(user_id=session['user_id']).order_by(TodoItem.created_at.desc()).all()
    return render_template('home.html', todos=todos)


@app.route('/add', methods=['POST'])
@login_required
def add_item():
    content = request.form.get('content')
    if content:
        new_todo = TodoItem(content=content, user_id=session['user_id'])
        db.session.add(new_todo)
        db.session.commit()
        flash('Task added successfully!', 'success')
    return redirect(url_for('home'))


@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    todo = TodoItem.query.get_or_404(id)
    if todo.user_id == session['user_id']:
        db.session.delete(todo)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    return redirect(url_for('home'))


@app.route('/toggle/<int:id>')
@login_required
def toggle_item(id):
    todo = TodoItem.query.get_or_404(id)
    if todo.user_id == session['user_id']:
        todo.completed = not todo.completed
        db.session.commit()
        flash('Task status updated!', 'success')
    return redirect(url_for('home'))


@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_item(id):
    todo = TodoItem.query.get_or_404(id)
    if todo.user_id == session['user_id']:
        content = request.form.get('content')
        if content:
            todo.content = content
            db.session.commit()
            flash('Task updated successfully!', 'success')
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    init_db()  #