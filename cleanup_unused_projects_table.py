"""
projectsテーブルを削除するクリーンアップスクリプト

projectsテーブルは使用されていない（データ0件）ため、削除します。
実際に使用されているのはproductionsテーブルです。
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "order_management.db"

def cleanup():
    print("=" * 60)
    print("projectsテーブル削除スクリプト")
    print("=" * 60)

    # データベース接続
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # データ件数確認
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        print(f"\n現在のprojectsテーブルのレコード数: {count}件")

        if count > 0:
            print("⚠️  データが存在するため、削除を中止します")
            return False

        # テーブル削除
        print("\nprojectsテーブルを削除中...")
        cursor.execute("DROP TABLE IF EXISTS projects")
        conn.commit()
        print("✓ projectsテーブルを削除しました")

        print("\n" + "=" * 60)
        print("✓ クリーンアップ完了")
        print("=" * 60)
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n✗ エラーが発生しました: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
