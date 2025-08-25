#!/usr/bin/env python3
"""
照合システムテストスクリプト
厳密モードでの動作確認
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import DatabaseManager
from utils import log_message

def test_strict_matching():
    """厳密照合モードのテスト"""
    print("=" * 60)
    print("厳密照合モードテスト開始")
    print("=" * 60)
    
    # DatabaseManagerのインスタンス作成
    db_manager = DatabaseManager()
    
    try:
        # 照合前の状態確認
        print("\n📊 照合前のデータ状態:")
        expense_rows, _ = db_manager.get_expense_data()
        payment_rows, _ = db_manager.get_payment_data()
        
        expense_status = {}
        payment_status = {}
        
        for row in expense_rows:
            status = row[6] if len(row) > 6 else '不明'
            expense_status[status] = expense_status.get(status, 0) + 1
            
        for row in payment_rows:
            status = row[7] if len(row) > 7 else '不明'
            payment_status[status] = payment_status.get(status, 0) + 1
        
        print(f"  費用データ: {expense_status}")
        print(f"  支払いデータ: {payment_status}")
        
        # 厳密照合実行
        print("\n🔍 厳密照合実行中...")
        matched_count, not_matched_count = db_manager.match_expenses_with_payments()
        
        print(f"\n📈 照合結果:")
        print(f"  照合成功: {matched_count}件")
        print(f"  照合失敗: {not_matched_count}件")
        print(f"  照合率: {matched_count/(matched_count+not_matched_count)*100:.1f}%")
        
        # 照合後の状態確認
        print("\n📊 照合後のデータ状態:")
        expense_rows, _ = db_manager.get_expense_data()
        payment_rows, _ = db_manager.get_payment_data()
        
        expense_status_after = {}
        payment_status_after = {}
        
        for row in expense_rows:
            status = row[6] if len(row) > 6 else '不明'
            expense_status_after[status] = expense_status_after.get(status, 0) + 1
            
        for row in payment_rows:
            status = row[7] if len(row) > 7 else '不明'
            payment_status_after[status] = payment_status_after.get(status, 0) + 1
        
        print(f"  費用データ: {expense_status_after}")
        print(f"  支払いデータ: {payment_status_after}")
        
        # 設定確認
        print(f"\n⚙️ 現在の照合設定:")
        print(f"  payment_rule: same_month")
        print(f"  date_tolerance_months: 0")
        print(f"  allow_partial_match: false") 
        print(f"  strict_amount_match: true")
        print(f"  金額比較: 整数完全一致")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strict_matching()