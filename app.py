import time
import psycopg2
from flask import Flask, request, render_template_string

app = Flask(__name__)

DB_CONFIG = {
    'host': 'postgres',
    'database': 'mydatabase',
    'user': 'myuser',
    'password': 'mypassword'
}

def initialize_database():
    """Создает таблицу, если она не существует."""
    with create_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_counter (
                id SERIAL PRIMARY KEY,
                visit_time TIMESTAMP NOT NULL,
                user_agent VARCHAR NOT NULL
            );
            """)
            conn.commit()

def create_db_connection():
    """Создает и возвращает подключение к базе данных."""
    return psycopg2.connect(**DB_CONFIG)

def record_visit(user_agent):
    """Получает и увеличивает счетчик посещений."""
    max_retries = 5
    while max_retries > 0:
        try:
            with create_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT COUNT(*) FROM visit_counter')
                    visit_count = cursor.fetchone()[0]
                    cursor.execute('INSERT INTO visit_counter (visit_time, user_agent) VALUES (NOW(), %s)', (user_agent,))
                    conn.commit()
                    return visit_count
        except (Exception, psycopg2.DatabaseError) as error:
            max_retries -= 1
            if max_retries == 0:
                raise error
            time.sleep(0.5)

@app.route('/')
def welcome():
    """Обрабатывает запрос на главной странице и увеличивает счетчик."""
    user_agent = request.headers.get('User-Agent')
    visit_count = record_visit(user_agent)
    return f'Hello World, Nastya! You have been seen {visit_count} times.\n'

@app.route('/visits')
def display_visits():
    """Отображает таблицу с данными о посещениях."""
    with create_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM visit_counter')
            visit_records = cursor.fetchall()

    visits_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visit Counter</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Table Counter</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Datetime</th>
                <th>Client Info</th>
            </tr>
            {% for record in visit_records %}
            <tr>
                <td>{{ record[0] }}</td>
                <td>{{ record[1] }}</td>
                <td>{{ record[2] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''

    return render_template_string(visits_html, visit_records=visit_records)

if __name__ == 'main':
    initialize_database()
    app.run(debug=True)