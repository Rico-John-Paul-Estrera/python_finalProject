import sqlite3

conn = sqlite3.connect('createqr.db')
cursor = conn.cursor()

cursor.execute("SELECT idno, firstname, lastname, photo FROM students")
students = cursor.fetchall()

print("Students in database:")
for student in students:
    idno, firstname, lastname, photo = student
    photo_status = "Has photo" if photo else "No photo"
    print(f"  ID: {idno}, Name: {firstname} {lastname}, Photo: {photo_status}")

conn.close()
