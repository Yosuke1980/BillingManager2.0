#!/usr/bin/env python3
"""
新規環境データベースセットアップスクリプト

使用方法:
    python init_database.py [--dry-run]

オプション:
    --dry-run    実行内容を表示のみ（実際には実行しない）
"""

import sys
import argparse
from migration_manager import MigrationManager


def main():
    parser = argparse.ArgumentParser(description='データベース初期セットアップ')
    parser.add_argument('--dry-run', action='store_true',
                       help='実行内容を表示のみ（実際には実行しない）')
    args = parser.parse_args()

    print("="*70)
    print("データベース初期セットアップ")
    print("="*70)

    # order_management.dbのセットアップ
    print("\n📁 order_management.db をセットアップ中...")

    mm = MigrationManager("order_management.db", "migrations")

    # ドライランモード
    if args.dry_run:
        print("  [DRY RUN モード]")
        pending = mm.get_pending_migrations()
        print(f"  実行予定: {len(pending)}件のマイグレーション")
        for mig in pending:
            print(f"    - {mig['version']:03d}: {mig['name']}")
    else:
        # マイグレーション実行
        result = mm.run_migrations()

        if result['applied'] > 0:
            print(f"  ✓ 適用: {result['applied']}件のマイグレーション")
        else:
            print(f"  ✓ すべてのマイグレーションは適用済みです")

        if result['errors']:
            print(f"  ✗ エラー: {len(result['errors'])}件")
            for err in result['errors']:
                print(f"      - [{err['version']:03d}] {err['name']}: {err['error']}")
            return 1

    # 成功
    if not args.dry_run:
        print("\n" + "="*70)
        print("✅ セットアップ完了！")
        print("="*70)
        print("\nアプリケーションを起動できます:")
        print("  python app.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
