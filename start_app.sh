#!/bin/bash

# 既存のapp.pyプロセスを停止
echo "既存のapp.pyプロセスをチェック中..."
pkill -f "python3 app.py"
sleep 1

# プロセスが残っていないか確認
RUNNING=$(ps aux | grep "python3 app.py" | grep -v grep | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "警告: まだ $RUNNING 個のプロセスが実行中です"
    ps aux | grep "python3 app.py" | grep -v grep
else
    echo "✓ 既存プロセスはありません"
fi

# アプリを起動
echo "アプリを起動中..."
cd "$(dirname "$0")"
python3 app.py
