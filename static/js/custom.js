document.addEventListener('mouseup', function(event) {
    const selectedText = window.getSelection().toString().trim();
    if (selectedText) {
        console.log('選択されたテキスト:', selectedText); // デバッグ用ログ
        const existingPopup = document.querySelector('.popup');
        if (!existingPopup) {
            showPopup(selectedText, event.clientX, event.clientY);
        }
    }
});

function showPopup(word, x, y) {
    closePopup();  // 既存のポップアップがあれば閉じる

    const popup = document.createElement('div');
    popup.className = 'popup';
    popup.innerHTML = `
        <p>選択された単語: ${word}</p>
        <button data-word="${word}" data-sentiment="positive" class="register-button">ポジティブに追加</button>
        <button data-word="${word}" data-sentiment="negative" class="register-button">ネガティブに追加</button>
        <button data-word="${word}" data-sentiment="stop" class="register-button">ストップワードに追加</button>
        <button onclick="closePopup()">閉じる</button>
    `;
    document.body.appendChild(popup);

    console.log('ポップアップ表示'); // ポップアップが表示されたか確認

    // ポップアップの位置を調整
    popup.style.position = 'fixed';
    popup.style.left = `${Math.min(x, window.innerWidth - popup.offsetWidth)}px`;
    popup.style.top = `${Math.min(y, window.innerHeight - popup.offsetHeight)}px`;
}

function closePopup() {
    const popup = document.querySelector('.popup');
    if (popup) {
        popup.remove();
    }
}

// キーワード登録時の処理
document.addEventListener('click', function(event) {
    if (event && event.target && event.target.classList.contains('register-button')) {
        event.stopPropagation();  // イベントの伝播を止める
        const word = event.target.getAttribute('data-word');
        const sentiment = event.target.getAttribute('data-sentiment');
        registerWord(word, sentiment);
    }
});

function registerWord(word, sentiment) {
    console.log(`登録ボタンがクリックされました。単語: ${word}, 感情: ${sentiment}`);  // デバッグ用

    fetch('/register_keyword', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()  // CSRFトークンを送信
        },
        body: JSON.stringify({ word: word, sentiment: sentiment })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('ネットワークの応答が正しくありません');
        }
        return response.json();
    })
    .then(data => {
        alert(`${word} が ${sentiment} に追加されました`);
        closePopup();  // ポップアップを閉じる
    })
    .catch(error => {
        console.error('エラーが発生しました:', error);
    });
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
