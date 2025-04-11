from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

bcrypt = Bcrypt(app)

# DB connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Qazplm123$$$',
        database='employee_mgmt'
    )

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user is an admin by username or checkbox
        is_admin = False
        if username == "admin_user":  # You can change this to your own admin username
            is_admin = True
        elif request.form.get('is_admin'):
            is_admin = True

        # Hashing the password with Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if the username already exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return render_template('register.html')  # Stay on the register page

        try:
            # Connect to the database and insert the new user
            conn = get_db_connection()  # Ensure you're using mysql.connector
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)", 
                           (username, hashed_password, is_admin))
            conn.commit()  # Commit the transaction
            cursor.close()
            conn.close()
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))  # Redirect to login after successful registration
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")  # Flash error message if there's an issue with DB operation
            return render_template('register.html')  # Stay on the register page in case of error

    return render_template('register.html')  # Ensure this is the right page for the GET request


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' not in session or not session.get('is_admin'):
        flash('You need to be an admin to access this page', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    search_query = request.args.get('search', '').strip().lower()

    # Determine search logic
    if search_query == "admin":
        cursor.execute("SELECT id, username, is_admin FROM users WHERE is_admin = TRUE")
    elif search_query == "user":
        cursor.execute("SELECT id, username, is_admin FROM users WHERE is_admin = FALSE")
    elif search_query:
        cursor.execute("SELECT id, username, is_admin FROM users WHERE username LIKE %s", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT id, username, is_admin FROM users")

    users = cursor.fetchall()

    # Handle form actions (Make Admin or Remove Admin)
    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']

        if action == 'make_admin':
            cursor.execute("UPDATE users SET is_admin = TRUE WHERE id = %s", (user_id,))
            conn.commit()
            flash('User has been promoted to admin.', 'success')
        elif action == 'remove_admin':
            cursor.execute("UPDATE users SET is_admin = FALSE WHERE id = %s", (user_id,))
            conn.commit()
            flash('Admin status removed from user.', 'success')

        # Refresh user list after change
        if search_query == "admin":
            cursor.execute("SELECT id, username, is_admin FROM users WHERE is_admin = TRUE")
        elif search_query == "user":
            cursor.execute("SELECT id, username, is_admin FROM users WHERE is_admin = FALSE")
        elif search_query:
            cursor.execute("SELECT id, username, is_admin FROM users WHERE username LIKE %s", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT id, username, is_admin FROM users")
        users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html', users=users, search_query=search_query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()

        # Check password hash using Flask-Bcrypt
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['is_admin'] = user['is_admin']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash("Check your username and password.", "danger")

    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if 'user' in session:  # Ensure the user is logged in
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', employees=employees, is_admin=session.get('is_admin'))
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))  # Redirect to login if not logged in


@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        job = request.form['job']
        salary = request.form['salary']
        dept = request.form['department']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO employees (name, job_position, salary, department) VALUES (%s, %s, %s, %s)',
                       (name, job, salary, dept))
        conn.commit()
        conn.close()
        flash("Employee added!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_employee.html')


@app.route('/confirm_delete/<int:id>', methods=['POST', 'GET'])
def confirm_delete(id):
    if not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM employees WHERE id = %s', (id,))
    employee = cursor.fetchone()
    conn.close()

    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for('dashboard'))

    return render_template('confirm_delete.html', employee=employee)


@app.route('/delete/<int:id>',methods=['POST'])
def delete_employee(id):
    if not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('dashboard'))

    # Handle deletion in the backend
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM employees WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash("Employee deleted!", "info")
    return redirect(url_for('dashboard'))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_employee(id):
    if not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM employees WHERE id = %s', (id,))
    employee = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        job = request.form['job']
        salary = request.form['salary']
        dept = request.form['department']

        cursor.execute('UPDATE employees SET name=%s, job_position=%s, salary=%s, department=%s WHERE id=%s',
                       (name, job, salary, dept, id))
        conn.commit()
        conn.close()
        flash("Employee updated!", "success")
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('update_employee.html', employee=employee)


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('is_admin', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))  # Redirect to login page after logout


if __name__ == '__main__':
    app.run(debug=True)
