#!/bin/bash
# バッチファイル作成用スクリプト（Shift_JIS自動変換）

if [ $# -eq 0 ]; then
    echo "使用法: $0 <バッチファイル名> [内容ファイル]"
    echo "例: $0 test.bat content.txt"
    exit 1
fi

BATCH_FILE="$1"
CONTENT_FILE="$2"

if [ -n "$CONTENT_FILE" ] && [ -f "$CONTENT_FILE" ]; then
    # 内容ファイルが指定されている場合
    iconv -f UTF-8 -t SHIFT_JIS "$CONTENT_FILE" > "$BATCH_FILE"
else
    # 標準入力から読み取り
    echo "バッチファイルの内容を入力してください（Ctrl+Dで終了）:"
    cat | iconv -f UTF-8 -t SHIFT_JIS > "$BATCH_FILE"
fi

echo "Shift_JISでバッチファイル '$BATCH_FILE' を作成しました"
file "$BATCH_FILE"