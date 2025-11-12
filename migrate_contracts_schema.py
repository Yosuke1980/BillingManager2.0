#!/usr/bin/env python3
"""
contractsテーブルに不足しているカラムを追加するマイグレーションスクリプト
"""
import sqlite3
import os

def migrate_contracts_table():
    """contractsテーブルに不足しているカラムを追加"""
    db_path = 'order_management.db'

    if not os.path.exists(db_path):
        print(f"エラー: {db_path} が見つかりません")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 現在のカラムを取得
        cursor.execute("PRAGMA table_info(contracts)")
        columns = {row[1] for row in cursor.fetchall()}

        print("現在のcontractsテーブルのカラム:")
        print(f"  - 合計 {len(columns)} カラム")

        added_columns = []

        # pdf_status カラムを追加
        if 'pdf_status' not in columns:
            print("\n追加: pdf_status カラム")
            cursor.execute("ALTER TABLE contracts ADD COLUMN pdf_status TEXT DEFAULT '未配布'")
            added_columns.append('pdf_status')
        else:
            print("\nスキップ: pdf_status カラムは既に存在します")

        # pdf_distributed_date カラムを追加
        if 'pdf_distributed_date' not in columns:
            print("追加: pdf_distributed_date カラム")
            cursor.execute("ALTER TABLE contracts ADD COLUMN pdf_distributed_date DATE")
            added_columns.append('pdf_distributed_date')
        else:
            print("スキップ: pdf_distributed_date カラムは既に存在します")

        # implementation_date カラムを追加
        if 'implementation_date' not in columns:
            print("追加: implementation_date カラム")
            cursor.execute("ALTER TABLE contracts ADD COLUMN implementation_date DATE")
            added_columns.append('implementation_date')
        else:
            print("スキップ: implementation_date カラムは既に存在します")

        if added_columns:
            conn.commit()
            print(f"\n✓ {len(added_columns)} カラムを追加しました: {', '.join(added_columns)}")
        else:
            print("\n✓ すべてのカラムは既に存在します。マイグレーション不要です。")

        # 確認
        cursor.execute("PRAGMA table_info(contracts)")
        final_columns = cursor.fetchall()
        print(f"\nマイグレーション後: {len(final_columns)} カラム")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\nエラーが発生しました: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("contractsテーブル マイグレーション")
    print("=" * 60)

    success = migrate_contracts_table()

    if success:
        print("\n" + "=" * 60)
        print("マイグレーション完了！")
        print("=" * 60)
        print("\nアプリを起動してください: python app.py")
    else:
        print("\n" + "=" * 60)
        print("マイグレーション失敗")
        print("=" * 60)
