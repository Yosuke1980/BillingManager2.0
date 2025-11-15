"""発注管理データベースマネージャー

発注管理機能のデータベース操作を担当します。
"""
import sqlite3
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from utils import log_message


def parse_flexible_date(date_str: str) -> Optional[str]:
    """柔軟な日付フォーマットをYYYY-MM-DD形式に変換

    対応フォーマット:
    - YYYY-MM-DD (例: 2025-01-01)
    - YYYY/MM/DD (例: 2025/01/01)
    - YYYY/M/D (例: 2025/1/1)
    - YYYY-M-D (例: 2025-1-1)

    Args:
        date_str: 日付文字列

    Returns:
        YYYY-MM-DD形式の日付文字列、変換失敗時はNone
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # 試行する日付フォーマット
    formats = [
        '%Y-%m-%d',  # 2025-01-01
        '%Y/%m/%d',  # 2025/01/01
        '%Y/%m/%d',  # 2025/1/1 (strptimeは0埋めなしでも対応)
        '%Y-%m-%d',  # 2025-1-1 (strptimeは0埋めなしでも対応)
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    return None


class OrderManagementDB:
    """発注管理データベースマネージャー"""

    def __init__(self, db_path="order_management.db"):
        self.db_path = db_path
        # テーブル存在チェックと自動作成
        self._ensure_tables_exist()
        # 起動時に自動マイグレーションを実行
        self._auto_migrate()

    def _get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)

    def _ensure_tables_exist(self):
        """必須テーブルが存在することを保証"""
        import os

        # DBファイルが存在しない場合は作成
        if not os.path.exists(self.db_path):
            open(self.db_path, 'a').close()
            print(f"📝 新規データベースファイルを作成: {self.db_path}")

        # 必須テーブルの存在確認
        required_tables = ['contracts', 'expense_items', 'productions', 'partners']
        missing_tables = []

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    missing_tables.append(table)
        finally:
            conn.close()

        # 不足テーブルがある場合はマイグレーション実行
        if missing_tables:
            print(f"⚠️  不足しているテーブル: {', '.join(missing_tables)}")
            print(f"📝 マイグレーションを実行してテーブルを作成します...")

            try:
                from migration_manager import MigrationManager

                mm = MigrationManager(self.db_path, "migrations")
                result = mm.run_migrations()

                if result['applied'] > 0:
                    print(f"✓ {result['applied']}件のマイグレーションを適用しました")

                if result['errors']:
                    print(f"⚠️  エラー: {result['errors']}")
                    raise Exception(f"マイグレーション実行に失敗しました: {result['errors']}")

            except Exception as e:
                print(f"❌ マイグレーションエラー: {e}")
                print(f"💡 手動で修復してください: python fix_windows_complete.py")
                raise

    def _check_column_exists(self, table_name, column_name):
        """テーブルに指定したカラムが存在するかチェック"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        finally:
            conn.close()

    def _auto_migrate(self):
        """起動時に自動でマイグレーションを実行"""
        import os
        if not os.path.exists(self.db_path):
            return  # データベースがまだ作成されていない場合はスキップ

        try:
            # expense_itemsテーブルにwork_typeカラムが存在しない場合は追加
            if not self._check_column_exists('expense_items', 'work_type'):
                print("📝 自動マイグレーション: expense_itemsテーブルにwork_typeカラムを追加中...")
                conn = self._get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        ALTER TABLE expense_items
                        ADD COLUMN work_type TEXT DEFAULT '制作'
                    """)

                    # 既存データを契約から更新
                    cursor.execute("""
                        UPDATE expense_items
                        SET work_type = (
                            SELECT c.work_type
                            FROM contracts c
                            WHERE c.id = expense_items.contract_id
                        )
                        WHERE expense_items.contract_id IS NOT NULL
                          AND EXISTS (
                            SELECT 1 FROM contracts c
                            WHERE c.id = expense_items.contract_id
                          )
                    """)

                    conn.commit()
                    print("✓ work_typeカラムを追加しました")
                except Exception as e:
                    conn.rollback()
                    print(f"⚠️  マイグレーション警告: {e}")
                finally:
                    conn.close()
        except Exception as e:
            print(f"⚠️  自動マイグレーションエラー: {e}")

    # ========================================
    # 統合取引先マスター操作（Phase 6）
    # ========================================

    def get_partners(self, search_term: str = "") -> List[Tuple]:
        """統合取引先マスター一覧を取得

        Args:
            search_term: 検索キーワード

        Returns:
            List[Tuple]: (id, name, code, contact_person, email, phone, address, partner_type, notes)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if search_term:
                cursor.execute("""
                    SELECT id, name, code, contact_person, email, phone, address, partner_type, notes
                    FROM partners
                    WHERE name LIKE ? OR contact_person LIKE ? OR email LIKE ?
                    ORDER BY name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT id, name, code, contact_person, email, phone, address, partner_type, notes
                    FROM partners
                    ORDER BY name
                """)

            return cursor.fetchall()
        finally:
            conn.close()

    def get_partner_by_id(self, partner_id: int) -> Optional[Tuple]:
        """IDで統合取引先を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, code, contact_person, email, phone, address, partner_type, notes,
                       created_at, updated_at
                FROM partners WHERE id = ?
            """, (partner_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    # ========================================
    # 発注先マスター操作（旧版・互換性のため残す）
    # ========================================

    def get_suppliers(self, search_term: str = "") -> List[Tuple]:
        """発注先マスター一覧を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if search_term:
                cursor.execute("""
                    SELECT id, name, contact_person, email, phone, address, notes
                    FROM suppliers
                    WHERE name LIKE ? OR contact_person LIKE ? OR email LIKE ?
                    ORDER BY name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT id, name, contact_person, email, phone, address, notes
                    FROM suppliers
                    ORDER BY name
                """)

            return cursor.fetchall()
        finally:
            conn.close()

    def get_supplier_by_id(self, supplier_id: int) -> Optional[Tuple]:
        """IDで発注先を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, contact_person, email, phone, address, notes,
                       created_at, updated_at
                FROM suppliers WHERE id = ?
            """, (supplier_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_supplier(self, supplier_data: dict, is_new: bool = False) -> int:
        """発注先を保存"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if is_new:
                cursor.execute("""
                    INSERT INTO suppliers (name, contact_person, email, phone, address, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    supplier_data.get('name', ''),
                    supplier_data.get('contact_person', ''),
                    supplier_data.get('email', ''),
                    supplier_data.get('phone', ''),
                    supplier_data.get('address', ''),
                    supplier_data.get('notes', ''),
                ))
                supplier_id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE suppliers
                    SET name = ?, contact_person = ?, email = ?, phone = ?,
                        address = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    supplier_data.get('name', ''),
                    supplier_data.get('contact_person', ''),
                    supplier_data.get('email', ''),
                    supplier_data.get('phone', ''),
                    supplier_data.get('address', ''),
                    supplier_data.get('notes', ''),
                    supplier_data['id'],
                ))
                supplier_id = supplier_data['id']

            conn.commit()
            log_message(f"発注先保存完了: ID={supplier_id}")
            return supplier_id
        except Exception as e:
            conn.rollback()
            log_message(f"発注先保存エラー: {e}")
            raise
        finally:
            conn.close()

    def delete_supplier(self, supplier_id: int) -> int:
        """発注先を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # ========================================
    # 案件操作
    # ========================================


    def get_expenses_by_production(self, production_id: int) -> List[Tuple]:
        """番組・イベントIDで費用項目を取得（新テーブル: expense_items）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, production_id, item_name, amount, partner_id, contact_person,
                       status, order_number, implementation_date, invoice_received_date
                FROM expense_items
                WHERE production_id = ?
                ORDER BY implementation_date, id
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_expense_order_by_id(self, expense_id: int) -> Optional[Tuple]:
        """IDで費用項目を取得（新テーブル: expense_items）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, production_id, item_name, amount, partner_id, contact_person,
                       status, order_number, order_date, implementation_date,
                       invoice_received_date, payment_scheduled_date, payment_date,
                       gmail_draft_id, gmail_message_id, email_sent_at, notes
                FROM expense_items WHERE id = ?
            """, (expense_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_expense_order(self, expense_data: dict, is_new: bool = False) -> int:
        """費用項目を保存（新テーブル: expense_items）

        注意: supplier_id は partner_id として保存されます
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # supplier_idがあればpartner_idとして扱う（後方互換性）
            partner_id = expense_data.get('partner_id') or expense_data.get('supplier_id')

            if is_new:
                cursor.execute("""
                    INSERT INTO expense_items (
                        production_id, item_name, amount, partner_id, contact_person,
                        status, order_number, order_date, implementation_date,
                        invoice_received_date, payment_scheduled_date, payment_date,
                        gmail_draft_id, gmail_message_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    expense_data.get('production_id', 0),
                    expense_data.get('item_name', ''),
                    expense_data.get('amount', 0.0),
                    partner_id,
                    expense_data.get('contact_person', ''),
                    expense_data.get('status', '発注予定'),
                    expense_data.get('order_number', ''),
                    expense_data.get('order_date', ''),
                    expense_data.get('implementation_date', ''),
                    expense_data.get('invoice_received_date', ''),
                    expense_data.get('payment_scheduled_date', ''),
                    expense_data.get('payment_date', ''),
                    expense_data.get('gmail_draft_id', ''),
                    expense_data.get('gmail_message_id', ''),
                    expense_data.get('notes', ''),
                ))
                expense_id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE expense_items
                    SET production_id = ?, item_name = ?, amount = ?, partner_id = ?,
                        contact_person = ?, status = ?, order_number = ?, order_date = ?,
                        implementation_date = ?, invoice_received_date = ?,
                        payment_scheduled_date = ?, payment_date = ?, gmail_draft_id = ?,
                        gmail_message_id = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    expense_data.get('production_id', 0),
                    expense_data.get('item_name', ''),
                    expense_data.get('amount', 0.0),
                    partner_id,
                    expense_data.get('contact_person', ''),
                    expense_data.get('status', '発注予定'),
                    expense_data.get('order_number', ''),
                    expense_data.get('order_date', ''),
                    expense_data.get('implementation_date', ''),
                    expense_data.get('invoice_received_date', ''),
                    expense_data.get('payment_scheduled_date', ''),
                    expense_data.get('payment_date', ''),
                    expense_data.get('gmail_draft_id', ''),
                    expense_data.get('gmail_message_id', ''),
                    expense_data.get('notes', ''),
                    expense_data['id'],
                ))
                expense_id = expense_data['id']

            conn.commit()
            log_message(f"費用項目保存完了: ID={expense_id}")
            return expense_id
        except Exception as e:
            conn.rollback()
            log_message(f"費用項目保存エラー: {e}")
            raise
        finally:
            conn.close()

    def delete_expense_order(self, expense_id: int) -> int:
        """費用項目を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM expense_items WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # ========================================
    # 統計・集計
    # ========================================

    def get_production_summary(self, production_id: int) -> dict:
        """制作物の実績サマリーを取得

        Note: budget カラム削除により、実績のみを返します
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 実績合計取得
            cursor.execute("""
                SELECT SUM(amount) FROM expense_items WHERE production_id = ?
            """, (production_id,))
            row = cursor.fetchone()
            actual = row[0] if row and row[0] else 0.0

            return {
                'actual': actual,
            }
        finally:
            conn.close()

    # ========================================
    # 制作物マスター操作
    # ========================================

    def get_productions(self, search_term: str = "", status: str = "") -> List[Tuple]:
        """制作物マスター一覧を取得

        Args:
            search_term: 検索キーワード
            status: ステータスフィルタ（'放送中' or '終了' or ''）

        Returns:
            List[Tuple]: (id, name, description, production_type, start_date, end_date,
                         start_time, end_time, broadcast_time, broadcast_days, status,
                         parent_production_id)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, description, production_type, start_date, end_date,
                       start_time, end_time, broadcast_time, broadcast_days, status,
                       parent_production_id
                FROM productions
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND name LIKE ?"
                params.append(f"%{search_term}%")

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_production_by_id(self, production_id: int) -> Optional[Tuple]:
        """IDで制作物を取得

        Returns:
            Tuple: (id, name, description, production_type, start_date, end_date,
                   start_time, end_time, broadcast_time, broadcast_days, status,
                   parent_production_id, created_at, updated_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, production_type, start_date, end_date,
                       start_time, end_time, broadcast_time, broadcast_days, status,
                       parent_production_id, created_at, updated_at
                FROM productions WHERE id = ?
            """, (production_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_corners_by_production(self, production_id: int) -> List[Tuple]:
        """指定した番組に紐づくコーナー一覧を取得

        Args:
            production_id: 親番組のID

        Returns:
            List[Tuple]: (id, name) のリスト
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name
                FROM productions
                WHERE parent_production_id = ?
                ORDER BY name
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_production(self, production_data: dict, is_new: bool = True):
        """制作物を保存

        Args:
            production_data: 制作物データ辞書
                - name: 制作物名（必須）
                - description: 備考
                - production_type: 種別
                - start_date: 開始日
                - end_date: 終了日
                - start_time: 実施開始時間
                - end_time: 実施終了時間
                - broadcast_time: 放送時間
                - broadcast_days: 放送曜日（カンマ区切り）
                - status: ステータス
                - parent_production_id: 親制作物ID
            is_new: 新規登録かどうか
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now()

            if is_new:
                cursor.execute("""
                    INSERT INTO productions (
                        name, description, production_type, start_date, end_date,
                        start_time, end_time, broadcast_time, broadcast_days, status,
                        parent_production_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    production_data['name'],
                    production_data.get('description', ''),
                    production_data.get('production_type', 'レギュラー番組'),
                    production_data.get('start_date'),
                    production_data.get('end_date'),
                    production_data.get('start_time'),
                    production_data.get('end_time'),
                    production_data.get('broadcast_time', ''),
                    production_data.get('broadcast_days', ''),
                    production_data.get('status', '放送中'),
                    production_data.get('parent_production_id'),
                    now,
                    now
                ))
                production_id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE productions SET
                        name = ?,
                        description = ?,
                        production_type = ?,
                        start_date = ?,
                        end_date = ?,
                        start_time = ?,
                        end_time = ?,
                        broadcast_time = ?,
                        broadcast_days = ?,
                        status = ?,
                        parent_production_id = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    production_data['name'],
                    production_data.get('description', ''),
                    production_data.get('production_type', 'レギュラー番組'),
                    production_data.get('start_date'),
                    production_data.get('end_date'),
                    production_data.get('start_time'),
                    production_data.get('end_time'),
                    production_data.get('broadcast_time', ''),
                    production_data.get('broadcast_days', ''),
                    production_data.get('status', '放送中'),
                    production_data.get('parent_production_id'),
                    now,
                    production_data['id']
                ))
                production_id = production_data['id']

            conn.commit()
            return production_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_production(self, production_id: int):
        """制作物を削除（関連する出演者・制作会社も削除）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 関連する費用項目が存在するかチェック
            cursor.execute("""
                SELECT COUNT(*) FROM expense_items WHERE production_id = ?
            """, (production_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                raise Exception(f"この制作物には{count}件の費用項目が関連付けられています。削除できません。")

            # CASCADE削除により出演者・制作会社も自動削除される
            cursor.execute("DELETE FROM productions WHERE id = ?", (production_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def duplicate_production(self, production_id: int) -> int:
        """制作物を複製（費用項目も含めて）

        Args:
            production_id: 複製元の制作物ID

        Returns:
            int: 新しい制作物のID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 元の制作物データを取得
            cursor.execute("""
                SELECT name, description, production_type, start_date, end_date,
                       start_time, end_time, broadcast_time, broadcast_days,
                       status, parent_production_id
                FROM productions WHERE id = ?
            """, (production_id,))

            production = cursor.fetchone()
            if not production:
                raise ValueError(f"制作物ID {production_id} が見つかりません")

            # 新しい制作物を作成（名前に「（コピー）」を追加）
            cursor.execute("""
                INSERT INTO productions (name, description, production_type, start_date, end_date,
                                       start_time, end_time, broadcast_time, broadcast_days,
                                       status, parent_production_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                production[0] + "（コピー）",  # name
                production[1],  # description
                production[2],  # production_type
                production[3],  # start_date
                production[4],  # end_date
                production[5],  # start_time
                production[6],  # end_time
                production[7],  # broadcast_time
                production[8],  # broadcast_days
                production[9],  # status
                production[10],  # parent_production_id
            ))

            new_production_id = cursor.lastrowid

            # 関連する費用項目をコピー
            cursor.execute("""
                SELECT item_name, amount, supplier_id, contact_person, status,
                       implementation_date, payment_scheduled_date, notes
                FROM expense_items WHERE production_id = ?
            """, (production_id,))

            expenses = cursor.fetchall()
            for expense in expenses:
                cursor.execute("""
                    INSERT INTO expense_items (
                        production_id, item_name, amount, supplier_id, contact_person,
                        status, implementation_date, payment_scheduled_date, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_production_id,
                    expense[0],  # item_name
                    expense[1],  # amount
                    expense[2],  # supplier_id
                    expense[3],  # contact_person
                    expense[4],  # status
                    expense[5],  # implementation_date
                    expense[6],  # payment_scheduled_date
                    expense[7],  # notes
                ))

            conn.commit()
            log_message(f"制作物複製完了: 元ID={production_id}, 新ID={new_production_id}, 費用項目={len(expenses)}件")
            return new_production_id

        except Exception as e:
            conn.rollback()
            log_message(f"制作物複製エラー: {e}")
            raise
        finally:
            conn.close()

    def get_production_cast(self, production_id: int) -> List[Tuple]:
        """制作物の出演者一覧を取得

        Returns:
            List[Tuple]: (id, production_id, cast_name, role)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT pc.id, pc.production_id, p.name as cast_name, pc.role
                FROM production_cast pc
                LEFT JOIN partners p ON pc.cast_id = p.id
                WHERE pc.production_id = ?
                ORDER BY p.name
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_production_cast(self, production_id: int, cast_list: List[dict]):
        """制作物の出演者を保存（既存データを全削除して再登録）

        Args:
            production_id: 制作物ID
            cast_list: 出演者リスト [{'cast_id': 1, 'role': '役割'}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 既存の出演者を全削除
            cursor.execute("DELETE FROM production_cast WHERE production_id = ?", (production_id,))

            # 新しい出演者を登録
            now = datetime.now()
            for cast in cast_list:
                cursor.execute("""
                    INSERT INTO production_cast (production_id, cast_id, role, created_at)
                    VALUES (?, ?, ?, ?)
                """, (production_id, cast['cast_id'], cast.get('role', ''), now))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_production_producers(self, production_id: int) -> List[Tuple]:
        """制作物の制作会社一覧を取得

        Returns:
            List[Tuple]: (production_producers.id, partner_id, partner_name, partner_code)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT pp.id, pp.partner_id, p.name, p.code
                FROM production_producers pp
                INNER JOIN partners p ON pp.partner_id = p.id
                WHERE pp.production_id = ?
                ORDER BY p.name
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_production_producers(self, production_id: int, partner_ids: List[int]):
        """制作物の制作会社を保存（既存データを全削除して再登録）

        Args:
            production_id: 制作物ID
            partner_ids: 取引先IDのリスト
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 既存の制作会社を全削除
            cursor.execute("DELETE FROM production_producers WHERE production_id = ?", (production_id,))

            # 新しい制作会社を登録
            now = datetime.now()
            for partner_id in partner_ids:
                cursor.execute("""
                    INSERT INTO production_producers (production_id, partner_id, created_at)
                    VALUES (?, ?, ?)
                """, (production_id, partner_id, now))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_production_cast_with_contracts(self, production_id: int) -> List[Tuple]:
        """番組の出演者と契約情報を取得（新テーブル: contracts）

        Args:
            production_id: 番組ID

        Returns:
            List[Tuple]: (production_cast_id, cast_id, cast_name, role, partner_id, partner_name,
                         contract_id, item_name, unit_price, document_status, payment_timing,
                         contract_start_date, contract_end_date)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    pc.id as production_cast_id,
                    c.id as cast_id,
                    c.name as cast_name,
                    pc.role,
                    p.id as partner_id,
                    p.name as partner_name,
                    oc.id as contract_id,
                    oc.item_name,
                    oc.unit_price,
                    oc.document_status,
                    oc.payment_timing,
                    oc.contract_start_date,
                    oc.contract_end_date
                FROM production_cast pc
                INNER JOIN cast c ON pc.cast_id = c.id
                INNER JOIN partners p ON c.partner_id = p.id
                LEFT JOIN contracts oc ON
                    oc.production_id = pc.production_id
                    AND oc.partner_id = p.id
                    AND oc.work_type = '出演'
                LEFT JOIN contract_cast cc ON
                    cc.contract_id = oc.id
                    AND cc.cast_id = c.id
                WHERE pc.production_id = ?
                  AND (oc.id IS NULL OR cc.id IS NOT NULL)
                ORDER BY c.name, oc.item_name
            """, (production_id,))

            return cursor.fetchall()
        finally:
            conn.close()

    def get_production_producers_with_contracts(self, production_id: int) -> List[Tuple]:
        """番組の制作会社と契約情報を取得

        Args:
            production_id: 番組ID

        Returns:
            List[Tuple]: (production_producer_id, partner_id, partner_name,
                         contract_id, item_name, unit_price, document_status, payment_timing,
                         contract_start_date, contract_end_date)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    pp.id as production_producer_id,
                    p.id as partner_id,
                    p.name as partner_name,
                    oc.id as contract_id,
                    oc.item_name,
                    oc.unit_price,
                    oc.document_status,
                    oc.payment_timing,
                    oc.contract_start_date,
                    oc.contract_end_date
                FROM production_producers pp
                INNER JOIN partners p ON pp.partner_id = p.id
                LEFT JOIN contracts oc ON
                    oc.production_id = pp.production_id
                    AND oc.partner_id = p.id
                WHERE pp.production_id = ?
                ORDER BY p.name, oc.item_name
            """, (production_id,))

            return cursor.fetchall()
        finally:
            conn.close()

    def get_contracts_by_production_and_partner(self, production_id: int, partner_id: int) -> List[Tuple]:
        """特定の番組と取引先の組み合わせで契約を取得

        Args:
            production_id: 番組ID
            partner_id: 取引先ID

        Returns:
            List[Tuple]: (contract_id, item_name, unit_price, document_status, payment_timing)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id, item_name, unit_price, document_status, payment_timing
                FROM contracts
                WHERE production_id = ? AND partner_id = ?
                ORDER BY item_name
            """, (production_id, partner_id))

            return cursor.fetchall()
        finally:
            conn.close()

    def delete_cast_from_production(self, production_cast_id: int, production_id: int, partner_id: int):
        """出演者を番組から削除（関連契約も削除）

        Args:
            production_cast_id: production_castのID
            production_id: 番組ID
            partner_id: 取引先ID（出演者の事務所）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # トランザクション開始
            # 1. production_castから削除
            cursor.execute("DELETE FROM production_cast WHERE id = ?", (production_cast_id,))

            # 2. 関連する契約を削除
            cursor.execute("""
                DELETE FROM contracts
                WHERE production_id = ? AND partner_id = ?
            """, (production_id, partner_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            log_message(f"出演者削除エラー: {e}")
            raise e
        finally:
            conn.close()

    def delete_producer_from_production(self, production_producer_id: int, production_id: int, partner_id: int):
        """制作会社を番組から削除（関連契約も削除）

        Args:
            production_producer_id: production_producersのID
            production_id: 番組ID
            partner_id: 取引先ID（制作会社）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # トランザクション開始
            # 1. production_producersから削除
            cursor.execute("DELETE FROM production_producers WHERE id = ?", (production_producer_id,))

            # 2. 関連する契約を削除
            cursor.execute("""
                DELETE FROM contracts
                WHERE production_id = ? AND partner_id = ?
            """, (production_id, partner_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            log_message(f"制作会社削除エラー: {e}")
            raise e
        finally:
            conn.close()

    def import_productions_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """CSVデータから番組・イベントをインポート

        Args:
            csv_data: CSVから読み込んだデータのリスト（辞書形式）
            overwrite: Trueの場合は既存データを削除してから挿入

        Returns:
            dict: インポート結果 {'success': 成功件数, 'inserted': 新規追加件数,
                                  'updated': 更新件数, 'skipped': スキップ件数,
                                  'errors': エラーリスト}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        result = {
            'success': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                # 費用項目が関連付けられている番組は削除できないため、
                # 関連データがない番組のみ削除
                cursor.execute("""
                    DELETE FROM productions
                    WHERE id NOT IN (SELECT DISTINCT production_id FROM expense_items)
                """)

            for idx, row in enumerate(csv_data, start=2):  # CSVの2行目から（ヘッダー除く）
                try:
                    # 必須項目のチェック
                    if not row.get('制作物名'):
                        result['errors'].append({
                            'row': idx,
                            'reason': '制作物名が空です'
                        })
                        result['skipped'] += 1
                        continue

                    # IDがある場合は更新、ない場合は新規追加
                    production_id = row.get('ID')

                    # 日付フィールドのパース
                    start_date = parse_flexible_date(row.get('開始日', ''))
                    end_date = parse_flexible_date(row.get('終了日', ''))

                    # 親制作物IDの処理
                    parent_production_id = None
                    parent_id_str = row.get('親制作物ID', '').strip()
                    if parent_id_str and parent_id_str.isdigit():
                        parent_production_id = int(parent_id_str)

                    production_data = {
                        'name': row.get('制作物名', '').strip(),
                        'description': row.get('説明', '').strip(),
                        'production_type': row.get('制作物種別', 'レギュラー番組').strip(),
                        'start_date': start_date,
                        'end_date': end_date,
                        'start_time': row.get('実施開始時間', '').strip() or None,
                        'end_time': row.get('実施終了時間', '').strip() or None,
                        'broadcast_time': row.get('放送時間', '').strip() or None,
                        'broadcast_days': row.get('放送曜日', '').strip() or None,
                        'status': row.get('ステータス', '放送中').strip(),
                        'parent_production_id': parent_production_id
                    }

                    now = datetime.now()

                    if production_id and str(production_id).strip().isdigit():
                        # 更新モード
                        production_data['id'] = int(production_id)

                        # 既存データが存在するか確認
                        cursor.execute("SELECT id FROM productions WHERE id = ?", (production_data['id'],))
                        if cursor.fetchone():
                            # 更新
                            cursor.execute("""
                                UPDATE productions SET
                                    name = ?,
                                    description = ?,
                                    production_type = ?,
                                    start_date = ?,
                                    end_date = ?,
                                    start_time = ?,
                                    end_time = ?,
                                    broadcast_time = ?,
                                    broadcast_days = ?,
                                    status = ?,
                                    parent_production_id = ?,
                                    updated_at = ?
                                WHERE id = ?
                            """, (
                                production_data['name'],
                                production_data['description'],
                                production_data['production_type'],
                                production_data['start_date'],
                                production_data['end_date'],
                                production_data['start_time'],
                                production_data['end_time'],
                                production_data['broadcast_time'],
                                production_data['broadcast_days'],
                                production_data['status'],
                                production_data['parent_production_id'],
                                now,
                                production_data['id']
                            ))
                            result['updated'] += 1
                            result['success'] += 1
                        else:
                            # IDが指定されているが存在しない場合は新規追加
                            cursor.execute("""
                                INSERT INTO productions (
                                    name, description, production_type, start_date, end_date,
                                    start_time, end_time, broadcast_time, broadcast_days, status,
                                    parent_production_id, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                production_data['name'],
                                production_data['description'],
                                production_data['production_type'],
                                production_data['start_date'],
                                production_data['end_date'],
                                production_data['start_time'],
                                production_data['end_time'],
                                production_data['broadcast_time'],
                                production_data['broadcast_days'],
                                production_data['status'],
                                production_data['parent_production_id'],
                                now,
                                now
                            ))
                            result['inserted'] += 1
                            result['success'] += 1
                    else:
                        # 新規追加モード
                        cursor.execute("""
                            INSERT INTO productions (
                                name, description, production_type, start_date, end_date,
                                start_time, end_time, broadcast_time, broadcast_days, status,
                                parent_production_id, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            production_data['name'],
                            production_data['description'],
                            production_data['production_type'],
                            production_data['start_date'],
                            production_data['end_date'],
                            production_data['start_time'],
                            production_data['end_time'],
                            production_data['broadcast_time'],
                            production_data['broadcast_days'],
                            production_data['status'],
                            production_data['parent_production_id'],
                            now,
                            now
                        ))
                        result['inserted'] += 1
                        result['success'] += 1

                except Exception as e:
                    result['errors'].append({
                        'row': idx,
                        'reason': str(e)
                    })
                    result['skipped'] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    # ========================================
    # 出演者マスター操作
    # ========================================

    def get_casts(self, search_term: str = "") -> List[Tuple]:
        """出演者マスター一覧を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT c.id, c.name, p.name, p.code, c.notes
                FROM cast c LEFT JOIN partners p ON c.partner_id = p.id WHERE 1=1
            """
            params = []
            if search_term:
                query += " AND (c.name LIKE ? OR p.name LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            query += " ORDER BY c.name"
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_cast_by_id(self, cast_id: int) -> Optional[Tuple]:
        """IDで出演者を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, partner_id, notes, created_at, updated_at FROM cast WHERE id = ?", (cast_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_cast(self, cast_data: dict, is_new: bool = True):
        """出演者を保存"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            if is_new:
                cursor.execute("INSERT INTO cast (name, partner_id, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                              (cast_data['name'], cast_data['partner_id'], cast_data.get('notes', ''), now, now))
                cast_id = cursor.lastrowid
            else:
                cursor.execute("UPDATE cast SET name=?, partner_id=?, notes=?, updated_at=? WHERE id=?",
                              (cast_data['name'], cast_data['partner_id'], cast_data.get('notes', ''), now, cast_data['id']))
                cast_id = cast_data['id']
            conn.commit()
            return cast_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_cast(self, cast_id: int):
        """出演者を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM production_cast WHERE cast_id = ?", (cast_id,))
            if cursor.fetchone()[0] > 0:
                raise Exception("この出演者は制作物に関連付けられています。削除できません。")
            cursor.execute("DELETE FROM cast WHERE id = ?", (cast_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_production_cast_v2(self, production_id: int) -> List[Tuple]:
        """制作物の出演者一覧を取得（castテーブル経由）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT pc.id, c.id, c.name, p.name, pc.role
                FROM production_cast pc
                INNER JOIN cast c ON pc.cast_id = c.id
                INNER JOIN partners p ON c.partner_id = p.id
                WHERE pc.production_id = ? ORDER BY c.name
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_production_cast_v2(self, production_id: int, cast_assignments: List[dict]):
        """制作物の出演者を保存（castテーブル経由）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM production_cast WHERE production_id = ?", (production_id,))
            now = datetime.now()
            for assignment in cast_assignments:
                cursor.execute("INSERT INTO production_cast (production_id, cast_id, role, created_at) VALUES (?, ?, ?, ?)",
                              (production_id, assignment['cast_id'], assignment.get('role', ''), now))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ========================================
    # 発注書マスター操作
    # ========================================

    def get_order_contracts(self, search_term: str = "", pdf_status: str = None, order_type: str = None, order_status: str = None) -> List[Tuple]:
        """発注書一覧を取得

        Args:
            search_term: 検索キーワード（取引先名、制作物名）
            pdf_status: PDFステータスフィルタ
            order_type: 発注種別フィルタ（契約書/発注書/メール発注）
            order_status: 発注ステータスフィルタ（未/済）

        Returns:
            List[Tuple]: (0:id, 1:production_id, 2:program_name, 3:partner_id, 4:partner_name,
                         5:contract_start_date, 6:contract_end_date, 7:contract_period_type,
                         8:pdf_status, 9:pdf_distributed_date, 10:pdf_file_path, 11:notes,
                         12:order_type, 13:order_status, 14:email_sent_date,
                         15:project_name, 16:item_name, 17:payment_type, 18:unit_price,
                         19:payment_timing, 20:contract_type, 21:implementation_date,
                         22:spot_amount, 23:order_category, 24:email_subject, 25:email_body,
                         26:email_to, 27:auto_renewal_enabled, 28:renewal_period_months,
                         29:termination_notice_date, 30:renewal_count, 31:work_type)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT oc.id, oc.production_id, prod.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes,
                       COALESCE(oc.document_type, '発注書') as document_type,
                       COALESCE(oc.document_status, '未') as document_status,
                       oc.email_sent_date,
                       prod.name as project_name,
                       oc.item_name,
                       COALESCE(oc.payment_type, '月額固定') as payment_type,
                       oc.unit_price,
                       COALESCE(oc.payment_timing, '翌月末払い') as payment_timing,
                       COALESCE(oc.contract_type, 'regular_fixed') as contract_type,
                       oc.implementation_date,
                       oc.spot_amount,
                       COALESCE(oc.order_category, 'レギュラー制作発注書') as order_category,
                       oc.email_subject,
                       oc.email_body,
                       oc.email_to,
                       COALESCE(oc.auto_renewal_enabled, 1) as auto_renewal_enabled,
                       COALESCE(oc.renewal_period_months, 3) as renewal_period_months,
                       oc.termination_notice_date,
                       COALESCE(oc.renewal_count, 0) as renewal_count,
                       COALESCE(oc.work_type, '制作') as work_type
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND (prod.name LIKE ? OR p.name LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])

            if pdf_status:
                query += " AND oc.pdf_status = ?"
                params.append(pdf_status)

            if order_type:
                query += " AND COALESCE(oc.document_type, '発注書') = ?"
                params.append(order_type)

            if order_status:
                query += " AND COALESCE(oc.document_status, '未') = ?"
                params.append(order_status)

            query += " ORDER BY oc.contract_end_date DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_order_contract_by_id(self, contract_id: int) -> Optional[Tuple]:
        """IDで発注書を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT oc.id, oc.production_id, prod.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes,
                       oc.created_at, oc.updated_at,
                       COALESCE(oc.document_type, '発注書') as document_type,
                       COALESCE(oc.document_status, '未完了') as document_status,
                       oc.email_sent_date,
                       COALESCE(oc.payment_type, '月額固定') as payment_type,
                       oc.unit_price,
                       COALESCE(oc.payment_timing, '翌月末払い') as payment_timing,
                       oc.project_id, proj.name as project_name,
                       oc.item_name,
                       COALESCE(oc.contract_type, 'regular_fixed') as contract_type,
                       COALESCE(oc.project_name_type, 'program') as project_name_type,
                       oc.implementation_date,
                       oc.spot_amount,
                       COALESCE(oc.order_category, 'レギュラー制作発注書') as order_category,
                       oc.email_subject,
                       oc.email_body,
                       oc.email_to,
                       COALESCE(oc.auto_renewal_enabled, 1) as auto_renewal_enabled,
                       COALESCE(oc.renewal_period_months, 3) as renewal_period_months,
                       oc.termination_notice_date,
                       oc.last_renewal_date,
                       COALESCE(oc.renewal_count, 0) as renewal_count,
                       COALESCE(oc.work_type, '制作') as work_type,
                       COALESCE(oc.amount_pending, 0) as amount_pending
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN productions proj ON oc.project_id = proj.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.id = ?
            """, (contract_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def check_duplicate_contract(self, production_id: int, partner_id: int, work_type: str,
                                  exclude_contract_id: int = None, cast_ids: list = None) -> Optional[Tuple]:
        """重複契約をチェック

        番組ID、取引先ID、業務種別が同じ契約が既に存在するかチェックします。
        出演契約の場合、出演者IDも含めて重複判定を行います。

        Args:
            production_id: 番組ID
            partner_id: 取引先ID
            work_type: 業務種別（制作/出演）
            exclude_contract_id: 除外する契約ID（編集時に自分自身を除外）
            cast_ids: 出演者IDのリスト（出演契約の場合のみ）

        Returns:
            重複する契約が存在する場合は契約データ、存在しない場合はNone
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 出演契約の場合、出演者も含めて重複判定
            if work_type == '出演' and cast_ids:
                # 出演者IDでソート（順序に関係なく同じ出演者グループを判定）
                sorted_cast_ids = sorted(cast_ids)

                # 同じ番組・取引先・業務種別の契約を検索
                if exclude_contract_id:
                    cursor.execute("""
                        SELECT
                            c.id,
                            prod.name as production_name,
                            part.name as partner_name,
                            c.work_type,
                            c.contract_start_date,
                            c.contract_end_date,
                            c.unit_price,
                            c.spot_amount,
                            c.item_name
                        FROM contracts c
                        LEFT JOIN productions prod ON c.production_id = prod.id
                        LEFT JOIN partners part ON c.partner_id = part.id
                        WHERE c.production_id = ?
                          AND c.partner_id = ?
                          AND c.work_type = ?
                          AND c.id != ?
                    """, (production_id, partner_id, work_type, exclude_contract_id))
                else:
                    cursor.execute("""
                        SELECT
                            c.id,
                            prod.name as production_name,
                            part.name as partner_name,
                            c.work_type,
                            c.contract_start_date,
                            c.contract_end_date,
                            c.unit_price,
                            c.spot_amount,
                            c.item_name
                        FROM contracts c
                        LEFT JOIN productions prod ON c.production_id = prod.id
                        LEFT JOIN partners part ON c.partner_id = part.id
                        WHERE c.production_id = ?
                          AND c.partner_id = ?
                          AND c.work_type = ?
                    """, (production_id, partner_id, work_type))

                # 候補契約をすべて取得して、出演者が完全一致するものを探す
                candidates = cursor.fetchall()
                for candidate in candidates:
                    candidate_id = candidate[0]
                    # この契約の出演者を取得
                    cursor.execute("""
                        SELECT cast_id FROM contract_cast
                        WHERE contract_id = ?
                        ORDER BY cast_id
                    """, (candidate_id,))
                    existing_cast_ids = sorted([row[0] for row in cursor.fetchall()])

                    # 出演者が完全一致する場合は重複
                    if existing_cast_ids == sorted_cast_ids:
                        return candidate

                # 出演者が異なる場合は重複ではない
                return None

            else:
                # 制作契約の場合、または出演契約でもcast_idsがない場合は従来通り
                if exclude_contract_id:
                    cursor.execute("""
                        SELECT
                            c.id,
                            prod.name as production_name,
                            part.name as partner_name,
                            c.work_type,
                            c.contract_start_date,
                            c.contract_end_date,
                            c.unit_price,
                            c.spot_amount,
                            c.item_name
                        FROM contracts c
                        LEFT JOIN productions prod ON c.production_id = prod.id
                        LEFT JOIN partners part ON c.partner_id = part.id
                        WHERE c.production_id = ?
                          AND c.partner_id = ?
                          AND c.work_type = ?
                          AND c.id != ?
                        LIMIT 1
                    """, (production_id, partner_id, work_type, exclude_contract_id))
                else:
                    cursor.execute("""
                        SELECT
                            c.id,
                            prod.name as production_name,
                            part.name as partner_name,
                            c.work_type,
                            c.contract_start_date,
                            c.contract_end_date,
                            c.unit_price,
                            c.spot_amount,
                            c.item_name
                        FROM contracts c
                        LEFT JOIN productions prod ON c.production_id = prod.id
                        LEFT JOIN partners part ON c.partner_id = part.id
                        WHERE c.production_id = ?
                          AND c.partner_id = ?
                          AND c.work_type = ?
                        LIMIT 1
                    """, (production_id, partner_id, work_type))

                return cursor.fetchone()
        finally:
            conn.close()

    def get_order_contracts_by_production(self, production_id: int) -> List[Tuple]:
        """制作物IDで発注書を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT oc.id, oc.production_id, prod.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.production_id = ?
                ORDER BY oc.contract_start_date DESC
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_order_contract(self, contract_data: dict) -> int:
        """契約を保存（新テーブル: contracts）

        Args:
            contract_data: 契約データ
                - id: 契約ID（更新時のみ）
                - production_id: 制作物ID
                - partner_id: 取引先ID
                - work_type: 業務種別（制作/出演）
                - item_name: 契約項目名
                - contract_start_date: 契約開始日
                - contract_end_date: 契約終了日
                - contract_period_type: 契約期間種別
                - payment_type: 支払タイプ
                - unit_price: 単価
                - spot_amount: 単発金額
                - payment_timing: 支払タイミング
                - document_type: 書類種別（契約書/発注書/発注メール）
                - document_status: 書類ステータス
                - auto_renewal_enabled: 自動延長有効フラグ
                - notes: 備考

        Returns:
            int: 契約ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            contract_id = contract_data.get('id')
            now = datetime.now()

            if contract_id:
                # 更新
                cursor.execute("""
                    UPDATE contracts SET
                        production_id = ?,
                        project_id = ?,
                        partner_id = ?,
                        work_type = ?,
                        item_name = ?,
                        contract_type = ?,
                        contract_start_date = ?,
                        contract_end_date = ?,
                        contract_period_type = ?,
                        payment_type = ?,
                        unit_price = ?,
                        spot_amount = ?,
                        payment_timing = ?,
                        document_type = ?,
                        document_status = ?,
                        pdf_file_path = ?,
                        email_to = ?,
                        email_subject = ?,
                        email_body = ?,
                        email_sent_date = ?,
                        auto_renewal_enabled = ?,
                        renewal_period_months = ?,
                        termination_notice_date = ?,
                        amount_pending = ?,
                        notes = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    contract_data.get('production_id'),
                    contract_data.get('project_id'),
                    contract_data['partner_id'],
                    contract_data.get('work_type', '制作'),
                    contract_data.get('item_name'),
                    contract_data.get('contract_type', 'regular_fixed'),
                    contract_data.get('contract_start_date', ''),
                    contract_data.get('contract_end_date', ''),
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('payment_type', '月額固定'),
                    contract_data.get('unit_price'),
                    contract_data.get('spot_amount'),
                    contract_data.get('payment_timing', '翌月末払い'),
                    contract_data.get('order_type', '発注書'),  # document_type
                    contract_data.get('order_status', '未'),  # document_status
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('email_to', ''),
                    contract_data.get('email_subject', ''),
                    contract_data.get('email_body', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('auto_renewal_enabled', 1),
                    contract_data.get('renewal_period_months', 3),
                    contract_data.get('termination_notice_date'),
                    contract_data.get('amount_pending', 0),
                    contract_data.get('notes', ''),
                    now,
                    contract_id
                ))
            else:
                # 新規追加
                cursor.execute("""
                    INSERT INTO contracts (
                        production_id, project_id, partner_id, work_type,
                        item_name, contract_type,
                        contract_start_date, contract_end_date, contract_period_type,
                        payment_type, unit_price, spot_amount, payment_timing,
                        document_type, document_status, pdf_file_path,
                        email_to, email_subject, email_body, email_sent_date,
                        auto_renewal_enabled, renewal_period_months, termination_notice_date,
                        amount_pending, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_data.get('production_id'),
                    contract_data.get('project_id'),
                    contract_data['partner_id'],
                    contract_data.get('work_type', '制作'),
                    contract_data.get('item_name'),
                    contract_data.get('contract_type', 'regular_fixed'),
                    contract_data.get('contract_start_date', ''),
                    contract_data.get('contract_end_date', ''),
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('payment_type', '月額固定'),
                    contract_data.get('unit_price'),
                    contract_data.get('spot_amount'),
                    contract_data.get('payment_timing', '翌月末払い'),
                    contract_data.get('order_type', '発注書'),  # document_type
                    contract_data.get('order_status', '未'),  # document_status
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('email_to', ''),
                    contract_data.get('email_subject', ''),
                    contract_data.get('email_body', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('auto_renewal_enabled', 1),
                    contract_data.get('renewal_period_months', 3),
                    contract_data.get('termination_notice_date'),
                    contract_data.get('amount_pending', 0),
                    contract_data.get('notes', ''),
                    now,
                    now
                ))
                contract_id = cursor.lastrowid

            conn.commit()
            return contract_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_order_contract(self, contract_id: int):
        """契約を削除（新テーブル: contracts）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_pdf_status(self, contract_id: int, pdf_status: str,
                         distributed_date: str = None):
        """PDF配布ステータスを更新（廃止予定）"""
        # 新テーブルではdocument_statusを使用
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now()
            cursor.execute("""
                UPDATE contracts SET
                    document_status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (pdf_status, now, contract_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def sync_contract_to_program(self, contract_id: int) -> bool:
        """契約の委託期間を番組マスタに同期"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 契約情報を取得
            cursor.execute("""
                SELECT production_id, contract_start_date, contract_end_date
                FROM contracts WHERE id = ?
            """, (contract_id,))

            row = cursor.fetchone()
            if not row:
                return False

            production_id, start_date, end_date = row

            # 番組マスタを更新
            now = datetime.now()
            cursor.execute("""
                UPDATE productions SET
                    start_date = ?,
                    end_date = ?,
                    updated_at = ?
                WHERE id = ?
            """, (start_date, end_date, now, production_id))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_expiring_contracts(self, days_before: int = 30) -> List[Tuple]:
        """期限切れ間近の発注書を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT oc.id, oc.production_id, prod.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE DATE(oc.contract_end_date) BETWEEN DATE('now')
                      AND DATE('now', '+' || ? || ' days')
                ORDER BY oc.contract_end_date ASC
            """, (days_before,))
            return cursor.fetchall()
        finally:
            conn.close()

    # ========================================
    # 発注・支払照合機能
    # ========================================

    def generate_monthly_payment_list(self, year: int, month: int) -> List[dict]:
        """指定月の発注から支払予定リストを生成

        Args:
            year: 年（例: 2024）
            month: 月（例: 10）

        Returns:
            List[dict]: 取引先ごとの支払予定情報
            [
                {
                    'partner_id': 取引先ID,
                    'partner_name': 取引先名,
                    'partner_code': 取引先コード,
                    'orders': [
                        {
                            'order_id': 発注ID,
                            'order_number': 発注番号,
                            'project_name': 制作物名,
                            'item_name': 項目名,
                            'amount': 金額,
                            'expected_payment_date': 支払予定日,
                            'payment_status': 支払ステータス,
                            'order_type': 発注種別（契約から取得）
                        },
                        ...
                    ],
                    'total_amount': 合計金額
                },
                ...
            ]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 指定月の支払予定がある発注を取得
            # expected_payment_dateがYYYY-MM形式で指定月と一致するもの
            target_month = f"{year:04d}-{month:02d}"

            cursor.execute("""
                SELECT
                    ei.id,
                    ei.order_number,
                    ei.production_id,
                    p.name as project_name,
                    p.broadcast_days,
                    ei.item_name,
                    ei.partner_id,
                    ei.expected_payment_amount,
                    ei.expected_payment_date,
                    ei.payment_status,
                    ei.payment_matched_id,
                    ei.payment_difference,
                    COALESCE(c.document_type, '発注書') as document_type,
                    COALESCE(c.payment_type, '月額固定') as payment_type,
                    c.unit_price,
                    COALESCE(c.payment_timing, '翌月末払い') as payment_timing
                FROM expense_items ei
                LEFT JOIN productions p ON ei.production_id = p.id
                LEFT JOIN contracts c ON (
                    ei.production_id = c.production_id AND ei.item_name = c.item_name
                ) AND ei.partner_id = c.partner_id
                WHERE strftime('%Y-%m', ei.expected_payment_date) = ?
                ORDER BY ei.partner_id, ei.expected_payment_date
            """, (target_month,))

            orders = cursor.fetchall()

            # 取引先ごとにグループ化
            partners_dict = {}

            for order in orders:
                (order_id, order_number, production_id, project_name, broadcast_days, item_name,
                 supplier_id, amount, payment_date, payment_status,
                 payment_matched_id, payment_difference, order_type,
                 payment_type, unit_price, payment_timing) = order

                if supplier_id is None:
                    continue  # 取引先が設定されていない発注はスキップ

                # 取引先情報を取得（初回のみ）
                if supplier_id not in partners_dict:
                    # partnersテーブルから取引先情報を取得
                    cursor.execute("""
                        SELECT id, name, code
                        FROM partners
                        WHERE id = ?
                    """, (supplier_id,))
                    partner_info = cursor.fetchone()

                    if partner_info:
                        partner_id, partner_name, partner_code = partner_info
                        partners_dict[supplier_id] = {
                            'partner_id': partner_id,
                            'partner_name': partner_name,
                            'partner_code': partner_code or '',
                            'orders': [],
                            'total_amount': 0
                        }

                # 計算内訳を生成
                calculation_detail = ""
                if payment_type == "回数ベース" and broadcast_days and unit_price:
                    # 放送回数を計算
                    from order_management.broadcast_utils import calculate_monthly_broadcast_count
                    try:
                        # payment_dateから年月を抽出
                        payment_year = int(payment_date[:4])
                        payment_month = int(payment_date[5:7])
                        broadcast_count = calculate_monthly_broadcast_count(
                            payment_year, payment_month, broadcast_days
                        )
                        calculation_detail = f"{broadcast_count}回 × {int(unit_price):,}円"
                    except:
                        calculation_detail = "計算エラー"
                elif payment_type == "月額固定":
                    calculation_detail = "月額固定"
                else:
                    calculation_detail = "-"

                # 発注情報を追加
                if supplier_id in partners_dict:
                    partners_dict[supplier_id]['orders'].append({
                        'order_id': order_id,
                        'order_number': order_number or '',
                        'project_name': project_name or '',
                        'item_name': item_name or '',
                        'amount': amount or 0,
                        'expected_payment_date': payment_date or '',
                        'payment_status': payment_status or '未払い',
                        'payment_matched_id': payment_matched_id,
                        'payment_difference': payment_difference or 0,
                        'order_type': order_type or '発注書',
                        'payment_type': payment_type or '月額固定',
                        'unit_price': unit_price,
                        'payment_timing': payment_timing or '翌月末払い',
                        'calculation_detail': calculation_detail
                    })
                    partners_dict[supplier_id]['total_amount'] += (amount or 0)

            # リストに変換して返す
            result = list(partners_dict.values())

            # 取引先名でソート
            result.sort(key=lambda x: x['partner_name'])

            return result

        finally:
            conn.close()

    def get_payment_summary(self, year: int, month: int) -> dict:
        """指定月の支払サマリーを取得

        Args:
            year: 年
            month: 月

        Returns:
            dict: サマリー情報
            {
                'total_orders': 発注件数,
                'total_amount': 発注総額,
                'paid_count': 支払済件数,
                'paid_amount': 支払済金額,
                'unpaid_count': 未払い件数,
                'unpaid_amount': 未払い金額,
                'mismatch_count': 金額相違件数,
                'mismatch_amount': 金額相違合計
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            target_month = f"{year:04d}-{month:02d}"

            # 全体統計
            cursor.execute("""
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(expected_payment_amount), 0) as total_amount
                FROM expense_items
                WHERE strftime('%Y-%m', expected_payment_date) = ?
            """, (target_month,))

            total_orders, total_amount = cursor.fetchone()

            # 支払済
            cursor.execute("""
                SELECT
                    COUNT(*) as paid_count,
                    COALESCE(SUM(expected_payment_amount), 0) as paid_amount
                FROM expense_items
                WHERE strftime('%Y-%m', expected_payment_date) = ?
                  AND payment_status = '支払済'
            """, (target_month,))

            paid_count, paid_amount = cursor.fetchone()

            # 未払い
            cursor.execute("""
                SELECT
                    COUNT(*) as unpaid_count,
                    COALESCE(SUM(expected_payment_amount), 0) as unpaid_amount
                FROM expense_items
                WHERE strftime('%Y-%m', expected_payment_date) = ?
                  AND payment_status = '未払い'
            """, (target_month,))

            unpaid_count, unpaid_amount = cursor.fetchone()

            # 金額相違
            cursor.execute("""
                SELECT
                    COUNT(*) as mismatch_count,
                    COALESCE(SUM(ABS(payment_difference)), 0) as mismatch_amount
                FROM expense_items
                WHERE strftime('%Y-%m', expected_payment_date) = ?
                  AND payment_status = '金額相違'
            """, (target_month,))

            mismatch_count, mismatch_amount = cursor.fetchone()

            return {
                'total_orders': total_orders or 0,
                'total_amount': total_amount or 0,
                'paid_count': paid_count or 0,
                'paid_amount': paid_amount or 0,
                'unpaid_count': unpaid_count or 0,
                'unpaid_amount': unpaid_amount or 0,
                'mismatch_count': mismatch_count or 0,
                'mismatch_amount': mismatch_amount or 0
            }

        finally:
            conn.close()

    # ========================================
    # データベーススキーマ拡張
    # ========================================

    def migrate_add_auto_renewal_fields(self) -> bool:
        """契約自動延長機能のためのカラムとテーブルを追加

        実行内容:
        1. order_contractsテーブルに自動延長関連カラムを追加
        2. contract_renewal_historyテーブルを作成

        Returns:
            bool: マイグレーション成功時True
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # order_contractsテーブルの拡張
            cursor.execute("PRAGMA table_info(order_contracts)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'auto_renewal_enabled' not in columns:
                log_message("order_contractsテーブルに自動延長関連カラムを追加")

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN auto_renewal_enabled INTEGER DEFAULT 1
                """)

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN renewal_period_months INTEGER DEFAULT 3
                """)

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN termination_notice_date DATE
                """)

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN last_renewal_date DATE
                """)

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN renewal_count INTEGER DEFAULT 0
                """)

            # 契約延長履歴テーブルの作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contract_renewal_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER NOT NULL,
                    previous_end_date DATE NOT NULL,
                    new_end_date DATE NOT NULL,
                    renewal_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    renewal_reason TEXT,
                    executed_by TEXT,
                    notes TEXT,
                    FOREIGN KEY (contract_id) REFERENCES order_contracts(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            log_message("契約自動延長機能のマイグレーションが完了しました")
            return True

        except Exception as e:
            conn.rollback()
            log_message(f"マイグレーションエラー: {e}")
            return False
        finally:
            conn.close()

    def migrate_to_hierarchy_structure(self) -> bool:
        """データベーススキーマを階層構造対応に拡張

        実行内容:
        1. programsテーブルに production_type, parent_production_id を追加
        2. projectsテーブルに project_type を追加
        3. 既存データにデフォルト値を設定

        Returns:
            bool: マイグレーション成功時True
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # programsテーブルの拡張
            # program_typeカラムが存在するか確認
            cursor.execute("PRAGMA table_info(programs)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'production_type' not in columns:
                log_message("programsテーブルにprogram_typeカラムを追加")
                cursor.execute("""
                    ALTER TABLE programs
                    ADD COLUMN production_type TEXT DEFAULT 'レギュラー'
                """)

                # 既存データにデフォルト値を設定
                cursor.execute("""
                    UPDATE productions
                    SET production_type = 'レギュラー'
                    WHERE production_type IS NULL
                """)

            if 'parent_production_id' not in columns:
                log_message("programsテーブルにparent_program_idカラムを追加")
                cursor.execute("""
                    ALTER TABLE programs
                    ADD COLUMN parent_production_id INTEGER REFERENCES programs(id)
                """)

            # projectsテーブルの拡張
            cursor.execute("PRAGMA table_info(projects)")
            project_columns = [col[1] for col in cursor.fetchall()]

            if 'project_type' not in project_columns:
                log_message("projectsテーブルにproject_typeカラムを追加")
                cursor.execute("""
                    ALTER TABLE projects
                    ADD COLUMN project_type TEXT DEFAULT 'イベント'
                """)

                # 既存のtypeフィールドの値をproject_typeに移行
                cursor.execute("""
                    UPDATE productions
                    SET project_type = CASE
                        WHEN type = 'レギュラー' THEN '通常'
                        WHEN type = '単発' THEN 'イベント'
                        ELSE 'イベント'
                    END
                    WHERE project_type IS NULL OR project_type = ''
                """)

            conn.commit()
            log_message("階層構造対応のマイグレーションが完了しました")
            return True

        except Exception as e:
            conn.rollback()
            log_message(f"マイグレーションエラー: {e}")
            return False
        finally:
            conn.close()

    # ========================================
    # 番組階層関連の操作
    # ========================================

    def get_productions_with_hierarchy(self, search_term: str = "",
                                    production_type: str = "",
                                    include_children: bool = True) -> List[Tuple]:
        """制作物一覧を階層情報付きで取得

        Args:
            search_term: 検索キーワード
            production_type: 制作物種別フィルタ（'レギュラー番組'/'特別番組'等）
            include_children: 子制作物を含めるか

        Returns:
            List[Tuple]: (id, name, description, production_type, start_date, end_date,
                         start_time, end_time, broadcast_time, broadcast_days, status,
                         parent_production_id, parent_name)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT p.id, p.name, p.description, p.production_type, p.start_date, p.end_date,
                       p.start_time, p.end_time, p.broadcast_time, p.broadcast_days, p.status,
                       p.parent_production_id,
                       parent.name as parent_name
                FROM productions p
                LEFT JOIN productions parent ON p.parent_production_id = parent.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND p.name LIKE ?"
                params.append(f"%{search_term}%")

            if production_type:
                query += " AND p.production_type = ?"
                params.append(production_type)

            if not include_children:
                query += " AND p.parent_production_id IS NULL"

            query += " ORDER BY p.parent_production_id NULLS FIRST, p.name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_production_children(self, parent_production_id: int) -> List[Tuple]:
        """指定制作物の子制作物一覧を取得

        Args:
            parent_production_id: 親制作物ID

        Returns:
            List[Tuple]: (id, name, description, production_type, start_date, end_date,
                         start_time, end_time, broadcast_time, broadcast_days, status)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, production_type, start_date, end_date,
                       start_time, end_time, broadcast_time, broadcast_days, status
                FROM productions
                WHERE parent_production_id = ?
                ORDER BY name
            """, (parent_production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    # ========================================
    # 制作物関連の拡張操作
    # ========================================

    def get_productions_by_parent(self, parent_production_id: int = None,
                                production_type: str = "") -> List[Tuple]:
        """指定制作物に紐づく子制作物一覧を取得

        Args:
            parent_production_id: 親制作物ID（Noneの場合はトップレベルを取得）
            production_type: 制作物種別フィルタ（'イベント'/'特別企画'/'通常'など）

        Returns:
            List[Tuple]: (id, name, start_date, production_type,
                         parent_production_id)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if parent_production_id is None:
                # 親IDがNullの制作物（トップレベル）を取得
                query = """
                    SELECT id, name, start_date,
                           COALESCE(production_type, 'イベント') as production_type,
                           parent_production_id
                    FROM productions
                    WHERE parent_production_id IS NULL
                """
                params = []
            else:
                query = """
                    SELECT id, name, start_date,
                           COALESCE(production_type, 'イベント') as production_type,
                           parent_production_id
                    FROM productions
                    WHERE parent_production_id = ?
                """
                params = [parent_production_id]

            if production_type:
                query += " AND COALESCE(production_type, 'イベント') = ?"
                params.append(production_type)

            query += " ORDER BY start_date DESC, name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_projects_by_program(self, program_id: int,
                                project_type: str = "") -> List[Tuple]:
        """指定番組(親制作物)に紐づく案件(子制作物)一覧を取得

        このメソッドは後方互換性のために残されています。
        内部的には get_productions_by_parent を呼び出します。

        Args:
            program_id: 番組ID(親制作物ID)
            project_type: 案件種別フィルタ（'イベント'/'特別企画'/'通常'）

        Returns:
            List[Tuple]: (id, name, implementation_date, project_type,
                         parent_id, program_id, program_name)
        """
        # get_productions_by_parent を使用して子制作物を取得
        results = self.get_productions_by_parent(program_id, project_type)

        # 返り値の形式を調整（program_id と program_name を追加）
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 親制作物（番組）の名前を取得
            cursor.execute("SELECT name FROM productions WHERE id = ?", (program_id,))
            program_result = cursor.fetchone()
            program_name = program_result[0] if program_result else ""

            # 結果を変換（start_date → implementation_date）
            # (id, name, start_date, production_type, parent_production_id) →
            # (id, name, implementation_date, project_type, parent_id, program_id, program_name)
            formatted_results = []
            for row in results:
                formatted_results.append((
                    row[0],  # id
                    row[1],  # name
                    row[2],  # start_date → implementation_date
                    row[3],  # production_type → project_type
                    row[4],  # parent_production_id → parent_id
                    program_id,  # program_id
                    program_name  # program_name
                ))

            return formatted_results
        finally:
            conn.close()

    def get_order_contracts_with_production_info(self, search_term: str = "",
                                                  production_id: int = None) -> List[Tuple]:
        """発注書一覧を制作物情報付きで取得

        Args:
            search_term: 検索キーワード
            production_id: 制作物IDフィルタ

        Returns:
            List[Tuple]: (id, production_id, production_name,
                         partner_id, partner_name, item_name, contract_start_date,
                         contract_end_date, order_type, order_status, ...)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT oc.id, oc.production_id, prod.name as production_name,
                       oc.partner_id, part.name as partner_name,
                       oc.item_name, oc.contract_start_date, oc.contract_end_date,
                       oc.document_type, oc.document_status, oc.pdf_status,
                       oc.notes, oc.created_at, oc.updated_at,
                       oc.payment_type, oc.unit_price
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners part ON oc.partner_id = part.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += """ AND (prod.name LIKE ? OR part.name LIKE ? OR oc.item_name LIKE ?)"""
                params.extend([f"%{search_term}%"] * 3)

            if production_id:
                query += " AND oc.production_id = ?"
                params.append(production_id)

            query += " ORDER BY oc.contract_start_date DESC, prod.name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    # ========================================
    # CSV一括インポート機能
    # ========================================

    def import_casts_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """出演者データをCSVから一括インポート

        Args:
            csv_data: CSVから読み込んだ辞書のリスト
                     期待されるキー: ID, 出演者名, 所属事務所, 所属コード, 備考
            overwrite: True=上書き（既存データ削除）、False=追記/更新

        Returns:
            dict: {
                'success': 成功件数,
                'updated': 更新件数,
                'inserted': 挿入件数,
                'skipped': スキップ件数,
                'errors': [{'row': 行番号, 'reason': 理由}]
            }
        """
        result = {
            'success': 0,
            'updated': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': []
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                cursor.execute("DELETE FROM cast")
                conn.commit()
            for row_num, row_data in enumerate(csv_data, start=2):  # ヘッダー行は1行目なので2から開始
                try:
                    # 必須項目チェック
                    cast_name = row_data.get('出演者名', '').strip()
                    partner_name = row_data.get('所属事務所', '').strip()

                    if not cast_name:
                        result['errors'].append({'row': row_num, 'reason': '出演者名が空です'})
                        result['skipped'] += 1
                        continue

                    if not partner_name:
                        result['errors'].append({'row': row_num, 'reason': '所属事務所が空です'})
                        result['skipped'] += 1
                        continue

                    # 所属事務所を検索
                    cursor.execute("SELECT id FROM partners WHERE name = ?", (partner_name,))
                    partner_result = cursor.fetchone()

                    if not partner_result:
                        result['errors'].append({'row': row_num, 'reason': f'所属事務所「{partner_name}」が見つかりません'})
                        result['skipped'] += 1
                        continue

                    partner_id = partner_result[0]
                    notes = row_data.get('備考', '').strip()
                    cast_id_str = row_data.get('ID', '').strip()

                    now = datetime.now()

                    # UPSERTロジック: IDまたは出演者名+所属事務所で既存レコードを検索
                    existing_cast = None
                    if cast_id_str and cast_id_str.isdigit():
                        # IDが指定されている場合はIDで検索
                        cast_id = int(cast_id_str)
                        cursor.execute("SELECT id FROM cast WHERE id = ?", (cast_id,))
                        existing_cast = cursor.fetchone()
                    else:
                        # IDがない場合は出演者名+所属事務所で検索
                        cursor.execute("SELECT id FROM cast WHERE name = ? AND partner_id = ?",
                                     (cast_name, partner_id))
                        existing_cast = cursor.fetchone()

                    if existing_cast:
                        # 既存出演者を更新
                        existing_id = existing_cast[0]
                        cursor.execute("""
                            UPDATE cast
                            SET name=?, partner_id=?, notes=?, updated_at=?
                            WHERE id=?
                        """, (cast_name, partner_id, notes, now, existing_id))
                        result['updated'] += 1
                        result['success'] += 1
                    else:
                        # 新規追加
                        cursor.execute("""
                            INSERT INTO cast (name, partner_id, notes, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (cast_name, partner_id, notes, now, now))
                        result['inserted'] += 1
                        result['success'] += 1

                except Exception as e:
                    result['errors'].append({'row': row_num, 'reason': str(e)})
                    result['skipped'] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    def import_expense_items_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """費用項目データをCSVから一括インポート

        Args:
            csv_data: CSVから読み込んだ辞書のリスト
                     期待されるキー: ID, 契約ID, 番組名, 取引先名, 項目名, 業務種別,
                                    金額, 実施日, 発注番号, 発注日, 状態,
                                    請求書受領日, 支払予定日, 実際支払日, 請求書番号,
                                    支払状態, 源泉徴収額, 消費税額, 支払金額,
                                    請求書ファイルパス, 支払方法, 承認者, 承認日, 備考
            overwrite: True=上書き（既存データ削除）、False=追記/更新

        Returns:
            dict: {
                'success': 成功件数,
                'updated': 更新件数,
                'inserted': 挿入件数,
                'skipped': スキップ件数,
                'errors': [{'row': 行番号, 'reason': 理由}]
            }
        """
        result = {
            'success': 0,
            'updated': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': []
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                cursor.execute("DELETE FROM expense_items")
                conn.commit()

            for row_num, row_data in enumerate(csv_data, start=2):  # ヘッダー行は1行目なので2から開始
                try:
                    # 必須項目チェック
                    item_name = row_data.get('項目名', '').strip()
                    amount_str = row_data.get('金額', '').strip()

                    if not item_name:
                        result['errors'].append({'row': row_num, 'reason': '項目名が空です'})
                        result['skipped'] += 1
                        continue

                    # 金額をfloatに変換
                    try:
                        amount = float(amount_str) if amount_str else 0
                    except ValueError:
                        result['errors'].append({'row': row_num, 'reason': f'金額の形式が不正です: {amount_str}'})
                        result['skipped'] += 1
                        continue

                    # 番組を検索
                    production_id = None
                    production_name = row_data.get('番組名', '').strip()
                    if production_name:
                        cursor.execute("SELECT id FROM productions WHERE name = ?", (production_name,))
                        prod_result = cursor.fetchone()
                        if prod_result:
                            production_id = prod_result[0]

                    # 取引先を検索
                    partner_id = None
                    partner_name = row_data.get('取引先名', '').strip()
                    if partner_name:
                        cursor.execute("SELECT id FROM partners WHERE name = ?", (partner_name,))
                        partner_result = cursor.fetchone()
                        if partner_result:
                            partner_id = partner_result[0]

                    # 契約IDの取得
                    contract_id_str = row_data.get('契約ID', '').strip()
                    contract_id = None
                    if contract_id_str and contract_id_str.isdigit():
                        contract_id = int(contract_id_str)

                    # その他のデータ
                    work_type = row_data.get('業務種別', '制作').strip()
                    implementation_date = row_data.get('実施日', '').strip()
                    order_number = row_data.get('発注番号', '').strip()
                    order_date = row_data.get('発注日', '').strip()
                    status = row_data.get('状態', '発注予定').strip()
                    invoice_received_date = row_data.get('請求書受領日', '').strip()
                    expected_payment_date = row_data.get('支払予定日', '').strip()
                    actual_payment_date = row_data.get('実際支払日', '').strip()
                    invoice_number = row_data.get('請求書番号', '').strip()
                    payment_status = row_data.get('支払状態', '未払い').strip()

                    # 数値フィールド
                    withholding_tax_str = row_data.get('源泉徴収額', '').strip()
                    consumption_tax_str = row_data.get('消費税額', '').strip()
                    payment_amount_str = row_data.get('支払金額', '').strip()

                    withholding_tax = float(withholding_tax_str) if withholding_tax_str else None
                    consumption_tax = float(consumption_tax_str) if consumption_tax_str else None
                    payment_amount = float(payment_amount_str) if payment_amount_str else None

                    invoice_file_path = row_data.get('請求書ファイルパス', '').strip()
                    payment_method = row_data.get('支払方法', '').strip()
                    approver = row_data.get('承認者', '').strip()
                    approval_date = row_data.get('承認日', '').strip()
                    notes = row_data.get('備考', '').strip()

                    expense_id_str = row_data.get('ID', '').strip()

                    now = datetime.now()

                    # UPSERTロジック: IDで既存レコードを検索
                    existing_expense = None
                    if expense_id_str and expense_id_str.isdigit():
                        expense_id = int(expense_id_str)
                        cursor.execute("SELECT id FROM expense_items WHERE id = ?", (expense_id,))
                        existing_expense = cursor.fetchone()

                    if existing_expense:
                        # 既存費用項目を更新
                        existing_id = existing_expense[0]
                        cursor.execute("""
                            UPDATE expense_items
                            SET contract_id=?, production_id=?, partner_id=?, item_name=?, work_type=?,
                                amount=?, implementation_date=?, order_number=?, order_date=?,
                                status=?, invoice_received_date=?, expected_payment_date=?,
                                actual_payment_date=?, invoice_number=?, payment_status=?,
                                withholding_tax=?, consumption_tax=?, payment_amount=?,
                                invoice_file_path=?, payment_method=?, approver=?, approval_date=?,
                                notes=?, updated_at=?
                            WHERE id=?
                        """, (contract_id, production_id, partner_id, item_name, work_type,
                              amount, implementation_date or None, order_number or None, order_date or None,
                              status, invoice_received_date or None, expected_payment_date or None,
                              actual_payment_date or None, invoice_number or None, payment_status,
                              withholding_tax, consumption_tax, payment_amount,
                              invoice_file_path or None, payment_method or None, approver or None, approval_date or None,
                              notes or None, now, existing_id))
                        result['updated'] += 1
                        result['success'] += 1
                    else:
                        # 新規追加
                        cursor.execute("""
                            INSERT INTO expense_items (
                                contract_id, production_id, partner_id, item_name, work_type,
                                amount, implementation_date, order_number, order_date,
                                status, invoice_received_date, expected_payment_date,
                                actual_payment_date, invoice_number, payment_status,
                                withholding_tax, consumption_tax, payment_amount,
                                invoice_file_path, payment_method, approver, approval_date,
                                notes, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (contract_id, production_id, partner_id, item_name, work_type,
                              amount, implementation_date or None, order_number or None, order_date or None,
                              status, invoice_received_date or None, expected_payment_date or None,
                              actual_payment_date or None, invoice_number or None, payment_status,
                              withholding_tax, consumption_tax, payment_amount,
                              invoice_file_path or None, payment_method or None, approver or None, approval_date or None,
                              notes or None, now, now))
                        result['inserted'] += 1
                        result['success'] += 1

                except Exception as e:
                    result['errors'].append({'row': row_num, 'reason': str(e)})
                    result['skipped'] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    def import_programs_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """番組データをCSVから一括インポート

        Args:
            csv_data: CSVから読み込んだ辞書のリスト
                     期待されるキー: ID, 制作物名, 説明, 開始日, 終了日,
                                    放送時間, 放送曜日, ステータス, 制作物種別, 親制作物ID
            overwrite: True=上書き（既存データ削除）、False=追記/更新

        Returns:
            dict: 処理結果サマリー
        """
        result = {
            'success': 0,
            'updated': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': []
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                cursor.execute("DELETE FROM productions")
                conn.commit()
            for row_num, row_data in enumerate(csv_data, start=2):
                try:
                    # 必須項目チェック
                    program_name = row_data.get('制作物名', '').strip()

                    if not program_name:
                        result['errors'].append({'row': row_num, 'reason': '制作物名が空です'})
                        result['skipped'] += 1
                        continue

                    # データ取得
                    description = row_data.get('説明', '').strip()
                    start_date_raw = row_data.get('開始日', '').strip()
                    end_date_raw = row_data.get('終了日', '').strip()
                    broadcast_time = row_data.get('放送時間', '').strip()
                    broadcast_days_raw = row_data.get('放送曜日', '').strip()
                    status = row_data.get('ステータス', '放送中').strip()
                    production_type = row_data.get('制作物種別', 'レギュラー').strip()
                    parent_program_id_str = row_data.get('親制作物ID', '').strip()

                    # 放送曜日に日付が入っていないかチェック（データ整合性）
                    if broadcast_days_raw and parse_flexible_date(broadcast_days_raw):
                        result['errors'].append({
                            'row': row_num,
                            'reason': f'放送曜日列に日付が入っています: {broadcast_days_raw}。CSVファイルの列順序を確認してください'
                        })
                        result['skipped'] += 1
                        continue

                    broadcast_days = broadcast_days_raw

                    # 日付フォーマット変換（柔軟に対応）
                    start_date = None
                    if start_date_raw:
                        start_date = parse_flexible_date(start_date_raw)
                        if start_date is None:
                            result['errors'].append({'row': row_num, 'reason': f'開始日のフォーマットが不正です: {start_date_raw}'})
                            result['skipped'] += 1
                            continue

                    end_date = None
                    if end_date_raw:
                        end_date = parse_flexible_date(end_date_raw)
                        if end_date is None:
                            result['errors'].append({'row': row_num, 'reason': f'終了日のフォーマットが不正です: {end_date_raw}'})
                            result['skipped'] += 1
                            continue

                    # 親制作物IDのチェック
                    parent_production_id = None
                    if parent_program_id_str and parent_program_id_str.isdigit():
                        parent_production_id = int(parent_program_id_str)
                        cursor.execute("SELECT id FROM productions WHERE id = ?", (parent_production_id,))
                        if not cursor.fetchone():
                            result['errors'].append({'row': row_num, 'reason': f'親制作物ID {parent_production_id} が見つかりません'})
                            result['skipped'] += 1
                            continue

                    program_id_str = row_data.get('ID', '').strip()
                    now = datetime.now()

                    # UPSERTロジック: IDまたは制作物名で既存レコードを検索
                    existing_program = None
                    if program_id_str and program_id_str.isdigit():
                        # IDが指定されている場合はIDで検索
                        production_id = int(program_id_str)
                        cursor.execute("SELECT id FROM productions WHERE id = ?", (production_id,))
                        existing_program = cursor.fetchone()
                    else:
                        # IDがない場合は制作物名で検索
                        cursor.execute("SELECT id FROM productions WHERE name = ?", (program_name,))
                        existing_program = cursor.fetchone()

                    if existing_program:
                        # 既存制作物を更新
                        existing_id = existing_program[0]
                        cursor.execute("""
                            UPDATE productions
                            SET name=?, description=?, start_date=?, end_date=?,
                                broadcast_time=?, broadcast_days=?, status=?,
                                production_type=?, parent_production_id=?, updated_at=?
                            WHERE id=?
                        """, (program_name, description, start_date or None, end_date or None,
                              broadcast_time, broadcast_days, status, production_type,
                              parent_production_id, now, existing_id))
                        result['updated'] += 1
                        result['success'] += 1
                    else:
                        # 新規追加
                        cursor.execute("""
                            INSERT INTO productions (name, description, start_date, end_date,
                                                 broadcast_time, broadcast_days, status,
                                                 production_type, parent_production_id, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (program_name, description, start_date or None, end_date or None,
                              broadcast_time, broadcast_days, status, production_type,
                              parent_production_id, now, now))
                        result['inserted'] += 1
                        result['success'] += 1

                except Exception as e:
                    result['errors'].append({'row': row_num, 'reason': str(e)})
                    result['skipped'] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    def import_order_contracts_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """発注データをCSVから一括インポート

        Args:
            csv_data: CSVから読み込んだ辞書のリスト
                     期待されるキー: ID, 番組・イベント名, 取引先名, 委託開始日, 委託終了日,
                                    発注種別, 発注ステータス, PDFステータス, 備考
            overwrite: True=上書き（既存データ削除）、False=追記/更新

        Returns:
            dict: 処理結果サマリー
        """
        result = {
            'success': 0,
            'updated': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': [],
            'warnings': []
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                cursor.execute("DELETE FROM contracts")
                conn.commit()
            for row_num, row_data in enumerate(csv_data, start=2):
                try:
                    # 必須項目チェック
                    program_name = row_data.get('番組・イベント名', '').strip()
                    partner_name = row_data.get('取引先名', '').strip()
                    start_date_raw = row_data.get('委託開始日', '').strip()
                    end_date_raw = row_data.get('委託終了日', '').strip()

                    if not program_name:
                        result['errors'].append({'row': row_num, 'reason': '番組・イベント名が空です'})
                        result['skipped'] += 1
                        continue

                    if not partner_name:
                        result['errors'].append({'row': row_num, 'reason': '取引先名が空です'})
                        result['skipped'] += 1
                        continue

                    if not start_date_raw:
                        result['errors'].append({'row': row_num, 'reason': '委託開始日が空です'})
                        result['skipped'] += 1
                        continue

                    if not end_date_raw:
                        result['errors'].append({'row': row_num, 'reason': '委託終了日が空です'})
                        result['skipped'] += 1
                        continue

                    # 日付フォーマット変換（柔軟に対応）
                    start_date = parse_flexible_date(start_date_raw)
                    if start_date is None:
                        result['errors'].append({'row': row_num, 'reason': f'委託開始日のフォーマットが不正です: {start_date_raw}'})
                        result['skipped'] += 1
                        continue

                    end_date = parse_flexible_date(end_date_raw)
                    if end_date is None:
                        result['errors'].append({'row': row_num, 'reason': f'委託終了日のフォーマットが不正です: {end_date_raw}'})
                        result['skipped'] += 1
                        continue

                    # 制作物IDを検索
                    cursor.execute("SELECT id FROM productions WHERE name = ?", (program_name,))
                    program_result = cursor.fetchone()

                    if not program_result:
                        # 番組が見つからない場合は警告のみでproduction_id=Nullで続行
                        production_id = None
                        result['warnings'].append({'row': row_num, 'reason': f'番組「{program_name}」が見つかりません（production_idはNULLで保存されます）'})
                    else:
                        production_id = program_result[0]

                    # 取引先IDを検索
                    cursor.execute("SELECT id FROM partners WHERE name = ?", (partner_name,))
                    partner_result = cursor.fetchone()

                    if not partner_result:
                        result['errors'].append({'row': row_num, 'reason': f'取引先「{partner_name}」が見つかりません'})
                        result['skipped'] += 1
                        continue

                    partner_id = partner_result[0]

                    # その他のデータ取得（全項目対応）
                    item_name = row_data.get('費用項目名', '').strip()
                    period_type = row_data.get('契約期間種別', '半年').strip()
                    order_type = row_data.get('発注種別', '発注書').strip()
                    order_status = row_data.get('発注ステータス', '未').strip()
                    pdf_status = row_data.get('PDFステータス', '未配布').strip()
                    pdf_file_path = row_data.get('PDFファイルパス', '').strip()
                    pdf_distributed_date = row_data.get('PDF配布日', '').strip()
                    payment_type = row_data.get('支払タイプ', '月額固定').strip()
                    unit_price_str = row_data.get('単価', '').strip()
                    payment_timing = row_data.get('支払タイミング', '翌月末払い').strip()
                    contract_type = row_data.get('契約種別', 'regular_fixed').strip()
                    implementation_date = row_data.get('実施日', '').strip()
                    spot_amount_str = row_data.get('スポット金額', '').strip()
                    order_category = row_data.get('発注カテゴリ', 'レギュラー制作発注書').strip()
                    email_subject = row_data.get('メール件名', '').strip()
                    email_body = row_data.get('メール本文', '').strip()
                    email_to = row_data.get('メール送信先', '').strip()
                    email_sent_date = row_data.get('メール送信日', '').strip()
                    auto_renewal_str = row_data.get('自動延長有効', '有効').strip()
                    renewal_period_str = row_data.get('延長期間（月）', '3').strip()
                    termination_notice_date = row_data.get('終了通知受領日', '').strip()
                    notes = row_data.get('備考', '').strip()

                    # 数値変換
                    unit_price = float(unit_price_str) if unit_price_str else None
                    spot_amount = float(spot_amount_str) if spot_amount_str else None
                    auto_renewal_enabled = 1 if auto_renewal_str == '有効' else 0
                    renewal_period_months = int(renewal_period_str) if renewal_period_str.isdigit() else 3

                    contract_id_str = row_data.get('ID', '').strip()
                    now = datetime.now()

                    # UPSERTロジック: IDまたは番組+取引先+期間で既存レコードを検索
                    existing_contract = None
                    if contract_id_str and contract_id_str.isdigit():
                        # IDが指定されている場合はIDで検索
                        contract_id = int(contract_id_str)
                        cursor.execute("SELECT id FROM contracts WHERE id = ?", (contract_id,))
                        existing_contract = cursor.fetchone()
                    else:
                        # IDがない場合は番組+取引先+期間で検索
                        cursor.execute("""
                            SELECT id FROM contracts
                            WHERE production_id = ? AND partner_id = ?
                            AND contract_start_date = ? AND contract_end_date = ?
                        """, (production_id, partner_id, start_date, end_date))
                        existing_contract = cursor.fetchone()

                    if existing_contract:
                        # 既存発注を更新（全項目対応）
                        existing_id = existing_contract[0]
                        cursor.execute("""
                            UPDATE contracts
                            SET production_id=?, partner_id=?, item_name=?,
                                contract_start_date=?, contract_end_date=?, contract_period_type=?,
                                order_type=?, order_status=?, pdf_status=?, pdf_file_path=?, pdf_distributed_date=?,
                                payment_type=?, unit_price=?, payment_timing=?, contract_type=?,
                                implementation_date=?, spot_amount=?, order_category=?,
                                email_subject=?, email_body=?, email_to=?, email_sent_date=?,
                                auto_renewal_enabled=?, renewal_period_months=?, termination_notice_date=?,
                                notes=?, updated_at=?
                            WHERE id=?
                        """, (production_id, partner_id, item_name,
                              start_date, end_date, period_type,
                              order_type, order_status, pdf_status, pdf_file_path, pdf_distributed_date,
                              payment_type, unit_price, payment_timing, contract_type,
                              implementation_date, spot_amount, order_category,
                              email_subject, email_body, email_to, email_sent_date,
                              auto_renewal_enabled, renewal_period_months, termination_notice_date,
                              notes, now, existing_id))
                        result['updated'] += 1
                        result['success'] += 1
                    else:
                        # 新規追加（全項目対応）
                        cursor.execute("""
                            INSERT INTO contracts (
                                production_id, partner_id, item_name,
                                contract_start_date, contract_end_date, contract_period_type,
                                order_type, order_status, pdf_status, pdf_file_path, pdf_distributed_date,
                                payment_type, unit_price, payment_timing, contract_type,
                                implementation_date, spot_amount, order_category,
                                email_subject, email_body, email_to, email_sent_date,
                                auto_renewal_enabled, renewal_period_months, termination_notice_date,
                                notes, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (production_id, partner_id, item_name,
                              start_date, end_date, period_type,
                              order_type, order_status, pdf_status, pdf_file_path, pdf_distributed_date,
                              payment_type, unit_price, payment_timing, contract_type,
                              implementation_date, spot_amount, order_category,
                              email_subject, email_body, email_to, email_sent_date,
                              auto_renewal_enabled, renewal_period_months, termination_notice_date,
                              notes, now, now))
                        result['inserted'] += 1
                        result['success'] += 1

                except Exception as e:
                    result['errors'].append({'row': row_num, 'reason': str(e)})
                    result['skipped'] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    # ========================================
    # 契約自動延長機能
    # ========================================

    def extend_contract(self, contract_id: int, reason: str = "自動延長",
                       executed_by: str = "システム", notes: str = "") -> bool:
        """契約を延長する

        Args:
            contract_id: 契約ID
            reason: 延長理由（"自動延長" or "手動延長"）
            executed_by: 実行者
            notes: 備考

        Returns:
            bool: 延長成功時True
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 現在の契約情報を取得
            cursor.execute("""
                SELECT contract_end_date, renewal_period_months, renewal_count
                FROM contracts
                WHERE id = ?
            """, (contract_id,))

            row = cursor.fetchone()
            if not row:
                log_message(f"契約ID {contract_id} が見つかりません")
                return False

            current_end_date_str, renewal_months, renewal_count = row
            renewal_months = renewal_months or 3  # デフォルト3ヶ月
            renewal_count = renewal_count or 0

            # 新しい終了日を計算
            current_end_date = datetime.strptime(current_end_date_str, '%Y-%m-%d')
            new_end_date = current_end_date + timedelta(days=renewal_months * 30)
            new_end_date_str = new_end_date.strftime('%Y-%m-%d')

            # 契約を更新
            now = datetime.now()
            cursor.execute("""
                UPDATE contracts
                SET contract_end_date = ?,
                    last_renewal_date = ?,
                    renewal_count = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_end_date_str, now.strftime('%Y-%m-%d'),
                  renewal_count + 1, now, contract_id))

            # 延長履歴を記録
            cursor.execute("""
                INSERT INTO contract_renewal_history (
                    contract_id, previous_end_date, new_end_date,
                    renewal_reason, executed_by, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (contract_id, current_end_date_str, new_end_date_str,
                  reason, executed_by, notes))

            conn.commit()
            log_message(f"契約ID {contract_id} を延長しました: {current_end_date_str} → {new_end_date_str}")
            return True

        except Exception as e:
            conn.rollback()
            log_message(f"契約延長エラー: {e}")
            return False
        finally:
            conn.close()

    def get_contracts_for_auto_renewal(self) -> List[Tuple]:
        """自動延長対象の契約を取得

        条件:
        - auto_renewal_enabled = 1
        - termination_notice_date が NULL（終了通知未受領）
        - 契約終了日が過去または今日

        Returns:
            List[Tuple]: (id, program_name, partner_name, contract_end_date, ...)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT oc.id, prod.name as program_name, p.name as partner_name,
                       oc.contract_end_date, oc.renewal_period_months,
                       oc.renewal_count, oc.item_name
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.auto_renewal_enabled = 1
                  AND (oc.termination_notice_date IS NULL OR oc.termination_notice_date = '')
                  AND oc.contract_end_date <= ?
                ORDER BY oc.contract_end_date
            """, (today,))

            return cursor.fetchall()
        finally:
            conn.close()

    def check_and_execute_auto_renewal(self, executed_by: str = "システム") -> dict:
        """自動延長チェックと実行

        Args:
            executed_by: 実行者

        Returns:
            dict: {
                'checked': チェック件数,
                'extended': 延長件数,
                'failed': 失敗件数,
                'details': [(contract_id, program_name, result), ...]
            }
        """
        result = {
            'checked': 0,
            'extended': 0,
            'failed': 0,
            'details': []
        }

        contracts = self.get_contracts_for_auto_renewal()
        result['checked'] = len(contracts)

        for contract in contracts:
            contract_id = contract[0]
            program_name = contract[1]
            partner_name = contract[2]

            try:
                if self.extend_contract(contract_id, "自動延長", executed_by):
                    result['extended'] += 1
                    result['details'].append((contract_id, f"{program_name} - {partner_name}", "成功"))
                else:
                    result['failed'] += 1
                    result['details'].append((contract_id, f"{program_name} - {partner_name}", "失敗"))
            except Exception as e:
                result['failed'] += 1
                result['details'].append((contract_id, f"{program_name} - {partner_name}", f"エラー: {e}"))

        return result

    def get_renewal_history(self, contract_id: int) -> List[Tuple]:
        """契約の延長履歴を取得

        Args:
            contract_id: 契約ID

        Returns:
            List[Tuple]: (id, previous_end_date, new_end_date, renewal_date,
                         renewal_reason, executed_by, notes)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, previous_end_date, new_end_date, renewal_date,
                       renewal_reason, executed_by, notes
                FROM contract_renewal_history
                WHERE contract_id = ?
                ORDER BY renewal_date DESC
            """, (contract_id,))

            return cursor.fetchall()
        finally:
            conn.close()

    def get_contracts_expiring_in_days(self, days_before: int = 30) -> List[Tuple]:
        """指定日数以内に期限が来る契約を取得（終了通知なし）

        Args:
            days_before: 何日前から対象にするか

        Returns:
            List[Tuple]: (id, program_name, partner_name, contract_end_date,
                         auto_renewal_enabled, termination_notice_date, 
                         renewal_count, item_name, days_until_expiry)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            today = datetime.now()
            target_date = (today + timedelta(days=days_before)).strftime('%Y-%m-%d')
            today_str = today.strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT oc.id, prod.name as program_name, p.name as partner_name,
                       oc.contract_end_date, oc.auto_renewal_enabled,
                       oc.termination_notice_date, oc.renewal_count,
                       oc.item_name
                FROM contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.contract_end_date BETWEEN ? AND ?
                  AND (oc.termination_notice_date IS NULL OR oc.termination_notice_date = '')
                ORDER BY oc.contract_end_date
            """, (today_str, target_date))

            results = cursor.fetchall()

            # 残り日数を計算
            enriched_results = []
            for row in results:
                contract_end_date = datetime.strptime(row[3], '%Y-%m-%d')
                days_until = (contract_end_date - today).days
                enriched_results.append(row + (days_until,))

            return enriched_results
        finally:
            conn.close()

    def migrate_add_work_type(self) -> bool:
        """業務種別カラムを追加

        実行内容:
        1. order_contractsテーブルにwork_typeカラムを追加

        Returns:
            bool: マイグレーション成功時True
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # order_contractsテーブルの拡張
            cursor.execute("PRAGMA table_info(order_contracts)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'work_type' not in columns:
                log_message("order_contractsテーブルにwork_typeカラムを追加")

                cursor.execute("""
                    ALTER TABLE order_contracts
                    ADD COLUMN work_type TEXT DEFAULT '制作'
                """)

                # 既存データのデフォルト値を設定
                cursor.execute("""
                    UPDATE contracts
                    SET work_type = '制作'
                    WHERE work_type IS NULL
                """)

            conn.commit()
            log_message("業務種別カラムの追加が完了しました")
            return True

        except Exception as e:
            conn.rollback()
            log_message(f"マイグレーションエラー: {e}")
            return False
        finally:
            conn.close()

    # ========================================
    # 費用項目管理
    # ========================================

    def get_expense_items_with_details(self, search_term=None, payment_status=None, status=None, payment_month=None, show_archived=False):
        """費用項目を詳細情報付きで取得

        Args:
            search_term: 検索キーワード（番組名、取引先名、項目名）
            payment_status: 支払状態フィルタ
            status: 状態フィルタ
            payment_month: 支払月フィルタ（YYYY-MM形式または"current_unpaid"）
            show_archived: アーカイブ済み項目を表示するか

        Returns:
            list: (id, production_id, production_name, partner_id, partner_name,
                   item_name, amount, implementation_date, expected_payment_date,
                   status, payment_status, contract_id, notes, work_type,
                   order_number, order_date, invoice_received_date, actual_payment_date,
                   invoice_number, withholding_tax, consumption_tax, payment_amount,
                   invoice_file_path, payment_method, approver, approval_date, amount_pending)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT ei.id, ei.production_id, prod.name as production_name,
                       ei.partner_id, part.name as partner_name,
                       ei.item_name, ei.amount, ei.implementation_date,
                       ei.expected_payment_date, ei.status, ei.payment_status,
                       ei.contract_id, ei.notes, ei.work_type,
                       ei.order_number, ei.order_date, ei.invoice_received_date,
                       ei.actual_payment_date, ei.invoice_number, ei.withholding_tax,
                       ei.consumption_tax, ei.payment_amount, ei.invoice_file_path,
                       ei.payment_method, ei.approver, ei.approval_date, ei.amount_pending
                FROM expense_items ei
                LEFT JOIN productions prod ON ei.production_id = prod.id
                LEFT JOIN partners part ON ei.partner_id = part.id
                WHERE 1=1
            """
            params = []

            # アーカイブフィルタ
            if not show_archived:
                query += " AND (ei.archived = 0 OR ei.archived IS NULL)"

            if search_term:
                query += """ AND (prod.name LIKE ? OR part.name LIKE ? OR ei.item_name LIKE ?)"""
                params.extend([f"%{search_term}%"] * 3)

            if payment_status:
                query += " AND ei.payment_status = ?"
                params.append(payment_status)

            if status:
                query += " AND ei.status = ?"
                params.append(status)

            if payment_month == "until_current_month_end":
                # 今月末までの支払予定
                query += """ AND ei.expected_payment_date <= date('now', 'start of month', '+1 month', '-1 day')"""
            elif payment_month == "until_next_month_end":
                # 来月末までの支払予定
                query += """ AND ei.expected_payment_date <= date('now', 'start of month', '+2 months', '-1 day')"""
            elif payment_month:
                # YYYY-MM形式の月でフィルタ（expected_payment_dateの年月が一致）
                query += " AND strftime('%Y-%m', ei.expected_payment_date) = ?"
                params.append(payment_month)

            query += " ORDER BY ei.expected_payment_date DESC, ei.id DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_payment_months(self):
        """費用項目の支払予定日から年月リストを取得

        Returns:
            list: YYYY-MM形式の年月リスト（降順）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', expected_payment_date) as payment_month
                FROM expense_items
                WHERE expected_payment_date IS NOT NULL
                ORDER BY payment_month DESC
            """)
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def archive_old_expense_items(self, months_old=12):
        """古い支払済み項目をアーカイブ

        Args:
            months_old: アーカイブ対象の月数（デフォルト12ヶ月）

        Returns:
            int: アーカイブした件数
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE expense_items
                SET archived = 1, archived_date = CURRENT_DATE
                WHERE payment_status = '支払済'
                AND expected_payment_date < date('now', ? || ' months')
                AND archived = 0
            """, (f'-{months_old}',))

            count = cursor.rowcount
            conn.commit()
            log_message(f"{count}件の費用項目をアーカイブしました")
            return count
        except Exception as e:
            conn.rollback()
            log_message(f"アーカイブエラー: {e}")
            raise
        finally:
            conn.close()

    def get_archive_candidate_count(self, months_old=12):
        """アーカイブ対象件数を取得

        Args:
            months_old: アーカイブ対象の月数（デフォルト12ヶ月）

        Returns:
            int: アーカイブ対象件数
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM expense_items
                WHERE payment_status = '支払済'
                AND expected_payment_date < date('now', ? || ' months')
                AND archived = 0
            """, (f'-{months_old}',))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def delete_expense_item(self, expense_id):
        """費用項目を削除

        Args:
            expense_id: 費用項目ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM expense_items WHERE id = ?", (expense_id,))
            conn.commit()
        finally:
            conn.close()

    def delete_expense_items_bulk(self, expense_ids):
        """複数の費用項目を一括削除

        Args:
            expense_ids: list of int - 費用項目IDのリスト

        Returns:
            int: 削除された件数
        """
        if not expense_ids:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # プレースホルダーを作成
            placeholders = ','.join('?' * len(expense_ids))
            query = f"DELETE FROM expense_items WHERE id IN ({placeholders})"

            cursor.execute(query, list(expense_ids))
            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_expense_items_production(self, expense_ids, new_production_id):
        """複数の費用項目の番組を一括変更

        Args:
            expense_ids: list of int - 費用項目IDのリスト
            new_production_id: int - 新しい番組ID

        Returns:
            int: 更新された件数
        """
        if not expense_ids:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # プレースホルダーを作成
            placeholders = ','.join('?' * len(expense_ids))
            query = f"""
                UPDATE expense_items
                SET production_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """

            # パラメータリスト: [new_production_id, expense_id1, expense_id2, ...]
            params = [new_production_id] + list(expense_ids)

            cursor.execute(query, params)
            updated_count = cursor.rowcount
            conn.commit()

            return updated_count
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_expense_item_by_id(self, expense_id):
        """費用項目を1件取得

        Args:
            expense_id: 費用項目ID

        Returns:
            tuple: 費用項目データ
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, contract_id, production_id, partner_id, item_name,
                       amount, implementation_date, order_number, order_date,
                       status, invoice_received_date, expected_payment_date,
                       expected_payment_amount, payment_scheduled_date, payment_date,
                       payment_status, payment_verified_date, payment_matched_id,
                       payment_difference, gmail_draft_id, gmail_message_id,
                       email_sent_at, contact_person, notes, created_at, updated_at,
                       work_type, amount_pending, corner_id
                FROM expense_items
                WHERE id = ?
            """, (expense_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_expense_item(self, expense_data):
        """費用項目を保存（新規/更新）

        Args:
            expense_data: dict with keys:
                - id (optional): 更新時のID
                - contract_id: 契約ID
                - production_id: 番組ID
                - partner_id: 取引先ID
                - item_name: 項目名
                - amount: 金額
                - implementation_date: 実施日
                - expected_payment_date: 支払予定日
                - status: 状態
                - payment_status: 支払状態
                - notes: 備考

        Returns:
            int: 保存した費用項目のID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            expense_id = expense_data.get('id')

            if expense_id:
                # 更新
                cursor.execute("""
                    UPDATE expense_items SET
                        contract_id = ?,
                        production_id = ?,
                        partner_id = ?,
                        item_name = ?,
                        work_type = ?,
                        amount = ?,
                        amount_pending = ?,
                        implementation_date = ?,
                        expected_payment_date = ?,
                        status = ?,
                        payment_status = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    expense_data.get('contract_id'),
                    expense_data.get('production_id'),
                    expense_data.get('partner_id'),
                    expense_data.get('item_name'),
                    expense_data.get('work_type', '制作'),
                    expense_data.get('amount', 0),
                    expense_data.get('amount_pending', 0),
                    expense_data.get('implementation_date'),
                    expense_data.get('expected_payment_date'),
                    expense_data.get('status', '発注予定'),
                    expense_data.get('payment_status', '未払い'),
                    expense_data.get('notes'),
                    expense_id
                ))
            else:
                # 新規作成
                cursor.execute("""
                    INSERT INTO expense_items (
                        contract_id, production_id, partner_id, item_name, work_type,
                        amount, amount_pending, implementation_date, expected_payment_date,
                        status, payment_status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    expense_data.get('contract_id'),
                    expense_data.get('production_id'),
                    expense_data.get('partner_id'),
                    expense_data.get('item_name'),
                    expense_data.get('work_type', '制作'),
                    expense_data.get('amount', 0),
                    expense_data.get('amount_pending', 0),
                    expense_data.get('implementation_date'),
                    expense_data.get('expected_payment_date'),
                    expense_data.get('status', '発注予定'),
                    expense_data.get('payment_status', '未払い'),
                    expense_data.get('notes')
                ))
                expense_id = cursor.lastrowid

            conn.commit()
            return expense_id
        finally:
            conn.close()

    def get_active_contracts(self):
        """有効な契約一覧を取得（費用項目編集用）

        Returns:
            list: (contract_id, production_name, partner_name, item_name,
                   unit_price, spot_amount, contract_start_date, contract_end_date)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT c.id, prod.name as production_name, part.name as partner_name,
                       c.item_name, c.unit_price, c.spot_amount,
                       c.contract_start_date, c.contract_end_date
                FROM contracts c
                LEFT JOIN productions prod ON c.production_id = prod.id
                LEFT JOIN partners part ON c.partner_id = part.id
                WHERE c.contract_end_date >= date('now')
                   OR c.contract_end_date IS NULL
                ORDER BY c.contract_start_date DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    def _count_weekdays_in_month(self, year, month, weekdays):
        """指定月の指定曜日の出現回数を計算

        Args:
            year: 年
            month: 月
            weekdays: 曜日のリスト ['月', '火', '水']

        Returns:
            int: 合計出現回数
        """
        from datetime import datetime
        import calendar

        # 曜日マッピング
        weekday_map = {
            '月': 0, '火': 1, '水': 2, '木': 3,
            '金': 4, '土': 5, '日': 6
        }

        total_count = 0
        for weekday_name in weekdays:
            if weekday_name not in weekday_map:
                continue

            target_weekday = weekday_map[weekday_name]

            # その月の日数を取得
            _, last_day = calendar.monthrange(year, month)

            count = 0
            for day in range(1, last_day + 1):
                date = datetime(year, month, day)
                if date.weekday() == target_weekday:
                    count += 1

            total_count += count

        return total_count

    def generate_expense_items_from_contract(self, contract_id):
        """契約から費用項目を自動生成

        Args:
            contract_id: 契約ID

        Returns:
            int: 生成した費用項目の件数
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 契約情報と番組のstart_dateを取得
            cursor.execute("""
                SELECT c.id, c.production_id, c.partner_id, c.item_name,
                       c.contract_start_date, c.contract_end_date, c.contract_type,
                       c.payment_type, c.unit_price, c.spot_amount, c.payment_timing,
                       c.implementation_date, c.work_type, p.start_date
                FROM contracts c
                LEFT JOIN productions p ON c.production_id = p.id
                WHERE c.id = ?
            """, (contract_id,))

            contract = cursor.fetchone()
            if not contract:
                return 0

            (cid, production_id, partner_id, item_name, start_date_str, end_date_str,
             contract_type, payment_type, unit_price, spot_amount, payment_timing,
             implementation_date, work_type, production_start_date) = contract

            # implementation_dateがNULLの場合、番組のstart_dateを使用
            if not implementation_date and production_start_date:
                implementation_date = production_start_date

            generated_count = 0

            # 単発契約の場合
            if spot_amount and spot_amount > 0:
                # 重複チェック：同じ契約ID・実施日・金額の費用項目が既に存在するか確認
                cursor.execute("""
                    SELECT COUNT(*) FROM expense_items
                    WHERE contract_id = ?
                      AND implementation_date = ?
                      AND amount = ?
                """, (contract_id, implementation_date, spot_amount))

                exists = cursor.fetchone()[0] > 0

                if not exists:
                    # 1件のみ生成
                    cursor.execute("""
                        INSERT INTO expense_items (
                            contract_id, production_id, partner_id, item_name,
                            amount, implementation_date, expected_payment_date,
                            status, payment_status, work_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, '発注予定', '未払い', ?)
                    """, (
                        contract_id, production_id, partner_id, item_name,
                        spot_amount, implementation_date, implementation_date, work_type
                    ))
                    generated_count = 1

            # 月額固定契約の場合（回数ベースを除く）
            elif payment_type != '回数ベース' and unit_price and unit_price > 0 and start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                # 月初に設定
                current_date = start_date.replace(day=1)
                end_month = end_date.replace(day=1)

                while current_date <= end_month:
                    # 支払予定日を計算
                    if payment_timing == '当月末払い':
                        # 当月末
                        payment_date = (current_date + relativedelta(months=1, days=-1)).strftime('%Y-%m-%d')
                    else:  # 翌月末払い（デフォルト）
                        # 翌月末
                        payment_date = (current_date + relativedelta(months=2, days=-1)).strftime('%Y-%m-%d')

                    impl_date_str = current_date.strftime('%Y-%m-%d')

                    # 重複チェック：同じ契約ID・実施日・金額の費用項目が既に存在するか確認
                    cursor.execute("""
                        SELECT COUNT(*) FROM expense_items
                        WHERE contract_id = ?
                          AND implementation_date = ?
                          AND amount = ?
                    """, (contract_id, impl_date_str, unit_price))

                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        cursor.execute("""
                            INSERT INTO expense_items (
                                contract_id, production_id, partner_id, item_name,
                                amount, implementation_date, expected_payment_date,
                                status, payment_status, work_type
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, '発注予定', '未払い', ?)
                        """, (
                            contract_id, production_id, partner_id, item_name,
                            unit_price, impl_date_str, payment_date, work_type
                        ))
                        generated_count += 1

                    current_date = current_date + relativedelta(months=1)

            # 回数ベース契約の場合
            elif payment_type == '回数ベース' and unit_price and unit_price > 0 and start_date_str and end_date_str:
                # 番組の放送曜日を取得
                cursor.execute("""
                    SELECT broadcast_days FROM productions WHERE id = ?
                """, (production_id,))

                result = cursor.fetchone()
                broadcast_days = result[0] if result else None

                if not broadcast_days or not broadcast_days.strip():
                    # 放送曜日が設定されていない場合はエラー
                    raise ValueError(f"回数ベース契約（ID: {contract_id}）の番組に放送曜日が設定されていません")

                # 曜日を分割（例: "月,火,水" → ['月', '火', '水']）
                weekdays = [day.strip() for day in broadcast_days.split(',')]

                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                # 月初に設定
                current_date = start_date.replace(day=1)
                end_month = end_date.replace(day=1)

                while current_date <= end_month:
                    # その月の実施回数を計算
                    count = self._count_weekdays_in_month(current_date.year, current_date.month, weekdays)

                    # 金額 = 回数 × 単価
                    amount = count * unit_price

                    # 支払予定日を計算
                    if payment_timing == '当月末払い':
                        # 当月末
                        payment_date = (current_date + relativedelta(months=1, days=-1)).strftime('%Y-%m-%d')
                    else:  # 翌月末払い
                        # 翌月末
                        payment_date = (current_date + relativedelta(months=2, days=-1)).strftime('%Y-%m-%d')

                    impl_date_str = current_date.strftime('%Y-%m-%d')

                    # 重複チェック
                    cursor.execute("""
                        SELECT COUNT(*) FROM expense_items
                        WHERE contract_id = ?
                          AND implementation_date = ?
                    """, (contract_id, impl_date_str))

                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        cursor.execute("""
                            INSERT INTO expense_items (
                                contract_id, production_id, partner_id, item_name,
                                amount, implementation_date, expected_payment_date,
                                status, payment_status, work_type, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, '発注予定', '未払い', ?, ?)
                        """, (
                            contract_id, production_id, partner_id, item_name,
                            amount, impl_date_str, payment_date, work_type,
                            f"実施回数: {count}回 × ¥{int(unit_price):,} = ¥{int(amount):,}"
                        ))
                        generated_count += 1

                    current_date = current_date + relativedelta(months=1)

            conn.commit()
            return generated_count
        finally:
            conn.close()

    def delete_expense_items_by_contract(self, contract_id):
        """契約に紐付く費用項目を削除

        Args:
            contract_id: 契約ID

        Returns:
            int: 削除した件数
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM expense_items
                WHERE contract_id = ?
            """, (contract_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        finally:
            conn.close()

    # ========================================
    # 契約と出演者の紐付け管理
    # ========================================

    def get_contract_cast(self, contract_id):
        """契約に紐付けられた出演者を取得

        Args:
            contract_id: 契約ID

        Returns:
            list: [(contract_cast_id, cast_id, cast_name, partner_name, role), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT cc.id, cc.cast_id, c.name as cast_name, 
                       p.name as partner_name, cc.role
                FROM contract_cast cc
                INNER JOIN cast c ON cc.cast_id = c.id
                LEFT JOIN partners p ON c.partner_id = p.id
                WHERE cc.contract_id = ?
                ORDER BY cc.id
            """, (contract_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def add_contract_cast(self, contract_id, cast_id, role=None):
        """契約に出演者を追加

        Args:
            contract_id: 契約ID
            cast_id: 出演者ID
            role: 役割（オプション）

        Returns:
            int: contract_cast ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO contract_cast (contract_id, cast_id, role)
                VALUES (?, ?, ?)
            """, (contract_id, cast_id, role))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def save_contract_cast_list(self, contract_id, cast_list):
        """契約の出演者リストを一括保存（既存データを削除して再作成）

        Args:
            contract_id: 契約ID
            cast_list: 出演者リスト [(cast_id, role), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 既存の出演者リンクを削除
            cursor.execute("DELETE FROM contract_cast WHERE contract_id = ?", (contract_id,))

            # 新しい出演者リンクを追加
            for cast_id, role in cast_list:
                cursor.execute("""
                    INSERT INTO contract_cast (contract_id, cast_id, role)
                    VALUES (?, ?, ?)
                """, (contract_id, cast_id, role))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def remove_contract_cast(self, contract_cast_id):
        """契約から出演者を削除

        Args:
            contract_cast_id: contract_cast ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM contract_cast WHERE id = ?", (contract_cast_id,))
            conn.commit()
        finally:
            conn.close()

    def update_contract_cast_role(self, contract_cast_id, role):
        """契約出演者の役割を更新

        Args:
            contract_cast_id: contract_cast ID
            role: 役割
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE contract_cast
                SET role = ?
                WHERE id = ?
            """, (role, contract_cast_id))
            conn.commit()
        finally:
            conn.close()

    def get_all_cast(self):
        """全出演者を取得

        Returns:
            list: [(cast_id, cast_name, partner_name), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT c.id, c.name, p.name as partner_name
                FROM cast c
                LEFT JOIN partners p ON c.partner_id = p.id
                ORDER BY c.name
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    # ========================================
    # 番組別費用集計
    # ========================================

    def get_production_expense_summary(self, search_term=None, sort_by='total_amount', production_type_filter=None):
        """番組ごとの費用集計を取得

        Args:
            search_term: 検索キーワード（番組名）
            sort_by: ソート基準（total_amount, unpaid_count, item_count, monthly_average）
            production_type_filter: 番組タイプフィルタ（レギュラー、イベント、特番など）

        Returns:
            list: [(production_id, production_name, production_type, item_count, total_amount,
                   unpaid_count, unpaid_amount, paid_count, paid_amount, pending_count,
                   month_count, monthly_average), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT
                    p.id,
                    p.name,
                    p.production_type,
                    COUNT(*) as item_count,
                    SUM(CASE WHEN ei.amount_pending = 1 THEN 0 ELSE ei.amount END) as total_amount,
                    SUM(CASE WHEN ei.payment_status = '未払い' THEN 1 ELSE 0 END) as unpaid_count,
                    SUM(CASE WHEN ei.payment_status = '未払い' AND ei.amount_pending = 0
                         THEN ei.amount ELSE 0 END) as unpaid_amount,
                    SUM(CASE WHEN ei.payment_status = '支払済' THEN 1 ELSE 0 END) as paid_count,
                    SUM(CASE WHEN ei.payment_status = '支払済' THEN ei.amount ELSE 0 END) as paid_amount,
                    SUM(CASE WHEN ei.amount_pending = 1 THEN 1 ELSE 0 END) as pending_count,
                    COUNT(DISTINCT strftime('%Y-%m', ei.expected_payment_date)) as month_count,
                    CASE WHEN COUNT(DISTINCT strftime('%Y-%m', ei.expected_payment_date)) > 0
                         THEN SUM(CASE WHEN ei.amount_pending = 1 THEN 0 ELSE ei.amount END) /
                              COUNT(DISTINCT strftime('%Y-%m', ei.expected_payment_date))
                         ELSE 0 END as monthly_average
                FROM expense_items ei
                JOIN productions p ON ei.production_id = p.id
                WHERE (ei.archived = 0 OR ei.archived IS NULL)
            """
            params = []

            if search_term:
                query += " AND p.name LIKE ?"
                params.append(f"%{search_term}%")

            if production_type_filter:
                query += " AND p.production_type = ?"
                params.append(production_type_filter)

            query += " GROUP BY p.id, p.name, p.production_type"

            # ソート
            if sort_by == 'unpaid_count':
                query += " ORDER BY unpaid_count DESC, total_amount DESC"
            elif sort_by == 'item_count':
                query += " ORDER BY item_count DESC, total_amount DESC"
            elif sort_by == 'monthly_average':
                query += " ORDER BY monthly_average DESC, total_amount DESC"
            else:  # total_amount
                query += " ORDER BY total_amount DESC, item_count DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_production_expense_details(self, production_id):
        """指定した番組の費用項目詳細を取得

        Args:
            production_id: 番組ID

        Returns:
            list: [(id, partner_name, item_name, amount, implementation_date,
                   expected_payment_date, payment_status, status, notes, amount_pending), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    ei.id,
                    part.name as partner_name,
                    ei.item_name,
                    ei.amount,
                    ei.implementation_date,
                    ei.expected_payment_date,
                    ei.payment_status,
                    ei.status,
                    ei.notes,
                    ei.amount_pending,
                    ei.work_type,
                    corner.name as corner_name,
                    ei.corner_id,
                    ei.contract_id,
                    ei.invoice_received_date,
                    ei.actual_payment_date,
                    ei.payment_matched_id,
                    c.document_status
                FROM expense_items ei
                LEFT JOIN partners part ON ei.partner_id = part.id
                LEFT JOIN productions corner ON ei.corner_id = corner.id
                LEFT JOIN contracts c ON ei.contract_id = c.id
                WHERE (ei.production_id = ?
                       OR ei.production_id IN (
                           SELECT id FROM productions WHERE parent_production_id = ?
                       ))
                  AND (ei.archived = 0 OR ei.archived IS NULL)
                ORDER BY ei.implementation_date ASC, ei.id ASC
            """, (production_id, production_id))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_production_expense_monthly_summary(self, production_id):
        """指定した番組の月別費用集計を取得

        Args:
            production_id: 番組ID

        Returns:
            list: [(month, item_count, total_amount, unpaid_count, paid_count), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', ei.expected_payment_date) as month,
                    COUNT(*) as item_count,
                    SUM(CASE WHEN ei.amount_pending = 1 THEN 0 ELSE ei.amount END) as total_amount,
                    SUM(CASE WHEN ei.payment_status = '未払い' THEN 1 ELSE 0 END) as unpaid_count,
                    SUM(CASE WHEN ei.payment_status = '支払済' THEN 1 ELSE 0 END) as paid_count
                FROM expense_items ei
                WHERE ei.production_id = ?
                  AND (ei.archived = 0 OR ei.archived IS NULL)
                  AND ei.expected_payment_date IS NOT NULL
                GROUP BY month
                ORDER BY month ASC
            """, (production_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_expense_months_by_production(self, production_id):
        """指定した番組の費用項目が存在する月のリストを取得

        Args:
            production_id: 番組ID

        Returns:
            list: ['2025-10', '2025-11', ...] のような年月文字列のリスト（昇順）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', ei.implementation_date) as year_month
                FROM expense_items ei
                WHERE (ei.production_id = ?
                       OR ei.production_id IN (
                           SELECT id FROM productions WHERE parent_production_id = ?
                       ))
                  AND ei.implementation_date IS NOT NULL
                  AND (ei.archived = 0 OR ei.archived IS NULL)
                ORDER BY year_month ASC
            """, (production_id, production_id))

            return [row[0] for row in cursor.fetchall() if row[0]]
        finally:
            conn.close()

    def get_production_expense_details_by_month(self, production_id, year_month):
        """指定した番組の特定月の費用項目詳細を取得

        Args:
            production_id: 番組ID
            year_month: 対象年月（'YYYY-MM'形式）

        Returns:
            list: [(id, partner_name, item_name, amount, implementation_date,
                   expected_payment_date, payment_status, status, notes, amount_pending, work_type), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    ei.id,
                    p.name as partner_name,
                    ei.item_name,
                    ei.amount,
                    ei.implementation_date,
                    ei.expected_payment_date,
                    ei.payment_status,
                    ei.status,
                    ei.notes,
                    ei.amount_pending,
                    ei.work_type,
                    corner.name as corner_name,
                    ei.corner_id,
                    ei.contract_id,
                    ei.invoice_received_date,
                    ei.actual_payment_date,
                    ei.payment_matched_id,
                    c.document_status
                FROM expense_items ei
                LEFT JOIN partners p ON ei.partner_id = p.id
                LEFT JOIN productions corner ON ei.corner_id = corner.id
                LEFT JOIN contracts c ON ei.contract_id = c.id
                WHERE (ei.production_id = ?
                       OR ei.production_id IN (
                           SELECT id FROM productions WHERE parent_production_id = ?
                       ))
                  AND strftime('%Y-%m', ei.expected_payment_date) = ?
                  AND (ei.archived = 0 OR ei.archived IS NULL)
                ORDER BY ei.implementation_date ASC, ei.id ASC
            """, (production_id, production_id, year_month))
            return cursor.fetchall()
        finally:
            conn.close()

    def reconcile_payments_with_expenses(self, billing_db_path='billing.db'):
        """billing.dbの支払いデータとexpense_itemsを照合して更新

        Args:
            billing_db_path: billing.dbのパス

        Returns:
            dict: {
                'matched': 照合成功件数,
                'unmatched_expenses': 未照合費用項目数,
                'unmatched_payments': 未照合支払い数
            }
        """
        import sqlite3
        from datetime import datetime, timedelta

        # billing.dbに接続
        billing_conn = sqlite3.connect(billing_db_path)
        billing_cursor = billing_conn.cursor()

        # order_management.dbに接続
        order_conn = self._get_connection()
        order_cursor = order_conn.cursor()

        try:
            # billing.dbから支払いデータを取得
            billing_cursor.execute("""
                SELECT id, payee, payee_code, amount, payment_date, status
                FROM payments
                WHERE status != '照合済み'
            """)
            payments = billing_cursor.fetchall()

            # 未照合の費用項目を取得
            order_cursor.execute("""
                SELECT ei.id, ei.item_name, p.name as partner_name, p.code as partner_code,
                       ei.amount, ei.expected_payment_date, ei.payment_status
                FROM expense_items ei
                LEFT JOIN partners p ON ei.partner_id = p.id
                WHERE ei.payment_matched_id IS NULL
                  AND ei.payment_status != '支払済'
                  AND (ei.archived = 0 OR ei.archived IS NULL)
            """)
            expenses = order_cursor.fetchall()

            matched_count = 0

            # 各支払いデータと費用項目を照合
            for payment in payments:
                payment_id, payee, payee_code, payment_amount, payment_date, payment_status = payment

                for expense in expenses:
                    (expense_id, item_name, partner_name, partner_code,
                     expense_amount, expected_payment_date, expense_payment_status) = expense

                    # 照合条件チェック
                    # 1. 取引先名またはコードが一致
                    name_match = (payee and partner_name and payee.strip() == partner_name.strip())
                    code_match = (payee_code and partner_code and payee_code.strip() == partner_code.strip())

                    if not (name_match or code_match):
                        continue

                    # 2. 金額が一致（±5%）
                    if payment_amount and expense_amount:
                        amount_diff = abs(payment_amount - expense_amount) / expense_amount
                        if amount_diff > 0.05:  # 5%以上の差異
                            continue
                    else:
                        continue

                    # 3. 日付が近い（±7日）
                    if payment_date and expected_payment_date:
                        try:
                            # 複数の日付形式に対応
                            pay_date = None
                            exp_date = None

                            for fmt in ['%Y-%m-%d', '%Y/%m/%d']:
                                try:
                                    pay_date = datetime.strptime(payment_date, fmt)
                                    break
                                except:
                                    pass

                            for fmt in ['%Y-%m-%d', '%Y/%m/%d']:
                                try:
                                    exp_date = datetime.strptime(expected_payment_date, fmt)
                                    break
                                except:
                                    pass

                            if not (pay_date and exp_date):
                                continue

                            date_diff = abs((pay_date - exp_date).days)
                            if date_diff > 7:
                                continue
                        except:
                            continue

                    # 照合成功：expense_itemsを更新
                    order_cursor.execute("""
                        UPDATE expense_items
                        SET payment_matched_id = ?,
                            actual_payment_date = ?,
                            payment_amount = ?,
                            payment_status = '支払済'
                        WHERE id = ?
                    """, (payment_id, payment_date, payment_amount, expense_id))

                    # paymentsの状態も更新
                    billing_cursor.execute("""
                        UPDATE payments
                        SET status = '照合済み'
                        WHERE id = ?
                    """, (payment_id,))

                    matched_count += 1
                    break  # この支払いは照合済み

            # 変更をコミット
            order_conn.commit()
            billing_conn.commit()

            # 未照合件数を取得
            order_cursor.execute("""
                SELECT COUNT(*) FROM expense_items
                WHERE payment_matched_id IS NULL
                  AND payment_status != '支払済'
                  AND (archived = 0 OR archived IS NULL)
            """)
            unmatched_expenses = order_cursor.fetchone()[0]

            billing_cursor.execute("""
                SELECT COUNT(*) FROM payments
                WHERE status != '照合済み'
            """)
            unmatched_payments = billing_cursor.fetchone()[0]

            return {
                'matched': matched_count,
                'unmatched_expenses': unmatched_expenses,
                'unmatched_payments': unmatched_payments
            }

        finally:
            billing_conn.close()
            order_conn.close()

    def get_unmatched_payments_from_billing(self, billing_db_path='billing.db'):
        """billing.dbから費用項目に未登録の支払いデータを取得

        billing.dbに存在する支払いデータのうち、expense_itemsテーブルに
        対応する費用項目が存在しないものを「未登録支払い」として抽出します。

        Args:
            billing_db_path: billing.dbのパス

        Returns:
            list: 未登録支払いデータのリスト
                  [(payment_id, subject, project_name, payee, payee_code, amount, payment_date, status), ...]
        """
        import sqlite3

        # billing.dbに接続
        billing_conn = sqlite3.connect(billing_db_path)
        billing_cursor = billing_conn.cursor()

        # order_management.dbに接続
        om_conn = self._get_connection()
        om_cursor = om_conn.cursor()

        try:
            # billing.dbからすべての支払いデータを取得
            billing_cursor.execute("""
                SELECT id, subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                ORDER BY payment_date DESC
            """)
            all_payments = billing_cursor.fetchall()

            # 未登録の支払いデータを格納するリスト
            unmatched_payments = []

            for payment in all_payments:
                payment_id, subject, project_name, payee, payee_code, amount, payment_date, status = payment

                # expense_itemsテーブルで対応する費用項目を検索
                # 照合キー: partner名 (payee) と amount の完全一致のみ
                # 項目名（item_name）は無視（billing.dbとexpense_itemsで項目名が異なるため）
                om_cursor.execute("""
                    SELECT ei.id
                    FROM expense_items ei
                    LEFT JOIN partners p ON ei.partner_id = p.id
                    WHERE p.name = ?
                      AND ei.amount = ?
                    LIMIT 1
                """, (payee, amount))

                # 対応する費用項目が見つからない場合のみ未登録として追加
                if om_cursor.fetchone() is None:
                    unmatched_payments.append(payment)

            return unmatched_payments

        finally:
            billing_conn.close()
            om_conn.close()

    def get_productions_for_month(self, month_str):
        """指定月の番組を取得

        Args:
            month_str: 月文字列（例: "2025-10"）

        Returns:
            list: 番組リスト [(id, name, production_type, start_date, ...), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 月の開始日と終了日を計算
            year, month = map(int, month_str.split('-'))
            start_date = f"{year}-{month:02d}-01"

            # 次月の1日を計算
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            end_date = f"{next_year}-{next_month:02d}-01"

            # レギュラー番組：番組名を1回だけ表示（放送中のもの）
            # 単発番組：開始日が指定月内のものを表示
            cursor.execute("""
                SELECT id, name, production_type, start_date, status
                FROM productions
                WHERE (
                    (production_type = 'レギュラー' AND status = '放送中')
                    OR
                    (production_type != 'レギュラー' AND start_date >= ? AND start_date < ?)
                )
                ORDER BY
                    CASE
                        WHEN production_type = 'レギュラー' THEN 0
                        ELSE 1
                    END,
                    start_date,
                    name
            """, (start_date, end_date))

            return cursor.fetchall()

        finally:
            conn.close()

    def get_production_by_id(self, production_id):
        """番組IDから番組情報を取得

        Args:
            production_id: 番組ID

        Returns:
            dict: 番組情報
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, production_type, start_date, end_date,
                       start_time, end_time, broadcast_time, broadcast_days, status, location
                FROM productions
                WHERE id = ?
            """, (production_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'production_type': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'start_time': row[6],
                'end_time': row[7],
                'broadcast_time': row[8],
                'broadcast_days': row[9],
                'status': row[10],
                'location': row[11]
            }

        finally:
            conn.close()

    def get_production_casts(self, production_id):
        """番組の出演者を取得

        Args:
            production_id: 番組ID

        Returns:
            list: [(cast_name, role), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT c.name, pc.role
                FROM production_cast pc
                JOIN cast c ON pc.cast_id = c.id
                WHERE pc.production_id = ?
                ORDER BY pc.id
            """, (production_id,))

            return cursor.fetchall()

        finally:
            conn.close()

    def get_expenses_by_production(self, production_id):
        """番組の費用項目を取得

        Args:
            production_id: 番組ID

        Returns:
            list: [{'item_name': ..., 'work_type': ..., 'amount': ..., ...}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT ei.item_name, ei.work_type, ei.amount, p.name as partner_name
                FROM expense_items ei
                LEFT JOIN partners p ON ei.partner_id = p.id
                WHERE ei.production_id = ?
                ORDER BY
                    CASE
                        WHEN ei.work_type LIKE '%出演%' THEN 0
                        ELSE 1
                    END,
                    ei.id
            """, (production_id,))

            rows = cursor.fetchall()
            expenses = []
            for row in rows:
                expenses.append({
                    'item_name': row[0],
                    'work_type': row[1],
                    'amount': row[2],
                    'partner_name': row[3]
                })

            return expenses

        finally:
            conn.close()
