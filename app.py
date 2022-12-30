import psycopg2
from flask import Flask, request, session, redirect, url_for, flash, render_template, g
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# !!! Before starting an application uncomment secret key string and database connection string !!!
# !!! Add your secret key, database superuser name and password !!!

# Your app's secret key:
app.secret_key = "oifjw984tug"

# Your database URI:
app.config['DB_URI'] = f"host='localhost' dbname='alcocompany' user='postgres' password='carpe_diem1965'"


@app.route('/', methods=['GET', 'POST'])
def render_auth(error=None):
    close_db(error)
    # Your database URI:
    app.config['DB_URI'] = f"host='localhost' dbname='alcocompany' user='postgres' password='carpe_diem1965'"
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE login = %s;", (login,))
        try:
            hash = cur.fetchone()[0]
        except:
            hash = ""
        conn.commit()
        cur.close()
        if check_password_hash(hash, password):
            app.config['DB_URI'] = f"host='localhost' dbname='alcocompany' user='{login}' password='{password}'"
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT token FROM users WHERE login = %s;", (login,))
            token = cur.fetchone()[0]
            conn.commit()
            cur.close()
            session['token'] = token
            return redirect(url_for("main"))
        flash("Неверный логин или пароль")
    return render_template('auth.html')


@app.route('/main', methods=['GET', 'POST'])
def main():
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM order_info;")
    orders = cur.fetchall()
    conn.commit()
    cur.close()

    return render_template("index.html", role_id=role_id, orders=orders)


@app.route('/order/<int:order_id>/departure', methods=['GET', 'POST'])
def update_status_departure(order_id):

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET order_status_id = 2 WHERE order_id = %s;", (order_id,))
    conn.commit()
    cur.close()

    return redirect(url_for('main'))


@app.route('/order/<int:order_id>/arrived', methods=['GET', 'POST'])
def update_status_arrived(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET order_status_id = 3 WHERE order_id = %s;", (order_id,))
    conn.commit()
    cur.close()

    return redirect(url_for('main'))


@app.route('/order/<int:order_id>/payed', methods=['GET', 'POST'])
def update_payment_status(order_id):

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET payment_status_id = 2 WHERE order_id = %s;", (order_id,))
    conn.commit()
    cur.close()

    return redirect(url_for('main'))


@app.route('/choose_org', methods=['GET', 'POST'])
def choose_org():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT org_name FROM client_organisation;')
    orgs = cur.fetchall()
    list_of_orgs = []
    for org_id in orgs:
        list_of_orgs.append(org_id[0])
    conn.commit()
    cur.close()
    if request.method == 'POST':
        org_name = request.form.get('org_name')
        session['org_name'] = org_name
        return redirect(url_for('client_registration'))
    return render_template("choose_org.html", list_of_orgs=list_of_orgs)


@app.route('/add_employee', methods=['GET', 'POST'])
def employee_registration():
    if request.method == 'POST':
        service_number = request.form.get('service_number')
        passport_number = request.form.get('passport_number')
        name = request.form.get('name')
        surname = request.form.get('surname')
        middle_name = request.form.get('middle_name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        post_id = request.form.get('post_id')
        login = request.form.get('login')
        password = request.form.get('password')

        hash = generate_password_hash(password)
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("CALL create_user_employee(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (service_number, passport_number, name, surname, middle_name,
                         phone_number, email, post_id, login, password, hash))
            conn.commit()
            cur.close()
            return redirect(url_for('get_employees'))
        except:
            flash('User already exists')
    return render_template('employee_register.html')


@app.route('/employees', methods=['GET', 'POST'])
def get_employees():
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees_info;")
    employees = cur.fetchall()
    conn.commit()
    cur.close()
    return render_template("employees.html", employees=employees, role_id=role_id)


@app.route('/employees/<int:pers_id>', methods=['GET', 'POST'])
def get_employee_info(pers_id):
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    if role_id == 1:
        cur.execute("SELECT * FROM extended_employees_info WHERE personnel_number = %s;", (pers_id,))
    else:
        cur.execute("SELECT personnel_number, passport_number, name, surname, middle_name, tel_number, email, "
                    "role_name FROM extended_employees_info WHERE personnel_number = %s;", (pers_id,))
    info = cur.fetchall()[0]
    print(info)
    conn.commit()
    cur.close()
    return render_template("employee_info.html", role_id=role_id, info=info)


@app.route('/clients', methods=['GET', 'POST'])
def get_orgs():
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM client_organisation;")
    orgs = cur.fetchall()
    print(orgs)
    conn.commit()
    cur.close()
    return render_template("clients.html", orgs=orgs, role_id=role_id)


@app.route('/clients/<int:org_id>', methods=['GET', 'POST'])
def get_contacts_info(org_id):
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    if role_id == 1:
        cur.execute("SELECT * FROM contact_person WHERE org_id = %s;", (org_id,))
    else:
        cur.execute("SELECT contact_id, tel_number, email, "
                    "name, surname, middle_name FROM contact_person WHERE org_id = %s;", (org_id,))
    info = cur.fetchall()
    conn.commit()
    cur.close()
    return render_template("contacts.html", role_id=role_id, info=info)


@app.route('/clients/<int:contact_id>/delete', methods=['GET', 'POST'])
def delete_contact(contact_id):
    print(contact_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CALL delete_contact(%s);", (contact_id,))
    conn.commit()
    cur.close()
    return redirect(url_for('get_orgs'))


@app.route('/products', methods=['GET', 'POST'])
def get_products():
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM product_info;")
    products = cur.fetchall()
    p_units_count = []
    for product in products:
        cur.execute("SELECT count_product_units(%s);", (product[0],))
        p_units_count.append(cur.fetchone()[0])
    print(p_units_count)
    conn.commit()
    cur.close()
    return render_template("products.html", products=products, role_id=role_id)


@app.route('/products/<int:id>', methods=['GET', 'POST'])
def get_products_info(id):
    role_id = get_role_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM product_unit_info WHERE product_id = %s;", (id,))
    info = cur.fetchall()
    print(info)
    conn.commit()
    cur.close()
    return render_template("product_info.html", role_id=role_id, info=info)


@app.route('/order_choose_type', methods=['GET', 'POST'])
def get_order_p_type():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT type_name FROM product_type;")
    list_of_types = cur.fetchall()
    conn.commit()
    cur.close()

    if request.method == 'POST':
        session['p_type_order'] = request.form.get('p_type')
        print(session['p_type_order'])
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT type_id FROM product_type WHERE type_name = %s;", (session['p_type_order'],))

        session['p_type_id_order'] = cur.fetchone()[0]
        print(session['p_type_id_order'])

        conn.commit()
        cur.close()
        return redirect(url_for('get_order_p_name'))
    return render_template("choose_order_type.html", list_of_types=list_of_types)


@app.route('/order_choose_name', methods=['GET', 'POST'])
def get_order_p_name():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT product_name FROM product WHERE type_id = %s;", (session['p_type_id_order'],))
    list_of_names = cur.fetchall()
    conn.commit()
    cur.close()

    if request.method == 'POST':
        p_type = session['p_type_order']
        p_name = request.form.get('p_name')

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT product_id FROM product WHERE product_name = %s;", (p_name,))
        session['p_id'] = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return redirect(url_for('get_order_p_amount'))
    return render_template('choose_order_name.html', list_of_names=list_of_names)


@app.route('/order_choose_amount', methods=['GET', 'POST'])
def get_order_p_amount():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM product_unit WHERE product_id = %s AND order_id IS NULL;", (session['p_id'],))
    amount = cur.fetchone()[0]
    conn.commit()
    cur.close()
    if amount == 0:
        return redirect(url_for('get_no_products'))
    if request.method == 'POST':
        client_amount = request.form.get('amount')
        note = request.form.get('note')
        if note is None:
            note = ''

        conn = get_db()
        cur = conn.cursor()
        cur.execute("CALL add_order(%s, %s, %s);", (note, client_amount, session['p_id']))
        conn.commit()
        cur.close()
        return redirect(url_for('main'))
    return render_template("choose_order_amount.html", amount=amount)


@app.route('/no_products', methods=['GET', 'POST'])
def get_no_products():
    return render_template('new_product.html')


@app.route('/choose_p_type', methods=['GET', 'POST'])
def get_p_type():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT type_name FROM product_type;")
    list_of_types = cur.fetchall()
    conn.commit()
    cur.close()

    if request.method == 'POST':
        session['p_type'] = request.form.get('p_type')
        print(session['p_type'])
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT type_id FROM product_type WHERE type_name = %s;", (session['p_type'],))
        try:
            session['p_type_id'] = cur.fetchone()[0]
            print(session['p_type_id'])
        except:
            session['p_type_id'] = 0
        conn.commit()
        cur.close()
        return redirect(url_for('new_product'))
    return render_template('choose_p_type.html', list_of_types=list_of_types)


@app.route('/new_product', methods=['GET', 'POST'])
def new_product():
    list_of_names = []
    print("new product")
    print(session['p_type_id'])
    if session['p_type_id'] != 0:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT product_name FROM product WHERE type_id = %s;", (session['p_type_id'],))
        list_of_names = cur.fetchall()
        conn.commit()
        cur.close()

    if request.method == 'POST':
        p_type = session['p_type']
        p_name = request.form.get('p_name')
        manuf = request.form.get('manuf')
        strength = request.form.get('strength')
        volume = request.form.get('volume')
        price = request.form.get('price')
        amount = request.form.get('amount')
        print(p_type)
        print(p_name)
        print(manuf)
        print(strength)
        print(volume)
        print(price)
        print(amount)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("CALL add_products(%s, %s, %s, %s, %s, %s, %s);", (p_type, p_name, manuf, strength, volume, price, amount))
            conn.commit()
            cur.close()
        except:
            flash("Такой товар уже есть")
        return redirect(url_for('get_products'))
    return render_template('new_product.html', list_of_names=list_of_names)


@app.route('/client_registration', methods=['GET', 'POST'])
def client_registration():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        name = request.form.get('name')
        surname = request.form.get('surname')
        middle_name = request.form.get('middle_name')
        login = request.form.get('login')
        password = request.form.get('password')

        hash = generate_password_hash(password)

        org_name = session['org_name']
        #try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CALL create_user_client(%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (phone_number, email, name, surname, middle_name, org_name,
                         login, password, hash))
        conn.commit()
        cur.close()

        app.config['DB_URI'] = f"host='localhost' dbname='alcocompany' user='{login}' password='{password}'"
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT token FROM users WHERE login = %s;", (login,))
        token = cur.fetchone()[0]
        conn.commit()
        cur.close()
        session['token'] = token
        return redirect(url_for("main"))
        #except:
            #flash('Такой пользователь уже есть')
    return render_template("client_register.html")


@app.route('/org_registration', methods=['GET', 'POST'])
def org_registration():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        name = request.form.get('name')
        surname = request.form.get('surname')
        middle_name = request.form.get('middle_name')
        login = request.form.get('login')
        password = request.form.get('password')

        org_name = request.form.get('org_name')
        inn_number = request.form.get('inn_number')
        ogrn_number = request.form.get('ogrn_number')
        kpp_number = request.form.get('kpp_number')
        legal_address = request.form.get('legal_address')
        actual_address = request.form.get('actual_address')

        hash = generate_password_hash(password)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO client_organisation(org_name, inn, ogrn, kpp, "
                        "legal_address, actual_address) VALUES (%s, %s, %s, %s, %s, %s);",
                        (org_name, inn_number, ogrn_number, kpp_number, legal_address, actual_address))
            conn.commit()
            cur.close()

            conn = get_db()
            cur = conn.cursor()
            cur.execute("CALL create_user_client(%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (phone_number, email, name, surname, middle_name, org_name,
                         login, password, hash))
            conn.commit()
            cur.close()

            app.config['DB_URI'] = f"host='localhost' dbname='alcocompany' user='{login}' password='{password}'"
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT token FROM users WHERE login = %s;", (login,))
            token = cur.fetchone()[0]
            conn.commit()
            cur.close()
            session['token'] = token
            return redirect(url_for("main"))
        except:
            flash('Неверные поля')
    return render_template("org_register.html")


@app.route('/logout')
def logout(error=None):
    close_db(error)
    return redirect(url_for('render_auth'))


def get_role_id():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT role_id FROM users WHERE token = %s;", (session['token'],))
    role_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return role_id


def get_list(table):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM %s;", (table,))
    data = cur.fetchall()
    conn.commit()
    cur.close()

    return data


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


def connect_db():
    conn = psycopg2.connect(app.config['DB_URI'])
    return conn


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run()
