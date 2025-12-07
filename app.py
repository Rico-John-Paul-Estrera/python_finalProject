from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from dbhelper import *

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

def login_required(f):
    """Decorator to check if user is logged in"""
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    """Homepage with QR code reader"""
    return render_template("index.html")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('user_management'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def logout():
    """Logout admin"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/users')
@login_required
def user_management():
    """User management page"""
    users = get_all_users()
    return render_template('user_management.html', users=users)

@app.route('/admin/users/save', methods=['POST'])
@login_required
def save_user():
    """Save or update user"""
    email = request.form.get('email')
    password = request.form.get('password')
    user_id = request.form.get('user_id')
    
    if not email or not password:
        flash('Email and password are required', 'danger')
        return redirect(url_for('user_management'))
    
    try:
        if user_id:
            if update_user(user_id, email, password):
                flash('User updated successfully!', 'success')
            else:
                flash('Email already exists', 'danger')
        else:
            if create_user(email, password):
                flash('User created successfully!', 'success')
            else:
                flash('Email already exists', 'danger')
    except Exception as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user_route(user_id):
    """Delete user"""
    if session.get('user_id') == user_id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('user_management'))
    
    delete_user(user_id)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('user_management'))

@app.route('/admin/students')
@login_required
def student_management():
    """Student management page"""
    students = get_all_students()
    return render_template('student_management.html', students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    """Add or edit student"""
    student = None
    student_id = request.args.get('id')
    
    if request.method == 'POST':
        idno = request.form.get('idno')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        course = request.form.get('course')
        level = request.form.get('level')
        
        if not all([idno, firstname, lastname, course, level]):
            flash('All fields are required', 'danger')
            return redirect(url_for('add_student', id=student_id))
        
        try:
            if student_id:
                if update_student(student_id, idno, firstname, lastname, course, level):
                    flash('Student updated successfully!', 'success')
                else:
                    flash('Student ID already exists', 'danger')
            else:
                if create_student(idno, firstname, lastname, course, level):
                    flash('Student created successfully!', 'success')
                else:
                    flash('Student ID already exists', 'danger')
            return redirect(url_for('student_management'))
        except Exception as e:
            flash(str(e), 'danger')
    
    if student_id:
        student = get_student_by_id(student_id)
    
    return render_template('add_student.html', student=student)

@app.route('/admin/students/save', methods=['POST'])
@login_required
def save_student():
    """Save student (for compatibility)"""
    return add_student()

@app.route('/admin/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student_route(student_id):
    """Delete student"""
    delete_student(student_id)
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('student_management'))

@app.route('/admin/attendance')
@login_required
def view_attendance():
    """View attendance records"""
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance = get_attendance_by_date(date_filter)
    return render_template('view_attendance.html', attendance=attendance, date_filter=date_filter)

@app.route('/api/attendance', methods=['POST'])
def record_attendance_api():
    """Record attendance via QR code scan"""
    data = request.get_json()
    idno = data.get('idno')
    
    if not idno:
        return jsonify({'success': False, 'message': 'Invalid QR code'}), 400
    
    student = get_student_by_idno(idno)
    
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    if record_attendance(student['id']):
        return jsonify({'success': True, 'message': f'Attendance recorded for {idno}'})
    else:
        return jsonify({'success': False, 'message': 'Error recording attendance'}), 500

@app.route('/api/qrcode/<idno>')
def generate_qrcode(idno):
    """Generate QR code for student"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(idno)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({'qrcode': f'data:image/png;base64,{img_str}'})

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
