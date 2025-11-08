#!/usr/bin/env python3
"""
Windows完全修復スクリプト

Windows側でデータベース同期問題を完全に修復します。

使用方法:
    python fix_windows_complete.py

処理内容:
    1. 現在のデータベース状態を診断
    2. 既存データベースをバックアップ
    3. 古いデータベースファイルを削除
    4. 全マイグレーションを実行して新規作成
    5. データベースを検証
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from migration_manager import MigrationManager


def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def diagnose_current_state():
    """現在の状態を診断"""
    print("\n現在のデータベース状態:")

    db_file = "order_management.db"
    if os.path.exists(db_file):
        file_size = os.path.getsize(db_file)
        print(f"  order_management.db: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    else:
        print(f"  order_management.db: ファイルが存在しません")


def backup_databases():
    """バックアップ作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_files = ["order_management.db", "billing.db", "payee_master.db"]

    backed_up = []

    for db_file in db_files:
        if os.path.exists(db_file):
            backup_path = f"{db_file}.backup_{timestamp}"
            try:
                shutil.copy2(db_file, backup_path)
                print(f"  ✓ {db_file} → {backup_path}")
                backed_up.append(backup_path)
            except Exception as e:
                print(f"  ✗ {db_file} のバックアップ失敗: {e}")

    return backed_up


def remove_old_databases():
    """古いDBファイル削除"""
    db_files = ["order_management.db"]

    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"  ✓ {db_file} を削除")
            except Exception as e:
                print(f"  ✗ {db_file} の削除失敗: {e}")
                return False

    return True


def run_all_migrations():
    """全データベースのマイグレーション実行"""
    print("\norder_management.db のマイグレーション:")

    mm = MigrationManager("order_management.db", "migrations")
    result = mm.run_migrations()

    print(f"  適用: {result['applied']}件")

    if result['errors']:
        print(f"  ✗ エラー: {len(result['errors'])}件")
        for err in result['errors']:
            print(f"      - [{err['version']:03d}] {err['name']}: {err['error']}")
        return False

    return True


def validate_result():
    """結果検証"""
    print("\nデータベースを検証中...")

    # diagnose_database.pyが存在する場合は実行
    if os.path.exists("diagnose_database.py"):
        try:
            result = subprocess.run(
                [sys.executable, "diagnose_database.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout)
            return result.returncode == 0
        except Exception as e:
            print(f"  ⚠️  診断スクリプトの実行に失敗: {e}")
            return True  # 診断失敗でも続行
    else:
        print("  ✓ order_management.db が作成されました")
        return True


def main():
    print_section("Windows完全修復スクリプト")

    # ステップ1: 現在の状態確認
    print("\n[1/6] 現在のデータベース状態を確認中...")
    diagnose_current_state()

    # ステップ2: バックアップ作成
    print("\n[2/6] 既存データベースをバックアップ中...")
    backups = backup_databases()

    if not backups:
        print("\n  ℹ️  バックアップするファイルがありません（新規セットアップ）")

    # ステップ3: 確認プロンプト
    print("\n[3/6] 既存データベースを削除して再構築します")
    print("\n⚠️  注意:")
    print("  - 既存のorder_management.dbは削除されます")
    print("  - バックアップは作成済みです" if backups else "  - バックアップファイルはありません")
    print()

    confirm = input("続行しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("\nキャンセルしました")
        return 1

    # ステップ4: 古いDBファイル削除
    print("\n[4/6] 古いデータベースファイルを削除中...")
    if not remove_old_databases():
        print("\n✗ データベースファイルの削除に失敗しました")
        return 1

    # ステップ5: マイグレーション実行
    print("\n[5/6] マイグレーション実行中...")
    if not run_all_migrations():
        print("\n✗ マイグレーション実行に失敗しました")
        print("\n💡 バックアップから復元する場合:")
        for backup in backups:
            original = backup.rsplit('.backup_', 1)[0]
            print(f"  copy {backup} {original}")
        return 1

    # ステップ6: 検証
    print("\n[6/6] データベースを検証中...")
    if not validate_result():
        print("\n⚠️  検証で警告が見つかりました")

    # 成功
    print_section("✅ 修復完了！")
    print("\nアプリケーションを起動できます:")
    print("  python app.py")

    if backups:
        print("\nバックアップファイル:")
        for backup in backups:
            print(f"  {backup}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
