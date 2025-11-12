#!/usr/bin/env python3
"""
回数ベースの契約から生成された費用項目を削除して再生成するスクリプト
"""
import sqlite3
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from order_management.database_manager import DatabaseManager

def fix_frequency_based_expenses():
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 回数ベースの契約を取得
        cursor.execute("""
            SELECT c.id, c.item_name, p.name as production_name, p.broadcast_days
            FROM contracts c
            LEFT JOIN productions p ON c.production_id = p.id
            WHERE c.payment_type = '回数ベース'
            ORDER BY c.id
        """)

        frequency_contracts = cursor.fetchall()

        if not frequency_contracts:
            print("回数ベースの契約はありませんでした。")
            return

        print("=" * 70)
        print(f"回数ベース契約の費用項目を再生成します")
        print("=" * 70)
        print(f"\n対象契約: {len(frequency_contracts)}件\n")

        db = DatabaseManager()
        success_count = 0
        error_count = 0
        skipped_count = 0

        for contract_id, item_name, production_name, broadcast_days in frequency_contracts:
            # 既存の費用項目数を確認
            cursor.execute("""
                SELECT COUNT(*) FROM expense_items
                WHERE contract_id = ?
            """, (contract_id,))

            old_count = cursor.fetchone()[0]

            print(f"\n契約ID {contract_id}: {item_name}")
            print(f"  番組: {production_name or '(なし)'}")
            print(f"  放送曜日: {broadcast_days or '(未設定)'}")
            print(f"  既存の費用項目: {old_count}件")

            # 放送曜日が未設定の場合はスキップ
            if not broadcast_days or not broadcast_days.strip():
                print(f"  ⚠️  スキップ: 放送曜日が未設定のため再生成できません")
                print(f"      番組編集画面で放送曜日を設定してから再実行してください")
                skipped_count += 1
                continue

            # 既存の費用項目を削除
            cursor.execute("""
                DELETE FROM expense_items
                WHERE contract_id = ?
            """, (contract_id,))

            conn.commit()
            print(f"  ✓ 既存の費用項目を削除しました")

            # 再生成
            try:
                generated_count = db.generate_expense_items_from_contract(contract_id)
                print(f"  ✓ 再生成完了: {generated_count}件")
                success_count += 1
            except ValueError as e:
                print(f"  ✗ エラー: {e}")
                error_count += 1
            except Exception as e:
                print(f"  ✗ 予期しないエラー: {e}")
                error_count += 1

        print("\n" + "=" * 70)
        print(f"処理完了")
        print("=" * 70)
        print(f"成功: {success_count}件")
        print(f"エラー: {error_count}件")
        print(f"スキップ: {skipped_count}件（放送曜日未設定）")

        if skipped_count > 0:
            print("\n⚠️  スキップされた契約があります。")
            print("番組編集画面で放送曜日を設定してから、このスクリプトを再実行してください。")

    except Exception as e:
        conn.rollback()
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

    return True

if __name__ == "__main__":
    print("\n回数ベース費用項目 再生成スクリプト")
    print("このスクリプトは、回数ベースの契約から生成された費用項目を")
    print("削除して、正しい金額で再生成します。\n")

    response = input("続行しますか？ (y/n): ")
    if response.lower() != 'y':
        print("キャンセルしました。")
        sys.exit(0)

    success = fix_frequency_based_expenses()

    if success:
        print("\n✓ すべての処理が完了しました")
    else:
        print("\n✗ エラーが発生しました")
        sys.exit(1)
