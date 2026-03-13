import mysql.connector
import pandas as pd

DB_CONFIG = {
    'host': 'localhost',
    'user': 'zeitapp',
    'password': 'anwesenheit',
    'database': 'zeiterfassung'
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            date DATE NOT NULL,
            start_time VARCHAR(5) NOT NULL,
            end_time VARCHAR(5) NOT NULL,
            duration DECIMAL(4,1) NOT NULL,
            comment VARCHAR(500) DEFAULT NULL,
            travel VARCHAR(50) DEFAULT NULL,
            UNIQUE KEY unique_user_date (user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()

    # Migrationen für bestehende Tabellen
    try:
        cursor.execute("ALTER TABLE entries MODIFY COLUMN travel VARCHAR(50) DEFAULT NULL")
        conn.commit()
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE entries ADD COLUMN comment VARCHAR(500) DEFAULT NULL AFTER duration")
        conn.commit()
    except Exception:
        pass

    cursor.close()
    conn.close()


def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users ORDER BY name")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def create_user(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    conn.commit()
    cursor.close()
    conn.close()


def save_entry(user_id, date, start_time, end_time, duration, comment, travel):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entries (user_id, date, start_time, end_time, duration, comment, travel)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            start_time = VALUES(start_time),
            end_time = VALUES(end_time),
            duration = VALUES(duration),
            comment = VALUES(comment),
            travel = VALUES(travel)
    """, (user_id, date, start_time, end_time, duration, comment or None, travel or None))
    conn.commit()
    cursor.close()
    conn.close()


def delete_entry(user_id, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE user_id = %s AND date = %s", (user_id, date))
    conn.commit()
    cursor.close()
    conn.close()


def get_entries(user_id, start_date, end_date):
    conn = get_connection()
    query = """
        SELECT date, start_time, end_time, duration, comment, travel
        FROM entries
        WHERE user_id = %s AND date BETWEEN %s AND %s
        ORDER BY date
    """
    df = pd.read_sql(query, conn, params=(user_id, start_date, end_date))
    conn.close()
    return df


def get_entry_for_date(user_id, date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT start_time, end_time, duration, comment, travel
        FROM entries
        WHERE user_id = %s AND date = %s
    """, (user_id, date))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row
