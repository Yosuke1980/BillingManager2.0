"""契約自動延長機能

契約の自動延長に関する機能を提供します。
"""
from datetime import datetime, timedelta
from typing import List, Tuple
from order_management.database_manager import OrderManagementDB
from utils import log_message


class ContractRenewalManager:
    """契約自動延長マネージャー"""

    def __init__(self, db: OrderManagementDB = None):
        self.db = db or OrderManagementDB()

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
        return self.db.extend_contract(contract_id, reason, executed_by, notes)

    def get_contracts_for_auto_renewal(self) -> List[Tuple]:
        """自動延長対象の契約を取得

        Returns:
            List[Tuple]: (id, program_name, partner_name, contract_end_date, ...)
        """
        return self.db.get_contracts_for_auto_renewal()

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
        return self.db.check_and_execute_auto_renewal(executed_by)

    def get_renewal_history(self, contract_id: int) -> List[Tuple]:
        """契約の延長履歴を取得

        Args:
            contract_id: 契約ID

        Returns:
            List[Tuple]: (id, previous_end_date, new_end_date, renewal_date,
                         renewal_reason, executed_by, notes)
        """
        return self.db.get_renewal_history(contract_id)

    def get_contracts_expiring_soon(self, days_before: int = 30) -> List[Tuple]:
        """期限間近の契約を取得

        Args:
            days_before: 何日前から対象にするか

        Returns:
            List[Tuple]: 契約情報のリスト
        """
        return self.db.get_contracts_expiring_in_days(days_before)
