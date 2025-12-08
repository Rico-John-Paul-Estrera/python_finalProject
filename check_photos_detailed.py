import sqlite3

conn = sqlite3.connect('createqr.db')
cursor = conn.cursor()

cursor.execute("SELECT id, idno, firstname, lastname, photo FROM students ORDER BY id")
students = cursor.fetchall()

print("All students in database:")
for student in students:
    student_id, idno, firstname, lastname, photo = student
    photo_status = f"Has photo ({len(photo)} bytes)" if photo else "No photo"
    print(f"  ID: {student_id}, IDNO: {idno}, Name: {firstname} {lastname}, Photo: {photo_status}")

conn.close()
