#!/bin/bash

# ファイル監視トレイアプリ起動スクリプト (macOS/Linux用)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAY_SCRIPT="$SCRIPT_DIR/tray_monitor.py"
PYTHON_CMD="python3"
PID_FILE="$SCRIPT_DIR/tray_monitor.pid"

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
    $PYTHON_CMD -c "import PyQt5, watchdog, psutil" 2>/dev/null
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
    echo "  $0         - トレイアプリを起動"
    echo "  $0 start   - トレイアプリを起動"
    echo "  $0 stop    - トレイアプリを停止"
    echo "  $0 status  - 実行状態を確認"
}

# トレイアプリ起動
start_tray() {
    echo "BillingManager ファイル監視トレイアプリを起動します..."
    check_python
    check_dependencies
    
    # 既に起動中かチェック
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "トレイアプリは既に起動中です (PID: $PID)"
            return
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    # バックグラウンドで起動
    nohup $PYTHON_CMD "$TRAY_SCRIPT" > /dev/null 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    # 起動確認
    if ps -p $PID > /dev/null 2>&1; then
        echo "トレイアプリを起動しました (PID: $PID)"
        echo "システムトレイのアイコンを確認してください"
    else
        echo "トレイアプリの起動に失敗しました"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# トレイアプリ停止
stop_tray() {
    echo "トレイアプリを停止します..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 2
            
            # 強制終了が必要な場合
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
            
            echo "トレイアプリを停止しました"
        else
            echo "トレイアプリは既に停止中です"
        fi
        rm -f "$PID_FILE"
    else
        echo "トレイアプリは実行されていません"
    fi
}

# 実行状態確認
check_status() {
    echo "トレイアプリの実行状態を確認中..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "トレイアプリは実行中です (PID: $PID)"
            
            # プロセス情報を表示
            echo "プロセス情報:"
            ps -p $PID -o pid,ppid,time,comm
        else
            echo "トレイアプリは停止中です (PIDファイルが残存)"
            rm -f "$PID_FILE"
        fi
    else
        echo "トレイアプリは停止中です"
    fi
}

# メイン処理
case "${1:-start}" in
    start)
        start_tray
        ;;
    stop)
        stop_tray
        ;;
    status)
        check_status
        ;;
    restart)
        echo "トレイアプリを再起動します..."
        stop_tray
        sleep 3
        start_tray
        ;;
    *)
        show_usage
        exit 1
        ;;
esac