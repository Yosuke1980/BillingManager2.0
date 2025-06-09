import os
import glob
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
