"""費用マスターから発注管理への移行スクリプト

expense_master.dbのデータをorder_management.dbに移行します。
- project_name単位でレギュラー案件を作成
- 各レコードを費用項目として登録
"""
import sqlite3
from datetime import datetime, date
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class ExpenseMasterMigrator:
    """費用マスター移行クラス"""

    def __init__(self, expense_master_db_path: str = "expense_master.db",
                 order_db_path: str = "order_management.db"):
        self.expense_master_db = expense_master_db_path
        self.order_db = order_db_path
        self.migration_log = []

    def migrate(self) -> Dict[str, int]:
        """
        移行を実行

        Returns:
            Dict[str, int]: 移行結果の統計情報
        """
        stats = {
            'projects_created': 0,
            'expenses_created': 0,
            'partners_matched': 0,
            'partners_not_found': 0,
            'skipped': 0,
            'errors': 0
        }

        try:
            # 費用マスターデータを読み込み
            expense_data = self._load_expense_master()
            self.migration_log.append(f"費用マスター: {len(expense_data)}件のレコードを読み込み")

            # project_nameでグループ化
            grouped = self._group_by_project_name(expense_data)
            self.migration_log.append(f"{len(grouped)}件の案件にグループ化")

            # 移行実行
            conn_order = sqlite3.connect(self.order_db)
            cursor_order = conn_order.cursor()

            for project_name, items in grouped.items():
                try:
                    # 重複チェック
                    cursor_order.execute(
                        "SELECT id FROM projects WHERE name = ? AND type = 'レギュラー'",
                        (project_name,)
                    )
                    existing = cursor_order.fetchone()

                    if existing:
                        self.migration_log.append(f"スキップ: {project_name}（既存）")
                        stats['skipped'] += 1
                        continue

                    # 案件作成
                    project_id = self._create_project(cursor_order, project_name, items)
                    stats['projects_created'] += 1
                    self.migration_log.append(f"案件作成: {project_name} (ID: {project_id})")

                    # 費用項目作成
                    for item in items:
                        supplier_id = self._find_partner_id(cursor_order, item['payee'], item['payee_code'])

                        if supplier_id:
                            stats['partners_matched'] += 1
                        else:
                            stats['partners_not_found'] += 1
                            self.migration_log.append(
                                f"  警告: 取引先が見つかりません - {item['payee']} ({item['payee_code']})"
                            )

                        expense_id = self._create_expense(
                            cursor_order, project_id, item, supplier_id
                        )
                        stats['expenses_created'] += 1

                    conn_order.commit()

                except Exception as e:
                    self.migration_log.append(f"エラー: {project_name} - {str(e)}")
                    stats['errors'] += 1
                    conn_order.rollback()

            conn_order.close()

        except Exception as e:
            self.migration_log.append(f"致命的エラー: {str(e)}")
            stats['errors'] += 1

        return stats

    def _load_expense_master(self) -> List[Dict]:
        """費用マスターからデータを読み込み"""
        conn = sqlite3.connect(self.expense_master_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, project_name, payee, payee_code, amount,
                payment_type, start_date, end_date, broadcast_days,
                client_name, department, budget
            FROM expense_master
            ORDER BY project_name, id
        """)

        data = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return data

    def _group_by_project_name(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """project_nameでグループ化"""
        grouped = defaultdict(list)

        for item in data:
            grouped[item['project_name']].append(item)

        return dict(grouped)

    def _create_project(self, cursor, project_name: str, items: List[Dict]) -> int:
        """
        レギュラー案件を作成

        Args:
            cursor: SQLiteカーソル
            project_name: 案件名
            items: 費用項目リスト

        Returns:
            int: 作成されたproject_id
        """
        # 開始日・終了日の決定
        start_dates = [item['start_date'] for item in items if item.get('start_date')]
        end_dates = [item['end_date'] for item in items if item.get('end_date')]

        start_date = min(start_dates) if start_dates else date.today().isoformat()
        end_date = max(end_dates) if end_dates else None

        # 予算の合計
        total_budget = sum(item['amount'] or 0 for item in items)

        # 案件作成
        cursor.execute("""
            INSERT INTO projects (
                name, type, date, start_date, end_date, budget,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_name,
            'レギュラー',
            start_date,
            start_date,
            end_date,
            total_budget,
            datetime.now(),
            datetime.now()
        ))

        return cursor.lastrowid

    def _find_partner_id(self, cursor, payee: str, payee_code: str) -> Optional[int]:
        """
        partnersテーブルから取引先IDを検索

        Args:
            cursor: SQLiteカーソル
            payee: 支払先名
            payee_code: 支払先コード

        Returns:
            Optional[int]: partner_id（見つからない場合はNone）
        """
        # 名前で検索
        cursor.execute(
            "SELECT id FROM partners WHERE name = ?",
            (payee,)
        )
        result = cursor.fetchone()

        if result:
            return result[0]

        # コードで検索
        if payee_code:
            cursor.execute(
                "SELECT id FROM partners WHERE code = ?",
                (payee_code,)
            )
            result = cursor.fetchone()

            if result:
                return result[0]

        return None

    def _create_expense(self, cursor, project_id: int, item: Dict,
                       supplier_id: Optional[int]) -> int:
        """
        費用項目を作成

        Args:
            cursor: SQLiteカーソル
            project_id: 案件ID
            item: 費用マスターデータ
            supplier_id: 取引先ID

        Returns:
            int: 作成されたexpense_id
        """
        # 項目名: "支払先名（コード）"形式
        item_name = f"{item['payee']}"
        if item['payee_code']:
            item_name += f"（{item['payee_code']}）"

        # 備考欄に元の情報を記録
        notes_parts = []
        if item.get('broadcast_days'):
            notes_parts.append(f"放送日: {item['broadcast_days']}")
        if item.get('client_name'):
            notes_parts.append(f"クライアント: {item['client_name']}")
        if item.get('department'):
            notes_parts.append(f"部署: {item['department']}")
        if item.get('payment_type'):
            notes_parts.append(f"種別: {item['payment_type']}")

        notes = "\n".join(notes_parts) if notes_parts else None

        cursor.execute("""
            INSERT INTO expenses_order (
                project_id, item_name, amount, supplier_id,
                status, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            item_name,
            item['amount'] or 0,
            supplier_id,
            '発注予定',
            notes,
            datetime.now(),
            datetime.now()
        ))

        return cursor.lastrowid

    def get_migration_log(self) -> List[str]:
        """移行ログを取得"""
        return self.migration_log
