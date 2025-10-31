"""統合取引先マスタ管理

支払先マスタと発注先マスタを統合した取引先マスタ(partners)のCRUD操作を提供します。
"""
import sqlite3
from typing import List, Optional, Tuple
from utils import log_message


class PartnerManager:
    """統合取引先マスタ管理クラス"""

    def __init__(self, db_path="order_management.db"):
        self.db_path = db_path

    def _get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)

    # ========================================
    # 取引先マスター操作
    # ========================================

    def get_partners(self, search_term: str = "", partner_type: str = "") -> List[Tuple]:
        """取引先一覧を取得

        Args:
            search_term: 検索文字列（名前、コード、担当者で検索）
            partner_type: 取引先区分でフィルタ（空文字列=全て、発注先、支払先、両方）

        Returns:
            [(id, name, code, contact_person, email, phone, address, partner_type, notes), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, name, code, contact_person, email, phone, address, partner_type, notes
                FROM partners
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND (name LIKE ? OR code LIKE ? OR contact_person LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if partner_type:
                query += " AND partner_type = ?"
                params.append(partner_type)

            query += " ORDER BY name"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_partner_by_id(self, partner_id: int) -> Optional[Tuple]:
        """IDで取引先を取得

        Returns:
            (id, name, code, contact_person, email, phone, address, partner_type, notes)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, code, contact_person, email, phone, address, partner_type, notes
                FROM partners WHERE id = ?
            """, (partner_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_partner_by_name(self, name: str) -> Optional[Tuple]:
        """名前で取引先を取得

        Returns:
            (id, name, code, contact_person, email, phone, address, partner_type, notes)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, code, contact_person, email, phone, address, partner_type, notes
                FROM partners WHERE name = ?
            """, (name,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_partner(self, partner_data: dict, is_new: bool = False) -> int:
        """取引先を保存

        Args:
            partner_data: {
                'id': int (更新時のみ),
                'name': str,
                'code': str,
                'contact_person': str,
                'email': str,
                'phone': str,
                'address': str,
                'partner_type': str,
                'notes': str
            }
            is_new: 新規作成の場合True

        Returns:
            取引先ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if is_new:
                cursor.execute("""
                    INSERT INTO partners (name, code, contact_person, email, phone,
                                         address, partner_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    partner_data.get('name', ''),
                    partner_data.get('code', ''),
                    partner_data.get('contact_person', ''),
                    partner_data.get('email', ''),
                    partner_data.get('phone', ''),
                    partner_data.get('address', ''),
                    partner_data.get('partner_type', '両方'),
                    partner_data.get('notes', ''),
                ))
                partner_id = cursor.lastrowid
                log_message(f"取引先保存完了: ID={partner_id}, 名前={partner_data.get('name')}")
            else:
                cursor.execute("""
                    UPDATE partners
                    SET name = ?, code = ?, contact_person = ?, email = ?,
                        phone = ?, address = ?, partner_type = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    partner_data.get('name', ''),
                    partner_data.get('code', ''),
                    partner_data.get('contact_person', ''),
                    partner_data.get('email', ''),
                    partner_data.get('phone', ''),
                    partner_data.get('address', ''),
                    partner_data.get('partner_type', '両方'),
                    partner_data.get('notes', ''),
                    partner_data['id'],
                ))
                partner_id = partner_data['id']
                log_message(f"取引先更新完了: ID={partner_id}")

            conn.commit()
            return partner_id

        except sqlite3.Error as e:
            log_message(f"取引先保存エラー: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_partner(self, partner_id: int):
        """取引先を削除

        Note: 外部キー制約により、関連する費用項目がある場合は削除できません
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM partners WHERE id = ?", (partner_id,))
            conn.commit()
            log_message(f"取引先削除完了: ID={partner_id}")

        except sqlite3.Error as e:
            log_message(f"取引先削除エラー: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_partner_suggestions(self, partial_name: str = "", partner_type: str = "") -> List[Tuple]:
        """取引先のオートコンプリート候補を取得

        Args:
            partial_name: 部分一致する名前
            partner_type: 取引先区分でフィルタ

        Returns:
            [(name, code, id), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT name, code, id FROM partners WHERE 1=1"
            params = []

            if partial_name:
                query += " AND name LIKE ?"
                params.append(f"%{partial_name}%")

            if partner_type:
                query += " AND (partner_type = ? OR partner_type = '両方')"
                params.append(partner_type)

            query += " ORDER BY name LIMIT 20"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_partner_count_by_type(self) -> dict:
        """取引先区分ごとの件数を取得

        Returns:
            {'発注先': int, '支払先': int, '両方': int, '合計': int}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT partner_type, COUNT(*) as count
                FROM partners
                GROUP BY partner_type
            """)

            results = {'発注先': 0, '支払先': 0, '両方': 0, '合計': 0}
            for partner_type, count in cursor.fetchall():
                results[partner_type] = count
                results['合計'] += count

            return results
        finally:
            conn.close()

    def check_duplicate_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """名前の重複チェック

        Args:
            name: チェックする名前
            exclude_id: 更新時に除外する自分自身のID

        Returns:
            重複がある場合True
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if exclude_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM partners
                    WHERE name = ? AND id != ?
                """, (name, exclude_id))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM partners
                    WHERE name = ?
                """, (name,))

            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    def check_duplicate_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """コードの重複チェック

        Args:
            code: チェックするコード
            exclude_id: 更新時に除外する自分自身のID

        Returns:
            重複がある場合True
        """
        if not code:  # コードが空の場合は重複チェックしない
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if exclude_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM partners
                    WHERE code = ? AND id != ?
                """, (code, exclude_id))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM partners
                    WHERE code = ?
                """, (code,))

            return cursor.fetchone()[0] > 0
        finally:
            conn.close()
