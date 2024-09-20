from flask import Blueprint, session, redirect, url_for, render_template, request
import os
import pandas as pd
import re
from collections import Counter
from sudachipy import tokenizer, dictionary
import random
from wordcloud import WordCloud
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Blueprintの設定
data_processing = Blueprint('data_processing', __name__)

# SudachiPyのセットアップ
tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C

# 頻出ワード解析処理
def analyze_frequent_words(df, top_n=50):
    # 頻出ワードを集計する処理
    word_counts = df['内容'].str.split(expand=True).stack().value_counts()
    top_words = word_counts.head(top_n)
    return top_words

def extract_nouns_verbs_sudachi(text):
    words = []
    tokens = tokenizer_obj.tokenize(text, mode)
    for token in tokens:
        pos = token.part_of_speech()[0]
        if pos in ['名詞', '動詞']:
            words.append(token.surface())
    return words

def analyze_frequent_words(df, top_n=50):
    # 日本語形態素解析を使って頻出ワードを集計
    all_words = []
    for text in df['内容'].dropna():
        words = extract_nouns_verbs_sudachi(text)
        all_words.extend(words)
    
    # 単語の出現回数をカウント
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(top_n)
    return top_words

def load_non_commercial_emails():
    non_commercial_file_path = os.path.join('filtered_emails', 'non_commercial_emails.csv')
    if os.path.exists(non_commercial_file_path):
        return pd.read_csv(non_commercial_file_path, encoding='utf-8-sig')
    else:
        return None

# 名詞と動詞を抽出する関数
def extract_nouns_verbs_sudachi(text):
    words = []
    tokens = tokenizer_obj.tokenize(text, mode)
    for token in tokens:
        pos = token.part_of_speech()
        word = token.surface()
        # 名詞、動詞のみを抽出し、無効な単語を除外
        if pos[0] in ['名詞', '動詞'] and not is_invalid_word(word):
            words.append(word)
    return words

# 無効な単語を判定する関数
def is_invalid_word(word):
    if len(word) == 1 or word.isdigit():
        return True
    if re.search(r'[\u4E00-\u9FFF]', word) and re.search(r'[\u3040-\u309F]', word):
        return True
    if re.fullmatch(r'[\u3040-\u309F]+', word):
        return True
    return False

# ストップワードを読み込む関数
def load_stop_words():
    try:
        with open('stop_words.txt', 'r', encoding='utf-8') as f:
            stop_words = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        # ストップワードファイルがない場合、空のリストを返す
        stop_words = []
    return stop_words

# ストップワードをファイルに保存する関数
def save_stop_words(stop_words):
    with open('stop_words.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(stop_words))

# データ処理の中でストップワードを定義
stop_words = load_stop_words()

# URLとメールアドレスを削除する関数
def clean_text(text):
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    return text

# 子要素別にキーワードの出現回数を集計する関数
def aggregate_keywords_by_store(df, keywords):
    result = {}
    total_counts = {}
    stop_words = load_stop_words()

    for keyword in keywords:
        # キーワードが1回以上含まれるかを確認する（1回以上あれば1カウントとする）
        store_counts = df[df['内容'].str.contains(keyword, na=False)].groupby('子要素').size().sort_values(ascending=False)
        total_counts[keyword] = store_counts.sum()

        # 3回以上の店舗を抽出
        filtered_store_counts = store_counts[store_counts >= 10]

        # 3回未満の店舗の合計回数と店舗数
        below_3_count = store_counts[store_counts < 10].sum()
        below_3_stores = len(store_counts[store_counts < 10])

        result[keyword] = {
            'filtered_stores': filtered_store_counts,
            'below_3_count': below_3_count,
            'below_3_stores': below_3_stores
        }

    # キーワードを合計出現回数順にソート
    sorted_keywords = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_result = {k: result.get(k, None) for k, _ in sorted_keywords if result.get(k)}

    return sorted_result, total_counts

# キーワードを含む文章を抽出し、店舗別にソートする関数
def extract_sentences_by_store(df, keyword):
    # 各店舗でキーワードを含む文章のリストを作成
    sentences_by_store = df[df['内容'].str.contains(keyword)].groupby('子要素').apply(
        lambda x: x[['内容', '性別', '受付日時']].to_dict(orient='records')
    )
    
    # 5回以上出現した店舗のみフィルタリング
    sentences_by_store = sentences_by_store[sentences_by_store.apply(len) >= 5]

    # リストの長さでソート
    sentences_by_store = sentences_by_store.sort_values(ascending=False, key=lambda x: x.apply(len))

    return sentences_by_store

# 店舗ごとのファイルから頻出単語を集計する関数
def analyze_frequent_words_by_store(file_path):
    # データの読み込み
    df = pd.read_csv(file_path, encoding='utf-8-sig')

    # 内容カラムからテキストを取得してクリーンアップ
    texts = df['内容'].dropna().apply(clean_text)

    # 名詞と動詞の抽出
    words = []
    for text in texts:
        words.extend(extract_nouns_verbs_sudachi(text))

    # 頻出単語をカウント
    word_counts = Counter(words)

    # 上位50件の頻出単語を返す
    return word_counts.most_common(50)

# 店舗ごとのファイルを一括処理する関数
def process_store_files(store_folder):
    store_word_counts = {}
    
    # 店舗ごとのファイルを処理
    for file_name in os.listdir(store_folder):
        if file_name.endswith('.csv'):
            # ファイル名から 'non_commercial_emails_' を削除し、拡張子を除いた店舗名を取得
            store_name = os.path.splitext(file_name)[0].replace('non_commercial_emails_', '')

            file_path = os.path.join(store_folder, file_name)
            
            # CSVファイルを読み込む
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # 各店舗ごとの文章から単語を抽出
            texts = df['内容'].dropna().apply(clean_text)
            words = []
            for text in texts:
                extracted_words = extract_nouns_verbs_sudachi(text)
                words.extend(extracted_words)

            # 単語の出現回数を集計
            word_counts = Counter(words).most_common(50)  # 上位50単語を取得
            store_word_counts[store_name] = word_counts

    return store_word_counts

# コマーシャルメールのフィルタリングと保存処理
def filter_commercial_emails(df):
    # コマーシャルに該当するパターン（株式会社、有限会社、貴社、弊社）
    patterns = [
        (r'(?:株式会社)', '株式会社'),
        (r'(?:有限会社)', '有限会社'),
        (r'(?:弊社)', '弊社'),
        (r'(?:製造)', '製造'),
        (r'(?:販売)', '販売')

    ]
    
    commercial_emails = []  # コマーシャルメールのリスト（全列を保持）
    highlighted_emails = []  # ハイライトされたメール（表示用）
    non_commercial_emails = df.copy()

    # 各パターンごとにフィルタリング処理
    for pattern, keyword in patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = df[df['内容'].str.contains(regex, na=False)]
        
        for _, row in matches.iterrows():
            # commercial_emails に元の行全体を追加（全列を保持）
            commercial_emails.append(row.to_dict())
            
            # ハイライトされたメールを保存
            highlighted_email = re.sub(pattern, f'<span class="keyword">{keyword}</span>', row['内容'], flags=re.IGNORECASE)
            highlighted_emails.append({
                '内容': highlighted_email,
                '受付日時': row['受付日時']
            })

        # コマーシャルに該当する行を non_commercial_emails から削除
        non_commercial_emails = non_commercial_emails[~non_commercial_emails['内容'].str.contains(regex, na=False)]

    # コマーシャルメールのリストを DataFrame に変換し、ファイルに保存
    commercial_emails_df = pd.DataFrame(commercial_emails)
    commercial_emails_df.to_csv('filtered_emails/commercial_emails.csv', encoding='utf-8-sig', index=False)

    return highlighted_emails, non_commercial_emails

# コマーシャルメール除外処理のエンドポイント
@data_processing.route('/filter_commercial', methods=['GET'])
def filter_commercial():
    sorted_data_file_path = 'uploads/sorted_data.csv'
    
    if not os.path.exists(sorted_data_file_path):
        return "Error: No data to filter", 400

    df = pd.read_csv(sorted_data_file_path, encoding='utf-8-sig')

    highlighted_emails, non_commercial_emails = filter_commercial_emails(df)

    # commercial_emails と non_commercial_emails をファイルに保存
    output_folder = 'filtered_emails'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    commercial_file_path = os.path.join(output_folder, 'commercial_emails.csv')
    non_commercial_file_path = os.path.join(output_folder, 'non_commercial_emails.csv')

    # 保存処理
    non_commercial_emails.to_csv(non_commercial_file_path, encoding='utf-8-sig', index=False)

    total_records = len(df)
    commercial_count = len(highlighted_emails)

    # ハイライトされたメールとキーワードをテンプレートに渡す
    return render_template('filter_commercial.html', commercial_count=commercial_count, highlighted_emails=highlighted_emails)

# データをソートする処理
@data_processing.route('/sort_data', methods=['POST'])
def sort_data():
    sorted_data_file_path = 'filtered_emails/sorted_data.csv'
    
    # データフレームに変換
    if not os.path.exists(sorted_data_file_path):
        return "No data to sort", 400
    
    df = pd.read_csv(sorted_data_file_path, encoding='utf-8-sig')

    # 日付でデータをソート
    df['受付日時'] = pd.to_datetime(df['受付日時'], errors='coerce')
    df_sorted = df.sort_values(by='受付日時', ascending=False)

    # ソートされたデータをファイルに保存
    df_sorted.to_csv(sorted_data_file_path, encoding='utf-8-sig', index=False)

    return redirect(url_for('result_display.show_results'))

@data_processing.route('/split_by_month', methods=['GET'])
def split_by_month():
    # ファイルの保存先フォルダ
    output_folder = 'filtered_emails'

    # non_commercial_emails.csv からデータを読み込む
    non_commercial_file_path = os.path.join(output_folder, 'non_commercial_emails.csv')
    
    # ファイルが存在するか確認
    if not os.path.exists(non_commercial_file_path):
        return "Error: non_commercial_emails.csv が存在しません", 400
    
    df = pd.read_csv(non_commercial_file_path, encoding='utf-8-sig')
    
    # 年月でデータを分割
    df['受付日時'] = pd.to_datetime(df['受付日時'], errors='coerce')
    df = df.dropna(subset=['受付日時'])  # 受付日時が無い行は削除
    df['year_month'] = df['受付日時'].dt.strftime('%Y年%m月')

    # 年月ごとの件数を集計
    year_month_counts = df['year_month'].value_counts().sort_index(ascending=False)

    # 年月ごとにデータをファイルに保存
    for year_month in df['year_month'].unique():
        month_df = df[df['year_month'] == year_month]
        file_name = f'non_commercial_emails_{year_month}.csv'
        month_file_path = os.path.join(output_folder, file_name)
        month_df.to_csv(month_file_path, encoding='utf-8-sig', index=False)

    # 店舗ごとにデータを分割
    store_counts = df['子要素'].value_counts().sort_values(ascending=False)

    for store in df['子要素'].unique():
        store_df = df[df['子要素'] == store]
        file_name = f'non_commercial_emails_{store}.csv'
        store_file_path = os.path.join(output_folder, file_name)
        store_df.to_csv(store_file_path, encoding='utf-8-sig', index=False)

    # 年月ごとのデータをテンプレートに渡す
    total_records = len(df)
    commercial_count = session.get('commercial_count', 0)
    target_records = total_records - commercial_count

    return render_template('split_by_month.html', year_month_counts=year_month_counts, store_counts=store_counts, total_records=total_records, commercial_count=commercial_count, target_records=target_records)


@data_processing.route('/proceed_analysis', methods=['POST'])
def proceed_analysis():
    return redirect(url_for('data_processing.analysis'))

# 解析結果ページのエンドポイント
@data_processing.route('/analysis', methods=['GET', 'POST'])
def analysis():
    # ファイルの保存先ディレクトリ
    output_folder = 'filtered_emails'
    non_commercial_file_path = os.path.join(output_folder, 'non_commercial_emails.csv')

    # ファイルが存在するかを確認
    if not os.path.exists(non_commercial_file_path):
        return "Error: non_commercial_emails.csv が存在しません", 400

    # non_commercial_emails.csv からデータを読み込む
    df = pd.read_csv(non_commercial_file_path, encoding='utf-8-sig')

    # POSTリクエスト時の処理
    if request.method == 'POST':
        # ストップワード追加処理
        if 'add_stop_word' in request.form:
            new_stop_word = request.form['add_stop_word']
            stop_words = load_stop_words()
            if new_stop_word not in stop_words:
                stop_words.append(new_stop_word)
                save_stop_words(stop_words)
            return redirect(url_for('data_processing.store_keyword_counts'))

        # ストップワード削除処理
        if 'remove_stop_word' in request.form:
            stop_word_to_remove = request.form['remove_stop_word']
            stop_words = load_stop_words()
            if stop_word_to_remove in stop_words:
                stop_words.remove(stop_word_to_remove)
                save_stop_words(stop_words)
            return redirect(url_for('data_processing.store_keyword_counts'))

        # 選択した単語を次のページに進む
        if 'selected_words' in request.form:
            selected_words = request.form.getlist('selected_words')
            session['selected_words'] = selected_words  # セッションに保存         

            # キーワードごとに店舗別の出現回数を集計
            store_keyword_counts, total_counts = aggregate_keywords_by_store(df, selected_words)

            return render_template('store_keyword_counts.html', store_keyword_counts=store_keyword_counts, total_counts=total_counts, selected_words=selected_words)

    # GETリクエスト時の処理
    texts = df['内容'].dropna().apply(clean_text)

    # 名詞と動詞を抽出し、無効な単語を除外
    words = []
    for text in df['内容'].dropna():
        # extract_nouns_verbs_sudachi 関数を使って名詞と動詞を抽出
        extracted_words = extract_nouns_verbs_sudachi(text)
        # 無効な単語を除外しつつ、重複を削除
        filtered_words = list(set([word for word in extracted_words if not is_invalid_word(word)]))
        words.extend(filtered_words)

    # ストップワードを読み込む
    stop_words = load_stop_words()

    # ストップワードを除外して頻出単語をカウント
    filtered_words = [word for word in words if word not in stop_words]
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(50)

    # 店舗ごとの件数を集計
    store_counts = df['子要素'].value_counts().to_dict()  # 店舗（子要素）ごとの件数を取得

    # GETリクエストの場合、分析画面をレンダリング
    return render_template('analysis.html', top_words=top_words, stop_words=stop_words, store_counts=store_counts)

@data_processing.route('/store_keyword_counts', methods=['GET', 'POST'])
def store_keyword_counts():
    sorted_data_file_path = 'filtered_emails/sorted_data.csv'

    if request.method == 'POST':
        selected_words = request.form.getlist('selected_words')

        if not os.path.exists(sorted_data_file_path):
            return redirect(url_for('data_processing.analysis'))

        df = pd.read_csv(sorted_data_file_path, encoding='utf-8-sig')

        store_keyword_counts, total_counts = aggregate_keywords_by_store(df, selected_words)

        # 分析結果をファイルに保存
        pd.DataFrame(store_keyword_counts).to_csv('filtered_emails/store_keyword_counts.csv', encoding='utf-8-sig', index=False)
        pd.DataFrame(total_counts).to_csv('filtered_emails/total_counts.csv', encoding='utf-8-sig', index=False)

    else:
        # ファイルから保存されたデータを取得
        store_keyword_counts = pd.read_csv('filtered_emails/store_keyword_counts.csv', encoding='utf-8-sig').to_dict()
        total_counts = pd.read_csv('filtered_emails/total_counts.csv', encoding='utf-8-sig').to_dict()
        selected_words = request.form.getlist('selected_words', [])

    return render_template('store_keyword_counts.html', store_keyword_counts=store_keyword_counts, total_counts=total_counts, selected_words=selected_words)

@data_processing.route('/keyword_sentences/<keyword>')
def keyword_sentences(keyword):
    # 正しいファイルパスを指定
    file_path = os.path.join('filtered_emails', 'non_commercial_emails.csv')
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        return "Error: non_commercial_emails.csv が存在しません", 400
    
    # ファイルを読み込む
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # キーワードに基づく文章の処理
    sentences_by_store = extract_sentences_by_store(df, keyword)

    return render_template('keyword_sentences.html', keyword=keyword, sentences_by_store=sentences_by_store)

@data_processing.route('/store_analysis_page/<store_name>')
def store_analysis_page(store_name):
    # 店舗ごとのファイルパスを生成
    store_folder = 'filtered_emails'
    file_name = f'non_commercial_emails_{store_name}.csv'
    file_path = os.path.join(store_folder, file_name)

    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        return f"Error: {store_name} のデータが見つかりません", 404

    # 店舗ごとのCSVファイルを読み込む
    df = pd.read_csv(file_path, encoding='utf-8-sig')

    # ストップワードを読み込む
    stop_words = load_stop_words()

    # 単語の抽出と集計（ストップワードを除外）
    texts = df['内容'].dropna().apply(clean_text)
    words = []
    for text in texts:
        # 各文章ごとに単語を抽出し、setで重複を除去
        extracted_words = set(extract_nouns_verbs_sudachi(text))
        # ストップワードを除外
        filtered_words = [word for word in extracted_words if word not in stop_words]
        words.extend(filtered_words)

    # 頻出単語の集計
    word_counts = Counter(words).most_common(50)
    
    # ワードクラウドを作成
    wordcloud_text = " ".join(words)
    font_path = 'static/fonts/NotoSansJP-Medium.ttf'
    
    # カラーマップをランダムに選択
    random_colormap = random.choice(colormap_list)
    
    # ワードクラウドを正方形にして、カラフルな表示
    wordcloud = WordCloud(
        width=800, height=800, background_color='white',
        font_path=font_path, colormap=random_colormap
    ).generate(wordcloud_text)

    # ワードクラウドの画像を保存
    wordcloud_folder = 'static/wordclouds'
    if not os.path.exists(wordcloud_folder):
        os.makedirs(wordcloud_folder)

    wordcloud_image_path = os.path.join(wordcloud_folder, f'{store_name}_wordcloud.png')
    wordcloud.to_file(wordcloud_image_path)

    # 画像の相対パスをテンプレートに渡す
    wordcloud_image_url = url_for('static', filename=f'wordclouds/{store_name}_wordcloud.png')

    return render_template('store_analysis.html', store_name=store_name, word_counts=word_counts, wordcloud_image_url=wordcloud_image_url)

# 利用可能なカラーマップのリスト
colormap_list = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'rainbow', 'Blues',
    'Greens', 'Reds', 'spring', 'summer', 'autumn', 'winter'
]

@data_processing.route('/store_analysis', methods=['GET', 'POST'])
def store_analysis():
    # 店舗ごとの頻出単語を抽出
    store_folder = 'filtered_emails'
    store_word_counts = process_store_files(store_folder)

    # 分析結果を保存するためのディレクトリ
    output_path = 'analysis_results'
    os.makedirs(output_path, exist_ok=True)

    # POSTリクエストなら結果をファイルに保存
    if request.method == 'POST':
        for store, word_counts in store_word_counts.items():
            output_file = os.path.join(output_path, f'{store}_frequent_words.csv')
            pd.DataFrame(word_counts, columns=['単語', '回数']).to_csv(output_file, index=False)
        return "分析結果を保存しました。"

    # GETリクエストなら結果を表示する
    return render_template('store_analysis.html', store_word_counts=store_word_counts)

@data_processing.route('/store_analysis_save', methods=['POST'])
def store_analysis_save():
    # 店舗ごとの頻出単語を抽出
    store_folder = 'filtered_emails'
    store_word_counts = process_store_files(store_folder)
    
    # 結果をファイルに保存する
    output_path = 'analysis_results'
    os.makedirs(output_path, exist_ok=True)
    
    for store, word_counts in store_word_counts.items():
        output_file = os.path.join(output_path, f'{store}_frequent_words.csv')
        pd.DataFrame(word_counts, columns=['単語', '回数']).to_csv(output_file, index=False)
    
    return "分析結果を保存しました。"

@data_processing.route('/store_analysis/<store_name>/<word>', methods=['GET'])
def word_sentences(store_name, word):
    # 店舗ごとのファイルを読み込む
    store_file = f'filtered_emails/non_commercial_emails_{store_name}.csv'
    df = pd.read_csv(store_file, encoding='utf-8-sig')

    # 指定された単語が含まれる文章を抽出し、性別と受付日時も含める
    matching_sentences = df[df['内容'].str.contains(word, na=False)][['内容', '性別', '受付日時']]

    # 単語をCSSクラスでハイライトし、感情分析を追加
    analyzed_sentences = []
    for _, row in matching_sentences.iterrows():
        highlighted_text = row['内容'].replace(word, f'<span class="keyword">{word}</span>')
        sentiment = analyze_sentiment(row['内容'])
        analyzed_sentences.append({
            '内容': highlighted_text,
            '性別': row['性別'],
            '受付日時': row['受付日時'],
            '感情': sentiment  # 感情分析結果を追加
        })

    # テンプレートに感情分析結果を渡す
    return render_template(
        'word_sentences.html',
        store_name=store_name,
        word=word,
        sentences=analyzed_sentences  # 感情分析結果を含む
    )

def analyze_sentiment(text):
    # TextBlobで感情を分析
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    # VADERで感情を分析
    analyzer = SentimentIntensityAnalyzer()
    vader_result = analyzer.polarity_scores(text)

    # 重み付け: VADERをさらに強調
    combined_score = 0.1 * polarity + 0.9 * vader_result['compound']

    # しきい値のさらなる調整
    if combined_score > 0.05:
        return "ポジティブ"
    elif combined_score < -0.05:
        return "ネガティブ"
    else:
        return "ニュートラル"


