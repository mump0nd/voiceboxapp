import subprocess

# requirements.txtファイルを読み込み
with open('requirements.txt', 'r') as file:
    packages = file.readlines()

# パッケージを1つずつインストール
for package in packages:
    package = package.strip()
    if package:  # 空行を無視
        print(f"Installing {package}...")
        try:
            # subprocessでpipを使ってインストール
            subprocess.run(['pip', 'install', package], check=True)
            print(f"{package} installed successfully.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}.")
