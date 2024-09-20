from flask import Blueprint, request, redirect, url_for, session, render_template, jsonify
import os
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ルートディレクトリにあるstop_words.txtのパス
STOP_WORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stop_words.txt')

keyword_management = Blueprint('keyword_management', __name__)

# キーワードを追加する共通関数
def add_keyword(keyword_list, keyword):
    if keyword and keyword not in keyword_list:
        keyword_list.append(keyword)
    return keyword_list

# キーワードを削除する共通関数
def delete_keyword(keyword_list, keyword):
    if keyword in keyword_list:
        keyword_list.remove(keyword)
    return keyword_list

# ポジティブ/ネガティブキーワードの追加
@keyword_management.route('/add_keyword', methods=['POST'])
def add_keyword_route():
    word = request.form['word']
    keyword_type = request.form['keyword_type']

    if keyword_type == 'positive':
        positive_keywords = load_keywords_from_file('positive_keywords.txt')
        positive_keywords = add_keyword(positive_keywords, word)
        save_keywords_to_file('positive_keywords.txt', positive_keywords)
    
    elif keyword_type == 'negative':
        negative_keywords = load_keywords_from_file('negative_keywords.txt')
        negative_keywords = add_keyword(negative_keywords, word)
        save_keywords_to_file('negative_keywords.txt', negative_keywords)
    
    return jsonify({'message': f'{word} が {keyword_type} キーワードに追加されました'}), 200

# ポジティブ/ネガティブキーワードの削除
@keyword_management.route('/delete_keyword', methods=['POST'])
def delete_keyword_route():
    word = request.form['word']
    keyword_type = request.form['keyword_type']
    
    if keyword_type == 'positive':
        positive_keywords = load_keywords_from_file('positive_keywords.txt')
        positive_keywords = delete_keyword(positive_keywords, word)
        save_keywords_to_file('positive_keywords.txt', positive_keywords)
    
    elif keyword_type == 'negative':
        negative_keywords = load_keywords_from_file('negative_keywords.txt')
        negative_keywords = delete_keyword(negative_keywords, word)
        save_keywords_to_file('negative_keywords.txt', negative_keywords)
    
    return redirect(url_for('keyword_management.manage_keywords'))

# ストップワードを読み込む関数
def load_stop_words():
    if os.path.exists(STOP_WORDS_FILE):
        with open(STOP_WORDS_FILE, 'r', encoding='utf-8') as f:
            stop_words = [line.strip() for line in f.readlines()]
    else:
        stop_words = []
    return stop_words

# ストップワードをファイルに書き込む関数
def save_stop_words(stop_words):
    with open(STOP_WORDS_FILE, 'w', encoding='utf-8') as f:
        for word in stop_words:
            f.write(f"{word}\n")

# ストップワードの追加
@keyword_management.route('/add_stop_word', methods=['POST'])
def add_stop_word():
    word = request.form['stop_word']
    stop_words = load_stop_words()
    if word and word not in stop_words:
        stop_words.append(word)
        save_stop_words(stop_words)
    return jsonify({'message': f'{word} がストップワードに追加されました'}), 200

# ストップワードの削除
@keyword_management.route('/delete_stop_word', methods=['POST'])
def delete_stop_word():
    word = request.form['stop_word']
    stop_words = load_stop_words()
    if word in stop_words:
        stop_words.remove(word)
        save_stop_words(stop_words)
    return redirect(url_for('keyword_management.manage_keywords'))

# Flaskルートハンドラでキーワードの管理ページを表示・処理
@keyword_management.route('/manage_keywords', methods=['POST', 'GET'])
def manage_keywords():
    if request.method == 'POST':
        if 'add_positive' in request.form:
            word = request.form['positive_word']
            positive_keywords = load_keywords_from_file('positive_keywords.txt')
            positive_keywords = add_keyword(positive_keywords, word)
            save_keywords_to_file(positive_keywords, 'positive_keywords.txt')
        
        elif 'add_negative' in request.form:
            word = request.form['negative_word']
            negative_keywords = load_keywords_from_file('negative_keywords.txt')
            negative_keywords = add_keyword(negative_keywords, word)
            save_keywords_to_file(negative_keywords, 'negative_keywords.txt')
        
        elif 'delete_positive' in request.form:
            word = request.form['delete_positive']
            positive_keywords = load_keywords_from_file('positive_keywords.txt')
            positive_keywords = delete_keyword(positive_keywords, word)
            save_keywords_to_file(positive_keywords, 'positive_keywords.txt')
        
        elif 'delete_negative' in request.form:
            word = request.form['delete_negative']
            negative_keywords = load_keywords_from_file('negative_keywords.txt')
            negative_keywords = delete_keyword(negative_keywords, word)
            save_keywords_to_file(negative_keywords, 'negative_keywords.txt')
        
        return redirect(url_for('keyword_management.manage_keywords'))

    # ファイルからポジティブ・ネガティブキーワードを読み込む
    positive_keywords = load_keywords_from_file('positive_keywords.txt')
    negative_keywords = load_keywords_from_file('negative_keywords.txt')
    stop_words = load_stop_words()

    return render_template('manage_keywords.html', positive_keywords=positive_keywords, negative_keywords=negative_keywords, stop_words=stop_words)

# キーワードをファイルに保存する関数
def save_keywords_to_file(filename, keywords):
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        for keyword in keywords:
            file.write(keyword + '\n')

# キーワードをファイルから読み込む関数
def load_keywords_from_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]
    
@keyword_management.route('/register_keyword', methods=['POST'])
def register_keyword():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    word = data.get('word')
    sentiment = data.get('sentiment')
    if not word or not sentiment:
        return jsonify({'error': 'Missing word or sentiment'}), 400

    # 追加処理（ポジティブ・ネガティブリストに保存）
    if sentiment == 'positive':
        save_keyword_to_list(word, 'positive_keywords.txt')
    elif sentiment == 'negative':
        save_keyword_to_list(word, 'negative_keywords.txt')
    elif sentiment == 'stop':
        stop_words = load_stop_words()
        if word not in stop_words:
            stop_words.append(word)
            save_stop_words(stop_words)

    return jsonify({'status': 'success', 'message': f'{word} が {sentiment} に追加されました'}), 200

# キーワードをファイルに保存する関数
def save_keyword_to_list(word, filename):
    # ファイルパスを適切に指定する
    file_path = os.path.join(os.getcwd(), filename)
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(word + '\n')
    except Exception as e:
        print(f"Error: {e}")


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
