from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Qazplm123$$$",
    database="employee_management"
)
cursor = db.cursor()

@app.route('/')
def index():
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    return render_template('index.html', employees=employees)

@app.route('/add', methods=['POST'])
def add_employee():
    name = request.form['name']
    job_position = request.form['job_position']
    department = request.form['department']
    salary = request.form['salary']

    cursor.execute("INSERT INTO employees (name, job_position, department, salary) VALUES (%s, %s, %s, %s)", 
                   (name, job_position, department, salary))
    db.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET'])
def edit_employee(id):
    cursor.execute("SELECT * FROM employees WHERE id = %s", (id,))
    employee = cursor.fetchone()
    if not employee:
        return "Employee not found", 404
    return render_template('update.html', employee=employee)

# Route to handle the update process
@app.route('/update/<int:id>', methods=['POST'])
def update_employee(id):
    name = request.form['name']
    job_position = request.form['job_position']
    department = request.form['department']
    salary = request.form['salary']

    cursor.execute("UPDATE employees SET name=%s, job_position=%s, department=%s, salary=%s WHERE id=%s",
                   (name, job_position, department, salary, id))
    db.commit()

    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    db.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
