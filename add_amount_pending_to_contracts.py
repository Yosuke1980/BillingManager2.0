#!/usr/bin/env python3
"""contractsテーブルにamount_pendingカラムを追加するマイグレーションスクリプト"""

import sqlite3
import sys

def main():
    db_path = 'order_management.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # カラムが既に存在するか確認
        cursor.execute("PRAGMA table_info(contracts)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'amount_pending' in columns:
            print("amount_pendingカラムは既に存在します。")
            return

        # amount_pendingカラムを追加
        print("contractsテーブルにamount_pendingカラムを追加しています...")
        cursor.execute("""
            ALTER TABLE contracts
            ADD COLUMN amount_pending INTEGER DEFAULT 0
        """)

        conn.commit()
        print("✓ amount_pendingカラムを追加しました。")

        # 確認
        cursor.execute("PRAGMA table_info(contracts)")
        columns = cursor.fetchall()
        print(f"\n確認: contractsテーブルには{len(columns)}個のカラムがあります。")

        # amount_pendingカラムを表示
        for col in columns:
            if col[1] == 'amount_pending':
                print(f"  - {col[1]} ({col[2]}, DEFAULT {col[4]})")

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
