"""
照合システム用のユーティリティモジュール
matching_config.jsonに基づく照合ロジックを提供
"""

import json
import os
from typing import Dict, List, Any, Optional
from utils import log_message

class MatchingConfig:
    """照合設定管理クラス"""

    def __init__(self, config_path: str = "matching_config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                log_message(f"照合設定を読み込みました: {self.config_path}")
                return config
            else:
                log_message(f"設定ファイルが見つかりません: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            log_message(f"設定ファイル読み込みエラー: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "matching_system": {
                "version": "1.0",
                "description": "照合システム設定ファイル"
            }
        }

    def get_matching_conditions(self) -> List[Dict[str, Any]]:
        """照合条件を取得"""
        try:
            return self.config["matching_system"]["matching_conditions"]["priority_order"]
        except KeyError:
            return []

    def get_judgment_results(self) -> List[Dict[str, Any]]:
        """判定結果設定を取得"""
        try:
            return self.config["matching_system"]["judgment_results"]
        except KeyError:
            return []

    def get_database_config(self) -> Dict[str, Dict[str, str]]:
        """データベース設定を取得"""
        try:
            return self.config["matching_system"]["database_structure"]
        except KeyError:
            return {}

    def get_matching_statistics_config(self) -> Dict[str, Any]:
        """統計設定を取得"""
        try:
            return self.config["matching_system"]["matching_statistics"]
        except KeyError:
            return {}

class MatchingLogic:
    """照合ロジック実装クラス"""

    def __init__(self):
        self.config = MatchingConfig()
        self.conditions = self.config.get_matching_conditions()
        self.judgment_results = self.config.get_judgment_results()
        self.db_config = self.config.get_database_config()

    def get_sql_conditions(self) -> List[str]:
        """SQL条件文のリストを取得"""
        return [condition["sql_condition"] for condition in self.conditions]

    def get_judgment_by_status(self, has_payment: bool, amount_match: bool) -> Dict[str, str]:
        """状況に応じた判定結果を取得"""
        if not has_payment:
            # 支払いデータが存在しない
            for result in self.judgment_results:
                if "未着" in result["status"]:
                    return result
        elif has_payment and not amount_match:
            # 支払いデータはあるが金額不一致
            for result in self.judgment_results:
                if "要確認" in result["status"]:
                    return result
        elif has_payment and amount_match:
            # 支払いデータがあり金額一致
            for result in self.judgment_results:
                if "到着済み" in result["status"]:
                    return result

        # デフォルト
        return {
            "status": "不明",
            "icon": "❓",
            "color": "#f5f5f5",
            "action": "確認が必要"
        }

    def format_date_for_db(self, date_str: str, target_db: str) -> str:
        """データベースに応じた日付フォーマットに変換"""
        if target_db == "expenses.db":
            # YYYY-MM-DD形式
            return date_str.replace("/", "-")
        elif target_db == "billing.db":
            # YYYY/MM/DD形式
            return date_str.replace("-", "/")
        return date_str

    def get_month_filter(self, date_str: str) -> str:
        """月フィルタ用の文字列を取得"""
        return date_str[:7]  # YYYY-MM or YYYY/MM

    def build_matching_query(self, payee_code: Optional[str], payee: Optional[str],
                           amount: Optional[float], payment_month: str) -> tuple:
        """照合用のクエリを構築"""
        conditions = []
        params = []

        # 1. 支払い先コード完全一致（最優先）
        if payee_code and str(payee_code).strip():
            conditions.append("payee_code = ?")
            params.append(str(payee_code).strip())

        # 支払い先名での検索（フォールバック）
        elif payee and str(payee).strip():
            conditions.append("payee LIKE ?")
            params.append(f"%{str(payee).strip()}%")

        if not conditions:
            return "", []

        # 2. 金額の完全一致
        if amount is not None:
            conditions.append("amount = ?")
            params.append(amount)

        # 3. 同一月フィルタ
        if payment_month:
            conditions.append("substr(payment_date, 1, 7) = ?")
            params.append(payment_month)

        query = f"""
            SELECT subject, project_name, payee, payee_code, amount, payment_date, status
            FROM payments
            WHERE {' AND '.join(conditions)}
            ORDER BY amount DESC, payment_date DESC
        """

        return query, params

# 使用例関数
def get_matching_config() -> MatchingConfig:
    """照合設定のインスタンスを取得"""
    return MatchingConfig()

def get_matching_logic() -> MatchingLogic:
    """照合ロジックのインスタンスを取得"""
    return MatchingLogic()