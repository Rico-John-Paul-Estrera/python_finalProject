import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'createqr.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with tables"""
    if not os.path.exists(DATABASE):
        db = get_db()
        cursor = db.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create students table
        cursor.execute('''
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idno TEXT UNIQUE NOT NULL,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                course TEXT NOT NULL,
                level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                time_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')
        
        # Insert default admin user
        admin_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', 
                      ('Admin', 'admin@example.com', admin_password))
        
        db.commit()
        db.close()

# User functions
def get_user_by_email(email):
    """Get user by email"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    db.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    return user

def get_all_users():
    """Get all users"""
    db = get_db()
    users = db.execute('SELECT id, name, email, created_at FROM users ORDER BY id ASC').fetchall()
    db.close()
    return users

def create_user(email, password, name=''):
    """Create new user"""
    db = get_db()
    try:
        hashed_password = generate_password_hash(password)
        db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                  (name, email, hashed_password))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
        return False

def update_user(user_id, email, password, name=''):
    """Update user"""
    db = get_db()
    try:
        hashed_password = generate_password_hash(password)
        db.execute('UPDATE users SET name=?, email=?, password=? WHERE id=?',
                  (name, email, hashed_password, user_id))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
        return False

def delete_user(user_id):
    """Delete user"""
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    db.close()

# Student functions
def get_all_students():
    """Get all students"""
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY lastname, firstname').fetchall()
    db.close()
    return students

def get_student_by_id(student_id):
    """Get student by ID"""
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    db.close()
    return student

def get_student_by_idno(idno):
    """Get student by IDNO"""
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE idno = ?', (idno,)).fetchone()
    db.close()
    return student

def create_student(idno, firstname, lastname, course, level):
    """Create new student"""
    db = get_db()
    try:
        db.execute('INSERT INTO students (idno, firstname, lastname, course, level) VALUES (?, ?, ?, ?, ?)',
                  (idno, firstname, lastname, course, level))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
        return False

def update_student(student_id, idno, firstname, lastname, course, level):
    """Update student"""
    db = get_db()
    try:
        db.execute('UPDATE students SET idno=?, firstname=?, lastname=?, course=?, level=? WHERE id=?',
                  (idno, firstname, lastname, course, level, student_id))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
        return False

def delete_student(student_id):
    """Delete student and related attendance records"""
    db = get_db()
    db.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.commit()
    db.close()

# Attendance functions
def record_attendance(student_id):
    """Record attendance for student"""
    db = get_db()
    try:
        db.execute('INSERT INTO attendance (student_id) VALUES (?)', (student_id,))
        db.commit()
        db.close()
        return True
    except Exception as e:
        db.close()
        return False

def get_attendance_by_date(date):
    """Get attendance records by date"""
    db = get_db()
    attendance = db.execute('''
        SELECT s.id, s.idno, s.firstname, s.lastname, s.course, s.level, a.time_in
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE DATE(a.date) = ?
        ORDER BY a.time_in DESC
    ''', (date,)).fetchall()
    db.close()
    return attendance

def get_all_attendance():
    """Get all attendance records"""
    db = get_db()
    attendance = db.execute('''
        SELECT s.id, s.idno, s.firstname, s.lastname, s.course, s.level, a.time_in, a.date
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time_in DESC
    ''').fetchall()
    db.close()
    return attendance

def reset_user_id_sequence():
    """Reset the user ID sequence to start from 1"""
    conn = sqlite3.connect('qrcode.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
    conn.commit()
    conn.close()