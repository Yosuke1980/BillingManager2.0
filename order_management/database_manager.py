"""発注管理データベースマネージャー

発注管理機能のデータベース操作を担当します。
"""
import sqlite3
from typing import List, Optional, Tuple
from datetime import datetime
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

    def _get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)

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

    def get_projects(self, search_term: str = "", project_type: str = "") -> List[Tuple]:
        """案件一覧を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, date, type, budget, parent_id
                FROM projects
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND name LIKE ?"
                params.append(f"%{search_term}%")

            if project_type:
                query += " AND type = ?"
                params.append(project_type)

            query += " ORDER BY date DESC, name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_project_by_id(self, project_id: int) -> Optional[Tuple]:
        """IDで案件を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, date, type, budget, parent_id, start_date, end_date,
                       created_at, updated_at
                FROM projects WHERE id = ?
            """, (project_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_project(self, project_data: dict, is_new: bool = False) -> int:
        """案件を保存"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if is_new:
                cursor.execute("""
                    INSERT INTO projects (name, date, type, budget, parent_id, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_data.get('name', ''),
                    project_data.get('date', ''),
                    project_data.get('type', '単発'),
                    project_data.get('budget', 0.0),
                    project_data.get('parent_id'),
                    project_data.get('start_date', ''),
                    project_data.get('end_date', ''),
                ))
                project_id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE projects
                    SET name = ?, date = ?, type = ?, budget = ?, parent_id = ?,
                        start_date = ?, end_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    project_data.get('name', ''),
                    project_data.get('date', ''),
                    project_data.get('type', '単発'),
                    project_data.get('budget', 0.0),
                    project_data.get('parent_id'),
                    project_data.get('start_date', ''),
                    project_data.get('end_date', ''),
                    project_data['id'],
                ))
                project_id = project_data['id']

            conn.commit()
            log_message(f"案件保存完了: ID={project_id}")
            return project_id
        except Exception as e:
            conn.rollback()
            log_message(f"案件保存エラー: {e}")
            raise
        finally:
            conn.close()

    def delete_project(self, project_id: int) -> int:
        """案件を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def duplicate_project(self, project_id: int) -> int:
        """案件を複製（費用項目も含めて）

        Args:
            project_id: 複製元の案件ID

        Returns:
            int: 新しい案件のID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 元の案件データを取得
            cursor.execute("""
                SELECT name, date, type, budget, parent_id, start_date, end_date
                FROM projects WHERE id = ?
            """, (project_id,))

            project = cursor.fetchone()
            if not project:
                raise ValueError(f"案件ID {project_id} が見つかりません")

            # 新しい案件を作成（名前に「（コピー）」を追加）
            cursor.execute("""
                INSERT INTO projects (name, date, type, budget, parent_id, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project[0] + "（コピー）",  # 名前
                project[1],  # date
                project[2],  # type
                project[3],  # budget
                project[4],  # parent_id
                project[5],  # start_date
                project[6],  # end_date
            ))

            new_project_id = cursor.lastrowid

            # 関連する費用項目をコピー
            cursor.execute("""
                SELECT item_name, amount, supplier_id, contact_person, status,
                       implementation_date, payment_scheduled_date, notes
                FROM expenses_order WHERE project_id = ?
            """, (project_id,))

            expenses = cursor.fetchall()
            for expense in expenses:
                cursor.execute("""
                    INSERT INTO expenses_order (
                        project_id, item_name, amount, supplier_id, contact_person,
                        status, implementation_date, payment_scheduled_date, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_project_id,
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
            log_message(f"案件複製完了: 元ID={project_id}, 新ID={new_project_id}, 費用項目={len(expenses)}件")
            return new_project_id

        except Exception as e:
            conn.rollback()
            log_message(f"案件複製エラー: {e}")
            raise
        finally:
            conn.close()

    # ========================================
    # 費用項目操作
    # ========================================

    def get_expenses_by_project(self, project_id: int) -> List[Tuple]:
        """案件IDで費用項目を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, project_id, item_name, amount, supplier_id, contact_person,
                       status, order_number, implementation_date, invoice_received_date
                FROM expenses_order
                WHERE project_id = ?
                ORDER BY implementation_date, id
            """, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_expense_order_by_id(self, expense_id: int) -> Optional[Tuple]:
        """IDで費用項目を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, project_id, item_name, amount, supplier_id, contact_person,
                       status, order_number, order_date, implementation_date,
                       invoice_received_date, payment_scheduled_date, payment_date,
                       gmail_draft_id, gmail_message_id, email_sent_at, notes
                FROM expenses_order WHERE id = ?
            """, (expense_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_expense_order(self, expense_data: dict, is_new: bool = False) -> int:
        """費用項目を保存"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if is_new:
                cursor.execute("""
                    INSERT INTO expenses_order (
                        project_id, item_name, amount, supplier_id, contact_person,
                        status, order_number, order_date, implementation_date,
                        invoice_received_date, payment_scheduled_date, payment_date,
                        gmail_draft_id, gmail_message_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    expense_data.get('project_id', 0),
                    expense_data.get('item_name', ''),
                    expense_data.get('amount', 0.0),
                    expense_data.get('supplier_id'),
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
                    UPDATE expenses_order
                    SET project_id = ?, item_name = ?, amount = ?, supplier_id = ?,
                        contact_person = ?, status = ?, order_number = ?, order_date = ?,
                        implementation_date = ?, invoice_received_date = ?,
                        payment_scheduled_date = ?, payment_date = ?, gmail_draft_id = ?,
                        gmail_message_id = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    expense_data.get('project_id', 0),
                    expense_data.get('item_name', ''),
                    expense_data.get('amount', 0.0),
                    expense_data.get('supplier_id'),
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
            cursor.execute("DELETE FROM expenses_order WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # ========================================
    # 統計・集計
    # ========================================

    def get_project_summary(self, project_id: int) -> dict:
        """案件の予算・実績サマリーを取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 案件情報取得
            cursor.execute("SELECT budget FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            budget = row[0] if row else 0.0

            # 実績合計取得
            cursor.execute("""
                SELECT SUM(amount) FROM expenses_order WHERE project_id = ?
            """, (project_id,))
            row = cursor.fetchone()
            actual = row[0] if row and row[0] else 0.0

            return {
                'budget': budget,
                'actual': actual,
                'remaining': budget - actual,
            }
        finally:
            conn.close()

    # ========================================
    # 番組マスター操作
    # ========================================

    def get_programs(self, search_term: str = "", status: str = "") -> List[Tuple]:
        """番組マスター一覧を取得

        Args:
            search_term: 検索キーワード
            status: ステータスフィルタ（'放送中' or '終了' or ''）

        Returns:
            List[Tuple]: (id, name, description, start_date, end_date,
                         broadcast_time, broadcast_days, status,
                         program_type, parent_program_id)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, description, start_date, end_date,
                       broadcast_time, broadcast_days, status,
                       program_type, parent_program_id
                FROM programs
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

    def get_program_by_id(self, program_id: int) -> Optional[Tuple]:
        """IDで番組を取得

        Returns:
            Tuple: (id, name, description, start_date, end_date,
                   broadcast_time, broadcast_days, status,
                   program_type, parent_program_id, created_at, updated_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, start_date, end_date,
                       broadcast_time, broadcast_days, status,
                       program_type, parent_program_id,
                       created_at, updated_at
                FROM programs WHERE id = ?
            """, (program_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_program(self, program_data: dict, is_new: bool = True):
        """番組を保存

        Args:
            program_data: 番組データ辞書
                - name: 番組名（必須）
                - description: 備考
                - start_date: 開始日
                - end_date: 終了日
                - broadcast_time: 放送時間
                - broadcast_days: 放送曜日（カンマ区切り）
                - status: ステータス
            is_new: 新規登録かどうか
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now()

            if is_new:
                cursor.execute("""
                    INSERT INTO programs (
                        name, description, start_date, end_date,
                        broadcast_time, broadcast_days, status,
                        program_type, parent_program_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    program_data['name'],
                    program_data.get('description', ''),
                    program_data.get('start_date'),
                    program_data.get('end_date'),
                    program_data.get('broadcast_time', ''),
                    program_data.get('broadcast_days', ''),
                    program_data.get('status', '放送中'),
                    program_data.get('program_type', 'レギュラー'),
                    program_data.get('parent_program_id'),
                    now,
                    now
                ))
                program_id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE programs SET
                        name = ?,
                        description = ?,
                        start_date = ?,
                        end_date = ?,
                        broadcast_time = ?,
                        broadcast_days = ?,
                        status = ?,
                        program_type = ?,
                        parent_program_id = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    program_data['name'],
                    program_data.get('description', ''),
                    program_data.get('start_date'),
                    program_data.get('end_date'),
                    program_data.get('broadcast_time', ''),
                    program_data.get('broadcast_days', ''),
                    program_data.get('status', '放送中'),
                    program_data.get('program_type', 'レギュラー'),
                    program_data.get('parent_program_id'),
                    now,
                    program_data['id']
                ))
                program_id = program_data['id']

            conn.commit()
            return program_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_program(self, program_id: int):
        """番組を削除（関連する出演者・制作会社も削除）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 関連案件が存在するかチェック
            cursor.execute("""
                SELECT COUNT(*) FROM projects WHERE program_id = ?
            """, (program_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                raise Exception(f"この番組には{count}件の案件が関連付けられています。削除できません。")

            # CASCADE削除により出演者・制作会社も自動削除される
            cursor.execute("DELETE FROM programs WHERE id = ?", (program_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_program_cast(self, program_id: int) -> List[Tuple]:
        """番組の出演者一覧を取得

        Returns:
            List[Tuple]: (id, program_id, cast_name, role)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, program_id, cast_name, role
                FROM program_cast
                WHERE program_id = ?
                ORDER BY cast_name
            """, (program_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_program_cast(self, program_id: int, cast_list: List[dict]):
        """番組の出演者を保存（既存データを全削除して再登録）

        Args:
            program_id: 番組ID
            cast_list: 出演者リスト [{'cast_name': '名前', 'role': '役割'}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 既存の出演者を全削除
            cursor.execute("DELETE FROM program_cast WHERE program_id = ?", (program_id,))

            # 新しい出演者を登録
            now = datetime.now()
            for cast in cast_list:
                cursor.execute("""
                    INSERT INTO program_cast (program_id, cast_name, role, created_at)
                    VALUES (?, ?, ?, ?)
                """, (program_id, cast['cast_name'], cast.get('role', ''), now))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_program_producers(self, program_id: int) -> List[Tuple]:
        """番組の制作会社一覧を取得

        Returns:
            List[Tuple]: (program_producers.id, partner_id, partner_name, partner_code)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT pp.id, pp.partner_id, p.name, p.code
                FROM program_producers pp
                INNER JOIN partners p ON pp.partner_id = p.id
                WHERE pp.program_id = ?
                ORDER BY p.name
            """, (program_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_program_producers(self, program_id: int, partner_ids: List[int]):
        """番組の制作会社を保存（既存データを全削除して再登録）

        Args:
            program_id: 番組ID
            partner_ids: 取引先IDのリスト
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 既存の制作会社を全削除
            cursor.execute("DELETE FROM program_producers WHERE program_id = ?", (program_id,))

            # 新しい制作会社を登録
            now = datetime.now()
            for partner_id in partner_ids:
                cursor.execute("""
                    INSERT INTO program_producers (program_id, partner_id, created_at)
                    VALUES (?, ?, ?)
                """, (program_id, partner_id, now))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

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
                FROM cast c INNER JOIN partners p ON c.partner_id = p.id WHERE 1=1
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
            cursor.execute("SELECT COUNT(*) FROM program_cast WHERE cast_id = ?", (cast_id,))
            if cursor.fetchone()[0] > 0:
                raise Exception("この出演者は番組に関連付けられています。削除できません。")
            cursor.execute("DELETE FROM cast WHERE id = ?", (cast_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_program_cast_v2(self, program_id: int) -> List[Tuple]:
        """番組の出演者一覧を取得（castテーブル経由）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT pc.id, c.id, c.name, p.name, pc.role
                FROM program_cast pc
                INNER JOIN cast c ON pc.cast_id = c.id
                INNER JOIN partners p ON c.partner_id = p.id
                WHERE pc.program_id = ? ORDER BY c.name
            """, (program_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_program_cast_v2(self, program_id: int, cast_assignments: List[dict]):
        """番組の出演者を保存（castテーブル経由）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM program_cast WHERE program_id = ?", (program_id,))
            now = datetime.now()
            for assignment in cast_assignments:
                cursor.execute("INSERT INTO program_cast (program_id, cast_id, role, created_at) VALUES (?, ?, ?, ?)",
                              (program_id, assignment['cast_id'], assignment.get('role', ''), now))
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
            search_term: 検索キーワード（取引先名、番組名）
            pdf_status: PDFステータスフィルタ
            order_type: 発注種別フィルタ（契約書/発注書/メール発注）
            order_status: 発注ステータスフィルタ（未/済）

        Returns:
            List[Tuple]: (id, program_id, program_name, partner_id, partner_name,
                         contract_start_date, contract_end_date, contract_period_type,
                         pdf_status, pdf_distributed_date,
                         pdf_file_path, notes, order_type, order_status,
                         email_sent_date)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes,
                       COALESCE(oc.order_type, '発注書') as order_type,
                       COALESCE(oc.order_status, '未') as order_status,
                       oc.email_sent_date,
                       proj.name as project_name,
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
                       COALESCE(oc.renewal_count, 0) as renewal_count
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                LEFT JOIN projects proj ON oc.project_id = proj.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND (prog.name LIKE ? OR p.name LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])

            if pdf_status:
                query += " AND oc.pdf_status = ?"
                params.append(pdf_status)

            if order_type:
                query += " AND COALESCE(oc.order_type, '発注書') = ?"
                params.append(order_type)

            if order_status:
                query += " AND COALESCE(oc.order_status, '未') = ?"
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
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes,
                       oc.created_at, oc.updated_at,
                       COALESCE(oc.order_type, '発注書') as order_type,
                       COALESCE(oc.order_status, '未完了') as order_status,
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
                       COALESCE(oc.renewal_count, 0) as renewal_count
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                LEFT JOIN projects proj ON oc.project_id = proj.id
                WHERE oc.id = ?
            """, (contract_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_order_contracts_by_program(self, program_id: int) -> List[Tuple]:
        """番組IDで発注書を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date,
                       oc.pdf_file_path, oc.notes
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.program_id = ?
                ORDER BY oc.contract_start_date DESC
            """, (program_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def save_order_contract(self, contract_data: dict) -> int:
        """発注書を保存

        Args:
            contract_data: 発注書データ
                - id: 契約ID（更新時のみ）
                - program_id: 番組ID
                - partner_id: 取引先ID
                - contract_start_date: 委託開始日
                - contract_end_date: 委託終了日
                - contract_period_type: 契約期間種別
                - order_type: 発注種別（契約書/発注書/メール発注）
                - order_status: 発注ステータス（未/済）
                - pdf_status: PDFステータス
                - pdf_file_path: PDFファイルパス
                - pdf_distributed_date: PDF配布日
                - email_sent_date: メール送信日
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
                    UPDATE order_contracts SET
                        project_id = ?,
                        item_name = ?,
                        program_id = ?,
                        partner_id = ?,
                        contract_start_date = ?,
                        contract_end_date = ?,
                        contract_period_type = ?,
                        order_type = ?,
                        order_status = ?,
                        pdf_status = ?,
                        pdf_file_path = ?,
                        pdf_distributed_date = ?,
                        email_sent_date = ?,
                        notes = ?,
                        payment_type = ?,
                        unit_price = ?,
                        payment_timing = ?,
                        contract_type = ?,
                        project_name_type = ?,
                        implementation_date = ?,
                        spot_amount = ?,
                        order_category = ?,
                        auto_renewal_enabled = ?,
                        renewal_period_months = ?,
                        termination_notice_date = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    contract_data.get('project_id'),
                    contract_data.get('item_name'),
                    contract_data['program_id'],  # NOT NULL制約があるため必須
                    contract_data['partner_id'],
                    contract_data.get('contract_start_date', ''),
                    contract_data.get('contract_end_date', ''),
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('order_type', '発注書'),
                    contract_data.get('order_status', '未完了'),
                    contract_data.get('pdf_status', '未配布'),
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('pdf_distributed_date', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('notes', ''),
                    contract_data.get('payment_type', '月額固定'),
                    contract_data.get('unit_price'),
                    contract_data.get('payment_timing', '翌月末払い'),
                    contract_data.get('contract_type', 'regular_fixed'),
                    contract_data.get('project_name_type', 'program'),
                    contract_data.get('implementation_date', ''),
                    contract_data.get('spot_amount'),
                    contract_data.get('order_category', 'レギュラー制作発注書'),
                    contract_data.get('auto_renewal_enabled', 1),
                    contract_data.get('renewal_period_months', 3),
                    contract_data.get('termination_notice_date'),
                    now,
                    contract_id
                ))
            else:
                # 新規追加
                cursor.execute("""
                    INSERT INTO order_contracts (
                        project_id, item_name, program_id, partner_id,
                        contract_start_date, contract_end_date,
                        contract_period_type, order_type, order_status,
                        pdf_status, pdf_file_path,
                        pdf_distributed_date,
                        email_sent_date,
                        notes, payment_type, unit_price, payment_timing,
                        contract_type, project_name_type,
                        implementation_date, spot_amount, order_category,
                        auto_renewal_enabled, renewal_period_months, termination_notice_date,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_data.get('project_id'),
                    contract_data.get('item_name'),
                    contract_data['program_id'],  # NOT NULL制約があるため必須
                    contract_data['partner_id'],
                    contract_data.get('contract_start_date', ''),
                    contract_data.get('contract_end_date', ''),
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('order_type', '発注書'),
                    contract_data.get('order_status', '未完了'),
                    contract_data.get('pdf_status', '未配布'),
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('pdf_distributed_date', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('notes', ''),
                    contract_data.get('payment_type', '月額固定'),
                    contract_data.get('unit_price'),
                    contract_data.get('payment_timing', '翌月末払い'),
                    contract_data.get('contract_type', 'regular_fixed'),
                    contract_data.get('project_name_type', 'program'),
                    contract_data.get('implementation_date', ''),
                    contract_data.get('spot_amount'),
                    contract_data.get('order_category', 'レギュラー制作発注書'),
                    contract_data.get('auto_renewal_enabled', 1),
                    contract_data.get('renewal_period_months', 3),
                    contract_data.get('termination_notice_date'),
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
        """発注書を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM order_contracts WHERE id = ?", (contract_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_pdf_status(self, contract_id: int, pdf_status: str,
                         distributed_date: str = None):
        """PDF配布ステータスを更新"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now()
            cursor.execute("""
                UPDATE order_contracts SET
                    pdf_status = ?,
                    pdf_distributed_date = ?,
                    updated_at = ?
                WHERE id = ?
            """, (pdf_status, distributed_date or '', now, contract_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def sync_contract_to_program(self, contract_id: int) -> bool:
        """発注書の委託期間を番組マスタに同期"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 発注書情報を取得
            cursor.execute("""
                SELECT program_id, contract_start_date, contract_end_date
                FROM order_contracts WHERE id = ?
            """, (contract_id,))

            row = cursor.fetchone()
            if not row:
                return False

            program_id, start_date, end_date = row

            # 番組マスタを更新
            now = datetime.now()
            cursor.execute("""
                UPDATE programs SET
                    start_date = ?,
                    end_date = ?,
                    updated_at = ?
                WHERE id = ?
            """, (start_date, end_date, now, program_id))

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
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
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
                            'project_name': 案件名,
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
                    eo.id,
                    eo.order_number,
                    eo.project_id,
                    p.name as project_name,
                    prog.broadcast_days,
                    eo.item_name,
                    eo.supplier_id,
                    eo.expected_payment_amount,
                    eo.expected_payment_date,
                    eo.payment_status,
                    eo.payment_matched_id,
                    eo.payment_difference,
                    COALESCE(oc.order_type, '発注書') as order_type,
                    COALESCE(oc.payment_type, '月額固定') as payment_type,
                    oc.unit_price,
                    COALESCE(oc.payment_timing, '翌月末払い') as payment_timing
                FROM expenses_order eo
                LEFT JOIN projects p ON eo.project_id = p.id
                LEFT JOIN programs prog ON p.program_id = prog.id
                LEFT JOIN order_contracts oc ON (
                    (oc.project_id IS NOT NULL AND eo.project_id = oc.project_id AND eo.item_name = oc.item_name)
                    OR (oc.project_id IS NULL AND p.program_id = oc.program_id)
                ) AND eo.supplier_id = oc.partner_id
                WHERE strftime('%Y-%m', eo.expected_payment_date) = ?
                ORDER BY eo.supplier_id, eo.expected_payment_date
            """, (target_month,))

            orders = cursor.fetchall()

            # 取引先ごとにグループ化
            partners_dict = {}

            for order in orders:
                (order_id, order_number, project_id, project_name, broadcast_days, item_name,
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
                FROM expenses_order
                WHERE strftime('%Y-%m', expected_payment_date) = ?
            """, (target_month,))

            total_orders, total_amount = cursor.fetchone()

            # 支払済
            cursor.execute("""
                SELECT
                    COUNT(*) as paid_count,
                    COALESCE(SUM(expected_payment_amount), 0) as paid_amount
                FROM expenses_order
                WHERE strftime('%Y-%m', expected_payment_date) = ?
                  AND payment_status = '支払済'
            """, (target_month,))

            paid_count, paid_amount = cursor.fetchone()

            # 未払い
            cursor.execute("""
                SELECT
                    COUNT(*) as unpaid_count,
                    COALESCE(SUM(expected_payment_amount), 0) as unpaid_amount
                FROM expenses_order
                WHERE strftime('%Y-%m', expected_payment_date) = ?
                  AND payment_status = '未払い'
            """, (target_month,))

            unpaid_count, unpaid_amount = cursor.fetchone()

            # 金額相違
            cursor.execute("""
                SELECT
                    COUNT(*) as mismatch_count,
                    COALESCE(SUM(ABS(payment_difference)), 0) as mismatch_amount
                FROM expenses_order
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
        1. programsテーブルに program_type, parent_program_id を追加
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

            if 'program_type' not in columns:
                log_message("programsテーブルにprogram_typeカラムを追加")
                cursor.execute("""
                    ALTER TABLE programs
                    ADD COLUMN program_type TEXT DEFAULT 'レギュラー'
                """)

                # 既存データにデフォルト値を設定
                cursor.execute("""
                    UPDATE programs
                    SET program_type = 'レギュラー'
                    WHERE program_type IS NULL
                """)

            if 'parent_program_id' not in columns:
                log_message("programsテーブルにparent_program_idカラムを追加")
                cursor.execute("""
                    ALTER TABLE programs
                    ADD COLUMN parent_program_id INTEGER REFERENCES programs(id)
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
                    UPDATE projects
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

    def get_programs_with_hierarchy(self, search_term: str = "",
                                    program_type: str = "",
                                    include_children: bool = True) -> List[Tuple]:
        """番組一覧を階層情報付きで取得

        Args:
            search_term: 検索キーワード
            program_type: 番組種別フィルタ（'レギュラー'/'単発'/'コーナー'）
            include_children: コーナー（子番組）を含めるか

        Returns:
            List[Tuple]: (id, name, description, start_date, end_date,
                         broadcast_time, broadcast_days, status,
                         program_type, parent_program_id, parent_name)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT p.id, p.name, p.description, p.start_date, p.end_date,
                       p.broadcast_time, p.broadcast_days, p.status,
                       COALESCE(p.program_type, 'レギュラー') as program_type,
                       p.parent_program_id,
                       parent.name as parent_name
                FROM programs p
                LEFT JOIN programs parent ON p.parent_program_id = parent.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND p.name LIKE ?"
                params.append(f"%{search_term}%")

            if program_type:
                query += " AND COALESCE(p.program_type, 'レギュラー') = ?"
                params.append(program_type)

            if not include_children:
                query += " AND p.parent_program_id IS NULL"

            query += " ORDER BY p.parent_program_id NULLS FIRST, p.name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_program_children(self, parent_program_id: int) -> List[Tuple]:
        """指定番組の子番組（コーナー）一覧を取得

        Args:
            parent_program_id: 親番組ID

        Returns:
            List[Tuple]: (id, name, description, start_date, end_date,
                         broadcast_time, broadcast_days, status, program_type)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, start_date, end_date,
                       broadcast_time, broadcast_days, status,
                       COALESCE(program_type, 'コーナー') as program_type
                FROM programs
                WHERE parent_program_id = ?
                ORDER BY name
            """, (parent_program_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    # ========================================
    # 案件（プロジェクト）関連の拡張操作
    # ========================================

    def get_projects_by_program(self, program_id: int,
                                project_type: str = "") -> List[Tuple]:
        """指定番組に紐づく案件一覧を取得

        Args:
            program_id: 番組ID
            project_type: 案件種別フィルタ（'イベント'/'特別企画'/'通常'）

        Returns:
            List[Tuple]: (id, name, date, type, budget, parent_id,
                         start_date, end_date, project_type, program_id, program_name)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT p.id, p.name, p.date, p.type, p.budget, p.parent_id,
                       p.start_date, p.end_date,
                       COALESCE(p.project_type, 'イベント') as project_type,
                       p.program_id,
                       prog.name as program_name
                FROM projects p
                LEFT JOIN programs prog ON p.program_id = prog.id
                WHERE p.program_id = ?
            """
            params = [program_id]

            if project_type:
                query += " AND COALESCE(p.project_type, 'イベント') = ?"
                params.append(project_type)

            query += " ORDER BY p.start_date DESC, p.name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_order_contracts_with_project_info(self, search_term: str = "",
                                              program_id: int = None,
                                              project_id: int = None) -> List[Tuple]:
        """発注書一覧を案件情報付きで取得

        Args:
            search_term: 検索キーワード
            program_id: 番組IDフィルタ
            project_id: 案件IDフィルタ

        Returns:
            List[Tuple]: (id, program_id, program_name, project_id, project_name,
                         partner_id, partner_name, item_name, contract_start_date,
                         contract_end_date, order_type, order_status, ...)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.project_id, proj.name as project_name,
                       oc.partner_id, part.name as partner_name,
                       oc.item_name, oc.contract_start_date, oc.contract_end_date,
                       oc.order_type, oc.order_status, oc.pdf_status,
                       oc.notes, oc.created_at, oc.updated_at,
                       oc.payment_type, oc.unit_price
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN projects proj ON oc.project_id = proj.id
                LEFT JOIN partners part ON oc.partner_id = part.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += """ AND (prog.name LIKE ? OR proj.name LIKE ?
                            OR part.name LIKE ? OR oc.item_name LIKE ?)"""
                params.extend([f"%{search_term}%"] * 4)

            if program_id:
                query += " AND oc.program_id = ?"
                params.append(program_id)

            if project_id:
                query += " AND oc.project_id = ?"
                params.append(project_id)

            query += " ORDER BY oc.contract_start_date DESC, prog.name, proj.name"

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

    def import_programs_from_csv(self, csv_data: List[dict], overwrite: bool = False) -> dict:
        """番組データをCSVから一括インポート

        Args:
            csv_data: CSVから読み込んだ辞書のリスト
                     期待されるキー: ID, 番組名, 説明, 開始日, 終了日,
                                    放送時間, 放送曜日, ステータス, 番組種別, 親番組ID
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
                cursor.execute("DELETE FROM programs")
                conn.commit()
            for row_num, row_data in enumerate(csv_data, start=2):
                try:
                    # 必須項目チェック
                    program_name = row_data.get('番組名', '').strip()

                    if not program_name:
                        result['errors'].append({'row': row_num, 'reason': '番組名が空です'})
                        result['skipped'] += 1
                        continue

                    # データ取得
                    description = row_data.get('説明', '').strip()
                    start_date_raw = row_data.get('開始日', '').strip()
                    end_date_raw = row_data.get('終了日', '').strip()
                    broadcast_time = row_data.get('放送時間', '').strip()
                    broadcast_days_raw = row_data.get('放送曜日', '').strip()
                    status = row_data.get('ステータス', '放送中').strip()
                    program_type = row_data.get('番組種別', 'レギュラー').strip()
                    parent_program_id_str = row_data.get('親番組ID', '').strip()

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

                    # 親番組IDのチェック
                    parent_program_id = None
                    if parent_program_id_str and parent_program_id_str.isdigit():
                        parent_program_id = int(parent_program_id_str)
                        cursor.execute("SELECT id FROM programs WHERE id = ?", (parent_program_id,))
                        if not cursor.fetchone():
                            result['errors'].append({'row': row_num, 'reason': f'親番組ID {parent_program_id} が見つかりません'})
                            result['skipped'] += 1
                            continue

                    program_id_str = row_data.get('ID', '').strip()
                    now = datetime.now()

                    # UPSERTロジック: IDまたは番組名で既存レコードを検索
                    existing_program = None
                    if program_id_str and program_id_str.isdigit():
                        # IDが指定されている場合はIDで検索
                        program_id = int(program_id_str)
                        cursor.execute("SELECT id FROM programs WHERE id = ?", (program_id,))
                        existing_program = cursor.fetchone()
                    else:
                        # IDがない場合は番組名で検索
                        cursor.execute("SELECT id FROM programs WHERE name = ?", (program_name,))
                        existing_program = cursor.fetchone()

                    if existing_program:
                        # 既存番組を更新
                        existing_id = existing_program[0]
                        cursor.execute("""
                            UPDATE programs
                            SET name=?, description=?, start_date=?, end_date=?,
                                broadcast_time=?, broadcast_days=?, status=?,
                                program_type=?, parent_program_id=?, updated_at=?
                            WHERE id=?
                        """, (program_name, description, start_date or None, end_date or None,
                              broadcast_time, broadcast_days, status, program_type,
                              parent_program_id, now, existing_id))
                        result['updated'] += 1
                        result['success'] += 1
                    else:
                        # 新規追加
                        cursor.execute("""
                            INSERT INTO programs (name, description, start_date, end_date,
                                                 broadcast_time, broadcast_days, status,
                                                 program_type, parent_program_id, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (program_name, description, start_date or None, end_date or None,
                              broadcast_time, broadcast_days, status, program_type,
                              parent_program_id, now, now))
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
                     期待されるキー: ID, 番組名, 取引先名, 委託開始日, 委託終了日,
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
            'errors': []
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 上書きモードの場合は既存データを削除
            if overwrite:
                cursor.execute("DELETE FROM order_contracts")
                conn.commit()
            for row_num, row_data in enumerate(csv_data, start=2):
                try:
                    # 必須項目チェック
                    program_name = row_data.get('番組名', '').strip()
                    partner_name = row_data.get('取引先名', '').strip()
                    start_date_raw = row_data.get('委託開始日', '').strip()
                    end_date_raw = row_data.get('委託終了日', '').strip()

                    if not program_name:
                        result['errors'].append({'row': row_num, 'reason': '番組名が空です'})
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

                    # 番組IDを検索
                    cursor.execute("SELECT id FROM programs WHERE name = ?", (program_name,))
                    program_result = cursor.fetchone()

                    if not program_result:
                        result['errors'].append({'row': row_num, 'reason': f'番組「{program_name}」が見つかりません'})
                        result['skipped'] += 1
                        continue

                    program_id = program_result[0]

                    # 取引先IDを検索
                    cursor.execute("SELECT id FROM partners WHERE name = ?", (partner_name,))
                    partner_result = cursor.fetchone()

                    if not partner_result:
                        result['errors'].append({'row': row_num, 'reason': f'取引先「{partner_name}」が見つかりません'})
                        result['skipped'] += 1
                        continue

                    partner_id = partner_result[0]

                    # その他のデータ取得（全項目対応）
                    project_name = row_data.get('案件名', '').strip()
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

                    # 案件IDを取得（案件名が指定されている場合）
                    project_id = None
                    if project_name:
                        cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
                        project_result = cursor.fetchone()
                        if project_result:
                            project_id = project_result[0]

                    contract_id_str = row_data.get('ID', '').strip()
                    now = datetime.now()

                    # UPSERTロジック: IDまたは番組+取引先+期間で既存レコードを検索
                    existing_contract = None
                    if contract_id_str and contract_id_str.isdigit():
                        # IDが指定されている場合はIDで検索
                        contract_id = int(contract_id_str)
                        cursor.execute("SELECT id FROM order_contracts WHERE id = ?", (contract_id,))
                        existing_contract = cursor.fetchone()
                    else:
                        # IDがない場合は番組+取引先+期間で検索
                        cursor.execute("""
                            SELECT id FROM order_contracts
                            WHERE program_id = ? AND partner_id = ?
                            AND contract_start_date = ? AND contract_end_date = ?
                        """, (program_id, partner_id, start_date, end_date))
                        existing_contract = cursor.fetchone()

                    if existing_contract:
                        # 既存発注を更新（全項目対応）
                        existing_id = existing_contract[0]
                        cursor.execute("""
                            UPDATE order_contracts
                            SET program_id=?, partner_id=?, project_id=?, item_name=?,
                                contract_start_date=?, contract_end_date=?, contract_period_type=?,
                                order_type=?, order_status=?, pdf_status=?, pdf_file_path=?, pdf_distributed_date=?,
                                payment_type=?, unit_price=?, payment_timing=?, contract_type=?,
                                implementation_date=?, spot_amount=?, order_category=?,
                                email_subject=?, email_body=?, email_to=?, email_sent_date=?,
                                auto_renewal_enabled=?, renewal_period_months=?, termination_notice_date=?,
                                notes=?, updated_at=?
                            WHERE id=?
                        """, (program_id, partner_id, project_id, item_name,
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
                            INSERT INTO order_contracts (
                                program_id, partner_id, project_id, item_name,
                                contract_start_date, contract_end_date, contract_period_type,
                                order_type, order_status, pdf_status, pdf_file_path, pdf_distributed_date,
                                payment_type, unit_price, payment_timing, contract_type,
                                implementation_date, spot_amount, order_category,
                                email_subject, email_body, email_to, email_sent_date,
                                auto_renewal_enabled, renewal_period_months, termination_notice_date,
                                notes, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (program_id, partner_id, project_id, item_name,
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
                FROM order_contracts
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
                UPDATE order_contracts
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
                SELECT oc.id, prog.name as program_name, p.name as partner_name,
                       oc.contract_end_date, oc.renewal_period_months,
                       oc.renewal_count, oc.item_name
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
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
                SELECT oc.id, prog.name as program_name, p.name as partner_name,
                       oc.contract_end_date, oc.auto_renewal_enabled,
                       oc.termination_notice_date, oc.renewal_count,
                       oc.item_name
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
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
