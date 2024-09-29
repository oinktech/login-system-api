from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import hashlib
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # 允許跨來源請求
app.secret_key = 'your_secret_key'  # 用於 session 的密鑰

# 創建數據庫
def init_db(username):
    conn = sqlite3.connect(f'{username}.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apis (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 註冊
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if os.path.exists(f'{username}.db'):
        return jsonify({'message': '用戶名已存在'}), 400
    
    # 密碼雜湊
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with open('users.txt', 'a') as f:
        f.write(f"{username},{hashed_password}\n")
    
    init_db(username)  # 為用戶創建數據庫
    return jsonify({'message': '註冊成功'}), 201

# 登入
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    with open('users.txt', 'r') as f:
        users = f.readlines()
    
    for user in users:
        user_info = user.strip().split(',')
        if user_info[0] == username and user_info[1] == hashed_password:
            session['username'] = username
            return jsonify({'message': '登入成功'}), 200
    
    return jsonify({'message': '用戶名或密碼錯誤'}), 401

# 登出
@app.route('/api/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# 主頁
@app.route('/')
def index():
    return render_template('index.html')

# API 生成
@app.route('/api/generate', methods=['POST'])
def generate_api():
    if 'username' not in session:
        return jsonify({'message': '未登入'}), 401

    data = request.json
    api_name = data.get('name')
    api_code = f"""
    <script>
        async function callApi() {{
            const response = await fetch('http://127.0.0.1:5000/api/{api_name}');
            const data = await response.json();
            console.log(data);
        }}
    </script>
    callApi();
    """
    
    # 儲存到數據庫
    conn = sqlite3.connect(f'{session["username"]}.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO apis (name, code) VALUES (?, ?)', (api_name, api_code))
    conn.commit()
    conn.close()

    return jsonify({'message': 'API 生成成功', 'code': api_code}), 201

# 獲取用戶生成的 API
@app.route('/api/user/apis', methods=['GET'])
def user_apis():
    if 'username' not in session:
        return jsonify({'message': '未登入'}), 401

    conn = sqlite3.connect(f'{session["username"]}.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM apis')
    apis = cursor.fetchall()
    conn.close()
    
    return jsonify(apis), 200

# 刪除 API
@app.route('/api/user/apis/<int:api_id>', methods=['DELETE'])
def delete_api(api_id):
    if 'username' not in session:
        return jsonify({'message': '未登入'}), 401

    conn = sqlite3.connect(f'{session["username"]}.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM apis WHERE id = ?', (api_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'API 已刪除'}), 200

# 更新 API
@app.route('/api/user/apis/<int:api_id>', methods=['PUT'])
def update_api(api_id):
    if 'username' not in session:
        return jsonify({'message': '未登入'}), 401

    data = request.json
    api_name = data.get('name')

    conn = sqlite3.connect(f'{session["username"]}.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE apis SET name = ? WHERE id = ?', (api_name, api_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'API 已更新'}), 200

# 渲染示例頁面
@app.route('/example')
def example():
    return render_template('example.html')

if __name__ == '__main__':
    app.run(debug=True)
