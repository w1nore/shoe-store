from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('shoe_store.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица ролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')
    
    # Таблица категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица производителей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manufacturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица поставщиков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            price REAL NOT NULL,
            supplier_id INTEGER NOT NULL,
            manufacturer_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            discount INTEGER DEFAULT 0,
            stock_quantity INTEGER DEFAULT 0,
            description TEXT,
            photo_path TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Таблица пунктов выдачи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pickup_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL
        )
    ''')
    
    # Таблица статусов заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            pickup_point_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            delivery_date TEXT,
            receive_code TEXT NOT NULL,
            status_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (pickup_point_id) REFERENCES pickup_points(id),
            FOREIGN KEY (status_id) REFERENCES order_statuses(id)
        )
    ''')
    
    # Таблица позиций заказа
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def import_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже данные
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Импорт ролей
    roles = ['Администратор', 'Менеджер', 'Авторизированный клиент']
    for role in roles:
        cursor.execute("INSERT OR IGNORE INTO roles (name) VALUES (?)", (role,))
    
    # Импорт пользователей
    users_data = [
        ('Никифорова Весения Николаевна', '94d5ous@gmail.com', 'uzWC67', 1),
        ('Сазонов Руслан Германович', 'uth4iz@mail.com', '2L6KZG', 1),
        ('Одинцов Серафим Артёмович', 'yzls62@outlook.com', 'JlFRCZ', 1),
        ('Степанов Михаил Артёмович', '1diph5e@tutanota.com', '8ntwUp', 2),
        ('Ворсин Петр Евгеньевич', 'tjde7c@yahoo.com', 'YOyhfR', 2),
        ('Старикова Елена Павловна', 'wpmrc3do@tutanota.com', 'RSbvHv', 2),
        ('Михайлюк Анна Вячеславовна', '5d4zbu@tutanota.com', 'rwVDh9', 3),
        ('Ситдикова Елена Анатольевна', 'ptec8ym@yahoo.com', 'LdNyos', 3),
        ('Ворсин Петр Евгеньевич', '1qz4kw@mail.com', 'gynQMT', 3),
        ('Старикова Елена Павловна', '4np6se@mail.com', 'AtnDjr', 3),
    ]
    for user in users_data:
        cursor.execute("""
            INSERT OR IGNORE INTO users (full_name, login, password, role_id) 
            VALUES (?, ?, ?, ?)
        """, (user[0], user[1], user[2], user[3]))
    
    # Импорт категорий
    categories = ['Женская обувь', 'Мужская обувь']
    for cat in categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    
    # Импорт производителей
    manufacturers = ['Kari', 'Marco Tozzi', 'Рос', 'Rieker', 'Alessio Nesca', 'CROSBY', 'Caprice']
    for man in manufacturers:
        cursor.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES (?)", (man,))
    
    # Импорт поставщиков
    suppliers = ['Kari', 'Обувь для вас']
    for sup in suppliers:
        cursor.execute("INSERT OR IGNORE INTO suppliers (name) VALUES (?)", (sup,))
    
    # Импорт товаров
    products_data = [
        ('А112Т4', 'Ботинки', 'шт.', 4990, 1, 1, 1, 3, 6, 'Женские Ботинки демисезонные kari', '1.jpg'),
        ('F635R4', 'Ботинки', 'шт.', 3244, 2, 2, 1, 2, 13, 'Ботинки Marco Tozzi женские демисезонные, размер 39, цвет бежевый', '2.jpg'),
        ('H782T5', 'Туфли', 'шт.', 4499, 1, 1, 2, 4, 5, 'Туфли kari мужские классика MYZ21AW-450A, размер 43, цвет: черный', '3.jpg'),
        ('G783F5', 'Ботинки', 'шт.', 5900, 1, 3, 2, 2, 8, 'Мужские ботинки Рос-Обувь кожаные с натуральным мехом', '4.jpg'),
        ('J384T6', 'Ботинки', 'шт.', 3800, 2, 4, 2, 2, 16, 'B3430/14 Полуботинки мужские Rieker', '5.jpg'),
        ('D572U8', 'Кроссовки', 'шт.', 4100, 2, 3, 2, 3, 6, '129615-4 Кроссовки мужские', '6.jpg'),
        ('F572H7', 'Туфли', 'шт.', 2700, 1, 2, 1, 2, 14, 'Туфли Marco Tozzi женские летние, размер 39, цвет черный', '7.jpg'),
        ('D329H3', 'Полуботинки', 'шт.', 1890, 2, 5, 1, 4, 4, 'Полуботинки Alessio Nesca женские 3-30797-47, размер 37, цвет: бордовый', '8.jpg'),
        ('B320R5', 'Туфли', 'шт.', 4300, 1, 4, 1, 2, 6, 'Туфли Rieker женские демисезонные, размер 41, цвет коричневый', '9.jpg'),
        ('G432E4', 'Туфли', 'шт.', 2800, 1, 1, 1, 3, 15, 'Туфли kari женские TR-YR-413017, размер 37, цвет: черный', '10.jpg'),
        ('S213E3', 'Полуботинки', 'шт.', 2156, 2, 6, 2, 3, 6, '407700/01-01 Полуботинки мужские CROSBY', None),
        ('E482R4', 'Полуботинки', 'шт.', 1800, 1, 1, 1, 2, 14, 'Полуботинки kari женские MYZ20S-149, размер 41, цвет: черный', None),
        ('S634B5', 'Кеды', 'шт.', 5500, 2, 6, 2, 3, 0, 'Кеды Caprice мужские демисезонные, размер 42, цвет черный', None),
        ('K345R4', 'Полуботинки', 'шт.', 2100, 2, 6, 2, 2, 3, '407700/01-02 Полуботинки мужские CROSBY', None),
        ('O754F4', 'Туфли', 'шт.', 5400, 2, 4, 1, 4, 18, 'Туфли женские демисезонные Rieker артикул 55073-68/37', None),
        ('G531F4', 'Ботинки', 'шт.', 6600, 1, 1, 1, 12, 9, 'Ботинки женские зимние ROMER арт. 893167-01 Черный', None),
        ('J542F5', 'Тапочки', 'шт.', 500, 1, 1, 2, 13, 0, 'Тапочки мужские Арт.70701-55-67син р.41', None),
        ('B431R5', 'Ботинки', 'шт.', 2700, 2, 4, 2, 2, 5, 'Мужские кожаные ботинки/мужские ботинки', None),
        ('P764G4', 'Туфли', 'шт.', 6800, 1, 6, 1, 15, 15, 'Туфли женские, ARGO, размер 38', None),
        ('C436G5', 'Ботинки', 'шт.', 10200, 1, 5, 1, 15, 9, 'Ботинки женские, ARGO, размер 40', None),
        ('F427R5', 'Ботинки', 'шт.', 11800, 2, 4, 1, 15, 11, 'Ботинки на молнии с декоративной пряжкой FRAU', None),
        ('N457T5', 'Полуботинки', 'шт.', 4600, 1, 6, 1, 3, 13, 'Полуботинки Ботинки черные зимние, мех', None),
        ('D364R4', 'Туфли', 'шт.', 12400, 1, 1, 1, 16, 5, 'Туфли Luiza Belly женские Kate-lazo черные из натуральной замши', None),
        ('S326R5', 'Тапочки', 'шт.', 9900, 2, 6, 2, 17, 15, 'Мужские кожаные тапочки "Профиль С.Дали"', None),
        ('L754R4', 'Полуботинки', 'шт.', 1700, 1, 1, 1, 2, 7, 'Полуботинки kari женские WB2020SS-26, размер 38, цвет: черный', None),
        ('M542T5', 'Кроссовки', 'шт.', 2800, 2, 4, 2, 18, 3, 'Кроссовки мужские TOFA', None),
        ('D268G5', 'Туфли', 'шт.', 4399, 2, 4, 1, 3, 12, 'Туфли Rieker женские демисезонные, размер 36, цвет коричневый', None),
        ('T324F5', 'Сапоги', 'шт.', 4699, 1, 6, 1, 2, 5, 'Сапоги замша Цвет: синий', None),
        ('K358H6', 'Тапочки', 'шт.', 599, 1, 4, 2, 20, 2, 'Тапочки мужские син р.41', None),
        ('H535R5', 'Ботинки', 'шт.', 2300, 2, 4, 1, 2, 7, 'Женские Ботинки демисезонные', None),
    ]
    
    for prod in products_data:
        photo_path = prod[10] if prod[10] else 'picture.png'
        cursor.execute("""
            INSERT OR IGNORE INTO products 
            (article, name, unit, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo_path) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prod[0], prod[1], prod[2], prod[3], prod[4], prod[5], prod[6], prod[7], prod[8], prod[9], photo_path))
    
    # Импорт пунктов выдачи
    pickup_points = [
        '420151, г. Лесной, ул. Вишневая, 32',
        '125061, г. Лесной, ул. Подгорная, 8',
        '630370, г. Лесной, ул. Шоссейная, 24',
        '400562, г. Лесной, ул. Зеленая, 32',
        '614510, г. Лесной, ул. Маяковского, 47',
        '410542, г. Лесной, ул. Светлая, 46',
        '620839, г. Лесной, ул. Цветочная, 8',
        '443890, г. Лесной, ул. Коммунистическая, 1',
        '603379, г. Лесной, ул. Спортивная, 46',
        '603721, г. Лесной, ул. Гоголя, 41',
        '410172, г. Лесной, ул. Северная, 13',
        '614611, г. Лесной, ул. Молодежная, 50',
        '454311, г.Лесной, ул. Новая, 19',
        '660007, г.Лесной, ул. Октябрьская, 19',
        '603036, г. Лесной, ул. Садовая, 4',
        '394060, г.Лесной, ул. Фрунзе, 43',
        '410661, г. Лесной, ул. Школьная, 50',
        '625590, г. Лесной, ул. Коммунистическая, 20',
        '625683, г. Лесной, ул. 8 Марта',
        '450983, г.Лесной, ул. Комсомольская, 26',
    ]
    for point in pickup_points:
        cursor.execute("INSERT OR IGNORE INTO pickup_points (address) VALUES (?)", (point,))
    
    # Импорт статусов заказов
    statuses = ['Новый', 'Завершен']
    for status in statuses:
        cursor.execute("INSERT OR IGNORE INTO order_statuses (name) VALUES (?)", (status,))
    
    # Импорт заказов
    orders_data = [
        ('ORD001', 5, 1, '2025-02-27', '2025-04-20', '901', 2),
        ('ORD002', 2, 11, '2022-09-28', '2025-04-21', '902', 2),
        ('ORD003', 3, 2, '2025-03-21', '2025-04-22', '903', 2),
        ('ORD004', 4, 11, '2025-02-20', '2025-04-23', '904', 2),
        ('ORD005', 5, 2, '2025-03-17', '2025-04-24', '905', 2),
        ('ORD006', 2, 15, '2025-03-01', '2025-04-25', '906', 2),
        ('ORD007', 3, 3, '2025-03-30', '2025-04-26', '907', 2),
        ('ORD008', 4, 19, '2025-03-31', '2025-04-27', '908', 1),
        ('ORD009', 5, 5, '2025-04-02', '2025-04-28', '909', 1),
        ('ORD010', 5, 19, '2025-04-03', '2025-04-29', '910', 1),
    ]
    
    for order in orders_data:
        cursor.execute("""
            INSERT OR IGNORE INTO orders 
            (order_code, user_id, pickup_point_id, order_date, delivery_date, receive_code, status_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, order)
    
    # Импорт позиций заказов
    order_items_data = [
        (1, 1, 2), (1, 2, 2),
        (2, 3, 1), (2, 4, 1),
        (3, 5, 10), (3, 6, 10),
        (4, 7, 5), (4, 8, 4),
        (5, 1, 2), (5, 2, 2),
        (6, 3, 1), (6, 4, 1),
        (7, 5, 10), (7, 6, 10),
        (8, 7, 5), (8, 8, 4),
        (9, 9, 5), (9, 10, 1),
        (10, 11, 5), (10, 12, 5),
    ]
    
    for item in order_items_data:
        cursor.execute("""
            INSERT OR IGNORE INTO order_items (order_id, product_id, quantity) 
            VALUES (?, ?, ?)
        """, item)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.login = ?
        ''', (login,)).fetchone()
        conn.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['role'] = user['role_name']
            flash(f'Добро пожаловать, {user["full_name"]}!', 'success')
            return redirect(url_for('products'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/guest')
def guest():
    session['role'] = 'Гость'
    session['user_name'] = 'Гость'
    return redirect(url_for('products'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/products')
def products():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    role = session['role']
    search = request.args.get('search', '')
    supplier_filter = request.args.get('supplier', '')
    sort = request.args.get('sort', '')
    
    conn = get_db_connection()
    
    # Получаем список поставщиков для фильтра
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    
    # Базовый запрос
    query = '''
        SELECT p.*, s.name as supplier_name, m.name as manufacturer_name, c.name as category_name
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.id
        JOIN manufacturers m ON p.manufacturer_id = m.id
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []
    
    # Поиск (только для менеджера и администратора)
    if role in ['Менеджер', 'Администратор'] and search:
        query += ''' AND (
            p.name LIKE ? OR 
            p.article LIKE ? OR 
            p.description LIKE ? OR 
            m.name LIKE ? OR 
            s.name LIKE ? OR
            c.name LIKE ?
        )'''
        search_param = f'%{search}%'
        params.extend([search_param] * 6)
    
    # Фильтр по поставщику (только для менеджера и администратора)
    if role in ['Менеджер', 'Администратор'] and supplier_filter:
        query += " AND p.supplier_id = ?"
        params.append(supplier_filter)
    
    # Сортировка (только для менеджера и администратора)
    if role in ['Менеджер', 'Администратор']:
        if sort == 'stock_asc':
            query += " ORDER BY p.stock_quantity ASC"
        elif sort == 'stock_desc':
            query += " ORDER BY p.stock_quantity DESC"
        else:
            query += " ORDER BY p.id"
    else:
        query += " ORDER BY p.id"
    
    products = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('products.html', 
                         products=products, 
                         suppliers=suppliers,
                         search=search,
                         supplier_filter=supplier_filter,
                         sort=sort)

@app.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('products'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        article = request.form['article']
        name = request.form['name']
        unit = request.form['unit']
        price = float(request.form['price'])
        supplier_id = request.form['supplier_id']
        manufacturer_id = request.form['manufacturer_id']
        category_id = request.form['category_id']
        discount = int(request.form['discount'])
        stock_quantity = int(request.form['stock_quantity'])
        description = request.form['description']
        
        # Обработка загрузки фото
        photo_path = 'picture.png'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename
        
        conn.execute('''
            INSERT INTO products (article, name, unit, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (article, name, unit, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo_path))
        conn.commit()
        conn.close()
        
        flash('Товар успешно добавлен', 'success')
        return redirect(url_for('products'))
    
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    manufacturers = conn.execute("SELECT * FROM manufacturers ORDER BY name").fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    
    return render_template('product_form.html', 
                         suppliers=suppliers, 
                         manufacturers=manufacturers, 
                         categories=categories,
                         product=None)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('products'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        article = request.form['article']
        name = request.form['name']
        unit = request.form['unit']
        price = float(request.form['price'])
        supplier_id = request.form['supplier_id']
        manufacturer_id = request.form['manufacturer_id']
        category_id = request.form['category_id']
        discount = int(request.form['discount'])
        stock_quantity = int(request.form['stock_quantity'])
        description = request.form['description']
        
        # Получаем текущее фото
        current = conn.execute("SELECT photo_path FROM products WHERE id = ?", (id,)).fetchone()
        photo_path = current['photo_path'] if current else 'picture.png'
        
        # Обработка загрузки нового фото
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                # Удаляем старое фото если оно не дефолтное
                if photo_path and photo_path != 'picture.png':
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename
        
        conn.execute('''
            UPDATE products 
            SET article=?, name=?, unit=?, price=?, supplier_id=?, manufacturer_id=?, category_id=?, discount=?, stock_quantity=?, description=?, photo_path=?
            WHERE id=?
        ''', (article, name, unit, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo_path, id))
        conn.commit()
        conn.close()
        
        flash('Товар успешно обновлен', 'success')
        return redirect(url_for('products'))
    
    product = conn.execute('''
        SELECT p.*, s.name as supplier_name, m.name as manufacturer_name, c.name as category_name
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.id
        JOIN manufacturers m ON p.manufacturer_id = m.id
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    manufacturers = conn.execute("SELECT * FROM manufacturers ORDER BY name").fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    
    return render_template('product_form.html', 
                         suppliers=suppliers, 
                         manufacturers=manufacturers, 
                         categories=categories,
                         product=product)

@app.route('/product/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('products'))
    
    conn = get_db_connection()
    
    # Проверяем, есть ли товар в заказах
    order_item = conn.execute("SELECT * FROM order_items WHERE product_id = ?", (id,)).fetchone()
    if order_item:
        conn.close()
        flash('Нельзя удалить товар, который присутствует в заказе', 'error')
        return redirect(url_for('products'))
    
    # Получаем фото для удаления
    product = conn.execute("SELECT photo_path FROM products WHERE id = ?", (id,)).fetchone()
    if product and product['photo_path'] and product['photo_path'] != 'picture.png':
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], product['photo_path'])
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Товар успешно удален', 'success')
    return redirect(url_for('products'))

@app.route('/orders')
def orders():
    if session.get('role') not in ['Менеджер', 'Администратор']:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('products'))
    
    conn = get_db_connection()
    orders = conn.execute('''
        SELECT o.*, u.full_name as user_name, pp.address as pickup_address, os.name as status_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN pickup_points pp ON o.pickup_point_id = pp.id
        JOIN order_statuses os ON o.status_id = os.id
        ORDER BY o.id DESC
    ''').fetchall()
    
    # Получаем товары для каждого заказа
    orders_with_items = []
    for order in orders:
        items = conn.execute('''
            SELECT oi.*, p.name as product_name, p.article as product_article
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        orders_with_items.append({
            'order': order,
            'order_items': items
        })
    
    conn.close()
    
    return render_template('orders.html', orders=orders_with_items)

@app.route('/order/add', methods=['GET', 'POST'])
def add_order():
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('orders'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        order_code = request.form['order_code']
        user_id = request.form['user_id']
        pickup_point_id = request.form['pickup_point_id']
        order_date = request.form['order_date']
        delivery_date = request.form['delivery_date']
        receive_code = request.form['receive_code']
        status_id = request.form['status_id']
        
        conn.execute('''
            INSERT INTO orders (order_code, user_id, pickup_point_id, order_date, delivery_date, receive_code, status_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_code, user_id, pickup_point_id, order_date, delivery_date, receive_code, status_id))
        conn.commit()
        conn.close()
        
        flash('Заказ успешно добавлен', 'success')
        return redirect(url_for('orders'))
    
    users = conn.execute("SELECT * FROM users WHERE role_id = 3 ORDER BY full_name").fetchall()
    pickup_points = conn.execute("SELECT * FROM pickup_points ORDER BY address").fetchall()
    statuses = conn.execute("SELECT * FROM order_statuses ORDER BY name").fetchall()
    conn.close()
    
    # Генерируем случайный код получения
    receive_code = ''.join(random.choices(string.digits, k=3))
    
    return render_template('order_form.html', 
                         users=users, 
                         pickup_points=pickup_points, 
                         statuses=statuses,
                         order=None,
                         receive_code=receive_code)

@app.route('/order/edit/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('orders'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        order_code = request.form['order_code']
        user_id = request.form['user_id']
        pickup_point_id = request.form['pickup_point_id']
        order_date = request.form['order_date']
        delivery_date = request.form['delivery_date']
        receive_code = request.form['receive_code']
        status_id = request.form['status_id']
        
        conn.execute('''
            UPDATE orders 
            SET order_code=?, user_id=?, pickup_point_id=?, order_date=?, delivery_date=?, receive_code=?, status_id=?
            WHERE id=?
        ''', (order_code, user_id, pickup_point_id, order_date, delivery_date, receive_code, status_id, id))
        conn.commit()
        conn.close()
        
        flash('Заказ успешно обновлен', 'success')
        return redirect(url_for('orders'))
    
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (id,)).fetchone()
    users = conn.execute("SELECT * FROM users WHERE role_id = 3 ORDER BY full_name").fetchall()
    pickup_points = conn.execute("SELECT * FROM pickup_points ORDER BY address").fetchall()
    statuses = conn.execute("SELECT * FROM order_statuses ORDER BY name").fetchall()
    conn.close()
    
    return render_template('order_form.html', 
                         users=users, 
                         pickup_points=pickup_points, 
                         statuses=statuses,
                         order=order)

@app.route('/order/delete/<int:id>', methods=['POST'])
def delete_order(id):
    if session.get('role') != 'Администратор':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('orders'))
    
    conn = get_db_connection()
    conn.execute("DELETE FROM order_items WHERE order_id = ?", (id,))
    conn.execute("DELETE FROM orders WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Заказ успешно удален', 'success')
    return redirect(url_for('orders'))

if __name__ == '__main__':
    init_db()
    import_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
