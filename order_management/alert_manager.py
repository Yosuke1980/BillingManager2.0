"""アラート管理

請求書未着や下書き未送信などのアラートを管理します。
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict


class AlertManager:
    """アラート管理クラス"""

    def __init__(self, db_path="order_management.db"):
        self.db_path = db_path

    def get_invoice_waiting_alerts(self) -> List[Dict]:
        """請求書未着アラートを取得

        条件:
        - ステータスが「実施済」または「請求書待ち」
        - 実施日の翌日を過ぎている
        - 請求書受領日が未設定

        Returns:
            List[Dict]: アラート情報のリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT e.id, e.item_name, e.implementation_date,
                       prod.name as production_name, prod.start_date as production_date,
                       s.name as supplier_name, e.contact_person
                FROM expenses_order e
                JOIN productions prod ON e.production_id = prod.id
                LEFT JOIN suppliers s ON e.supplier_id = s.id
                WHERE (e.status = '実施済' OR e.status = '請求書待ち')
                  AND e.implementation_date <= ?
                  AND (e.invoice_received_date IS NULL OR e.invoice_received_date = '')
                ORDER BY e.implementation_date
            """, (yesterday_str,))

            rows = cursor.fetchall()
            alerts = []

            for row in rows:
                alerts.append({
                    'expense_id': row[0],
                    'item_name': row[1],
                    'implementation_date': row[2],
                    'production_name': row[3],
                    'production_date': row[4],
                    'supplier_name': row[5] or "(未設定)",
                    'contact_person': row[6] or "",
                })

            return alerts

        finally:
            conn.close()

    def get_draft_unsent_alerts(self) -> List[Dict]:
        """下書き未送信アラートを取得

        条件:
        - ステータスが「下書き作成済」
        - 作成から24時間以上経過

        Returns:
            List[Dict]: アラート情報のリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            threshold = datetime.now() - timedelta(hours=24)
            threshold_str = threshold.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                SELECT e.id, e.item_name, e.updated_at,
                       prod.name as production_name, prod.start_date as production_date,
                       s.name as supplier_name, e.contact_person
                FROM expenses_order e
                JOIN productions prod ON e.production_id = prod.id
                LEFT JOIN suppliers s ON e.supplier_id = s.id
                WHERE e.status = '下書き作成済'
                  AND e.updated_at <= ?
                ORDER BY e.updated_at
            """, (threshold_str,))

            rows = cursor.fetchall()
            alerts = []

            for row in rows:
                alerts.append({
                    'expense_id': row[0],
                    'item_name': row[1],
                    'updated_at': row[2],
                    'production_name': row[3],
                    'production_date': row[4],
                    'supplier_name': row[5] or "(未設定)",
                    'contact_person': row[6] or "",
                })

            return alerts

        finally:
            conn.close()

    def get_contract_expiring_alerts(self, days_before: int = 30) -> List[Dict]:
        """契約期限切れ間近アラートを取得

        条件:
        - 契約終了日が指定日数以内
        - 終了通知未受領
        - 自動延長が有効な契約も含む

        Args:
            days_before: 何日前から対象にするか（デフォルト: 30日）

        Returns:
            List[Dict]: アラート情報のリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            today = datetime.now().date()
            target_date = today + timedelta(days=days_before)
            today_str = today.strftime("%Y-%m-%d")
            target_str = target_date.strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT oc.id, prod.name as production_name, p.name as partner_name,
                       oc.contract_end_date, oc.auto_renewal_enabled,
                       oc.termination_notice_date, oc.item_name
                FROM order_contracts oc
                LEFT JOIN productions prod ON oc.production_id = prod.id
                LEFT JOIN partners p ON oc.partner_id = p.id
                WHERE oc.contract_end_date BETWEEN ? AND ?
                  AND (oc.termination_notice_date IS NULL OR oc.termination_notice_date = '')
                ORDER BY oc.contract_end_date
            """, (today_str, target_str))

            rows = cursor.fetchall()
            alerts = []

            for row in rows:
                end_date = datetime.strptime(row[3], '%Y-%m-%d').date()
                days_until = (end_date - today).days

                alerts.append({
                    'contract_id': row[0],
                    'production_name': row[1],
                    'partner_name': row[2] or "(未設定)",
                    'contract_end_date': row[3],
                    'days_until_expiry': days_until,
                    'auto_renewal_enabled': bool(row[4]),
                    'item_name': row[6] or "",
                })

            return alerts

        finally:
            conn.close()

    def get_all_alerts(self) -> Dict[str, List[Dict]]:
        """全アラートを取得

        Returns:
            Dict: アラートタイプをキーとしたアラート情報の辞書
        """
        return {
            'invoice_waiting': self.get_invoice_waiting_alerts(),
            'draft_unsent': self.get_draft_unsent_alerts(),
            'contract_expiring': self.get_contract_expiring_alerts(30),
        }

    def get_alert_count(self) -> Dict[str, int]:
        """アラート件数を取得

        Returns:
            Dict: アラートタイプごとの件数
        """
        alerts = self.get_all_alerts()
        return {
            'invoice_waiting': len(alerts['invoice_waiting']),
            'draft_unsent': len(alerts['draft_unsent']),
            'contract_expiring': len(alerts['contract_expiring']),
            'total': len(alerts['invoice_waiting']) + len(alerts['draft_unsent']) + len(alerts['contract_expiring']),
        }
