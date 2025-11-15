"""費用項目の自動生成エンジン

月次費用の自動生成機能を提供します。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from order_management.database_manager import OrderManagementDB
from utils import log_message


class ExpenseAutoGenerator:
    """費用項目の自動生成エンジン"""

    def __init__(self, db: OrderManagementDB = None):
        """
        Args:
            db: OrderManagementDB インスタンス
        """
        self.db = db or OrderManagementDB()

    def generate_monthly_expenses(self, target_month: Optional[str] = None) -> Dict:
        """月次費用を自動生成

        Args:
            target_month: 'YYYY-MM'形式。Noneなら当月

        Returns:
            dict: {
                'generated': 生成件数,
                'skipped': スキップ件数（既に生成済み）,
                'failed': 失敗件数,
                'details': [(template_id, item_name, result_message), ...]
            }
        """
        if target_month is None:
            target_month = datetime.now().strftime('%Y-%m')

        log_message(f"📅 {target_month} の費用項目を自動生成中...")

        result = {
            'generated': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }

        # 自動生成対象のテンプレートを取得
        templates = self.db.get_active_monthly_templates(target_month)

        if not templates:
            log_message("  → 自動生成対象のテンプレートがありません")
            return result

        log_message(f"  → {len(templates)}件のテンプレートを検出")

        for template in templates:
            template_id = template[0]
            item_name = template[4]  # item_name

            try:
                # 既に生成済みかチェック
                if self.db.check_generation_log(template_id, target_month):
                    log_message(f"  ⊘ {item_name}: 既に生成済み（スキップ）")
                    result['skipped'] += 1
                    result['details'].append((template_id, item_name, 'スキップ（既に生成済み）'))
                    continue

                # 費用項目を生成
                expense_id = self.generate_from_template(template_id, target_month)

                if expense_id:
                    log_message(f"  ✓ {item_name}: 生成成功（ID={expense_id}）")
                    result['generated'] += 1
                    result['details'].append((template_id, item_name, f'生成成功（ID={expense_id}）'))
                else:
                    log_message(f"  ✗ {item_name}: 生成失敗")
                    result['failed'] += 1
                    result['details'].append((template_id, item_name, '生成失敗'))

            except Exception as e:
                log_message(f"  ✗ {item_name}: エラー - {e}")
                result['failed'] += 1
                result['details'].append((template_id, item_name, f'エラー: {e}'))

        log_message(f"\n📊 生成結果: 成功={result['generated']}件, スキップ={result['skipped']}件, 失敗={result['failed']}件")
        return result

    def generate_from_template(self, template_id: int, target_month: str) -> Optional[int]:
        """テンプレートから費用項目を1件生成

        Args:
            template_id: 費用テンプレートID
            target_month: 'YYYY-MM'形式

        Returns:
            int: 生成された expense_items.id。失敗時はNone
        """
        # テンプレート情報を取得
        template = self.db.get_expense_template_by_id(template_id)
        if not template:
            log_message(f"  エラー: テンプレートID={template_id} が見つかりません")
            return None

        # テンプレートデータの展開
        (tid, production_id, partner_id, cast_id, item_name, work_type, amount,
         generation_type, generation_day, payment_timing, auto_generate_enabled,
         start_date, end_date, notes, created_at, updated_at) = template

        # 支払予定日を計算
        expected_payment_date = self._calculate_payment_date(target_month, payment_timing)

        # 費用項目名を生成（月次の場合は月を追加）
        if generation_type == '月次':
            year, month = target_month.split('-')
            full_item_name = f"{item_name} {year}年{int(month)}月分"
        else:
            full_item_name = item_name

        # expense_items に挿入
        expense_data = {
            'production_id': production_id,
            'partner_id': partner_id,
            'cast_id': cast_id,
            'item_name': full_item_name,
            'work_type': work_type,
            'amount': amount,
            'expected_payment_date': expected_payment_date,
            'payment_status': '未払い',
            'status': '発注予定',
            'template_id': template_id,
            'generation_month': target_month,
            'notes': f"自動生成（テンプレートID={template_id}）" + (f"\n{notes}" if notes else "")
        }

        try:
            expense_id = self.db.add_expense_item(expense_data)

            # 生成ログを記録
            self.db.record_generation_log(template_id, target_month, expense_id)

            return expense_id

        except Exception as e:
            log_message(f"  エラー: 費用項目生成失敗 - {e}")
            import traceback
            log_message(traceback.format_exc())
            return None

    def _calculate_payment_date(self, target_month: str, payment_timing: str) -> str:
        """支払予定日を計算

        Args:
            target_month: 'YYYY-MM'形式
            payment_timing: 支払タイミング（例: '翌月末払い', '当月末払い', '翌月15日払い'）

        Returns:
            str: 支払予定日 'YYYY-MM-DD'形式
        """
        year, month = map(int, target_month.split('-'))

        if '翌月末' in payment_timing:
            # 翌月末
            if month == 12:
                next_year, next_month = year + 1, 1
            else:
                next_year, next_month = year, month + 1

            # 翌月の最終日を取得
            if next_month == 12:
                last_day = 31
            elif next_month in [4, 6, 9, 11]:
                last_day = 30
            elif next_month == 2:
                # うるう年チェック
                if (next_year % 4 == 0 and next_year % 100 != 0) or (next_year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31

            return f"{next_year:04d}-{next_month:02d}-{last_day:02d}"

        elif '当月末' in payment_timing:
            # 当月末
            if month == 12:
                last_day = 31
            elif month in [4, 6, 9, 11]:
                last_day = 30
            elif month == 2:
                if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31

            return f"{year:04d}-{month:02d}-{last_day:02d}"

        elif '翌月15日' in payment_timing:
            # 翌月15日
            if month == 12:
                next_year, next_month = year + 1, 1
            else:
                next_year, next_month = year, month + 1

            return f"{next_year:04d}-{next_month:02d}-15"

        elif '当月15日' in payment_timing:
            # 当月15日
            return f"{year:04d}-{month:02d}-15"

        else:
            # デフォルト: 翌月末
            if month == 12:
                next_year, next_month = year + 1, 1
            else:
                next_year, next_month = year, month + 1

            # 簡易的に28日を返す（月末計算を省略）
            return f"{next_year:04d}-{next_month:02d}-28"

    def generate_event_expense(self, template_id: int) -> Optional[int]:
        """イベント費用を手動生成

        Args:
            template_id: 費用テンプレートID

        Returns:
            int: 生成された expense_items.id。失敗時はNone
        """
        # テンプレート情報を取得
        template = self.db.get_expense_template_by_id(template_id)
        if not template:
            log_message(f"  エラー: テンプレートID={template_id} が見つかりません")
            return None

        # イベントの場合は generation_month は NULL
        (tid, production_id, partner_id, cast_id, item_name, work_type, amount,
         generation_type, generation_day, payment_timing, auto_generate_enabled,
         start_date, end_date, notes, created_at, updated_at) = template

        # 実施日を support_date として使用
        implementation_date = start_date if start_date else datetime.now().strftime('%Y-%m-%d')

        # 支払予定日を計算（実施月ベース）
        if start_date:
            target_month = start_date[:7]  # 'YYYY-MM'
        else:
            target_month = datetime.now().strftime('%Y-%m')

        expected_payment_date = self._calculate_payment_date(target_month, payment_timing)

        # expense_items に挿入
        expense_data = {
            'production_id': production_id,
            'partner_id': partner_id,
            'cast_id': cast_id,
            'item_name': item_name,
            'work_type': work_type,
            'amount': amount,
            'implementation_date': implementation_date,
            'expected_payment_date': expected_payment_date,
            'payment_status': '未払い',
            'status': '発注予定',
            'template_id': template_id,
            'generation_month': None,  # イベントなのでNULL
            'notes': f"イベント費用（テンプレートID={template_id}）" + (f"\n{notes}" if notes else "")
        }

        try:
            expense_id = self.db.add_expense_item(expense_data)
            log_message(f"✓ イベント費用生成成功: {item_name}（ID={expense_id}）")
            return expense_id

        except Exception as e:
            log_message(f"✗ イベント費用生成失敗: {e}")
            import traceback
            log_message(traceback.format_exc())
            return None


def test_auto_generator():
    """テスト用関数"""
    log_message("=== 費用自動生成テスト ===\n")

    generator = ExpenseAutoGenerator()

    # 当月分を生成
    result = generator.generate_monthly_expenses()

    log_message(f"\n結果:")
    log_message(f"  生成: {result['generated']}件")
    log_message(f"  スキップ: {result['skipped']}件")
    log_message(f"  失敗: {result['failed']}件")

    if result['details']:
        log_message(f"\n詳細:")
        for template_id, item_name, message in result['details']:
            log_message(f"  - [{template_id}] {item_name}: {message}")


if __name__ == "__main__":
    test_auto_generator()
