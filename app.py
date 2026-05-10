from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'synent_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── DATABASE MODELS ────────────────────────────────
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks    = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default='pending')
    priority    = db.Column(db.String(20), default='medium')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ─── ROUTES ─────────────────────────────────────────
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user  = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id']   = user.id
            session['username']  = user.username
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    filter_status   = request.args.get('status', 'all')
    filter_priority = request.args.get('priority', 'all')

    query = Task.query.filter_by(user_id=session['user_id'])

    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    if filter_priority != 'all':
        query = query.filter_by(priority=filter_priority)

    tasks      = query.order_by(Task.created_at.desc()).all()
    all_tasks  = Task.query.filter_by(user_id=session['user_id']).all()
    total      = len(all_tasks)
    completed  = len([t for t in all_tasks if t.status == 'completed'])
    pending    = len([t for t in all_tasks if t.status == 'pending'])

    return render_template('dashboard.html',
                           tasks=tasks,
                           total=total,
                           completed=completed,
                           pending=pending,
                           filter_status=filter_status,
                           filter_priority=filter_priority)

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title       = request.form['title']
    description = request.form.get('description', '')
    priority    = request.form.get('priority', 'medium')

    new_task = Task(title=title,
                    description=description,
                    priority=priority,
                    user_id=session['user_id'])
    db.session.add(new_task)
    db.session.commit()
    flash('Task added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    if task.user_id == session['user_id']:
        task.status = 'completed'
        db.session.commit()
        flash('Task marked as complete!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    if task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted!', 'success')
    return redirect(url_for('dashboard'))

# ─── RUN ────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)