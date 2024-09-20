from flask import Blueprint, request, redirect, url_for, session, render_template
import os
import pandas as pd
import chardet

# Blueprintの設定
file_management = Blueprint('file_management', __name__)

# アップロードするファイルの保存先
UPLOAD_FOLDER = 'uploads'

# インデックスページ: ファイル一覧と総レコード数の表示
@file_management.route('/')
def index():
    files = session.get('uploaded_files', {}).keys()  # セッションからファイルリストを取得
    total_records = 0
    if 'uploaded_files' in session:
        dataframes = [pd.read_csv(session['uploaded_files'][filename], encoding='cp932') for filename in session['uploaded_files']]
        total_records = sum([len(df) for df in dataframes])
    return render_template('index.html', files=files, total_records=total_records)

# ファイルアップロード処理
@file_management.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if files:
        all_data = pd.DataFrame()
        if 'uploaded_files' not in session:
            session['uploaded_files'] = {}

        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            # アップロードファイルをセッションに保存
            session['uploaded_files'][file.filename] = file_path

            # エンコーディングを試行
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='cp932')  # 'cp932' エンコーディングに切り替え

            all_data = pd.concat([all_data, df], ignore_index=True)

        all_data['受付日時'] = pd.to_datetime(all_data['受付日時'], errors='coerce')
        sorted_data = all_data.sort_values(by='受付日時', ascending=False)
        sorted_data.to_csv(os.path.join(UPLOAD_FOLDER, 'sorted_combined_data.csv'), encoding='utf-8-sig', index=False)
        session['sorted_data'] = sorted_data.to_dict(orient='records')
    return redirect(url_for('file_management.index'))

# アップロードファイル削除処理
@file_management.route('/remove_file', methods=['POST'])
def remove_file():
    filename = request.form['filename']
    if 'uploaded_files' in session and filename in session['uploaded_files']:
        # ファイルパスを取得
        file_path = session['uploaded_files'][filename]

        # セッションからファイル情報を削除
        del session['uploaded_files'][filename]

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
    if filename in session['uploaded_files']:
        file_path = session['uploaded_files'][filename]
        if os.path.exists(file_path):
            os.remove(file_path)
        del session['uploaded_files'][filename]
    return redirect(url_for('file_management.index'))
