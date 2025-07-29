#!/bin/bash

# CSVファイル監視スクリプトの起動/停止用スクリプト (macOS/Linux用)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHER_SCRIPT="$SCRIPT_DIR/file_watcher.py"
PYTHON_CMD="python3"

# Pythonの存在確認
check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "エラー: Python3がインストールされていません"
        exit 1
    fi
}

# 依存関係の確認
check_dependencies() {
    echo "依存関係を確認中..."
    $PYTHON_CMD -c "import watchdog, psutil" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "必要なライブラリがインストールされていません"
        echo "以下のコマンドでインストールしてください:"
        echo "pip3 install -r requirements.txt"
        exit 1
    fi
    echo "依存関係OK"
}

# 使用方法を表示
show_usage() {
    echo "使用方法:"
    echo "  $0 start   - ファイル監視を開始"
    echo "  $0 stop    - ファイル監視を停止"
    echo "  $0 status  - ファイル監視の状態を確認"
    echo "  $0 restart - ファイル監視を再起動"
}

# 監視開始
start_watcher() {
    echo "CSVファイル監視を開始します..."
    check_python
    check_dependencies
    
    # バックグラウンドで実行
    nohup $PYTHON_CMD "$WATCHER_SCRIPT" > /dev/null 2>&1 &
    
    sleep 2
    
    # 起動確認
    $PYTHON_CMD "$WATCHER_SCRIPT" --status
}

# 監視停止
stop_watcher() {
    echo "CSVファイル監視を停止します..."
    check_python
    $PYTHON_CMD "$WATCHER_SCRIPT" --stop
}

# 監視状態確認
check_status() {
    check_python
    $PYTHON_CMD "$WATCHER_SCRIPT" --status
}

# 監視再起動
restart_watcher() {
    echo "CSVファイル監視を再起動します..."
    stop_watcher
    sleep 3
    start_watcher
}

# メイン処理
case "$1" in
    start)
        start_watcher
        ;;
    stop)
        stop_watcher
        ;;
    status)
        check_status
        ;;
    restart)
        restart_watcher
        ;;
    *)
        show_usage
        exit 1
        ;;
esac