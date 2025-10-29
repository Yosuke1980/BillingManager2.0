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

        # 新しいスキーマでテーブルを作成（案件管理用フィールド追加）
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
                type TEXT DEFAULT '',
                client_name TEXT DEFAULT '',
                department TEXT DEFAULT '',
                project_status TEXT DEFAULT '進行中',
                project_start_date TEXT DEFAULT '',
                project_end_date TEXT DEFAULT '',
                budget REAL DEFAULT 0,
                approver TEXT DEFAULT '',
                urgency_level TEXT DEFAULT '通常'
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

                # 既存のカラム追加
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

                # 案件情報カラムを追加
                project_columns = [
                    ("client_name", "TEXT DEFAULT ''"),
                    ("department", "TEXT DEFAULT ''"),
                    ("project_status", "TEXT DEFAULT '進行中'"),
                    ("project_start_date", "TEXT DEFAULT ''"),
                    ("project_end_date", "TEXT DEFAULT ''"),
                    ("budget", "REAL DEFAULT 0"),
                    ("approver", "TEXT DEFAULT ''"),
                    ("urgency_level", "TEXT DEFAULT '通常'"),
                    ("payment_timing", "TEXT DEFAULT '翌月末払い'")
                ]

                for col_name, col_def in project_columns:
                    if col_name not in columns:
                        cursor.execute(f"ALTER TABLE expenses ADD COLUMN {col_name} {col_def}")
                        log_message(f"expenses テーブルに {col_name} カラムを追加しました")

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
                        master_id INTEGER DEFAULT NULL,
                        client_name TEXT DEFAULT '',
                        department TEXT DEFAULT '',
                        project_status TEXT DEFAULT '進行中',
                        project_start_date TEXT DEFAULT '',
                        project_end_date TEXT DEFAULT '',
                        budget REAL DEFAULT 0,
                        approver TEXT DEFAULT '',
                        urgency_level TEXT DEFAULT '通常',
                        payment_timing TEXT DEFAULT '翌月末払い'
                    )
                """
                )
                log_message("expenses テーブルを新規作成しました（案件情報フィールド含む）")

        except sqlite3.Error as e:
            log_message(f"expenses テーブル初期化エラー: {e}")

        conn.commit()
        conn.close()

        # 費用マスターデータベース
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        # 費用マスターテーブル（案件情報フィールド追加）
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
                broadcast_days TEXT,
                client_name TEXT DEFAULT '',
                department TEXT DEFAULT '',
                project_status TEXT DEFAULT '進行中',
                project_start_date TEXT DEFAULT '',
                project_end_date TEXT DEFAULT '',
                budget REAL DEFAULT 0,
                approver TEXT DEFAULT '',
                urgency_level TEXT DEFAULT '通常',
                payment_timing TEXT DEFAULT '翌月末払い'
            )
        """
        )

        # 既存のexpense_masterテーブルに案件情報カラムを追加（存在しない場合のみ）
        try:
            cursor.execute("PRAGMA table_info(expense_master)")
            master_columns = [column[1] for column in cursor.fetchall()]

            project_columns = [
                ("client_name", "TEXT DEFAULT ''"),
                ("department", "TEXT DEFAULT ''"),
                ("project_status", "TEXT DEFAULT '進行中'"),
                ("project_start_date", "TEXT DEFAULT ''"),
                ("project_end_date", "TEXT DEFAULT ''"),
                ("budget", "REAL DEFAULT 0"),
                ("approver", "TEXT DEFAULT ''"),
                ("urgency_level", "TEXT DEFAULT '通常'"),
                ("payment_timing", "TEXT DEFAULT '翌月末払い'")
            ]

            for col_name, col_def in project_columns:
                if col_name not in master_columns:
                    cursor.execute(f"ALTER TABLE expense_master ADD COLUMN {col_name} {col_def}")
                    log_message(f"expense_master テーブルに {col_name} カラムを追加しました")

        except sqlite3.Error as e:
            log_message(f"expense_master テーブル案件情報カラム追加エラー: {e}")

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
        """CSVファイルからデータをインポート（支払いコード0埋め対応）"""
        from utils import format_payee_code  # 追加

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

                # 【追加】支払い先コードの0埋め処理
                if "payee_code" in values and values["payee_code"]:
                    values["payee_code"] = format_payee_code(values["payee_code"])

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
        """支払いデータを取得（支払いコード0埋め対応）"""
        from utils import format_payee_code  # 追加

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

        # 【追加】支払い先コードの0埋め処理
        formatted_rows = []
        for row in payment_rows:
            row_list = list(row)
            if row_list[4]:  # payee_code が存在する場合
                row_list[4] = format_payee_code(row_list[4])
            formatted_rows.append(tuple(row_list))

        # 照合済み件数を取得
        cursor.execute(
            """
            SELECT COUNT(*) FROM payments
            WHERE status = '照合済'
            """
        )
        matched_count = cursor.fetchone()[0]

        conn.close()
        return formatted_rows, matched_count  # formatted_rows を返す

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
        from utils import format_payee_code

        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        try:
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

            # 支払い先コードの0埋め処理
            formatted_rows = []
            for row in expense_rows:
                row_list = list(row)
                row_list[3] = format_payee_code(row[3])  # payee_code を0埋め
                formatted_rows.append(tuple(row_list))

            # 照合済み件数を取得
            cursor.execute(
                """
                SELECT COUNT(*) FROM expenses
                WHERE status = '照合済'
                """
            )

            matched_count = cursor.fetchone()[0]

            return formatted_rows, matched_count  # formatted_rows を返す

        except Exception as e:
            log_message(f"費用データ取得エラー: {e}")
            return [], 0
        finally:
            conn.close()

    def get_expense_by_id(self, expense_id):
        """IDで費用データを取得"""
        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_name, payee, payee_code, amount, payment_date, status,
                   client_name, department, project_status, project_start_date,
                   project_end_date, budget, approver, urgency_level, payment_timing
            FROM expenses WHERE id = ?
            """,
            (expense_id,),
        )

        row = cursor.fetchone()
        conn.close()
        return row

    def save_expense(self, data, is_new=False):
        """費用データを保存"""
        # 関数の最初に追加
        from utils import format_payee_code

        conn = sqlite3.connect(self.expenses_db)
        cursor = conn.cursor()

        # 【追加】支払い先コードの0埋め処理
        if data.get("payee_code"):
            data["payee_code"] = format_payee_code(data["payee_code"])

        # 支払い先マスターを更新
        if data.get("payee") and data.get("payee_code"):
            self.update_or_create_payee_master(data["payee"], data["payee_code"])

        try:
            if is_new:
                cursor.execute(
                    """
                    INSERT INTO expenses (
                        project_name, payee, payee_code, amount, payment_date, status,
                        source_type, master_id, client_name, department, project_status,
                        project_start_date, project_end_date, budget, approver, urgency_level, payment_timing
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        data.get("client_name", ""),
                        data.get("department", ""),
                        data.get("project_status", "進行中"),
                        data.get("project_start_date", ""),
                        data.get("project_end_date", ""),
                        data.get("budget", 0),
                        data.get("approver", ""),
                        data.get("urgency_level", "通常"),
                        data.get("payment_timing", "翌月末払い"),
                    ),
                )
                expense_id = cursor.lastrowid
            else:
                cursor.execute(
                    """
                    UPDATE expenses
                    SET project_name = ?, payee = ?, payee_code = ?, amount = ?, payment_date = ?, status = ?,
                        client_name = ?, department = ?, project_status = ?, project_start_date = ?,
                        project_end_date = ?, budget = ?, approver = ?, urgency_level = ?, payment_timing = ?
                    WHERE id = ?
                    """,
                    (
                        data["project_name"],
                        data["payee"],
                        data["payee_code"],
                        data["amount"],
                        data["payment_date"],
                        data["status"],
                        data.get("client_name", ""),
                        data.get("department", ""),
                        data.get("project_status", "進行中"),
                        data.get("project_start_date", ""),
                        data.get("project_end_date", ""),
                        data.get("budget", 0),
                        data.get("approver", ""),
                        data.get("urgency_level", "通常"),
                        data.get("payment_timing", "翌月末払い"),
                        data["id"],
                    ),
                )
                expense_id = data["id"]

            conn.commit()
            log_message(f"費用データ保存完了: ID={expense_id}")
            return expense_id

        except Exception as e:
            conn.rollback()
            log_message(f"費用データ保存エラー: {e}")
            raise
        finally:
            conn.close()

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

    def get_master_data(self, search_term=None, full_data=False):
        # 関数の最初に追加
        from utils import format_payee_code

        """費用マスターデータを取得"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        if full_data:
            # 全フィールドを取得（CSV出力用）
            if search_term:
                search_param = f"%{search_term}%"
                cursor.execute(
                    """
                    SELECT id, project_name, payee, payee_code, amount, payment_type,
                           broadcast_days, start_date, end_date, client_name, department,
                           project_status, project_start_date, project_end_date, budget,
                           approver, urgency_level
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
                           broadcast_days, start_date, end_date, client_name, department,
                           project_status, project_start_date, project_end_date, budget,
                           approver, urgency_level
                    FROM expense_master
                    ORDER BY id
                    """)
        else:
            # 基本フィールドのみ取得（既存の動作を維持）
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
        # 【追加】支払い先コードの0埋め処理
        formatted_rows = []
        for row in master_rows:
            row_list = list(row)
            row_list[3] = format_payee_code(row[3])  # payee_code を0埋め
            formatted_rows.append(tuple(row_list))

        conn.close()
        return formatted_rows  # formatted_rows に変更

    def get_master_by_id(self, master_id):
        """IDで費用マスターデータを取得"""
        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_name, payee, payee_code, amount, payment_type,
                   broadcast_days, start_date, end_date, client_name, department,
                   project_status, project_start_date, project_end_date, budget,
                   approver, urgency_level, payment_timing
            FROM expense_master WHERE id = ?
            """,
            (master_id,),
        )

        row = cursor.fetchone()
        conn.close()
        return row

    def save_master(self, data, is_new=False):
        """費用マスターデータを保存"""
        # 関数の最初に追加
        from utils import format_payee_code

        conn = sqlite3.connect(self.expense_master_db)
        cursor = conn.cursor()

        # 【追加】支払い先コードの0埋め処理
        if data.get("payee_code"):
            data["payee_code"] = format_payee_code(data["payee_code"])

        # 支払い先マスターを更新
        if data.get("payee") and data.get("payee_code"):
            self.update_or_create_payee_master(data["payee"], data["payee_code"])

        try:
            if is_new:
                cursor.execute(
                    """
                    INSERT INTO expense_master (
                        project_name, payee, payee_code, amount, payment_type,
                        start_date, end_date, broadcast_days, status,
                        client_name, department, project_status, project_start_date,
                        project_end_date, budget, approver, urgency_level, payment_timing
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '未処理', ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        data.get("client_name", ""),
                        data.get("department", ""),
                        data.get("project_status", "進行中"),
                        data.get("project_start_date", ""),
                        data.get("project_end_date", ""),
                        data.get("budget", 0),
                        data.get("approver", ""),
                        data.get("urgency_level", "通常"),
                        data.get("payment_timing", "翌月末払い"),
                    ),
                )
                master_id = cursor.lastrowid
            else:
                cursor.execute(
                    """
                    UPDATE expense_master
                    SET project_name = ?, payee = ?, payee_code = ?, amount = ?,
                        payment_type = ?, start_date = ?, end_date = ?, broadcast_days = ?,
                        client_name = ?, department = ?, project_status = ?, project_start_date = ?,
                        project_end_date = ?, budget = ?, approver = ?, urgency_level = ?, payment_timing = ?
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
                        data.get("client_name", ""),
                        data.get("department", ""),
                        data.get("project_status", "進行中"),
                        data.get("project_start_date", ""),
                        data.get("project_end_date", ""),
                        data.get("budget", 0),
                        data.get("approver", ""),
                        data.get("urgency_level", "通常"),
                        data.get("payment_timing", "翌月末払い"),
                        data["id"],
                    ),
                )
                master_id = data["id"]

            conn.commit()
            log_message(f"マスターデータ保存完了: ID={master_id}")
            return master_id

        except Exception as e:
            conn.rollback()
            log_message(f"マスターデータ保存エラー: {e}")
            raise
        finally:
            conn.close()

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

    # database.py の修正が必要な部分

    def _calculate_previous_month(self, year, month):
        """前月の年月を計算するヘルパー関数

        Args:
            year: 年
            month: 月

        Returns:
            tuple: (前月の年, 前月の月)
        """
        if month == 1:
            return (year - 1, 12)
        else:
            return (year, month - 1)

    def generate_expenses_from_master(self, target_year, target_month):
        """マスターデータから指定月の費用データを生成（支払い月ベース）

        target_year/target_month = 支払い月として処理
        payment_timingに応じて発生月を計算し、回数ベースの計算を行う
        """
        master_conn = sqlite3.connect(self.expense_master_db)
        master_cursor = master_conn.cursor()

        expense_conn = sqlite3.connect(self.expenses_db)
        expense_cursor = expense_conn.cursor()

        try:
            # 指定月の最終日を取得（支払日用）
            last_day = calendar.monthrange(target_year, target_month)[1]
            target_month_str = f"{target_year:04d}-{target_month:02d}"

            # マスターデータを取得（payment_timingも含む）
            master_cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_type,
                    broadcast_days, start_date, end_date, payment_timing
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
                payment_timing = master_row[9] if len(master_row) > 9 and master_row[9] else "翌月末払い"

                # payment_timingに基づいて発生月を計算
                # target_year/target_month = 支払い月
                if payment_timing == "翌月末払い":
                    # 翌月末払い = 支払い月の前月が発生月
                    occurrence_year, occurrence_month = self._calculate_previous_month(target_year, target_month)
                else:  # "当月末払い"
                    # 当月末払い = 支払い月が発生月
                    occurrence_year = target_year
                    occurrence_month = target_month

                # 開始日と終了日のチェック（発生月で確認）
                occurrence_date = datetime(occurrence_year, occurrence_month, 1)

                # 開始日のチェック
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        if occurrence_date < start_dt:
                            continue  # まだ開始されていない
                    except ValueError:
                        pass

                # 終了日のチェック
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        if occurrence_date > end_dt:
                            continue  # 既に終了している
                    except ValueError:
                        pass

                # 支払日と金額を決定
                if payment_type == "回数ベース" and broadcast_days:
                    # 回数ベース計算は発生月の前月実績で計算
                    result = calculate_count_based_amount(
                        amount, broadcast_days, occurrence_year, occurrence_month, use_previous_month=True
                    )
                    
                    if result['error']:
                        log_message(f"回数ベース計算エラー（マスターID: {master_id}）: {result['error']}")
                        continue  # エラーの場合はこのマスターをスキップ
                    
                    calculated_amount = result['amount']
                    # 支払日は支払い月の末日
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
                        SET project_name = ?, payee = ?, payee_code = ?, amount = ?, payment_date = ?, payment_timing = ?
                        WHERE id = ?
                        """,
                        (
                            project_name,
                            payee,
                            payee_code,
                            calculated_amount,
                            payment_date,
                            payment_timing,
                            existing_expense[0],
                        ),
                    )
                    updated_count += 1
                else:
                    # 新規データを作成
                    expense_cursor.execute(
                        """
                        INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status, source_type, master_id, payment_timing)
                        VALUES (?, ?, ?, ?, ?, '未処理', 'master', ?, ?)
                        """,
                        (
                            project_name,
                            payee,
                            payee_code,
                            calculated_amount,
                            payment_date,
                            master_id,
                            payment_timing,
                        ),
                    )
                    generated_count += 1

            expense_conn.commit()

            log_message(
                f"{target_year}年{target_month}月支払い分の費用データを生成: 新規{generated_count}件、更新{updated_count}件"
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
        """新たに追加されたマスター項目のみを今月分に反映（修正版）"""
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
                    m.broadcast_days, m.start_date, m.end_date, m.payment_timing
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
                payment_timing = master_row[9] if len(master_row) > 9 and master_row[9] else "翌月末払い"

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
                        log_message(f"新規マスター回数ベース計算エラー（マスターID: {master_id}）: {result['error']}")
                        continue  # エラーの場合はこのマスターをスキップ
                    
                    calculated_amount = result['amount']
                    # 支払日は今月の末日
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
                    INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status, source_type, master_id, payment_timing)
                    VALUES (?, ?, ?, ?, ?, '未処理', 'master', ?, ?)
                    """,
                    (
                        project_name,
                        payee,
                        payee_code,
                        calculated_amount,
                        payment_date,
                        master_id,
                        payment_timing,
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

    def match_expenses_with_payments(self):
        """費用テーブルと支払いテーブルを照合（シンプル版: 支払い先コード + 金額 + 支払い月）"""
        from utils import format_payee_code

        # データベース接続
        expenses_conn = sqlite3.connect(self.expenses_db)
        expenses_cursor = expenses_conn.cursor()

        billing_conn = sqlite3.connect(self.billing_db)
        billing_cursor = billing_conn.cursor()

        try:
            # 費用データを取得（payment_timingも含む）
            expenses_cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_date, status, payment_timing
                FROM expenses
                WHERE payee_code IS NOT NULL AND payee_code != ''
                AND status != '照合済'
                ORDER BY id
                """
            )
            expense_rows = expenses_cursor.fetchall()

            if not expense_rows:
                log_message("照合対象の費用データがありません")
                return 0, 0

            # 支払いデータを取得
            billing_cursor.execute(
                """
                SELECT id, subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                WHERE payee_code IS NOT NULL AND payee_code != ''
                AND status != '照合済'
                ORDER BY id
                """
            )
            payment_rows = billing_cursor.fetchall()

            if not payment_rows:
                log_message("照合対象の支払いデータがありません")
                return 0, 0

            log_message(f"照合処理開始: 費用データ {len(expense_rows)}件、支払いデータ {len(payment_rows)}件")

            # 照合結果カウント
            matched_count = 0
            not_matched_count = 0

            # 日付文字列から年月を抽出する関数
            def extract_year_month(date_str):
                if not date_str:
                    return None
                try:
                    normalized = date_str.replace("/", "-").replace(".", "-").split("-")
                    if len(normalized) >= 2:
                        # 年の処理: 2桁の場合は20XXとして扱う
                        if len(normalized[0]) == 2:
                            year = "20" + normalized[0]
                        elif len(normalized[0]) == 4:
                            year = normalized[0]
                        else:
                            return None
                        month = normalized[1].zfill(2)
                        return f"{year}-{month}"
                except:
                    pass
                return None

            # 期待支払い月を計算する関数
            def calculate_expected_payment_month(expense_date, payment_timing):
                """費用の支払日と支払い時期から期待支払い月を計算"""
                year_month = extract_year_month(expense_date)
                if not year_month:
                    return None

                try:
                    year, month = map(int, year_month.split("-"))

                    if payment_timing == "当月末払い":
                        # 同じ月に支払い
                        return f"{year:04d}-{month:02d}"
                    else:  # 翌月末払い（デフォルト）
                        # 翌月に支払い
                        month += 1
                        if month > 12:
                            month = 1
                            year += 1
                        return f"{year:04d}-{month:02d}"
                except:
                    return None

            # 成功した更新ID一覧（重複更新を避けるため）
            updated_payment_ids = set()
            updated_expense_ids = set()

            # 各費用データについて支払いデータと照合
            for expense in expense_rows:
                if expense[0] in updated_expense_ids:
                    continue

                expense_id = expense[0]
                expense_payee_code = format_payee_code(expense[3].strip())
                expense_amount = int(float(expense[4])) if expense[4] else 0  # 整数化
                expense_payment_date = expense[5]
                expense_payment_timing = expense[7] if len(expense) > 7 and expense[7] else "翌月末払い"

                # 期待支払い月を計算
                expected_payment_month = calculate_expected_payment_month(
                    expense_payment_date, expense_payment_timing
                )

                if not expected_payment_month:
                    log_message(f"費用ID:{expense_id} - 日付が不正です: {expense_payment_date}")
                    not_matched_count += 1
                    continue

                # 一致する支払いデータを検索
                best_match = None

                for payment in payment_rows:
                    if payment[0] in updated_payment_ids:
                        continue

                    payment_id = payment[0]
                    payment_payee_code = format_payee_code(payment[4].strip()) if payment[4] else ""
                    payment_amount = int(float(payment[5])) if payment[5] else 0  # 整数化
                    payment_year_month = extract_year_month(payment[6])

                    # 照合条件: 支払い先コード + 金額 + 支払い月
                    code_match = expense_payee_code == payment_payee_code
                    amount_match = expense_amount == payment_amount
                    month_match = expected_payment_month == payment_year_month

                    # デバッグログ
                    if code_match and amount_match:
                        log_message(f"照合チェック - 費用ID:{expense_id}, 支払ID:{payment_id}")
                        log_message(f"  コード: {expense_payee_code} == {payment_payee_code} -> {code_match}")
                        log_message(f"  金額: {expense_amount} == {payment_amount} -> {amount_match}")
                        log_message(f"  月: {expected_payment_month} ({expense_payment_timing}) == {payment_year_month} -> {month_match}")

                    # 3条件全て一致したら照合成功
                    if code_match and amount_match and month_match:
                        best_match = payment_id
                        log_message(f"照合成功: 費用ID:{expense_id} <-> 支払ID:{payment_id}")
                        break

                if best_match:
                    try:
                        # 費用データを照合済みに更新
                        expenses_cursor.execute(
                            "UPDATE expenses SET status = '照合済' WHERE id = ?",
                            (expense_id,),
                        )

                        if expenses_cursor.rowcount == 0:
                            log_message(f"⚠️ 費用データ更新失敗: ID={expense_id}")
                            continue

                        # 支払いデータを照合済みに更新
                        billing_cursor.execute(
                            "UPDATE payments SET status = '照合済' WHERE id = ?",
                            (best_match,),
                        )

                        if billing_cursor.rowcount == 0:
                            log_message(f"⚠️ 支払いデータ更新失敗: ID={best_match}")
                            expenses_conn.rollback()
                            billing_conn.rollback()
                            continue

                        updated_expense_ids.add(expense_id)
                        updated_payment_ids.add(best_match)
                        matched_count += 1

                    except sqlite3.Error as e:
                        log_message(f"データベース更新エラー: {e}")
                else:
                    not_matched_count += 1

            # コミット
            expenses_conn.commit()
            billing_conn.commit()

            # 統計情報をログ出力
            log_message("=" * 50)
            log_message("照合処理統計結果:")
            log_message(f"  対象費用データ: {len(expense_rows)}件")
            log_message(f"  対象支払いデータ: {len(payment_rows)}件")
            log_message(f"  照合成功: {matched_count}件")
            log_message(f"  照合失敗: {not_matched_count}件")
            log_message(f"  照合率: {matched_count/(len(expense_rows)) * 100:.1f}%")
            log_message("=" * 50)

            return matched_count, not_matched_count

        except Exception as e:
            log_message(f"照合処理中にエラー: {e}")
            expenses_conn.rollback()
            billing_conn.rollback()
            raise

        finally:
            expenses_conn.close()
            billing_conn.close()

    def get_project_filter_data(self, filters=None):
        """案件絞込み用のデータを取得"""
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        try:
            # 基本クエリ
            base_query = """
                SELECT DISTINCT project_name, client_name, department, project_status, 
                       project_start_date, project_end_date, budget,
                       COUNT(*) as payment_count,
                       SUM(amount) as total_amount
                FROM payments 
                WHERE project_name IS NOT NULL AND project_name != ''
            """
            
            params = []
            conditions = []

            # フィルター条件を追加
            if filters:
                if filters.get('search_term'):
                    conditions.append("(project_name LIKE ? OR client_name LIKE ?)")
                    search_param = f"%{filters['search_term']}%"
                    params.extend([search_param, search_param])
                
                if filters.get('project_status'):
                    conditions.append("project_status = ?")
                    params.append(filters['project_status'])
                
                if filters.get('department'):
                    conditions.append("department = ?")
                    params.append(filters['department'])
                
                if filters.get('client_name'):
                    conditions.append("client_name = ?")
                    params.append(filters['client_name'])
                
                if filters.get('payment_month'):
                    conditions.append("strftime('%Y-%m', REPLACE(payment_date, '/', '-')) = ?")
                    params.append(filters['payment_month'])
                
                if filters.get('payment_status'):
                    conditions.append("status = ?")
                    params.append(filters['payment_status'])

            # 条件を結合
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " GROUP BY project_name, client_name, department, project_status"
            base_query += " ORDER BY project_name"

            cursor.execute(base_query, params)
            project_rows = cursor.fetchall()

            return project_rows

        except Exception as e:
            log_message(f"案件データ取得エラー: {e}")
            return []
        finally:
            conn.close()

    def get_payments_by_project(self, project_name, payment_month=None):
        """指定案件の支払いデータを取得"""
        from utils import format_payee_code
        
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        try:
            base_query = """
                SELECT id, subject, project_name, payee, payee_code, amount, 
                       payment_date, status, urgency_level, approver
                FROM payments
                WHERE project_name = ?
            """
            params = [project_name]
            
            # 支払い月フィルターを追加（日付形式変換対応）
            if payment_month:
                base_query += " AND strftime('%Y-%m', REPLACE(payment_date, '/', '-')) = ?"
                params.append(payment_month)
            
            base_query += " ORDER BY payment_date DESC"
            
            cursor.execute(base_query, params)

            payment_rows = cursor.fetchall()

            # 支払い先コードの0埋め処理
            formatted_rows = []
            for row in payment_rows:
                row_list = list(row)
                if row_list[4]:  # payee_code が存在する場合
                    row_list[4] = format_payee_code(row_list[4])
                formatted_rows.append(tuple(row_list))

            return formatted_rows

        except Exception as e:
            log_message(f"案件支払いデータ取得エラー: {e}")
            return []
        finally:
            conn.close()

    def get_filter_options(self):
        """絞込み用の選択肢を取得"""
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        try:
            # 案件進行状況の選択肢
            cursor.execute("SELECT DISTINCT project_status FROM payments WHERE project_status IS NOT NULL AND project_status != ''")
            project_status_options = [row[0] for row in cursor.fetchall()]
            
            # 支払い状態の選択肢
            cursor.execute("SELECT DISTINCT status FROM payments WHERE status IS NOT NULL AND status != ''")
            payment_status_options = [row[0] for row in cursor.fetchall()]

            # 担当部門の選択肢
            cursor.execute("SELECT DISTINCT department FROM payments WHERE department IS NOT NULL AND department != ''")
            department_options = [row[0] for row in cursor.fetchall()]

            # クライアントの選択肢
            cursor.execute("SELECT DISTINCT client_name FROM payments WHERE client_name IS NOT NULL AND client_name != ''")
            client_options = [row[0] for row in cursor.fetchall()]
            
            # 支払い月の選択肢（日付形式変換対応）
            cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', REPLACE(payment_date, '/', '-')) as payment_month
                FROM payments 
                WHERE payment_date IS NOT NULL AND payment_date != ''
                AND strftime('%Y-%m', REPLACE(payment_date, '/', '-')) IS NOT NULL
                ORDER BY payment_month DESC
            """)
            payment_month_options = [row[0] for row in cursor.fetchall() if row[0]]
            
            # デバッグログ出力
            log_message(f"フィルターオプション取得結果:")
            log_message(f"  案件進行状況: {len(project_status_options)}件")
            log_message(f"  支払い状態: {len(payment_status_options)}件")
            log_message(f"  担当部門: {len(department_options)}件")
            log_message(f"  クライアント: {len(client_options)}件")
            log_message(f"  支払い月: {len(payment_month_options)}件 - {payment_month_options[:5]}")

            return {
                'project_status_options': project_status_options,
                'payment_status_options': payment_status_options,
                'department_options': department_options,
                'client_options': client_options,
                'payment_month_options': payment_month_options
            }

        except Exception as e:
            log_message(f"フィルターオプション取得エラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")
            return {
                'project_status_options': [],
                'payment_status_options': [],
                'department_options': [],
                'client_options': [],
                'payment_month_options': []
            }
        finally:
            conn.close()

    def update_payment_project_info(self, payment_id, project_info):
        """支払いデータの案件情報を更新"""
        conn = sqlite3.connect(self.billing_db)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE payments
                SET client_name = ?, department = ?, project_status = ?, 
                    project_start_date = ?, project_end_date = ?, budget = ?, 
                    approver = ?, urgency_level = ?
                WHERE id = ?
                """,
                (
                    project_info.get('client_name', ''),
                    project_info.get('department', ''),
                    project_info.get('project_status', '進行中'),
                    project_info.get('project_start_date', ''),
                    project_info.get('project_end_date', ''),
                    project_info.get('budget', 0),
                    project_info.get('approver', ''),
                    project_info.get('urgency_level', '通常'),
                    payment_id
                )
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            log_message(f"案件情報更新エラー: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# ファイル終了確認用のコメント - database.py完了
