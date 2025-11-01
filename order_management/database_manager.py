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
                         broadcast_time, broadcast_days, status)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, description, start_date, end_date,
                       broadcast_time, broadcast_days, status
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
                   broadcast_time, broadcast_days, status, created_at, updated_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, description, start_date, end_date,
                       broadcast_time, broadcast_days, status,
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
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    program_data['name'],
                    program_data.get('description', ''),
                    program_data.get('start_date'),
                    program_data.get('end_date'),
                    program_data.get('broadcast_time', ''),
                    program_data.get('broadcast_days', ''),
                    program_data.get('status', '放送中'),
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
                         pdf_status, pdf_distributed_date, confirmed_by,
                         pdf_file_path, notes, order_type, order_status,
                         email_subject, email_body, email_sent_date, email_to)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT oc.id, oc.program_id, prog.name as program_name,
                       oc.partner_id, p.name as partner_name,
                       oc.contract_start_date, oc.contract_end_date,
                       oc.contract_period_type, oc.pdf_status,
                       oc.pdf_distributed_date, oc.confirmed_by,
                       oc.pdf_file_path, oc.notes,
                       COALESCE(oc.order_type, '発注書') as order_type,
                       COALESCE(oc.order_status, '未') as order_status,
                       oc.email_subject, oc.email_body, oc.email_sent_date, oc.email_to
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN partners p ON oc.partner_id = p.id
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
                       oc.pdf_distributed_date, oc.confirmed_by,
                       oc.pdf_file_path, oc.notes,
                       oc.created_at, oc.updated_at,
                       COALESCE(oc.order_type, '発注書') as order_type,
                       COALESCE(oc.order_status, '未') as order_status,
                       oc.email_subject, oc.email_body, oc.email_sent_date, oc.email_to
                FROM order_contracts oc
                LEFT JOIN programs prog ON oc.program_id = prog.id
                LEFT JOIN partners p ON oc.partner_id = p.id
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
                       oc.pdf_distributed_date, oc.confirmed_by,
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
                - confirmed_by: 確認者
                - email_subject: メール件名
                - email_body: メール本文
                - email_sent_date: メール送信日
                - email_to: メール送信先
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
                        confirmed_by = ?,
                        email_subject = ?,
                        email_body = ?,
                        email_sent_date = ?,
                        email_to = ?,
                        notes = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    contract_data['program_id'],
                    contract_data['partner_id'],
                    contract_data['contract_start_date'],
                    contract_data['contract_end_date'],
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('order_type', '発注書'),
                    contract_data.get('order_status', '未'),
                    contract_data.get('pdf_status', '未配布'),
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('pdf_distributed_date', ''),
                    contract_data.get('confirmed_by', ''),
                    contract_data.get('email_subject', ''),
                    contract_data.get('email_body', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('email_to', ''),
                    contract_data.get('notes', ''),
                    now,
                    contract_id
                ))
            else:
                # 新規追加
                cursor.execute("""
                    INSERT INTO order_contracts (
                        program_id, partner_id, contract_start_date, contract_end_date,
                        contract_period_type, order_type, order_status,
                        pdf_status, pdf_file_path,
                        pdf_distributed_date, confirmed_by,
                        email_subject, email_body, email_sent_date, email_to,
                        notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_data['program_id'],
                    contract_data['partner_id'],
                    contract_data['contract_start_date'],
                    contract_data['contract_end_date'],
                    contract_data.get('contract_period_type', '半年'),
                    contract_data.get('order_type', '発注書'),
                    contract_data.get('order_status', '未'),
                    contract_data.get('pdf_status', '未配布'),
                    contract_data.get('pdf_file_path', ''),
                    contract_data.get('pdf_distributed_date', ''),
                    contract_data.get('confirmed_by', ''),
                    contract_data.get('email_subject', ''),
                    contract_data.get('email_body', ''),
                    contract_data.get('email_sent_date', ''),
                    contract_data.get('email_to', ''),
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
                         distributed_date: str = None, confirmed_by: str = None):
        """PDF配布ステータスを更新"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now()
            cursor.execute("""
                UPDATE order_contracts SET
                    pdf_status = ?,
                    pdf_distributed_date = ?,
                    confirmed_by = ?,
                    updated_at = ?
                WHERE id = ?
            """, (pdf_status, distributed_date or '', confirmed_by or '', now, contract_id))
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
                       oc.pdf_distributed_date, oc.confirmed_by
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
