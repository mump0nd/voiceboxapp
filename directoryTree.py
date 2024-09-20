/voiceboxapp
│
├── app.py                    # Flaskアプリケーションのメインファイル
├── stop_words.txt             # ストップワードが保存されているテキストファイル
├── negative_keywords.txt
├── positive_keywords.txt
└── static/
│   ├── css/
│   │   └── style.css          # サイト全体のデザインを管理するCSSファイル
│   ├── fonts/
│   │   └── NotoSansJP-Medium.ttf  # サイトで使用するフォント
│   └── wordclouds/            # 生成されたワードクラウド画像が保存されるフォルダ
│   └── js/            # 生成されたワードクラウド画像が保存されるフォルダ
│   │   └── custom.js          # 
└── templates/
    ├── index.html             # アップロードとファイル管理ページ
    ├── filter_commercial.html # コマーシャルメールを除外するページ
    ├── split_by_month.html    # ファイルを年月・店舗ごとに分割するページ
    ├── analysis.html          # 頻出単語解析ページ
    ├── store_analysis.html    # 店舗ごとの解析結果ページ
    ├── keyword_sentences.html # キーワードごとの文章表示ページ
    ├── word_sentences.html    # クリックした頻出単語の文章を表示するページ
    └── store_keyword_counts.html  # 店舗ごとのキーワード出現回数表示ページ
    └── manage_keywords.html  # 
└── filtered_emails/
└── uploads/
