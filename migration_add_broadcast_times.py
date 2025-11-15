"""曜日別放送時間カラムの追加マイグレーション

このスクリプトは以下の変更を実行します:
1. productionsテーブルに曜日別放送時間カラムを追加
   - broadcast_time_mon (月曜日)
   - broadcast_time_tue (火曜日)
   - broadcast_time_wed (水曜日)
   - broadcast_time_thu (木曜日)
   - broadcast_time_fri (金曜日)
   - broadcast_time_sat (土曜日)
   - broadcast_time_sun (日曜日)

2. 既存のbroadcast_timeデータを各曜日にコピー（broadcast_daysに基づく）
"""

import sqlite3
import sys
from datetime import datetime
from utils import log_message


def backup_database(db_path):
    """データベースをバックアップ"""
    backup_path = db_path.replace('.db', f'_broadcast_times_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    import shutil
    shutil.copy2(db_path, backup_path)
    log_message(f"✓ データベースバックアップ作成: {backup_path}")
    return backup_path


def execute_migration(db_path='billing.db', dry_run=False):
    """マイグレーションを実行

    Args:
        db_path: データベースファイルパス
        dry_run: Trueの場合、実行せずにSQLを表示のみ
    """

    if not dry_run:
        # バックアップ作成
        backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if dry_run:
            log_message("=== DRY RUN MODE (実行せずSQL表示のみ) ===\n")

        # ========================================
        # Step 1: 曜日別放送時間カラムを追加
        # ========================================

        log_message("Step 1: productionsテーブルに曜日別放送時間カラムを追加中...")

        # 既存カラムをチェック
        cursor.execute("PRAGMA table_info(productions)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        day_columns = {
            'broadcast_time_mon': '月曜日',
            'broadcast_time_tue': '火曜日',
            'broadcast_time_wed': '水曜日',
            'broadcast_time_thu': '木曜日',
            'broadcast_time_fri': '金曜日',
            'broadcast_time_sat': '土曜日',
            'broadcast_time_sun': '日曜日'
        }

        for col_name, day_name in day_columns.items():
            if col_name not in existing_columns:
                sql = f"ALTER TABLE productions ADD COLUMN {col_name} TEXT;"
                if dry_run:
                    print(sql)
                else:
                    cursor.execute(sql)
                    log_message(f"  ✓ {col_name} カラム追加 ({day_name})")
            else:
                log_message(f"  → {col_name} カラムは既に存在")

        # ========================================
        # Step 2: 既存データの移行
        # ========================================

        log_message("\nStep 2: 既存のbroadcast_timeデータを曜日別カラムに移行中...")

        if not dry_run:
            # 既存の番組データを取得
            cursor.execute("""
                SELECT id, broadcast_days, broadcast_time
                FROM productions
                WHERE broadcast_time IS NOT NULL AND broadcast_time != ''
            """)
            productions = cursor.fetchall()

            day_mapping = {
                '月': 'broadcast_time_mon',
                '火': 'broadcast_time_tue',
                '水': 'broadcast_time_wed',
                '木': 'broadcast_time_thu',
                '金': 'broadcast_time_fri',
                '土': 'broadcast_time_sat',
                '日': 'broadcast_time_sun'
            }

            migrated_count = 0
            for prod_id, broadcast_days, broadcast_time in productions:
                if broadcast_days:
                    # カンマ区切りまたは単一曜日
                    days_list = broadcast_days.split(',') if ',' in broadcast_days else [broadcast_days]

                    # 各曜日に放送時間を設定
                    for day in days_list:
                        day = day.strip()
                        if day in day_mapping:
                            col_name = day_mapping[day]
                            cursor.execute(
                                f"UPDATE productions SET {col_name} = ? WHERE id = ?",
                                (broadcast_time, prod_id)
                            )
                    migrated_count += 1

            log_message(f"  ✓ {migrated_count}件の番組の放送時間を移行")
        else:
            print("-- 既存のbroadcast_timeを各曜日カラムにコピー")

        # ========================================
        # Step 3: スキーマバージョンを記録
        # ========================================

        log_message("\nStep 3: スキーマバージョンを記録中...")

        if not dry_run:
            # schema_versionsテーブルが存在するか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'")
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO schema_versions (version, migration_name, success)
                    VALUES (?, ?, ?)
                """, (9, 'add_broadcast_times_by_day', 1))
                log_message("  ✓ スキーマバージョン 9 を記録")
            else:
                log_message("  → schema_versionsテーブルが存在しないためスキップ")

        # コミット
        if not dry_run:
            conn.commit()
            log_message("\n✅ マイグレーション完了！")
        else:
            log_message("\n=== DRY RUN 完了（実際の変更は行われていません） ===")

        return True

    except Exception as e:
        if not dry_run:
            conn.rollback()
        log_message(f"\n❌ マイグレーションエラー: {e}")
        import traceback
        log_message(traceback.format_exc())
        return False

    finally:
        conn.close()


def verify_migration(db_path='billing.db'):
    """マイグレーション結果を検証"""
    log_message("\n=== マイグレーション検証 ===")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # productionsテーブルのカラム確認
        log_message("\nproductionsテーブルのカラム:")
        cursor.execute("PRAGMA table_info(productions)")
        columns = [row[1] for row in cursor.fetchall()]

        expected_columns = [
            'broadcast_time_mon', 'broadcast_time_tue', 'broadcast_time_wed',
            'broadcast_time_thu', 'broadcast_time_fri', 'broadcast_time_sat',
            'broadcast_time_sun'
        ]

        for col in expected_columns:
            if col in columns:
                log_message(f"  ✓ {col} - 存在")
            else:
                log_message(f"  ✗ {col} - 存在しない（エラー）")

        # データ移行の確認
        log_message("\nデータ移行:")
        cursor.execute("""
            SELECT COUNT(*)
            FROM productions
            WHERE broadcast_time_mon IS NOT NULL
               OR broadcast_time_tue IS NOT NULL
               OR broadcast_time_wed IS NOT NULL
               OR broadcast_time_thu IS NOT NULL
               OR broadcast_time_fri IS NOT NULL
               OR broadcast_time_sat IS NOT NULL
               OR broadcast_time_sun IS NOT NULL
        """)
        count = cursor.fetchone()[0]
        log_message(f"  曜日別放送時間が設定されている番組: {count}件")

        log_message("\n✅ 検証完了")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='曜日別放送時間カラム追加マイグレーション')
    parser.add_argument('--dry-run', action='store_true', help='実行せずにSQLを表示のみ')
    parser.add_argument('--verify', action='store_true', help='マイグレーション結果を検証')
    parser.add_argument('--db', default='billing.db', help='データベースファイルパス')

    args = parser.parse_args()

    if args.verify:
        verify_migration(args.db)
    else:
        success = execute_migration(args.db, args.dry_run)

        if success and not args.dry_run:
            verify_migration(args.db)
            sys.exit(0)
        elif not success:
            log_message("\n⚠️ マイグレーション失敗")
            sys.exit(1)
