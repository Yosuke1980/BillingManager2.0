#!/usr/bin/env python3
"""
データベースの状態を診断するスクリプト

使用方法:
    python diagnose_database.py
"""

import sqlite3
import os
import sys

def diagnose_database(db_name):
    """データベースファイルを診断"""
    print(f"\n{'='*70}")
    print(f"診断: {db_name}")
    print(f"{'='*70}")

    # ファイルの存在確認
    if not os.path.exists(db_name):
        print(f"❌ ファイルが存在しません: {db_name}")
        print(f"   カレントディレクトリ: {os.getcwd()}")
        return False

    # ファイルサイズ
    file_size = os.path.getsize(db_name)
    print(f"📁 ファイルサイズ: {file_size:,} bytes ({file_size/1024:.2f} KB)")

    if file_size == 0:
        print(f"❌ ファイルサイズが0です（空のファイル）")
        return False

    if file_size < 1024:
        print(f"⚠️  ファイルサイズが小さすぎます（破損している可能性）")

    # データベース接続とテーブル確認
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # SQLiteバージョン
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"📊 SQLiteバージョン: {version}")

        # テーブル一覧
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\n📋 テーブル一覧 ({len(tables)}個):")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✓ {table:<30} {count:>6}行")
            except Exception as e:
                print(f"   ✗ {table:<30} エラー: {e}")

        # 重要テーブルのチェック
        print(f"\n🔍 重要テーブルの確認:")

        critical_tables = {
            'order_management.db': ['contracts', 'expense_items', 'productions', 'partners'],
            'billing.db': ['expenses', 'payees', 'programs'],
            'payee_master.db': ['payee']
        }

        db_critical = critical_tables.get(db_name, [])
        all_ok = True

        for table in db_critical:
            if table in tables:
                print(f"   ✅ {table} - 存在します")
            else:
                print(f"   ❌ {table} - 存在しません！")
                all_ok = False

        # contractsテーブルの詳細（order_management.dbの場合）
        if db_name == 'order_management.db' and 'contracts' in tables:
            print(f"\n🔍 contractsテーブルの構造:")
            cursor.execute("PRAGMA table_info(contracts)")
            columns = cursor.fetchall()
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                pk_mark = " [PRIMARY KEY]" if pk else ""
                null_mark = " NOT NULL" if not_null else ""
                print(f"   - {name:<25} {col_type:<15}{null_mark}{pk_mark}")

        conn.close()

        return all_ok

    except sqlite3.DatabaseError as e:
        print(f"\n❌ データベースエラー: {e}")
        print(f"   データベースファイルが破損している可能性があります")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("データベース診断ツール")
    print("="*70)
    print(f"カレントディレクトリ: {os.getcwd()}")

    # 診断するデータベース一覧
    databases = [
        'order_management.db',
        'billing.db',
        'payee_master.db'
    ]

    results = {}
    for db_name in databases:
        results[db_name] = diagnose_database(db_name)

    # サマリー
    print(f"\n{'='*70}")
    print("診断結果サマリー")
    print(f"{'='*70}")

    all_ok = True
    for db_name, is_ok in results.items():
        status = "✅ OK" if is_ok else "❌ NG"
        print(f"{status} - {db_name}")
        if not is_ok:
            all_ok = False

    print(f"\n{'='*70}")

    if all_ok:
        print("✅ すべてのデータベースが正常です")
        print("\nアプリケーションを起動できます:")
        print("  python app.py")
        return 0
    else:
        print("❌ 一部のデータベースに問題があります")
        print("\n修復方法:")
        print("  1. emergency_fix_windows.bat を実行")
        print("  2. または python fix_database_windows.py を実行")
        print("  3. または手動で git reset --hard origin/main を実行")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
