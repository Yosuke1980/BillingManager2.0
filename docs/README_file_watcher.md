# CSVファイル自動監視・アプリ起動機能

dataフォルダにCSVファイルが追加されたときに自動でアプリを起動する機能です。

## セットアップ

### 1. 必要なライブラリのインストール
```bash
pip install -r requirements.txt
```

### 2. 監視の開始
```bash
# macOS/Linux
./start_watcher.sh start

# Windows
start_watcher.bat start
```

## 使用方法

### 基本操作

#### macOS/Linux
```bash
./start_watcher.sh start    # 監視開始
./start_watcher.sh stop     # 監視停止
./start_watcher.sh status   # 状態確認
./start_watcher.sh restart  # 再起動
```

#### Windows
```cmd
start_watcher.bat start    # 監視開始
start_watcher.bat stop     # 監視停止
start_watcher.bat status   # 状態確認
start_watcher.bat restart  # 再起動
```

### 直接実行
```bash
python3 file_watcher.py           # 監視開始
python3 file_watcher.py --stop    # 監視停止
python3 file_watcher.py --status  # 状態確認
```

## 機能

- **ファイル監視**: dataフォルダ内のCSVファイルの追加・更新を監視
- **自動起動**: CSVファイルが検出されると自動でアプリを起動してインポート実行
- **重複防止**: 同じファイルの重複処理や複数アプリの起動を防止
- **ログ出力**: 監視状況やエラーをログファイルに記録
- **プロセス管理**: PIDファイルによる重複起動防止

## 動作の流れ

1. `file_watcher.py`がdataフォルダを監視開始
2. CSVファイルが追加または更新される
3. ファイルの書き込み完了を待機
4. アプリが起動中でないことを確認
5. `python3 app.py --import-csv [ファイルパス]`でアプリを起動
6. アプリが指定されたCSVファイルを自動インポート

## ログ

- 監視状況：`logs/app_YYYYMMDD.log`
- PIDファイル：`file_watcher.pid`

## 注意事項

- アプリが既に起動中の場合は新しいインスタンスの起動をスキップします
- CSVファイルは完全に書き込まれてから処理されます
- 同じファイルの5秒以内の重複検出は無視されます