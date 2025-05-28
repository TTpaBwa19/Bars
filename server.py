from flask import Flask, jsonify, request
import mysql.connector
from flask_cors import CORS
from functools import wraps
import time

app = Flask(__name__)
CORS(app)

# Конфигурация базы данных
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "barsiq",
    "pool_name": "barsiq_pool",
    "pool_size": 5
}

# Декоратор для обработки ошибок БД
def handle_db_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except mysql.connector.Error as err:
            print(f"Ошибка базы данных: {err}")
            return jsonify({"error": "Database error", "details": str(err)}), 500
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return jsonify({"error": "Internal server error"}), 500
    return wrapper

# Подключение к MySQL с пулом соединений
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к базе данных: {err}")
        raise

# Получение рейтинга
@app.route("/leaderboard")
@handle_db_errors
def leaderboard():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=100, type=int)
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT user_id, username, coins 
        FROM users 
        ORDER BY coins DESC 
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    rows = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total = cursor.fetchone()['total']
    
    conn.close()

    return jsonify({
        "data": rows,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    })

# Получение данных пользователя
@app.route("/get_user")
@handle_db_errors
def get_user():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT user_id, username, coins 
        FROM users 
        WHERE user_id = %s
    """, (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify(user)
    else:
        return jsonify({
            "user_id": user_id,
            "username": "Неизвестно",
            "coins": 0
        })

# Обновление данных пользователя
@app.route("/update_user", methods=["POST"])
@handle_db_errors
def update_user():
    data = request.get_json()
    user_id = data.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id обязателен"}), 400

    username = data.get("username")
    coins = data.get("coins")

    if username is None and coins is None:
        return jsonify({"error": "Необходимо указать username или coins"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if username and coins is not None:
        cursor.execute("""
            INSERT INTO users (user_id, username, coins, last_active)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                username = VALUES(username),
                coins = VALUES(coins),
                last_active = NOW()
        """, (user_id, username, coins))
    elif username:
        cursor.execute("""
            INSERT INTO users (user_id, username, last_active)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                username = VALUES(username),
                last_active = NOW()
        """, (user_id, username))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, coins, last_active)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                coins = VALUES(coins),
                last_active = NOW()
        """, (user_id, coins))

    conn.commit()
    
    # Получаем обновленные данные пользователя
    cursor.execute("SELECT username, coins FROM users WHERE user_id = %s", (user_id,))
    updated_data = cursor.fetchone()
    
    conn.close()

    return jsonify({
        "success": True,
        "user": {
            "user_id": user_id,
            "username": updated_data['username'] if updated_data else username,
            "coins": updated_data['coins'] if updated_data else coins
        }
    })

# Получение активных пользователей
@app.route("/active_users")
@handle_db_errors
def active_users():
    hours = request.args.get("hours", default=24, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT user_id, username, coins 
        FROM users 
        WHERE last_active >= NOW() - INTERVAL %s HOUR
        ORDER BY coins DESC
        LIMIT 100
    """, (hours,))
    
    users = cursor.fetchall()
    conn.close()
    
    return jsonify(users)

if __name__ == "__main__":
    # Создаем таблицу, если ее нет
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255),
                coins INT DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX (coins),
                INDEX (last_active)
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")

    app.run(host="0.0.0.0", port=5000, debug=True)




