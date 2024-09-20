from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from webdriver_manager.chrome import ChromeDriverManager


# Chromeドライバーのパスを指定
driver_path = '/path/to/chromedriver'  # あなたの環境に合わせてchromedriverのパスを指定
login_url = 'https://tayori.com/admin/signin/'
export_url = 'https://tayori.com/admin/form/80a2385b0efe6d3234a20c96b889de92ef373b1f/export/'

# ログイン情報
username = 'kazuo.sugiura@to-sho.net'  # 実際のメールアドレス
password = 'tosho8920'  # 実際のパスワード

# Chromeのオプションを設定
options = webdriver.ChromeOptions()

# 必要に応じて、オプションを追加
# options.add_argument('--headless')  # ヘッドレスモードで実行（UIなしで動作）

# ChromeDriverをセットアップして起動
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

try:
    # 1. ログインページにアクセス
    driver.get(login_url)

    # 2. メールアドレスとパスワードを入力してログイン
    email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
    password_input = wait.until(EC.presence_of_element_located((By.ID, "login-password")))
    
    email_input.send_keys(username)
    password_input.send_keys(password)
    
    # ログインボタンをクリック
    login_button = driver.find_element(By.CLASS_NAME, "btn-primary")
    login_button.click()
    
    # 3. エクスポートページに移動
    wait.until(EC.url_changes(login_url))
    driver.get(export_url)
    
    # 4. ドロップダウンメニューを操作して範囲を選択
    dropdown = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "el-select__placeholder")))
    dropdown.click()

    # ドロップダウンから"1件~500件"を選択（選択肢は範囲に応じて変更可能）
    range_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='1件~500件']")))
    range_option.click()

    # 5. エクスポートボタンをクリック
    export_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='エクスポート']")))
    export_button.click()

    # ダウンロード完了まで待つ（必要に応じて調整）
    time.sleep(10)

finally:
    driver.quit()
