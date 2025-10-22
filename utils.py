import os
import glob
import calendar
from datetime import datetime


def get_latest_csv_file(folder_path):
    """
    指定されたフォルダ内の最新のCSVファイルを返す
    """
    if not os.path.exists(folder_path):
        return None

    # CSVファイルのリストを取得
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        return None

    # 最新のファイルを返す（更新日時でソート）
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file


def format_amount(amount):
    """
    金額を「XX,XXX円」形式にフォーマット
    """
    if not amount:
        return ""
    try:
        # カンマや円記号を除去してから数値に変換
        if isinstance(amount, str):
            amount = amount.replace(",", "").replace("円", "").strip()

        amount_value = float(amount)
        return f"{int(amount_value):,}円"
    except (ValueError, TypeError):
        return str(amount)


def log_message(message):
    """
    ログにメッセージを書き込む
    """
    try:
        # ログディレクトリの作成
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 日付別のログファイル
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

        # ログファイルに書き込み
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")

        # コンソールにも出力
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    except Exception as e:
        print(f"ログ書き込みエラー: {e}")


def validate_date_string(date_str):
    """
    日付文字列の妥当性をチェック
    """
    if not date_str:
        return False

    try:
        # 様々な形式をサポート
        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]

        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue

        return False
    except Exception:
        return False


def normalize_date_string(date_str):
    """
    日付文字列をYYYY-MM-DD形式に正規化
    """
    if not date_str:
        return ""

    try:
        # 区切り文字を統一
        normalized = date_str.replace("/", "-").replace(".", "-")

        # YYYYMMDD形式の場合
        if len(normalized) == 8 and normalized.isdigit():
            return f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:]}"

        # 既に適切な形式の場合はそのまま返す
        if validate_date_string(normalized):
            return normalized

        return date_str
    except Exception:
        return date_str


def safe_float_convert(value):
    """
    安全に数値に変換する
    """
    if value is None:
        return 0.0

    try:
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # カンマや円記号を除去
            cleaned_value = value.replace(",", "").replace("円", "").strip()
            if cleaned_value == "":
                return 0.0
            return float(cleaned_value)

        return 0.0
    except (ValueError, TypeError):
        return 0.0


def create_backup_filename(original_path, suffix="backup"):
    """
    バックアップファイル名を生成
    """
    try:
        directory = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_filename = f"{name}_{suffix}_{timestamp}{ext}"
        return os.path.join(directory, backup_filename)
    except Exception:
        return original_path + ".backup"


def ensure_directory_exists(directory_path):
    """
    ディレクトリが存在しない場合は作成
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            log_message(f"ディレクトリを作成しました: {directory_path}")
        return True
    except Exception as e:
        log_message(f"ディレクトリ作成エラー: {e}")
        return False


def format_payee_code(code, length=4):
    """
    支払い先コードを指定桁数で0埋めする

    Args:
        code: 支払い先コード
        length: 桁数（デフォルト4桁）

    Returns:
        str: 0埋めされたコード
    """
    if not code:
        return ""

    # 文字列に変換して前後の空白を除去
    code_str = str(code).strip()

    # 空文字の場合はそのまま返す
    if not code_str:
        return ""

    # 数値のみの場合は0埋め
    if code_str.isdigit():
        return code_str.zfill(length)

    # 英数字混在の場合はそのまま返す（例：A001）
    return code_str


def calculate_count_based_amount(
    base_amount, broadcast_days, target_year, target_month, use_previous_month=True
):
    """
    回数ベースの費用計算を行う共通関数
    
    Args:
        base_amount (float): 基本金額（1回あたり）
        broadcast_days (str): 放送曜日（カンマ区切り、例："月,水,金"）
        target_year (int): 支払い年
        target_month (int): 支払い月
        use_previous_month (bool): 前月実績を使うかどうか（デフォルト: True）
    
    Returns:
        dict: {
            'amount': 計算された金額,
            'broadcast_count': 放送回数,
            'calculation_year': 計算に使用した年,
            'calculation_month': 計算に使用した月,
            'error': エラーメッセージ（エラーがある場合）
        }
    """
    try:
        # 入力検証
        if not broadcast_days or not broadcast_days.strip():
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': target_year,
                'calculation_month': target_month,
                'error': '放送曜日が指定されていません'
            }
        
        # base_amountの数値検証
        try:
            base_amount = safe_float_convert(base_amount)
            if base_amount < 0:
                return {
                    'amount': 0,
                    'broadcast_count': 0,
                    'calculation_year': target_year,
                    'calculation_month': target_month,
                    'error': '基本金額は0以上である必要があります'
                }
        except (ValueError, TypeError):
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': target_year,
                'calculation_month': target_month,
                'error': '基本金額が不正です'
            }
        
        # 年月の検証
        if not (1 <= target_month <= 12):
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': target_year,
                'calculation_month': target_month,
                'error': f'不正な月です: {target_month}'
            }
        
        if target_year < 1900 or target_year > 2100:
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': target_year,
                'calculation_month': target_month,
                'error': f'不正な年です: {target_year}'
            }
        
        # 計算基準月を決定
        if use_previous_month:
            # 前月実績を使用
            if target_month == 1:
                calculation_year = target_year - 1
                calculation_month = 12
            else:
                calculation_year = target_year
                calculation_month = target_month - 1
        else:
            # 同月実績を使用
            calculation_year = target_year
            calculation_month = target_month
        
        # 放送曜日をパース
        days = [day.strip() for day in broadcast_days.split(",") if day.strip()]
        
        # 有効な曜日名の検証
        valid_weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        invalid_days = [day for day in days if day not in valid_weekdays]
        if invalid_days:
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': calculation_year,
                'calculation_month': calculation_month,
                'error': f'不正な曜日が含まれています: {", ".join(invalid_days)}'
            }
        
        if not days:
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': calculation_year,
                'calculation_month': calculation_month,
                'error': '有効な放送曜日が指定されていません'
            }
        
        # 曜日名から曜日番号へのマッピング
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        
        # 計算月の放送日数を計算
        try:
            last_day = calendar.monthrange(calculation_year, calculation_month)[1]
        except (ValueError, calendar.IllegalMonthError):
            return {
                'amount': 0,
                'broadcast_count': 0,
                'calculation_year': calculation_year,
                'calculation_month': calculation_month,
                'error': f'不正な日付です: {calculation_year}年{calculation_month}月'
            }
        
        broadcast_count = 0
        for day in range(1, last_day + 1):
            try:
                date_obj = datetime(calculation_year, calculation_month, day)
                weekday_str = weekday_names[date_obj.weekday()]
                if weekday_str in days:
                    broadcast_count += 1
            except (ValueError, IndexError) as e:
                return {
                    'amount': 0,
                    'broadcast_count': 0,
                    'calculation_year': calculation_year,
                    'calculation_month': calculation_month,
                    'error': f'日付計算エラー: {e}'
                }
        
        # 最終金額を計算
        calculated_amount = base_amount * broadcast_count
        
        # 成功時のログ出力
        if use_previous_month:
            log_message(
                f"回数ベース計算: {target_year}年{target_month}月支払い分 = "
                f"{calculation_year}年{calculation_month}月実績 "
                f"(放送回数: {broadcast_count}回, 金額: {calculated_amount}円)"
            )
        else:
            log_message(
                f"回数ベース計算: {target_year}年{target_month}月支払い分 "
                f"(同月実績, 放送回数: {broadcast_count}回, 金額: {calculated_amount}円)"
            )
        
        return {
            'amount': calculated_amount,
            'broadcast_count': broadcast_count,
            'calculation_year': calculation_year,
            'calculation_month': calculation_month,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"回数ベース計算でエラーが発生しました: {e}"
        log_message(error_msg)
        return {
            'amount': 0,
            'broadcast_count': 0,
            'calculation_year': target_year if 'calculation_year' not in locals() else calculation_year,
            'calculation_month': target_month if 'calculation_month' not in locals() else calculation_month,
            'error': error_msg
        }
