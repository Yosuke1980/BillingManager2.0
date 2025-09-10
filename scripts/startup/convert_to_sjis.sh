#!/bin/bash
# 既存のバッチファイルをShift_JISに一括変換

echo "バッチファイルをShift_JISに変換中..."

for file in *.bat; do
    if [ -f "$file" ]; then
        # 現在のエンコーディングを確認
        current_encoding=$(file -bi "$file" | cut -d'=' -f2)
        echo "処理中: $file (現在: $current_encoding)"
        
        # バックアップを作成
        cp "$file" "$file.backup"
        
        # UTF-8からShift_JISに変換
        if iconv -f UTF-8 -t SHIFT_JIS "$file.backup" > "$file" 2>/dev/null; then
            echo "  → Shift_JISに変換完了"
            rm "$file.backup"
        else
            echo "  → 変換に失敗、元のファイルを復元"
            mv "$file.backup" "$file"
        fi
    fi
done

echo "変換完了"