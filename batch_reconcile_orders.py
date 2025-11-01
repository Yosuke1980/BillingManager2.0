"""既存発注データの遡及照合スクリプト

既存のすべての発注データについて、支払データとの照合を実行します。
"""
import sqlite3
from datetime import datetime
from database import DatabaseManager
from utils import log_message


def get_all_order_months():
    """発注データが存在するすべての年月を取得"""
    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT DISTINCT strftime('%Y-%m', expected_payment_date) as year_month
            FROM expenses_order
            WHERE expected_payment_date IS NOT NULL
            ORDER BY year_month
        """)

        months = [row[0] for row in cursor.fetchall() if row[0]]
        return months

    finally:
        conn.close()


def batch_reconcile_all_orders():
    """すべての発注データを遡って照合"""
    log_message("=" * 80)
    log_message("既存発注データの遡及照合を開始")
    log_message("=" * 80)

    # すべての年月を取得
    months = get_all_order_months()

    if not months:
        log_message("照合対象の発注データがありません")
        return

    log_message(f"照合対象: {len(months)}ヶ月分のデータ")
    log_message(f"対象期間: {months[0]} 〜 {months[-1]}")
    log_message("")

    db_manager = DatabaseManager()

    total_matched = 0
    total_not_matched = 0
    processed_months = 0

    for month_str in months:
        try:
            # YYYY-MM形式からyear, monthを抽出
            year, month = map(int, month_str.split('-'))

            log_message(f"[{month_str}] 照合処理開始...")

            # 照合実行
            matched, not_matched, errors = db_manager.match_orders_with_payments(year, month)

            if errors:
                log_message(f"[{month_str}] エラー発生: {errors}")
            else:
                log_message(f"[{month_str}] 完了 - 照合: {matched}件、未照合: {not_matched}件")

            total_matched += matched
            total_not_matched += not_matched
            processed_months += 1

        except Exception as e:
            log_message(f"[{month_str}] 処理エラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")

    log_message("")
    log_message("=" * 80)
    log_message("遡及照合完了")
    log_message("=" * 80)
    log_message(f"処理月数: {processed_months}ヶ月")
    log_message(f"総照合件数: {total_matched}件")
    log_message(f"総未照合件数: {total_not_matched}件")
    log_message(f"照合率: {(total_matched / (total_matched + total_not_matched) * 100) if (total_matched + total_not_matched) > 0 else 0:.1f}%")
    log_message("=" * 80)


if __name__ == "__main__":
    import sys

    print("\n" + "=" * 80)
    print("既存発注データ遡及照合ツール")
    print("=" * 80)
    print("\nこのスクリプトは、既存のすべての発注データについて")
    print("支払データとの照合を実行します。")
    print("\n実行してよろしいですか？ (yes/no): ", end="")

    # ユーザー確認
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        # コマンドライン引数で自動実行
        confirmation = "yes"
    else:
        confirmation = input().strip().lower()

    if confirmation in ['yes', 'y']:
        print("\n照合処理を開始します...\n")
        batch_reconcile_all_orders()
        print("\n✅ 処理が完了しました\n")
    else:
        print("\n処理をキャンセルしました\n")
        sys.exit(0)
