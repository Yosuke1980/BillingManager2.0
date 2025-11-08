#!/usr/bin/env python3
"""
シンプルなSQLマイグレーション管理システム

使用方法:
    from migration_manager import MigrationManager

    mm = MigrationManager("database.db", "migrations")
    result = mm.run_migrations()

機能:
    - SQLファイルベースのマイグレーション管理
    - バージョン番号による順序制御
    - チェックサムによる改ざん検出
    - トランザクション管理
    - ロールバック機能
    - ドライランモード
"""

import sqlite3
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class MigrationManager:
    """SQLマイグレーション管理システム"""

    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        """
        Args:
            db_path: データベースファイルパス
            migrations_dir: マイグレーションSQLファイルのディレクトリ
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir

        # データベースファイルが存在しない場合は作成
        if not os.path.exists(db_path):
            open(db_path, 'a').close()

        # schema_versionsテーブルを作成
        self._create_schema_versions_table()

    def _create_schema_versions_table(self):
        """マイグレーション履歴管理テーブル作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER UNIQUE NOT NULL,
                    migration_name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get_current_version(self) -> int:
        """現在のスキーマバージョン番号を取得

        Returns:
            int: 現在のバージョン番号（マイグレーション未実行の場合は0）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT MAX(version) FROM schema_versions WHERE success = 1
            """)
            result = cursor.fetchone()[0]
            return result if result is not None else 0
        finally:
            conn.close()

    def get_pending_migrations(self) -> List[Dict]:
        """未実行のマイグレーション一覧取得

        Returns:
            List[Dict]: 未実行のマイグレーション情報リスト
                [{'version': 1, 'name': 'create_table', 'filepath': '...', 'sql': '...'}, ...]
        """
        current_version = self.get_current_version()
        all_migrations = self._scan_migration_files()

        # 現在のバージョンより新しいマイグレーションのみ返す
        pending = [m for m in all_migrations if m['version'] > current_version]
        return pending

    def _scan_migration_files(self) -> List[Dict]:
        """migrations/ディレクトリからSQLファイルをスキャン

        Returns:
            List[Dict]: マイグレーション情報リスト（バージョン順にソート済み）
        """
        if not os.path.exists(self.migrations_dir):
            return []

        migrations = []
        pattern = re.compile(r'^(\d{3})_(.+)\.sql$')

        for filename in os.listdir(self.migrations_dir):
            match = pattern.match(filename)
            if match:
                version = int(match.group(1))
                name = match.group(2)
                filepath = os.path.join(self.migrations_dir, filename)

                # SQLファイルを読み込み
                with open(filepath, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                migrations.append({
                    'version': version,
                    'name': name,
                    'filename': filename,
                    'filepath': filepath,
                    'sql': sql_content,
                    'checksum': self._calculate_checksum(sql_content)
                })

        # バージョン番号でソート
        migrations.sort(key=lambda x: x['version'])
        return migrations

    def _calculate_checksum(self, sql_content: str) -> str:
        """SQLファイルのMD5チェックサム計算

        Args:
            sql_content: SQL文字列

        Returns:
            str: MD5ハッシュ（16進数文字列）
        """
        return hashlib.md5(sql_content.encode('utf-8')).hexdigest()

    def run_migrations(self, target_version: Optional[int] = None, dry_run: bool = False) -> Dict:
        """マイグレーション実行

        Args:
            target_version: 特定バージョンまで実行（Noneで全て実行）
            dry_run: Trueの場合は実行内容を表示のみ（実際には実行しない）

        Returns:
            dict: {
                'applied': 適用されたマイグレーション数,
                'skipped': スキップされた数,
                'errors': エラーリスト
            }
        """
        result = {
            'applied': 0,
            'skipped': 0,
            'errors': []
        }

        pending = self.get_pending_migrations()

        # target_versionが指定されている場合はフィルタ
        if target_version is not None:
            pending = [m for m in pending if m['version'] <= target_version]

        if not pending:
            return result

        # ドライランモード
        if dry_run:
            print(f"[DRY RUN] {len(pending)}件のマイグレーションを実行予定:")
            for mig in pending:
                print(f"  {mig['version']:03d}: {mig['name']}")
            result['skipped'] = len(pending)
            return result

        # 実際の実行
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for migration in pending:
            try:
                # トランザクション開始
                cursor.execute("BEGIN")

                # SQLを実行
                cursor.executescript(migration['sql'])

                # schema_versionsに記録
                cursor.execute("""
                    INSERT INTO schema_versions (version, migration_name, checksum, success)
                    VALUES (?, ?, ?, 1)
                """, (migration['version'], migration['name'], migration['checksum']))

                # コミット
                conn.commit()

                result['applied'] += 1
                print(f"✓ [{migration['version']:03d}] {migration['name']}")

            except Exception as e:
                # ロールバック
                conn.rollback()

                error_msg = str(e)
                result['errors'].append({
                    'version': migration['version'],
                    'name': migration['name'],
                    'error': error_msg
                })

                # エラーを記録
                try:
                    cursor.execute("""
                        INSERT INTO schema_versions (version, migration_name, checksum, success, error_message)
                        VALUES (?, ?, ?, 0, ?)
                    """, (migration['version'], migration['name'], migration['checksum'], error_msg))
                    conn.commit()
                except:
                    pass

                print(f"✗ [{migration['version']:03d}] {migration['name']}: {error_msg}")

                # エラーが発生したら以降のマイグレーションは実行しない
                break

        conn.close()
        return result

    def rollback(self, steps: int = 1) -> Dict:
        """指定ステップ分ロールバック

        Args:
            steps: ロールバックするステップ数

        Returns:
            dict: {
                'rolled_back': ロールバックされた数,
                'errors': エラーリスト
            }
        """
        result = {
            'rolled_back': 0,
            'errors': []
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 成功したマイグレーションを新しい順に取得
            cursor.execute("""
                SELECT version, migration_name, checksum
                FROM schema_versions
                WHERE success = 1
                ORDER BY version DESC
                LIMIT ?
            """, (steps,))

            migrations_to_rollback = cursor.fetchall()

            for version, name, checksum in migrations_to_rollback:
                # ロールバックSQLファイルを探す
                rollback_file = os.path.join(
                    self.migrations_dir,
                    "rollback",
                    f"{version:03d}_rollback.sql"
                )

                if not os.path.exists(rollback_file):
                    result['errors'].append({
                        'version': version,
                        'name': name,
                        'error': f'ロールバックファイルが見つかりません: {rollback_file}'
                    })
                    continue

                try:
                    # ロールバックSQL実行
                    with open(rollback_file, 'r', encoding='utf-8') as f:
                        rollback_sql = f.read()

                    cursor.execute("BEGIN")
                    cursor.executescript(rollback_sql)

                    # schema_versionsから削除
                    cursor.execute("""
                        DELETE FROM schema_versions WHERE version = ?
                    """, (version,))

                    conn.commit()
                    result['rolled_back'] += 1
                    print(f"⟲ [{version:03d}] {name} をロールバックしました")

                except Exception as e:
                    conn.rollback()
                    result['errors'].append({
                        'version': version,
                        'name': name,
                        'error': str(e)
                    })
                    print(f"✗ [{version:03d}] {name} のロールバック失敗: {e}")
                    break

        finally:
            conn.close()

        return result

    def validate_migrations(self) -> List[str]:
        """マイグレーションファイルの整合性チェック

        Returns:
            List[str]: 警告メッセージのリスト（問題なければ空リスト）
        """
        warnings = []

        all_migrations = self._scan_migration_files()

        # バージョン番号の連番チェック
        expected_version = 1
        for mig in all_migrations:
            if mig['version'] != expected_version:
                warnings.append(
                    f"バージョン番号の欠番: {expected_version}が存在しません "
                    f"({mig['version']:03d}_{mig['name']}.sql の前)"
                )
            expected_version = mig['version'] + 1

        # 適用済みマイグレーションのチェックサム確認
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT version, migration_name, checksum
                FROM schema_versions
                WHERE success = 1
            """)

            applied_migrations = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

            for mig in all_migrations:
                if mig['version'] in applied_migrations:
                    stored_name, stored_checksum = applied_migrations[mig['version']]

                    if mig['checksum'] != stored_checksum:
                        warnings.append(
                            f"チェックサム不一致: {mig['version']:03d}_{mig['name']}.sql "
                            f"が適用後に変更されています"
                        )

        finally:
            conn.close()

        return warnings

    def get_migration_history(self) -> List[Dict]:
        """実行済みマイグレーション履歴を取得

        Returns:
            List[Dict]: マイグレーション履歴
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT version, migration_name, applied_at, success, error_message
                FROM schema_versions
                ORDER BY version
            """)

            history = []
            for row in cursor.fetchall():
                history.append({
                    'version': row[0],
                    'name': row[1],
                    'applied_at': row[2],
                    'success': bool(row[3]),
                    'error': row[4]
                })

            return history

        finally:
            conn.close()


# コマンドライン実行用
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='マイグレーション管理ツール')
    parser.add_argument('db_path', help='データベースファイルパス')
    parser.add_argument('--migrations-dir', default='migrations', help='マイグレーションディレクトリ')
    parser.add_argument('--dry-run', action='store_true', help='ドライラン（実行内容を表示のみ）')
    parser.add_argument('--rollback', type=int, metavar='STEPS', help='指定ステップ分ロールバック')
    parser.add_argument('--validate', action='store_true', help='マイグレーションファイルの整合性チェック')
    parser.add_argument('--history', action='store_true', help='マイグレーション履歴を表示')

    args = parser.parse_args()

    mm = MigrationManager(args.db_path, args.migrations_dir)

    if args.validate:
        warnings = mm.validate_migrations()
        if warnings:
            print("⚠️  警告:")
            for warning in warnings:
                print(f"  - {warning}")
            sys.exit(1)
        else:
            print("✓ すべてのマイグレーションファイルは正常です")

    elif args.history:
        history = mm.get_migration_history()
        print(f"マイグレーション履歴 ({len(history)}件):")
        for h in history:
            status = "✓" if h['success'] else "✗"
            print(f"  {status} [{h['version']:03d}] {h['name']} - {h['applied_at']}")
            if h['error']:
                print(f"      エラー: {h['error']}")

    elif args.rollback:
        print(f"{args.rollback}ステップのロールバックを実行します...")
        result = mm.rollback(args.rollback)
        print(f"\nロールバック完了: {result['rolled_back']}件")
        if result['errors']:
            print(f"エラー: {len(result['errors'])}件")
            for err in result['errors']:
                print(f"  - [{err['version']:03d}] {err['name']}: {err['error']}")

    else:
        print(f"現在のバージョン: {mm.get_current_version()}")
        pending = mm.get_pending_migrations()
        print(f"未実行のマイグレーション: {len(pending)}件")

        if pending:
            result = mm.run_migrations(dry_run=args.dry_run)
            if not args.dry_run:
                print(f"\n適用: {result['applied']}件")
                if result['errors']:
                    print(f"エラー: {len(result['errors'])}件")
                    for err in result['errors']:
                        print(f"  - [{err['version']:03d}] {err['name']}: {err['error']}")
                    sys.exit(1)
        else:
            print("すべてのマイグレーションは適用済みです")
