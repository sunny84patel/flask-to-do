from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from io import BytesIO
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index')) 
        else:
            return 'Invalid username or password'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST']) 
@app.route('/signup', methods=['GET', 'POST']) 
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return 'Username or email already exists'

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

# Add login_required decorator to routes that require authentication
def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_view

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)

# db.create_all() COMMENTED IN THIS VERSION

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_task = Task(title=title, description=description)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/complete/<int:task_id>')
def complete(task_id):
    task = Task.query.get(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download_excel')
def download_excel():
    all_tasks = Task.query.all()

    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        workbook = writer.book
        bold_format = workbook.add_format({'bold': True})

        worksheet = workbook.add_worksheet('All Tasks')

        # Установка ширины колонок в таблице Excel
        worksheet.set_column('A:C', 20)

        # Заголовки таблицы
        headers = ['Status', 'Title', 'Description']

        # Запись заголовков таблицы
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold_format)

        # Запись данных в таблицу Excel
        for idx, task in enumerate(all_tasks, start=1):
            status = 'Completed' if task.completed else 'Not Completed'
            task_data = [status, task.title, task.description]
            worksheet.write_row(idx, 0, task_data)

    excel_file.seek(0)
    return send_file(
        excel_file,
        as_attachment=True,
        download_name='tasks.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/sort_tasks/<criteria>')
def sort_tasks(criteria):
    if criteria == 'alphabetically':
        sorted_tasks = Task.query.order_by(Task.title).all()
    elif criteria == 'completed':
        sorted_tasks = Task.query.filter_by(completed=True).all()
    elif criteria == 'notCompleted':
        sorted_tasks = Task.query.filter_by(completed=False).all()
    else:
        sorted_tasks = Task.query.all()

    tasks = [{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'completed': task.completed
    } for task in sorted_tasks]

    return jsonify({'tasks': tasks})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)







#using mongoDB


# from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
# from flask_pymongo import PyMongo
# from werkzeug.security import generate_password_hash, check_password_hash
# from functools import wraps
# import os
# from io import BytesIO
# import pandas as pd
# from bson import ObjectId 


# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.urandom(24)
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/tasksdb'
# mongo = PyMongo(app)

# class User:
#     def __init__(self, username, email, password_hash):
#         self.username = username
#         self.email = email
#         self.password_hash = password_hash

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if 'user_id' in session:
#         return redirect(url_for('index'))

#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         user = mongo.db.users.find_one({'username': username})

#         if user and check_password_hash(user['password_hash'], password):
#             session['user_id'] = str(user['_id'])
#             return redirect(url_for('index'))
#         else:
#             return 'Invalid username or password'

#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     return redirect(url_for('login'))

# @app.route('/', methods=['GET', 'POST']) 
# @app.route('/signup', methods=['GET', 'POST']) 
# def signup():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']

#         # Check if username or email already exists
#         if mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
#             return 'Username or email already exists'

#         # Create new user
#         password_hash = generate_password_hash(password)
#         mongo.db.users.insert_one({'username': username, 'email': email, 'password_hash': password_hash})
#         return redirect(url_for('login'))
#     return render_template('signup.html')

# # Add login_required decorator to routes that require authentication
# def login_required(func):
#     @wraps(func)
#     def decorated_view(*args, **kwargs):
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
#         return func(*args, **kwargs)
#     return decorated_view

# class Task:
#     def __init__(self, title, description, completed=False):
#         self.title = title
#         self.description = description
#         self.completed = completed

# @app.route('/index', methods=['GET', 'POST'])
# @login_required
# def index():
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         new_task = {'title': title, 'description': description, 'completed': False}
#         mongo.db.tasks.insert_one(new_task)
#         new_task['_id'] = str(new_task['_id'])  # Convert ObjectId to string for JSON serialization
#         return jsonify(new_task)

#     tasks = list(mongo.db.tasks.find())
#     tasks = [{'_id': str(task['_id']), 'title': task['title'], 'description': task['description'], 'completed': task['completed']} for task in tasks]
#     return render_template('index.html', tasks=tasks)


# @app.route('/complete/<task_id>')
# def complete(task_id):
#     mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'completed': True}})
#     return redirect(url_for('index'))

# @app.route('/delete/<task_id>')
# def delete(task_id):
#     mongo.db.tasks.delete_one({'_id': ObjectId(task_id)})
#     return redirect(url_for('index'))

# @app.route('/download_excel')
# def download_excel():
#     all_tasks = list(mongo.db.tasks.find())

#     # Create a DataFrame from tasks data
#     df = pd.DataFrame(all_tasks, columns=['title', 'description', 'completed'])
    
#     # Create a BytesIO buffer to store Excel file
#     excel_file = BytesIO()
    
#     # Write DataFrame to Excel file
#     df.to_excel(excel_file, index=False)

#     # Set the cursor to the beginning of the buffer
#     excel_file.seek(0)
    
#     return send_file(
#         excel_file,
#         as_attachment=True,
#         attachment_filename='tasks.xlsx',
#         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )

# if __name__ == '__main__':
#     app.run(debug=True)
