from flask import Blueprint, request, redirect, url_for, render_template
import os
import pandas as pd

# Blueprintの設定
file_management = Blueprint('file_management', __name__)

# アップロードするファイルの保存先
UPLOAD_FOLDER = 'uploads'

# アップロードフォルダが存在しない場合、作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# インデックスページ: ファイル一覧と総レコード数の表示
@file_management.route('/')
def index():
    # セッションではなく、アップロードフォルダからファイルを取得
    files = os.listdir(UPLOAD_FOLDER)
    total_records = 0
    all_data = pd.DataFrame()

    # アップロードされたCSVファイルごとのレコード数をカウント
    for filename in files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp932')
        all_data = pd.concat([all_data, df], ignore_index=True)

    total_records = len(all_data)
    
    return render_template('index.html', files=files, total_records=total_records)

# ファイルアップロード処理
@file_management.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if files:
        all_data = pd.DataFrame()

        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # エンコーディングを試行
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='cp932')  # 'cp932' エンコーディングに切り替え

            all_data = pd.concat([all_data, df], ignore_index=True)

        all_data['受付日時'] = pd.to_datetime(all_data['受付日時'], errors='coerce')
        sorted_data = all_data.sort_values(by='受付日時', ascending=False)
        sorted_data.to_csv(os.path.join(UPLOAD_FOLDER, 'sorted_combined_data.csv'), encoding='utf-8-sig', index=False)
        
    return redirect(url_for('file_management.index'))

# アップロードファイル削除処理
@file_management.route('/remove_file', methods=['POST'])
def remove_file():
    filename = request.form['filename']
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # 実際のファイルを削除
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"{file_path} を削除しました。")  # デバッグ用ログ
        except Exception as e:
            print(f"ファイルの削除に失敗しました: {e}")

    return redirect(url_for('file_management.index'))

# サーバー上のファイル削除処理
@file_management.route('/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('file_management.index'))
