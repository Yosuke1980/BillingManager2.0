import sqlite3
import csv
import calendar
from datetime import datetime, timedelta
from utils import log_message, calculate_count_based_amount


class DatabaseManager:
    def __init__(self):
        self.billing_db = "billing.db"
        self.expenses_db = "expenses.db"
        self.expense_master_db = "expense_master.db"
        self.payee_master_db = "payee_master.db"  # 支払い先マスター追加

    def init_db(self):
        """データベースの初期化"""
        # 支払いデータベース
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        # payments テーブルを削除して再作成
        cursor.execute("DROP TABLE IF EXISTS payments")

        # 新しいスキーマでテーブルを作成
        cursor.execute(
            """
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                project_name TEXT,
                payee TEXT,
                payee_code TEXT,
                amount REAL,
                payment_date TEXT,
                status TEXT DEFAULT '未処理',
                type TEXT DEFAULT ''
            )
        """
        )
        log_message("payments テーブルを再作成しました")

        conn.commit()
        conn.close()

        # 費用データベース
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        # 既存のexpensesテーブルに新しいカラムを追加（存在しない場合のみ）
        try:
            # まずテーブルの存在確認
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
            )
            table_exists = cursor.fetchone()

            if table_exists:
                # テーブルが存在する場合、カラムの存在確認
                cursor.execute("PRAGMA table_info(expenses)")
                columns = [column[1] for column in cursor.fetchall()]

                if "source_type" not in columns:
                    cursor.execute(
                        "ALTER TABLE expenses ADD COLUMN source_type TEXT DEFAULT 'manual'"
                    )
                    log_message("expenses テーブルに source_type カラムを追加しました")

                if "master_id" not in columns:
                    cursor.execute(
                        "ALTER TABLE expenses ADD COLUMN master_id INTEGER DEFAULT NULL"
                    )
                    log_message("expenses テーブルに master_id カラムを追加しました")
            else:
                # テーブルが存在しない場合は新規作成
                cursor.execute(
                    """
                    CREATE TABLE expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_name TEXT,
                        payee TEXT,
                        payee_code TEXT,
                        amount REAL,
                        payment_date TEXT,
                        status TEXT DEFAULT '未処理',
                        source_type TEXT DEFAULT 'manual',
                        master_id INTEGER DEFAULT NULL
                    )
                """
                )
                log_message("expenses テーブルを新規作成しました")

        except sqlite3.Error as e:
            log_message(f"expenses テーブル初期化エラー: {e}")

        conn.commit()
        conn.close()

        # 費用マスターデータベース
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        # 費用マスターテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expense_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                payee TEXT,
                payee_code TEXT,
                amount REAL,
                payment_date TEXT,
                status TEXT DEFAULT '未処理',
                payment_type TEXT DEFAULT '月額固定',
                start_date TEXT,
                end_date TEXT,
                broadcast_days TEXT
            )
        """
        )

        conn.commit()
        conn.close()

        # 支払い先マスターデータベースを初期化
        self.init_payee_master_db()

    def init_payee_master_db(self):
        """支払い先マスターデータベースの初期化"""
        conn = sqlite3.connect(self.payee_master_db)
        cursor = conn.cursor()

        # 支払い先マスターテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payee_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payee_name TEXT UNIQUE,
                payee_code TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()
        log_message("支払い先マスターデータベースを初期化しました")

    def get_payee_suggestions(self, partial_name=""):
        """支払い先の候補を取得（オートコンプリート用）"""
        conn = sqlite3.connect(self.payee_master_db)
        cursor = conn.cursor()

        if partial_name:
            cursor.execute(
                """
                SELECT payee_name, payee_code FROM payee_master 
                WHERE payee_name LIKE ? 
                ORDER BY payee_name
                """,
                (f"%{partial_name}%",),
            )
        else:
            cursor.execute(
                """
                SELECT payee_name, payee_code FROM payee_master 
                ORDER BY payee_name
                """
            )

        results = cursor.fetchall()
        conn.close()
        return results

    def get_payee_code_by_name(self, payee_name):
        """支払い先名からコードを取得"""
        conn = sqlite3.connect(self.payee_master_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT payee_code FROM payee_master 
            WHERE payee_name = ?
            """,
            (payee_name,),
        )

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else ""

    def update_or_create_payee_master(self, payee_name, payee_code):
        """支払い先マスターを更新または新規作成"""
        if not payee_name or not payee_code:
            return False

        conn = sqlite3.connect(self.payee_master_db)
        cursor = conn.cursor()

        try:
            # 既存レコードがあるかチェック
            cursor.execute(
                "SELECT id FROM payee_master WHERE payee_name = ?", (payee_name,)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新
                cursor.execute(
                    """
                    UPDATE payee_master 
                    SET payee_code = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE payee_name = ?
                    """,
                    (payee_code, payee_name),
                )
                log_message(f"支払い先マスター更新: {payee_name} -> {payee_code}")
            else:
                # 新規作成
                cursor.execute(
                    """
                    INSERT INTO payee_master (payee_name, payee_code) 
                    VALUES (?, ?)
                    """,
                    (payee_name, payee_code),
                )
                log_message(f"支払い先マスター追加: {payee_name} -> {payee_code}")

            conn.commit()
            return True

        except sqlite3.Error as e:
            log_message(f"支払い先マスター更新エラー: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def sync_payee_master_from_data(self):
        """既存データから支払い先マスターを同期"""
        # 支払いデータから支払い先情報を収集
        billing_conn = sqlite3.connect(self.billing_db)
        billing_cursor = billing_conn.cursor()

        billing_cursor.execute(
            """
            SELECT DISTINCT payee, payee_code FROM payments 
            WHERE payee IS NOT NULL AND payee != '' 
            AND payee_code IS NOT NULL AND payee_code != ''
            """
        )
        billing_payees = billing_cursor.fetchall()
        billing_conn.close()

        # 費用データからも収集
        expenses_conn = sqlite3.connect(self.expenses_db)
        expenses_cursor = expenses_conn.cursor()

        expenses_cursor.execute(
            """
            SELECT DISTINCT payee, payee_code FROM expenses 
            WHERE payee IS NOT NULL AND payee != '' 
            AND payee_code IS NOT NULL AND payee_code != ''
            """
        )
        expense_payees = expenses_cursor.fetchall()
        expenses_conn.close()

        # マスターデータからも収集
        master_conn = sqlite3.connect(self.expense_master_db)
        master_cursor = master_conn.cursor()

        master_cursor.execute(
            """
            SELECT DISTINCT payee, payee_code FROM expense_master 
            WHERE payee IS NOT NULL AND payee != '' 
            AND payee_code IS NOT NULL AND payee_code != ''
            """
        )
        master_payees = master_cursor.fetchall()
        master_conn.close()

        # すべてのデータを統合
        all_payees = set(billing_payees + expense_payees + master_payees)

        # 支払い先マスターに反映
        count = 0
        for payee_name, payee_code in all_payees:
            if self.update_or_create_payee_master(payee_name, payee_code):
                count += 1

        log_message(f"支払い先マスター同期完了: {count}件")
        return count

    def import_csv_data(self, csv_file, header_mapping):
        """CSVファイルからデータをインポート"""
        # データベース接続
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        # 既存のデータを削除
        cursor.execute("DELETE FROM payments")

        # CSVファイルを読み込む
        row_count = 0
        with open(csv_file, "r", encoding="shift_jis", errors="replace") as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)  # ヘッダー行を読み込み

            # ヘッダーマッピングの作成
            header_indices = {}
            for header_name, db_field in header_mapping.items():
                try:
                    index = headers.index(header_name)
                    header_indices[db_field] = index
                except ValueError:
                    log_message(
                        f"ヘッダー '{header_name}' がCSVファイルに見つかりません"
                    )

            # 必須フィールドのチェック
            required_fields = ["project_name", "payee", "amount", "payment_date"]
            missing_fields = [
                field for field in required_fields if field not in header_indices
            ]

            if missing_fields:
                missing_headers = [
                    header
                    for header, field in header_mapping.items()
                    if field in missing_fields
                ]
                log_message(
                    f"CSVファイルのヘッダーが不正です: {', '.join(missing_headers)}"
                )
                conn.close()
                return 0

            # データの挿入
            for row in csv_reader:
                if not row:  # 空行はスキップ
                    continue

                # 各フィールドの値を取得
                values = {}
                for db_field, index in header_indices.items():
                    values[db_field] = row[index] if index < len(row) else ""

                # 金額を数値に変換
                try:
                    if "amount" in values:
                        amount_str = (
                            values["amount"].replace(",", "").replace("円", "").strip()
                        )
                        values["amount"] = float(amount_str)
                except ValueError:
                    log_message(f"金額の変換エラー: {values.get('amount')}")
                    values["amount"] = 0

                # ステータスのデフォルト値
                if "status" not in values or not values["status"]:
                    values["status"] = "未処理"

                # データをデータベースに挿入
                fields = list(values.keys())
                placeholders = ", ".join(["?"] * len(fields))

                query = f"INSERT INTO payments ({', '.join(fields)}) VALUES ({placeholders})"
                cursor.execute(query, [values[field] for field in fields])

                row_count += 1

        conn.commit()
        conn.close()

        # 支払い先マスターを同期
        self.sync_payee_master_from_data()

        return row_count

    def get_payment_data(self, search_term=None):
        """支払いデータを取得"""
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        if search_term:
            search_param = f"%{search_term}%"
            cursor.execute(
                """
                SELECT id, subject, project_name, payee, payee_code, amount, payment_date, status 
                FROM payments
                WHERE subject LIKE ? OR project_name LIKE ? OR payee LIKE ? OR payee_code LIKE ? OR payment_date LIKE ?
                ORDER BY payment_date DESC
                """,
                (search_param, search_param, search_param, search_param, search_param),
            )
        else:
            cursor.execute(
                """
                SELECT id, subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                ORDER BY payment_date DESC
                """
            )

        payment_rows = cursor.fetchall()

        # 照合済み件数を取得
        cursor.execute(
            """
            SELECT COUNT(*) FROM payments
            WHERE status = '照合済'
            """
        )
        matched_count = cursor.fetchone()[0]

        conn.close()
        return payment_rows, matched_count

    def update_payment_status(self, subject, payment_date, payee, status):
        """支払いデータのステータスを更新"""
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE payments
            SET status = ?
            WHERE subject = ? AND payment_date = ? AND payee = ?
            """,
            (status, subject, payment_date, payee),
        )

        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def get_expense_data(self, search_term=None):
        """費用データを取得"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        if search_term:
            search_param = f"%{search_term}%"
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_date, status FROM expenses
                WHERE project_name LIKE ? OR payee LIKE ? OR payee_code LIKE ? OR payment_date LIKE ?
                ORDER BY payment_date DESC
                """,
                (search_param, search_param, search_param, search_param),
            )
        else:
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_date, status
                FROM expenses
                ORDER BY payment_date DESC
                """
            )

        expense_rows = cursor.fetchall()

        # 照合済み件数を取得
        cursor.execute(
            """
            SELECT COUNT(*) FROM expenses
            WHERE status = '照合済'
            """
        )
        matched_count = cursor.fetchone()[0]

        conn.close()
        return expense_rows, matched_count

    def get_expense_by_id(self, expense_id):
        """IDで費用データを取得"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_name, payee, payee_code, amount, payment_date, status
            FROM expenses WHERE id = ?
            """,
            (expense_id,),
        )

        row = cursor.fetchone()
        conn.close()
        return row

    def save_expense(self, data, is_new=False):
        """費用データを保存"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        # 支払い先マスターを更新
        if data.get("payee") and data.get("payee_code"):
            self.update_or_create_payee_master(data["payee"], data["payee_code"])

        if is_new:
            cursor.execute(
                """
                INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status, source_type, master_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["project_name"],
                    data["payee"],
                    data["payee_code"],
                    data["amount"],
                    data["payment_date"],
                    data["status"],
                    data.get("source_type", "manual"),
                    data.get("master_id", None),
                ),
            )
            expense_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                UPDATE expenses
                SET project_name = ?, payee = ?, payee_code = ?, amount = ?, payment_date = ?, status = ?
                WHERE id = ?
                """,
                (
                    data["project_name"],
                    data["payee"],
                    data["payee_code"],
                    data["amount"],
                    data["payment_date"],
                    data["status"],
                    data["id"],
                ),
            )
            expense_id = data["id"]

        conn.commit()
        conn.close()
        return expense_id

    def delete_expense(self, expense_id):
        """費用データを削除"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount

    def duplicate_expense(self, expense_id):
        """費用データを複製"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT project_name, payee, payee_code, amount, payment_date, status
            FROM expenses WHERE id = ?
            """,
            (expense_id,),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        cursor.execute(
            """
            INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row[0] + " (複製)",  # 案件名に「(複製)」を追加
                row[1],  # 支払い先
                row[2],  # 支払い先コード
                row[3],  # 金額
                row[4],  # 支払日
                "未処理",  # ステータスはリセット
            ),
        )

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def get_master_data(self, search_term=None):
        """費用マスターデータを取得"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        if search_term:
            search_param = f"%{search_term}%"
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_type, 
                    broadcast_days, start_date, end_date
                FROM expense_master
                WHERE project_name LIKE ? OR payee LIKE ? OR payee_code LIKE ?
                ORDER BY id
                """,
                (search_param, search_param, search_param),
            )
        else:
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_type, 
                    broadcast_days, start_date, end_date
                FROM expense_master
                ORDER BY id
                """
            )

        master_rows = cursor.fetchall()
        conn.close()
        return master_rows

    def get_master_by_id(self, master_id):
        """IDで費用マスターデータを取得"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_name, payee, payee_code, amount, payment_type, 
                broadcast_days, start_date, end_date
            FROM expense_master WHERE id = ?
            """,
            (master_id,),
        )

        row = cursor.fetchone()
        conn.close()
        return row

    def save_master(self, data, is_new=False):
        """費用マスターデータを保存"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        # 支払い先マスターを更新
        if data.get("payee") and data.get("payee_code"):
            self.update_or_create_payee_master(data["payee"], data["payee_code"])

        if is_new:
            cursor.execute(
                """
                INSERT INTO expense_master (
                    project_name, payee, payee_code, amount, payment_type, 
                    start_date, end_date, broadcast_days, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '未処理')
                """,
                (
                    data["project_name"],
                    data["payee"],
                    data["payee_code"],
                    data["amount"],
                    data["payment_type"],
                    data["start_date"],
                    data["end_date"],
                    data["broadcast_days"],
                ),
            )
            master_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                UPDATE expense_master
                SET project_name = ?, payee = ?, payee_code = ?, amount = ?, 
                    payment_type = ?, start_date = ?, end_date = ?, broadcast_days = ?
                WHERE id = ?
                """,
                (
                    data["project_name"],
                    data["payee"],
                    data["payee_code"],
                    data["amount"],
                    data["payment_type"],
                    data["start_date"],
                    data["end_date"],
                    data["broadcast_days"],
                    data["id"],
                ),
            )
            master_id = data["id"]

        conn.commit()
        conn.close()
        return master_id

    def delete_master(self, master_id):
        """費用マスターデータを削除"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expense_master WHERE id = ?", (master_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount

    def duplicate_master(self, master_id):
        """費用マスターデータを複製"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT project_name, payee, payee_code, amount, payment_type, 
                start_date, end_date, broadcast_days
            FROM expense_master WHERE id = ?
            """,
            (master_id,),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        cursor.execute(
            """
            INSERT INTO expense_master (
                project_name, payee, payee_code, amount, payment_type, 
                start_date, end_date, broadcast_days, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '未処理')
            """,
            (
                row[0] + " (複製)",  # 案件名に「(複製)」を追加
                row[1],  # 支払い先
                row[2],  # 支払い先コード
                row[3],  # 金額
                row[4] if len(row) > 4 else "月額固定",  # 種別
                row[5] if len(row) > 5 else "",  # 開始日
                row[6] if len(row) > 6 else "",  # 終了日
                row[7] if len(row) > 7 else "",  # 放送曜日
            ),
        )

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def generate_expenses_from_master(self, target_year, target_month):
        """マスターデータから指定月の費用データを生成"""
        master_conn = sqlite3.connect(self.expense_master_db)
        master_cursor = master_conn.cursor()

        expense_conn = sqlite3.connect(self.expenses_db)
        expense_cursor = expense_conn.cursor()

        try:
            # 指定月の最終日を取得
            last_day = calendar.monthrange(target_year, target_month)[1]
            target_month_str = f"{target_year:04d}-{target_month:02d}"

            # マスターデータを取得
            master_cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_type, 
                       broadcast_days, start_date, end_date
                FROM expense_master
                """
            )
            master_rows = master_cursor.fetchall()

            generated_count = 0
            updated_count = 0

            for master_row in master_rows:
                master_id = master_row[0]
                project_name = master_row[1]
                payee = master_row[2]
                payee_code = master_row[3]
                amount = master_row[4]
                payment_type = master_row[5] if len(master_row) > 5 else "月額固定"
                broadcast_days = master_row[6] if len(master_row) > 6 else ""
                start_date = master_row[7] if len(master_row) > 7 else ""
                end_date = master_row[8] if len(master_row) > 8 else ""

                # 開始日と終了日のチェック
                target_date = datetime(target_year, target_month, 1)

                # 開始日のチェック
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        if target_date < start_dt:
                            continue  # まだ開始されていない
                    except ValueError:
                        pass

                # 終了日のチェック
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        if target_date > end_dt:
                            continue  # 既に終了している
                    except ValueError:
                        pass

                # 支払日と金額を決定
                if payment_type == "回数ベース" and broadcast_days:
                    # 共通の回数ベース計算関数を使用（前月実績ベース）
                    result = calculate_count_based_amount(
                        amount, broadcast_days, target_year, target_month, use_previous_month=True
                    )
                    
                    if result['error']:
                        log_message(f"回数ベース計算エラー: {result['error']}")
                        continue  # エラーの場合はこのマスターをスキップ
                    
                    calculated_amount = result['amount']
                    payment_date = (
                        f"{target_year:04d}-{target_month:02d}-{last_day:02d}"
                    )
                else:
                    # 月額固定の場合
                    calculated_amount = amount
                    payment_date = (
                        f"{target_year:04d}-{target_month:02d}-{last_day:02d}"
                    )

                # 既存の費用データをチェック
                expense_cursor.execute(
                    """
                    SELECT id FROM expenses 
                    WHERE master_id = ? AND payment_date LIKE ? || '%'
                    """,
                    (master_id, target_month_str),
                )
                existing_expense = expense_cursor.fetchone()

                if existing_expense:
                    # 既存データを更新
                    expense_cursor.execute(
                        """
                        UPDATE expenses
                        SET project_name = ?, payee = ?, payee_code = ?, amount = ?, payment_date = ?
                        WHERE id = ?
                        """,
                        (
                            project_name,
                            payee,
                            payee_code,
                            calculated_amount,
                            payment_date,
                            existing_expense[0],
                        ),
                    )
                    updated_count += 1
                else:
                    # 新規データを作成
                    expense_cursor.execute(
                        """
                        INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status, source_type, master_id)
                        VALUES (?, ?, ?, ?, ?, '未処理', 'master', ?)
                        """,
                        (
                            project_name,
                            payee,
                            payee_code,
                            calculated_amount,
                            payment_date,
                            master_id,
                        ),
                    )
                    generated_count += 1

            expense_conn.commit()

            log_message(
                f"{target_year}年{target_month}月の費用データを生成: 新規{generated_count}件、更新{updated_count}件"
            )
            return generated_count, updated_count

        except Exception as e:
            expense_conn.rollback()
            log_message(f"マスターデータからの費用生成エラー: {e}")
            raise
        finally:
            master_conn.close()
            expense_conn.close()

    def generate_new_master_expenses_for_current_month(self):
        """新たに追加されたマスター項目のみを今月分に反映"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        master_conn = sqlite3.connect(self.expense_master_db)
        master_cursor = master_conn.cursor()

        expense_conn = sqlite3.connect(self.expenses_db)
        expense_cursor = expense_conn.cursor()

        try:
            current_month_str = f"{current_year:04d}-{current_month:02d}"
            last_day = calendar.monthrange(current_year, current_month)[1]

            # 今月分がまだ生成されていないマスター項目を検出
            master_cursor.execute(
                """
                SELECT m.id, m.project_name, m.payee, m.payee_code, m.amount, m.payment_type, 
                       m.broadcast_days, m.start_date, m.end_date
                FROM expense_master m
                WHERE NOT EXISTS (
                    SELECT 1 FROM expenses e 
                    WHERE e.master_id = m.id 
                    AND e.payment_date LIKE ? || '%'
                )
                """,
                (current_month_str,),
            )

            new_master_rows = master_cursor.fetchall()

            if not new_master_rows:
                log_message("今月分に追加すべき新規マスター項目はありません")
                return 0, []

            generated_count = 0
            generated_items = []

            for master_row in new_master_rows:
                master_id = master_row[0]
                project_name = master_row[1]
                payee = master_row[2]
                payee_code = master_row[3]
                amount = master_row[4]
                payment_type = master_row[5] if len(master_row) > 5 else "月額固定"
                broadcast_days = master_row[6] if len(master_row) > 6 else ""
                start_date = master_row[7] if len(master_row) > 7 else ""
                end_date = master_row[8] if len(master_row) > 8 else ""

                # 今月が有効期間内かチェック
                current_date_obj = datetime(current_year, current_month, 1)

                # 開始日のチェック
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        if current_date_obj < start_dt:
                            continue  # まだ開始されていない
                    except ValueError:
                        pass

                # 終了日のチェック
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        if current_date_obj > end_dt:
                            continue  # 既に終了している
                    except ValueError:
                        pass

                # 支払日と金額を計算
                if payment_type == "回数ベース" and broadcast_days:
                    # 共通の回数ベース計算関数を使用（前月実績ベース）
                    result = calculate_count_based_amount(
                        amount, broadcast_days, current_year, current_month, use_previous_month=True
                    )
                    
                    if result['error']:
                        log_message(f"新規マスター回数ベース計算エラー: {result['error']}")
                        continue  # エラーの場合はこのマスターをスキップ
                    
                    calculated_amount = result['amount']
                    payment_date = (
                        f"{current_year:04d}-{current_month:02d}-{last_day:02d}"
                    )
                else:
                    # 月額固定の場合
                    calculated_amount = amount
                    payment_date = (
                        f"{current_year:04d}-{current_month:02d}-{last_day:02d}"
                    )

                # 新規データを作成
                expense_cursor.execute(
                    """
                    INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status, source_type, master_id)
                    VALUES (?, ?, ?, ?, ?, '未処理', 'master', ?)
                    """,
                    (
                        project_name,
                        payee,
                        payee_code,
                        calculated_amount,
                        payment_date,
                        master_id,
                    ),
                )

                generated_count += 1
                generated_items.append(
                    {
                        "project_name": project_name,
                        "payee": payee,
                        "amount": calculated_amount,
                        "payment_type": payment_type,
                    }
                )

            expense_conn.commit()

            log_message(f"新規マスター項目を今月分に反映: {generated_count}件")
            return generated_count, generated_items

        except Exception as e:
            expense_conn.rollback()
            log_message(f"新規マスター項目の今月反映エラー: {e}")
            raise
        finally:
            master_conn.close()
            expense_conn.close()

    def get_missing_master_expenses_for_month(self, target_year, target_month):
        """指定月に未反映のマスター項目を取得"""
        master_conn = sqlite3.connect(self.expense_master_db)
        master_cursor = master_conn.cursor()

        try:
            target_month_str = f"{target_year:04d}-{target_month:02d}"

            # 指定月分がまだ生成されていないマスター項目を取得
            master_cursor.execute(
                """
                SELECT m.id, m.project_name, m.payee, m.payee_code, m.amount, m.payment_type, 
                       m.broadcast_days, m.start_date, m.end_date
                FROM expense_master m
                WHERE NOT EXISTS (
                    SELECT 1 FROM expenses e 
                    WHERE e.master_id = m.id 
                    AND e.payment_date LIKE ? || '%'
                )
                """,
                (target_month_str,),
            )

            missing_rows = master_cursor.fetchall()
            return missing_rows

        except Exception as e:
            log_message(f"未反映マスター項目取得エラー: {e}")
            return []
        finally:
            master_conn.close()



# ファイル終了確認用のコメント - database.py完了
