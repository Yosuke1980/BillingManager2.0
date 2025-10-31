"""メールテンプレート

発注メールのテンプレートを生成します。
"""
from datetime import datetime
from typing import Dict


class EmailTemplate:
    """メールテンプレートクラス"""

    @staticmethod
    def generate_subject(order_number: str, implementation_date: str,
                        project_name: str, item_name: str) -> str:
        """件名を生成

        Args:
            order_number: 発注番号
            implementation_date: 実施日
            project_name: 案件名
            item_name: 項目名

        Returns:
            str: メール件名
        """
        return f"【発注 {order_number}】{implementation_date} {project_name} - {item_name}"

    @staticmethod
    def generate_body(data: Dict[str, any], signature: str = "") -> str:
        """本文を生成

        Args:
            data: メールデータ
                - contact_person: 担当者名
                - order_number: 発注番号
                - project_name: 案件名
                - implementation_date: 実施日
                - item_name: 項目名（出演者/作業者名）
                - amount: 金額
                - payment_scheduled_date: 支払予定日

        Returns:
            str: メール本文
        """
        contact_person = data.get('contact_person', '担当者')
        order_number = data.get('order_number', '')
        project_name = data.get('project_name', '')
        implementation_date = data.get('implementation_date', '')
        item_name = data.get('item_name', '')
        amount = data.get('amount', 0)
        payment_scheduled_date = data.get('payment_scheduled_date', '')

        # 金額をカンマ区切りに
        amount_str = f"{amount:,.0f}"

        body = f"""{contact_person}様

お世話になっております。

下記の通り、ご依頼申し上げます。

━━━━━━━━━━━━━━━━━━━━━━
■発注番号: {order_number}
■案件名: {project_name}
■実施日: {implementation_date}
■ご担当: {item_name}
■金額: {amount_str}円
━━━━━━━━━━━━━━━━━━━━━━

■お支払予定日: {payment_scheduled_date}

実施後、下記内容を含む請求書をお送りいただけますと幸いです。
・発注番号: {order_number}
・案件名: {project_name}
・金額: {amount_str}円

何卒よろしくお願いいたします。

{signature}"""

        return body

    @staticmethod
    def format_date(date_str: str, format: str = "%Y年%m月%d日") -> str:
        """日付文字列をフォーマット

        Args:
            date_str: 日付文字列 (YYYY-MM-DD)
            format: 出力フォーマット

        Returns:
            str: フォーマット済み日付
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime(format)
        except ValueError:
            return date_str
