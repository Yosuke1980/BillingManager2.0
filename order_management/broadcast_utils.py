"""放送回数計算ユーティリティ

レギュラー番組の月次放送回数を計算する関数群
"""
import calendar
from datetime import datetime, date


def get_weekday_name_to_number():
    """曜日名→曜日番号の対応辞書を返す

    Returns:
        dict: {曜日名: 曜日番号(0=月曜, 6=日曜)}
    """
    return {
        "月": 0,
        "火": 1,
        "水": 2,
        "木": 3,
        "金": 4,
        "土": 5,
        "日": 6
    }


def count_weekdays_in_month(year: int, month: int, weekday: int) -> int:
    """指定月の特定曜日の出現回数を計算

    Args:
        year: 年
        month: 月
        weekday: 曜日番号（0=月曜, 6=日曜）

    Returns:
        int: 指定曜日の出現回数
    """
    # 月の日数を取得
    _, last_day = calendar.monthrange(year, month)

    count = 0
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        if d.weekday() == weekday:
            count += 1

    return count


def calculate_monthly_broadcast_count(year: int, month: int, broadcast_days: str) -> int:
    """指定月の放送回数を計算

    Args:
        year: 年
        month: 月
        broadcast_days: 放送曜日の文字列（例: "月,水,金" or "月水金"）

    Returns:
        int: 月間放送回数

    Examples:
        >>> calculate_monthly_broadcast_count(2024, 10, "月,水,金")
        13  # 10月の月曜・水曜・金曜の合計

        >>> calculate_monthly_broadcast_count(2024, 10, "月水金")
        13
    """
    if not broadcast_days or broadcast_days.strip() == "":
        return 0

    # カンマ区切りまたは連続した曜日名を処理
    # "月,水,金" or "月水金" の両方に対応
    broadcast_days = broadcast_days.replace(",", "").replace("、", "")

    weekday_map = get_weekday_name_to_number()
    total_count = 0

    # 各曜日文字について処理
    for day_char in broadcast_days:
        if day_char in weekday_map:
            weekday_num = weekday_map[day_char]
            count = count_weekdays_in_month(year, month, weekday_num)
            total_count += count

    return total_count


def calculate_payment_amount(year: int, month: int, broadcast_days: str,
                            payment_type: str, unit_price: float = None) -> float:
    """指定月の支払予定額を計算

    Args:
        year: 年
        month: 月
        broadcast_days: 放送曜日
        payment_type: 支払タイプ（'月額固定' or '回数ベース'）
        unit_price: 単価（回数ベースの場合必須）

    Returns:
        float: 支払予定額

    Raises:
        ValueError: 回数ベースで単価が指定されていない場合
    """
    if payment_type == "月額固定":
        # 月額固定の場合は単価がそのまま月額
        return unit_price if unit_price else 0

    elif payment_type == "回数ベース":
        if unit_price is None:
            raise ValueError("回数ベースの場合、単価が必要です")

        # 放送回数を計算
        broadcast_count = calculate_monthly_broadcast_count(year, month, broadcast_days)

        # 回数 × 単価
        return broadcast_count * unit_price

    else:
        return 0


def adjust_payment_date_by_timing(base_year: int, base_month: int,
                                  payment_timing: str) -> tuple:
    """支払タイミングに基づいて支払予定月を調整

    Args:
        base_year: 基準年（発注の年）
        base_month: 基準月（発注の月）
        payment_timing: 支払タイミング（'当月末払い' or '翌月末払い'）

    Returns:
        tuple: (支払年, 支払月)

    Examples:
        >>> adjust_payment_date_by_timing(2024, 10, "翌月末払い")
        (2024, 11)

        >>> adjust_payment_date_by_timing(2024, 12, "翌月末払い")
        (2025, 1)

        >>> adjust_payment_date_by_timing(2024, 10, "当月末払い")
        (2024, 10)
    """
    if payment_timing == "翌月末払い":
        # 翌月末払い
        payment_month = base_month + 1
        payment_year = base_year

        if payment_month > 12:
            payment_month = 1
            payment_year += 1

        return payment_year, payment_month

    else:  # "当月末払い"
        return base_year, base_month


def get_month_end_date(year: int, month: int) -> date:
    """指定月の月末日を取得

    Args:
        year: 年
        month: 月

    Returns:
        date: 月末日
    """
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, last_day)


if __name__ == "__main__":
    # テスト
    print("=== 放送回数計算テスト ===")
    print(f"2024年10月の月曜: {count_weekdays_in_month(2024, 10, 0)}回")
    print(f"2024年10月の水曜: {count_weekdays_in_month(2024, 10, 2)}回")
    print(f"2024年10月の金曜: {count_weekdays_in_month(2024, 10, 4)}回")
    print(f"2024年10月の月水金: {calculate_monthly_broadcast_count(2024, 10, '月水金')}回")

    print("\n=== 支払金額計算テスト ===")
    # 回数ベース: 月水金 × 50,000円
    amount = calculate_payment_amount(2024, 10, "月水金", "回数ベース", 50000)
    broadcast_count = calculate_monthly_broadcast_count(2024, 10, "月水金")
    print(f"回数ベース: {broadcast_count}回 × 50,000円 = {amount:,.0f}円")

    # 月額固定: 200,000円
    amount = calculate_payment_amount(2024, 10, "月水金", "月額固定", 200000)
    print(f"月額固定: {amount:,.0f}円")

    print("\n=== 支払月調整テスト ===")
    print(f"2024年10月 + 翌月末払い = {adjust_payment_date_by_timing(2024, 10, '翌月末払い')}")
    print(f"2024年12月 + 翌月末払い = {adjust_payment_date_by_timing(2024, 12, '翌月末払い')}")
    print(f"2024年10月 + 当月末払い = {adjust_payment_date_by_timing(2024, 10, '当月末払い')}")
