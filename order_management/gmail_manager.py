"""Gmail IMAP連携マネージャー

GmailとのIMAP連携を管理します。
"""
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, List, Tuple, Dict
from datetime import datetime
import time


class GmailManager:
    """Gmail IMAP連携マネージャー"""

    def __init__(self, email_address: str, app_password: str,
                 imap_server: str = "imap.gmail.com", imap_port: int = 993):
        """
        Args:
            email_address: Gmailアドレス
            app_password: アプリパスワード
            imap_server: IMAPサーバー
            imap_port: IMAPポート
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.imap = None

    def connect(self) -> bool:
        """Gmailに接続

        Returns:
            bool: 接続成功時True
        """
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap.login(self.email_address, self.app_password)
            return True
        except Exception as e:
            print(f"Gmail接続エラー: {e}")
            self.imap = None
            return False

    def disconnect(self):
        """Gmailから切断"""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
            self.imap = None

    def create_draft(self, to: str, subject: str, body: str) -> Optional[str]:
        """下書きを作成

        Args:
            to: 送信先メールアドレス
            subject: 件名
            body: 本文

        Returns:
            Optional[str]: 下書きID（失敗時はNone）
        """
        if not self.imap:
            if not self.connect():
                return None

        try:
            # メッセージ作成
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = Header(subject, 'utf-8')

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 下書きフォルダに保存
            self.imap.select('[Gmail]/Drafts')
            result = self.imap.append(
                '[Gmail]/Drafts',
                '',
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes()
            )

            if result[0] == 'OK':
                # 下書きIDを取得（最後に追加されたメッセージ）
                self.imap.select('[Gmail]/Drafts')
                _, data = self.imap.search(None, 'ALL')
                if data and data[0]:
                    draft_ids = data[0].split()
                    if draft_ids:
                        return draft_ids[-1].decode('utf-8')

            return None

        except Exception as e:
            print(f"下書き作成エラー: {e}")
            return None

    def search_sent_mail(self, order_number: str) -> Optional[Dict]:
        """送信メールを検索

        Args:
            order_number: 発注番号

        Returns:
            Optional[Dict]: メール情報（見つからない場合はNone）
        """
        if not self.imap:
            if not self.connect():
                return None

        try:
            # 送信済みフォルダを選択
            self.imap.select('[Gmail]/Sent Mail')

            # 件名で検索
            search_criteria = f'SUBJECT "{order_number}"'
            _, data = self.imap.search(None, search_criteria.encode('utf-8'))

            if data and data[0]:
                message_ids = data[0].split()
                if message_ids:
                    # 最新のメールを取得
                    latest_id = message_ids[-1]
                    _, msg_data = self.imap.fetch(latest_id, '(RFC822)')

                    if msg_data and msg_data[0]:
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # 送信日時を取得
                        date_str = email_message.get('Date', '')
                        try:
                            sent_date = email.utils.parsedate_to_datetime(date_str)
                        except:
                            sent_date = datetime.now()

                        return {
                            'message_id': latest_id.decode('utf-8'),
                            'subject': email_message.get('Subject', ''),
                            'to': email_message.get('To', ''),
                            'sent_at': sent_date,
                        }

            return None

        except Exception as e:
            print(f"送信メール検索エラー: {e}")
            return None

    def check_multiple_sent_mails(self, order_numbers: List[str]) -> Dict[str, Optional[Dict]]:
        """複数の発注番号の送信状況を一括チェック

        Args:
            order_numbers: 発注番号のリスト

        Returns:
            Dict[str, Optional[Dict]]: 発注番号をキーとした送信メール情報の辞書
        """
        results = {}

        if not self.imap:
            if not self.connect():
                return {num: None for num in order_numbers}

        for order_number in order_numbers:
            results[order_number] = self.search_sent_mail(order_number)

        return results

    def test_connection(self) -> Tuple[bool, str]:
        """接続テスト

        Returns:
            Tuple[bool, str]: (成功/失敗, メッセージ)
        """
        try:
            if self.connect():
                self.disconnect()
                return True, "Gmail接続に成功しました"
            else:
                return False, "Gmail接続に失敗しました"
        except Exception as e:
            return False, f"接続エラー: {str(e)}"

    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.disconnect()
