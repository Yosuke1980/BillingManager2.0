#!/usr/bin/env python3
"""
Windows側でのデータベース同期問題を自動修復するスクリプト

使用方法:
    python fix_database_windows.py
"""

import sqlite3
import subprocess
import sys
import os
import shutil
from datetime import datetime

def check_database_structure(db_path):
    """データベースの構造をチェック"""
    print(f"\n{'='*60}")
    print(f"データベースチェック: {db_path}")
    print(f"{'='*60}")

    if not os.path.exists(db_path):
        print(f"❌ データベースファイルが存在しません: {db_path}")
        return False

    file_size = os.path.getsize(db_path)
    print(f"📁 ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # テーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\n📋 テーブル一覧 ({len(tables)}個):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count}行")

        # contractsテーブルの存在チェック
        has_contracts = 'contracts' in tables

        if has_contracts:
            print(f"\n✅ contractsテーブルが存在します")

            # contractsテーブルのカラムを確認
            cursor.execute("PRAGMA table_info(contracts)")
            columns = cursor.fetchall()
            print(f"\n🔍 contractsテーブルの構造 ({len(columns)}カラム):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print(f"\n❌ contractsテーブルが存在しません")

        conn.close()
        return has_contracts

    except Exception as e:
        print(f"\n❌ データベースチェック中にエラーが発生: {e}")
        return False

def backup_database(db_path):
    """データベースをバックアップ"""
    if not os.path.exists(db_path):
        print("バックアップ対象のファイルが存在しません")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ バックアップ作成: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ バックアップ失敗: {e}")
        return None

def restore_from_git(db_path):
    """GitHubから最新のデータベースを取得"""
    print(f"\n{'='*60}")
    print("GitHubから最新のデータベースを取得中...")
    print(f"{'='*60}")

    try:
        # git fetch
        print("\n1️⃣ git fetch origin")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ git fetch 失敗: {result.stderr}")
            return False
        print("✅ fetch完了")

        # git checkout
        print(f"\n2️⃣ git checkout origin/main -- {db_path}")
        result = subprocess.run(
            ["git", "checkout", "origin/main", "--", db_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ git checkout 失敗: {result.stderr}")
            return False
        print("✅ checkout完了")

        print("\n✅ GitHubから最新のデータベースを取得しました")
        return True

    except Exception as e:
        print(f"\n❌ Git操作中にエラーが発生: {e}")
        return False

def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("Windows データベース修復スクリプト")
    print("="*60)

    db_path = "order_management.db"

    # ステップ1: 現在のデータベースをチェック
    print("\n【ステップ1】現在のデータベースをチェック")
    has_contracts = check_database_structure(db_path)

    if has_contracts:
        print("\n✅ データベースは正常です。修復の必要はありません。")
        return 0

    # ステップ2: バックアップ作成
    print("\n【ステップ2】現在のデータベースをバックアップ")
    backup_path = backup_database(db_path)

    # ステップ3: GitHubから最新版を取得
    print("\n【ステップ3】GitHubから最新のデータベースを取得")

    response = input("\nGitHubから最新のデータベースを取得しますか？ (y/n): ")
    if response.lower() != 'y':
        print("\n❌ 処理をキャンセルしました")
        return 1

    success = restore_from_git(db_path)

    if not success:
        print("\n❌ Git操作に失敗しました")
        if backup_path:
            print(f"バックアップから復元する場合: copy {backup_path} {db_path}")
        return 1

    # ステップ4: 修復後のデータベースをチェック
    print("\n【ステップ4】修復後のデータベースをチェック")
    has_contracts = check_database_structure(db_path)

    if has_contracts:
        print("\n" + "="*60)
        print("✅ データベースの修復が完了しました！")
        print("="*60)
        print("\nアプリケーションを起動できます:")
        print("  python app.py")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ データベースの修復に失敗しました")
        print("="*60)
        print("\n手動での対応が必要です。fix_windows_database.md を参照してください。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
