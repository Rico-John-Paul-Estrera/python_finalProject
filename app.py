from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime
from dbhelper import *

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

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

@app.route('/logout')
def logout():
    """Logout admin"""
    session.clear()
    return redirect(url_for('index'))

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
    name = request.form.get('name')
    user_id = request.form.get('user_id')
    
    if not email or not password or not name:
        flash('Email, name and password are required', 'danger')
        return redirect(url_for('user_management'))
    
    try:
        if user_id:
            if update_user(user_id, email, password, name):
                flash('User updated successfully!', 'success')
            else:
                flash('Email already exists', 'danger')
        else:
            if create_user(email, password, name):
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
    # Sort students numerically by idno
    try:
        students = sorted(students, key=lambda s: int(s['idno']))
    except (ValueError, TypeError):
        # If idno cannot be converted to int, sort alphabetically
        students = sorted(students, key=lambda s: s['idno'])
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
        photo_data = request.form.get('photo')
        student_id = request.form.get('student_id') or student_id
        
        print(f"DEBUG: Request method: POST")
        print(f"DEBUG: Form data - idno: {idno}, firstname: {firstname}, lastname: {lastname}")
        print(f"DEBUG: Student ID: {student_id}")
        print(f"DEBUG: Photo data present: {bool(photo_data)}")
        if photo_data:
            print(f"DEBUG: Photo data preview: {photo_data[:100]}")
        
        if not all([idno, firstname, lastname, course, level]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Convert base64 photo to binary
        photo_binary = None
        if photo_data and photo_data.startswith('data:image'):
            import base64
            try:
                photo_binary = base64.b64decode(photo_data.split(',')[1])
                print(f"DEBUG: Converted photo to binary, size: {len(photo_binary)} bytes")
            except Exception as e:
                print(f"DEBUG: Error converting photo: {str(e)}")
                return jsonify({'success': False, 'message': 'Error processing photo'})
        else:
            print(f"DEBUG: Photo data not in expected format")
        
        try:
            if student_id:
                if update_student(student_id, idno, firstname, lastname, course, level, photo_binary):
                    print(f"DEBUG: Student {student_id} updated successfully")
                    return jsonify({'success': True, 'id': student_id, 'message': 'Student updated successfully!'})
                else:
                    return jsonify({'success': False, 'message': 'Student ID already exists'})
            else:
                result = create_student(idno, firstname, lastname, course, level, photo_binary)
                print(f"DEBUG: Create student result: {result}")
                if result:
                    # Get the newly created student ID
                    new_student = get_student_by_idno(idno)
                    return jsonify({'success': True, 'id': new_student['id'], 'message': 'Student created successfully!'})
                else:
                    return jsonify({'success': False, 'message': 'Student ID already exists'})
        except Exception as e:
            print(f"DEBUG: Exception during save: {str(e)}")
            return jsonify({'success': False, 'message': str(e)})
    
    if student_id:
        student = get_student_by_id(student_id)
    
    return render_template('add_student.html', student=student)

@app.route('/api/student/data', methods=['GET'])
@login_required
def get_student_data():
    """Get student data including photo as base64"""
    student_id = request.args.get('id')
    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required'}), 400
    
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    photo_base64 = None
    try:
        if student['photo']:
            import base64
            photo_base64 = base64.b64encode(student['photo']).decode('utf-8')
    except (KeyError, TypeError):
        pass
    
    return jsonify({
        'success': True,
        'student': {
            'id': student['id'],
            'idno': student['idno'],
            'firstname': student['firstname'],
            'lastname': student['lastname'],
            'course': student['course'],
            'level': student['level']
        },
        'photo': photo_base64
    })

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

@app.route('/api/scan/<idno>')
def scan_student(idno):
    """Get student information by scanning QR code"""
    student = get_student_by_idno(idno)
    
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    photo_base64 = None
    try:
        if student['photo']:
            import base64
            photo_base64 = base64.b64encode(student['photo']).decode('utf-8')
    except (KeyError, TypeError):
        pass
    
    return jsonify({
        'success': True,
        'student': {
            'idno': student['idno'],
            'firstname': student['firstname'],
            'lastname': student['lastname'],
            'course': student['course'],
            'level': student['level']
        },
        'photo': photo_base64
    })

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
    
    result = record_attendance(student['id'])
    
    if result['recorded']:
        return jsonify({'success': True, 'message': 'MARKED AS PRESENT!', 'already_present': False})
    elif result['already_present']:
        return jsonify({'success': True, 'message': 'ALREADY MARKED AS PRESENT TODAY', 'already_present': True})
    else:
        return jsonify({'success': False, 'message': 'Error recording attendance'}), 500
    
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
    app.run(debug=True)
