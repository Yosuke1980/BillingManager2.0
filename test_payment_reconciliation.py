#!/usr/bin/env python3
"""支払い照合機能のテストスクリプト"""

from order_management.database_manager import OrderManagementDB

def main():
    db = OrderManagementDB()

    print("支払い照合を開始します...")
    result = db.reconcile_payments_with_expenses()

    print(f"\n照合結果:")
    print(f"  照合成功: {result['matched']}件")
    print(f"  未照合費用項目: {result['unmatched_expenses']}件")
    print(f"  未照合支払い: {result['unmatched_payments']}件")

if __name__ == "__main__":
    main()
