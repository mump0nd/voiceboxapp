from flask import Flask, session, redirect, url_for, render_template, request
from flask_session import Session
import os
from flask_wtf.csrf import CSRFProtect
from file_management import file_management
from data_processing import data_processing
from keyword_management import keyword_management  # keyword_management の依存関係を追加


app = Flask(__name__)

# Flask-Sessionの設定
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your_secret_key'
Session(app)

# ブループリントを登録
app.register_blueprint(file_management)   # ファイル管理モジュールを登録
app.register_blueprint(data_processing)   # データ処理モジュールを登録
app.register_blueprint(keyword_management) # キーワード管理モジュールを登録


# アプリケーションに CSRF保護を設定
csrf = CSRFProtect(app)
app.config['WTF_CSRF_ENABLED'] = True

# ファイル保存フォルダの定義
UPLOAD_FOLDER = 'uploads'
FILTERED_FOLDER = 'filtered_emails'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FILTERED_FOLDER, exist_ok=True)

@app.before_request
def save_last_page():
    # 現在のリクエストがAPIや静的ファイルでない場合のみ処理
    if request.endpoint not in ['static']:
        session['last_page'] = session.get('current_page', '/')
        session['current_page'] = request.path
        print(f"Current Page: {session['current_page']}, Last Page: {session.get('last_page', '/')}")


@app.route('/')
def index():
    files = session.get('uploaded_files', {}).keys()
    total_records = sum(len(pd.read_csv(session['uploaded_files'][filename])) for filename in files)
    return render_template('index.html', files=files, total_records=total_records)


if __name__ == '__main__':
    app.run(debug=True)
