"""発注番号自動生成

発注番号を自動生成します。形式: RB-YYYYMMDD-XXX
"""
import sqlite3
from datetime import datetime
from typing import Optional


class OrderNumberGenerator:
    """発注番号生成クラス"""

    def __init__(self, db_path="order_management.db"):
        self.db_path = db_path

    def generate_order_number(self, date: Optional[str] = None) -> str:
        """発注番号を生成

        Args:
            date: 発注日 (YYYY-MM-DD形式)。Noneの場合は今日の日付を使用

        Returns:
            str: 発注番号 (例: RB-20250809-001)
        """
        # 日付を取得
        if date:
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()

        date_str = dt.strftime("%Y%m%d")

        # その日の最大連番を取得
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT order_number FROM expenses_order
                WHERE order_number LIKE ? || '%'
                ORDER BY order_number DESC
                LIMIT 1
            """, (f"RB-{date_str}-",))

            row = cursor.fetchone()

            if row:
                # 既存の最大番号から連番を抽出
                last_number = row[0]
                try:
                    last_seq = int(last_number.split('-')[-1])
                    next_seq = last_seq + 1
                except (ValueError, IndexError):
                    next_seq = 1
            else:
                # その日の最初の発注
                next_seq = 1

            # 発注番号を生成 (3桁ゼロ埋め)
            order_number = f"RB-{date_str}-{next_seq:03d}"

            # 重複チェック（念のため）
            cursor.execute("""
                SELECT COUNT(*) FROM expenses_order WHERE order_number = ?
            """, (order_number,))

            if cursor.fetchone()[0] > 0:
                # 重複していた場合は連番を増やす
                next_seq += 1
                order_number = f"RB-{date_str}-{next_seq:03d}"

            return order_number

        finally:
            conn.close()

    def validate_order_number(self, order_number: str) -> bool:
        """発注番号の形式をチェック

        Args:
            order_number: 発注番号

        Returns:
            bool: 有効な形式の場合True
        """
        import re
        pattern = r'^RB-\d{8}-\d{3}$'
        return bool(re.match(pattern, order_number))

    def is_duplicate(self, order_number: str) -> bool:
        """発注番号の重複チェック

        Args:
            order_number: 発注番号

        Returns:
            bool: 重複している場合True
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM expenses_order WHERE order_number = ?
            """, (order_number,))

            return cursor.fetchone()[0] > 0

        finally:
            conn.close()
