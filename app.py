from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# 確保 SQLite 數據庫存在
DB_NAME = 'users.db'
if not os.path.exists(DB_NAME):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
        conn.execute('CREATE TABLE apis (id INTEGER PRIMARY KEY, user_id INTEGER, api_name TEXT, api_code TEXT, FOREIGN KEY(user_id) REFERENCES users(id))')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    with sqlite3.connect(DB_NAME) as conn:
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            return jsonify({'message': '註冊成功！'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'message': '用戶名已存在！'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    with sqlite3.connect(DB_NAME) as conn:
        user = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password)).fetchone()
        if user:
            return jsonify({'message': '登入成功！'}), 200
        else:
            return jsonify({'message': '用戶名或密碼錯誤！'}), 401

@app.route('/api/generate', methods=['POST'])
def generate_api():
    data = request.get_json()
    username = data['username']
    api_name = data['name']
    
    with sqlite3.connect(DB_NAME) as conn:
        user = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
        if user:
            api_code = f"https://login-system-api-zzmx.onrender.com/api/{username}/{user[0]}"
            conn.execute('INSERT INTO apis (user_id, api_name, api_code) VALUES (?, ?, ?)', (user[0], api_name, api_code))
            return jsonify({'message': 'API 生成成功！', 'code': api_code}), 201
        return jsonify({'message': '用戶未找到！'}), 404

@app.route('/api/user/apis', methods=['GET'])
def user_apis():
    username = request.args.get('username')
    with sqlite3.connect(DB_NAME) as conn:
        user = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
        if user:
            apis = conn.execute('SELECT id, api_name FROM apis WHERE user_id=?', (user[0],)).fetchall()
            return jsonify(apis), 200
        return jsonify({'message': '用戶未找到！'}), 404

@app.route('/api/user/apis/<int:api_id>', methods=['DELETE'])
def delete_api(api_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM apis WHERE id=?', (api_id,))
        return jsonify({'message': 'API 刪除成功！'}), 200

# 新增路由以處理用戶的 API 請求
@app.route('/api/<username>/<int:api_id>', methods=['GET'])
def call_api(username, api_id):
    # 這裡可以添加相應的邏輯來處理 API 請求
    return jsonify({'message': f'這是用戶 {username} 的 API {api_id} 的回應！'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
