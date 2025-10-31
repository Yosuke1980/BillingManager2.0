"""発注管理データベースマネージャー

発注管理機能のデータベース操作を担当します。
"""
import sqlite3
from typing import List, Optional, Tuple
from datetime import datetime
from utils import log_message


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
