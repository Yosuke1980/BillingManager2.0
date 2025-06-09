from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QScrollArea,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QMessageBox,
    QCompleter,
    QSplitter,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, pyqtSlot, QStringListModel
from PyQt5.QtGui import QColor, QFont, QBrush
import csv
import os
from datetime import datetime, timedelta
from utils import format_amount, log_message

# 不要なインポートを削除
import sqlite3


class PayeeLineEdit(QLineEdit):
    """支払い先入力用のカスタムLineEdit（自動補完機能付き）"""

    def __init__(self, db_manager, code_field=None):
        super().__init__()
        self.db_manager = db_manager
        self.code_field = code_field  # 連動するコードフィールド
        self.setup_completer()

    def setup_completer(self):
        """オートコンプリーターの設定"""
        # 支払い先候補を取得
        suggestions = self.db_manager.get_payee_suggestions()
        payee_names = [suggestion[0] for suggestion in suggestions]

        # コンプリーターを設定
        completer = QCompleter(payee_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(completer)

        # テキスト変更時にコードを自動入力
        self.textChanged.connect(self.auto_fill_code)

    def auto_fill_code(self, text):
        """支払い先名が変更された時にコードを自動入力（0埋め対応）"""
        from utils import format_payee_code  # 追加

        if self.code_field and text:
            code = self.db_manager.get_payee_code_by_name(text)
            if code:
                # 【追加】コードを0埋めしてから設定
                formatted_code = format_payee_code(code)
                self.code_field.setText(formatted_code)


class ExpenseTab(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db_manager = app.db_manager
        self.status_label = app.status_label

        # ソート情報
        self.sort_info = {"column": None, "reverse": False}

        # 色分け設定（より明確な色を使用）
        self.matched_color = QColor(144, 238, 144)  # ライトグリーン（照合済み）
        self.processing_color = QColor(255, 255, 153)  # 薄い黄色（処理中）
        self.unprocessed_color = QColor(255, 255, 255)  # 白（未処理）
        self.completed_color = QColor(173, 216, 230)  # ライトブルー（完了）

        # レイアウト設定
        self.setup_ui()

    def setup_ui(self):
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # 上部操作エリア
        top_frame = QFrame()
        top_frame.setFrameStyle(QFrame.StyledPanel)
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(8)
        main_layout.addWidget(top_frame)

        # 凡例エリア（色分けの説明）
        legend_widget = QWidget()
        legend_layout = QHBoxLayout(legend_widget)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(legend_widget)

        legend_layout.addWidget(QLabel("🎨 色分け凡例:"))

        # 各状態の色見本を表示
        legend_items = [
            ("照合済み", self.matched_color),
            ("処理中", self.processing_color),
            ("完了", self.completed_color),
            ("未処理", self.unprocessed_color),
        ]

        for status, color in legend_items:
            color_label = QLabel(f" {status} ")
            color_label.setStyleSheet(
                f"""
                background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                border: 1px solid #888;
                padding: 2px 8px;
                border-radius: 3px;
                font-weight: bold;
            """
            )
            legend_layout.addWidget(color_label)

        legend_layout.addStretch()

        # 検索・フィルタエリア
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(search_widget)

        # 支払い月フィルタ
        search_layout.addWidget(QLabel("📅 支払い月:"))
        self.payment_month_filter = QComboBox()
        self.payment_month_filter.addItem("すべて表示")
        self.payment_month_filter.setFixedWidth(120)
        self.payment_month_filter.currentTextChanged.connect(self.filter_by_month)
        search_layout.addWidget(self.payment_month_filter)

        # 状態フィルタ
        search_layout.addWidget(QLabel("📊 状態:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["すべて", "未処理", "処理中", "照合済", "完了"])
        self.status_filter.setFixedWidth(100)
        self.status_filter.currentTextChanged.connect(self.filter_by_status)
        search_layout.addWidget(self.status_filter)

        # 検索フィールド
        search_layout.addWidget(QLabel("🔍 検索:"))
        self.search_entry = QLineEdit()
        self.search_entry.setFixedWidth(200)
        self.search_entry.setPlaceholderText("案件名、支払い先で検索...")
        self.search_entry.returnPressed.connect(self.search_records)  # Enterキーで検索
        search_layout.addWidget(self.search_entry)

        # 検索ボタン
        search_button = QPushButton("検索")
        search_button.setFixedSize(60, 30)
        search_button.clicked.connect(self.search_records)
        search_layout.addWidget(search_button)

        # リセットボタン
        reset_button = QPushButton("リセット")
        reset_button.setFixedSize(60, 30)
        reset_button.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_button)

        search_layout.addStretch()

        # マスター費用生成エリア
        master_widget = QWidget()
        master_layout = QHBoxLayout(master_widget)
        master_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(master_widget)

        # マスター費用生成グループ
        master_group = QGroupBox("📊 マスター費用生成")
        master_group_layout = QHBoxLayout(master_group)
        master_group_layout.setContentsMargins(8, 8, 8, 8)
        master_layout.addWidget(master_group)

        # 年月選択
        self.target_year_combo = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 3):
            self.target_year_combo.addItem(str(year))
        self.target_year_combo.setCurrentText(str(current_year))
        self.target_year_combo.setFixedWidth(80)
        master_group_layout.addWidget(self.target_year_combo)

        master_group_layout.addWidget(QLabel("年"))

        self.target_month_combo = QComboBox()
        for month in range(1, 13):
            self.target_month_combo.addItem(f"{month:02d}")
        current_month = datetime.now().month
        self.target_month_combo.setCurrentText(f"{current_month:02d}")
        self.target_month_combo.setFixedWidth(60)
        master_group_layout.addWidget(self.target_month_combo)

        master_group_layout.addWidget(QLabel("月"))

        # マスター生成ボタン
        reflect_new_button = QPushButton("🆕 新規マスター項目を今月反映")
        reflect_new_button.clicked.connect(self.reflect_new_master_to_current_month)
        master_group_layout.addWidget(reflect_new_button)

        generate_next_button = QPushButton("➡️ 来月分生成")
        generate_next_button.clicked.connect(self.generate_next_month_expenses)
        master_group_layout.addWidget(generate_next_button)

        generate_button = QPushButton("📋 選択月生成")
        generate_button.clicked.connect(self.generate_selected_month_expenses)
        master_group_layout.addWidget(generate_button)

        # 操作ボタンエリア
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(action_widget)

        # レコード操作グループ
        record_group = QGroupBox("📝 レコード操作")
        record_group_layout = QHBoxLayout(record_group)
        record_group_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.addWidget(record_group)

        create_button = QPushButton("➕ 新規作成")
        create_button.clicked.connect(self.create_record)
        record_group_layout.addWidget(create_button)

        delete_button = QPushButton("🗑️ 削除")
        delete_button.clicked.connect(self.delete_record)
        record_group_layout.addWidget(delete_button)

        duplicate_button = QPushButton("📄 複製")
        duplicate_button.clicked.connect(self.duplicate_record)
        record_group_layout.addWidget(duplicate_button)

        # 照合操作グループ
        match_group = QGroupBox("🔄 照合・データ操作")
        match_group_layout = QHBoxLayout(match_group)
        match_group_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.addWidget(match_group)

        match_button = QPushButton("💰 支払いと照合")
        match_button.clicked.connect(self.match_with_payments)
        match_group_layout.addWidget(match_button)

        export_button = QPushButton("📤 CSVエクスポート")
        export_button.clicked.connect(self.export_to_csv)
        match_group_layout.addWidget(export_button)

        import_button = QPushButton("📥 CSVインポート")
        import_button.clicked.connect(self.import_from_csv)
        match_group_layout.addWidget(import_button)

        # メインコンテンツエリア（スプリッター使用）
        content_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(content_splitter)

        # 上部：テーブル表示エリア
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(8, 8, 8, 8)
        content_splitter.addWidget(table_frame)

        # テーブルタイトル
        table_title = QLabel("💼 費用管理一覧")
        table_title.setFont(QFont("", 10, QFont.Bold))
        table_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        table_layout.addWidget(table_title)

        # ツリーウィジェットの作成
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["ID", "案件名", "支払い先", "コード", "金額", "支払日", "状態"]
        )
        table_layout.addWidget(self.tree)

        # 列の設定
        self.tree.setColumnHidden(0, True)  # IDを非表示
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)  # 案件名
        self.tree.header().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )  # 支払い先
        self.tree.header().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )  # コード
        self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 金額
        self.tree.header().setSectionResizeMode(
            5, QHeaderView.ResizeToContents
        )  # 支払日
        self.tree.header().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 状態

        # 複数選択を可能に
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setAlternatingRowColors(False)  # 交互背景色を無効化（色分けのため）

        # ヘッダークリックでソート機能（改善版）
        self.tree.header().sectionClicked.connect(self.on_header_clicked)
        self.tree.header().setSectionsClickable(True)
        self.tree.header().setSectionsMovable(False)

        # 選択時イベント
        self.tree.itemSelectionChanged.connect(self.on_tree_select_for_edit)

        # 下部：レコード編集エリア
        edit_frame = QFrame()
        edit_frame.setFrameStyle(QFrame.StyledPanel)
        edit_frame.setMaximumHeight(280)
        edit_layout = QVBoxLayout(edit_frame)
        edit_layout.setContentsMargins(8, 8, 8, 8)
        content_splitter.addWidget(edit_frame)

        # 編集エリアタイトル
        edit_title = QLabel("✏️ レコード編集")
        edit_title.setFont(QFont("", 10, QFont.Bold))
        edit_title.setStyleSheet("color: #2c3e50; margin-bottom: 8px;")
        edit_layout.addWidget(edit_title)

        # 編集フォームのグリッドレイアウト
        edit_grid = QWidget()
        edit_grid_layout = QGridLayout(edit_grid)
        edit_grid_layout.setContentsMargins(0, 0, 0, 0)
        edit_grid_layout.setSpacing(8)
        edit_layout.addWidget(edit_grid)

        # 編集フィールドの作成
        self.edit_entries = {}
        edit_fields = [
            ("ID:", "id", 0, 0, True),
            ("案件名:", "project_name", 0, 2, False),
            ("支払い先:", "payee", 1, 0, False),
            ("支払い先コード:", "payee_code", 1, 2, False),
            ("金額:", "amount", 2, 0, False),
            ("支払日:", "payment_date", 2, 2, False),
            ("状態:", "status", 3, 0, False),
        ]

        for label_text, field_key, row, col, read_only in edit_fields:
            # ラベル
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            edit_grid_layout.addWidget(label, row, col)

            # 入力ウィジェット
            if field_key == "id":
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setStyleSheet("background-color: #f8f9fa;")
            elif field_key == "payee":
                # 支払い先用のカスタムLineEdit（自動補完機能付き）
                widget = PayeeLineEdit(self.db_manager)
            elif field_key == "payee_code":
                widget = QLineEdit()
            elif field_key == "status":
                widget = QComboBox()
                widget.addItems(["未処理", "処理中", "照合済", "完了"])
            elif field_key == "payment_date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
            else:
                widget = QLineEdit()

            widget.setMinimumWidth(150)
            edit_grid_layout.addWidget(widget, row, col + 1)
            self.edit_entries[field_key] = widget

        # 支払い先と支払い先コードの連動を設定
        payee_widget = self.edit_entries.get("payee")
        payee_code_widget = self.edit_entries.get("payee_code")
        if isinstance(payee_widget, PayeeLineEdit) and payee_code_widget:
            payee_widget.code_field = payee_code_widget

        # 編集ボタンエリア
        edit_button_widget = QWidget()
        edit_button_layout = QHBoxLayout(edit_button_widget)
        edit_button_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.addWidget(edit_button_widget)

        edit_button_layout.addStretch()

        cancel_button = QPushButton("❌ キャンセル")
        cancel_button.setFixedSize(100, 35)
        cancel_button.clicked.connect(self.cancel_direct_edit)
        edit_button_layout.addWidget(cancel_button)

        save_button = QPushButton("💾 保存")
        save_button.setFixedSize(100, 35)
        save_button.clicked.connect(self.save_direct_edit)
        edit_button_layout.addWidget(save_button)

        # 初期状態では編集エリアは非表示
        edit_frame.hide()
        self.edit_frame = edit_frame

        # スプリッターの初期サイズ設定
        content_splitter.setSizes([600, 280])

    def get_color_for_status(self, status):
        """状態に応じた背景色を返す"""
        color_map = {
            "照合済": self.matched_color,
            "処理中": self.processing_color,
            "完了": self.completed_color,
            "未処理": self.unprocessed_color,
        }
        return color_map.get(status, self.unprocessed_color)

    def apply_row_colors(self, item, status, column_count=7):
        """行に色を適用する共通メソッド"""
        background_color = self.get_color_for_status(status)
        brush = QBrush(background_color)

        for i in range(column_count):
            item.setBackground(i, brush)
            # さらに確実にするため、データも設定
            item.setData(i, Qt.BackgroundRole, background_color)

        # 照合済みの場合は太字
        if status == "照合済":
            font = QFont()
            font.setBold(True)
            for i in range(column_count):
                item.setFont(i, font)

    def filter_by_status(self):
        """状態でフィルタリング"""
        selected_status = self.status_filter.currentText()

        if selected_status == "すべて":
            self.refresh_data()
            return

        # 現在表示されている項目をフィルタリング
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            status = item.text(6)  # 状態列
            item.setHidden(status != selected_status)

        # 表示件数を更新
        visible_count = sum(
            1 for i in range(root.childCount()) if not root.child(i).isHidden()
        )
        self.app.status_label.setText(
            f"{selected_status}の費用データ: {visible_count}件"
        )

    def on_header_clicked(self, logical_index):
        """ヘッダークリック時のソート処理（改善版）"""
        if logical_index == 0:  # ID列は非表示なのでソートしない
            return

        # ヘッダー名を取得
        header_item = self.tree.headerItem()
        column_name = header_item.text(logical_index)

        # 同じ列を再度クリックした場合は昇順/降順を切り替え
        if self.sort_info["column"] == column_name:
            self.sort_info["reverse"] = not self.sort_info["reverse"]
        else:
            self.sort_info["reverse"] = False
            self.sort_info["column"] = column_name

        # ソート実行
        self.sort_tree_widget(column_name, self.sort_info["reverse"])

        # ソート状態を視覚的に表示（改善版）
        for i in range(self.tree.columnCount()):
            current_text = self.tree.headerItem().text(i)
            base_text = current_text.split(" ")[0]  # ▲▼を除いた部分

            if i == logical_index:
                # ソート対象の列には矢印を追加
                direction = " 🔽" if self.sort_info["reverse"] else " 🔼"
                self.tree.headerItem().setText(i, base_text + direction)
            else:
                # 他の列は元のテキストに戻す
                if " 🔼" in current_text or " 🔽" in current_text:
                    self.tree.headerItem().setText(i, base_text)

        # ソート方向を状態表示に反映
        direction_text = "降順" if self.sort_info["reverse"] else "昇順"
        self.app.status_label.setText(f"{column_name}で{direction_text}ソート中")

    def sort_tree_widget(self, column_name, reverse):
        """ツリーウィジェットのデータを指定された列で並べ替え（改善版）"""
        # ヘッダーのテキストからインデックスを取得
        column_index = -1
        for i in range(self.tree.columnCount()):
            header_text = self.tree.headerItem().text(i).split(" ")[0]
            if header_text == column_name:
                column_index = i
                break

        if column_index == -1:
            return  # 列が見つからない場合

        # 現在の項目をすべて取得
        items = []
        root = self.tree.invisibleRootItem()

        for i in range(root.childCount()):
            items.append(root.takeChild(0))

        # ソート関数（改善版）
        def get_sort_key(item):
            value = item.text(column_index)

            # 値のタイプに応じてソート
            if column_name in ["金額"]:
                # 金額は円マークとカンマを取り除いて数値としてソート
                try:
                    value = value.replace(",", "").replace("円", "").strip()
                    return float(value) if value else 0
                except (ValueError, TypeError):
                    return 0
            elif column_name in ["支払日"]:
                # 日付は文字列としてソート（YYYY-MM-DD形式想定）
                return value if value else "0000-00-00"
            elif column_name in ["状態"]:
                # 状態は優先順位でソート
                status_priority = {"未処理": 1, "処理中": 2, "照合済": 3, "完了": 4}
                return status_priority.get(value, 0)
            else:
                # その他は文字列としてソート
                return value.lower() if value else ""

        # ソート実行
        try:
            items.sort(key=get_sort_key, reverse=reverse)
        except Exception as e:
            log_message(f"ソート中にエラー: {e}")
            # エラーが発生した場合は文字列ソートで再試行
            items.sort(
                key=lambda item: item.text(column_index).lower(), reverse=reverse
            )

        # ツリーに再追加
        for item in items:
            self.tree.addTopLevelItem(item)

    def reflect_new_master_to_current_month(self):
        """新たに追加されたマスター項目のみを今月分に反映"""
        try:
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month

            log_message(
                f"新規マスター項目の今月反映開始: {current_year}年{current_month}月"
            )

            # まず、未反映の項目があるかチェック
            missing_items = self.db_manager.get_missing_master_expenses_for_month(
                current_year, current_month
            )

            if not missing_items:
                QMessageBox.information(
                    self,
                    "情報",
                    f"{current_year}年{current_month}月分に追加すべき新規マスター項目はありません。\n\n"
                    "すべてのマスター項目が既に今月分に反映済みです。",
                )
                return

            # 未反映項目の一覧を表示して確認
            item_list = []
            for item in missing_items:
                project_name = item[1]
                payee = item[2]
                amount = item[4]
                payment_type = item[5] if len(item) > 5 else "月額固定"
                item_list.append(
                    f"• {project_name} ({payee}) - {payment_type}: {amount:,.0f}円"
                )

            item_text = "\n".join(item_list)

            reply = QMessageBox.question(
                self,
                "新規マスター項目の今月反映",
                f"{current_year}年{current_month}月分に以下の{len(missing_items)}件のマスター項目を追加しますか？\n\n"
                f"{item_text}\n\n"
                "※ 既存のデータには影響しません。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply != QMessageBox.Yes:
                return

            # 新規マスター項目を今月分に反映
            generated_count, generated_items = (
                self.db_manager.generate_new_master_expenses_for_current_month()
            )

            log_message(f"新規マスター項目反映完了: {generated_count}件")

            # データを更新表示
            self.refresh_data()

            # 結果表示
            if generated_count > 0:
                result_list = []
                for item in generated_items:
                    result_list.append(
                        f"• {item['project_name']} ({item['payee']}) - "
                        f"{item['payment_type']}: {item['amount']:,.0f}円"
                    )
                result_text = "\n".join(result_list)

                message = (
                    f"{current_year}年{current_month}月分に{generated_count}件の新規マスター項目を反映しました。\n\n"
                    f"{result_text}"
                )

                self.app.status_label.setText(
                    f"新規マスター項目を今月分に{generated_count}件反映完了"
                )

                QMessageBox.information(self, "反映完了", message)
            else:
                QMessageBox.information(
                    self,
                    "情報",
                    "今月分に反映可能な新規マスター項目がありませんでした。",
                )

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            log_message(f"新規マスター項目の今月反映中にエラー: {e}")
            log_message(f"エラー詳細: {error_detail}")
            QMessageBox.critical(
                self,
                "エラー",
                f"新規マスター項目の今月反映に失敗しました。\n\n"
                f"エラー内容: {e}\n\n"
                f"詳細はログファイルを確認してください。",
            )

    def generate_next_month_expenses(self):
        """来月分の費用データをマスターから生成"""
        current_date = datetime.now()
        next_month = current_date.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)

        self.generate_expenses_from_master(next_month.year, next_month.month)

    def generate_selected_month_expenses(self):
        """選択された月の費用データをマスターから生成"""
        target_year = int(self.target_year_combo.currentText())
        target_month = int(self.target_month_combo.currentText())

        self.generate_expenses_from_master(target_year, target_month)

    def generate_expenses_from_master(self, year, month):
        """マスターデータから指定月の費用データを生成"""
        try:
            # 確認ダイアログ
            reply = QMessageBox.question(
                self,
                "確認",
                f"{year}年{month}月の費用データをマスターから生成しますか？\n\n"
                "既存のデータがある場合は更新されます。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

            log_message(f"マスター費用生成開始: {year}年{month}月")

            # マスターデータから費用データを生成
            generated_count, updated_count = (
                self.db_manager.generate_expenses_from_master(year, month)
            )

            log_message(
                f"マスター費用生成完了: 新規{generated_count}件、更新{updated_count}件"
            )

            # データを更新表示
            self.refresh_data()

            # 結果メッセージ
            message = f"{year}年{month}月の費用データを生成完了: 新規{generated_count}件、更新{updated_count}件"
            self.app.status_label.setText(message)

            # 結果ダイアログ
            QMessageBox.information(self, "生成完了", message)

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            log_message(f"マスター費用生成中にエラー: {e}")
            log_message(f"エラー詳細: {error_detail}")
            QMessageBox.critical(
                self,
                "エラー",
                f"マスター費用の生成に失敗しました。\n\n"
                f"エラー内容: {e}\n\n"
                f"詳細はログファイルを確認してください。",
            )

    def search_records(self):
        """費用レコードの検索"""
        search_term = self.search_entry.text().strip()
        if not search_term:
            self.refresh_data()
            return

        # ツリーのクリア
        self.tree.clear()

        try:
            # データベースから検索
            expense_rows, _ = self.db_manager.get_expense_data(search_term)

            # 検索結果をツリーウィジェットに追加
            for row in expense_rows:
                item = QTreeWidgetItem()

                # 値を設定
                item.setText(0, str(row[0]))  # ID
                item.setText(1, row[1])  # 案件名
                item.setText(2, row[2])  # 支払い先
                item.setText(3, row[3] if row[3] else "")  # 支払い先コード
                item.setText(4, format_amount(row[4]))  # 金額（整形）
                item.setText(5, row[5])  # 支払日
                item.setText(6, row[6])  # 状態

                # 状態に応じた背景色を適用
                status = row[6]
                self.apply_row_colors(item, status, 7)

                self.tree.addTopLevelItem(item)

            # 状態表示の更新
            self.app.status_label.setText(
                f"「{search_term}」の検索結果: {len(expense_rows)}件"
            )

        except Exception as e:
            log_message(f"費用データ検索中にエラーが発生: {e}")
            self.app.status_label.setText(f"エラー: 費用データ検索に失敗しました")

    def update_payment_month_filter(self):
        """支払い月フィルタのドロップダウンを更新（改善版）"""
        if not hasattr(self, "payment_month_filter"):
            return

        # シグナルを一時的にブロック
        self.payment_month_filter.blockSignals(True)

        current_filter = self.payment_month_filter.currentText()

        # 現在のドロップダウンの内容をクリア
        self.payment_month_filter.clear()
        self.payment_month_filter.addItem("すべて表示")

        # データベースから支払い月リストを取得
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_manager.expenses_db)
            cursor = conn.cursor()

            # 支払日から年月を抽出 (YYYY-MM形式)
            cursor.execute(
                """
                SELECT DISTINCT substr(payment_date, 1, 7) as month
                FROM expenses
                WHERE payment_date IS NOT NULL 
                AND payment_date != '' 
                AND length(payment_date) >= 7
                ORDER BY month DESC
                """
            )

            months = cursor.fetchall()
            conn.close()

            log_message(f"取得した支払い月: {len(months)}件")

            # ドロップダウンに追加
            for month_tuple in months:
                if month_tuple[0]:
                    month_value = month_tuple[0]  # YYYY-MM形式
                    # 年月の表示形式を調整（例：2024-03 → 2024年03月）
                    try:
                        year, month = month_value.split("-")
                        display_text = f"{year}年{month}月"
                        self.payment_month_filter.addItem(display_text, month_value)
                        log_message(f"月フィルタ追加: {display_text} -> {month_value}")
                    except ValueError:
                        log_message(f"不正な月フォーマット: {month_value}")
                        continue

            # 以前に選択されていた値があれば再設定
            if current_filter != "すべて表示":
                index = self.payment_month_filter.findText(current_filter)
                if index >= 0:
                    self.payment_month_filter.setCurrentIndex(index)

        except Exception as e:
            log_message(f"支払い月フィルタの更新中にエラー: {e}")
            import traceback

            log_message(f"エラー詳細: {traceback.format_exc()}")

        # シグナルブロックを解除
        self.payment_month_filter.blockSignals(False)

    def filter_by_month(self):
        """支払い月でフィルタリング（改善版）"""
        selected_month_text = self.payment_month_filter.currentText()

        log_message(f"月フィルタ実行: 選択テキスト='{selected_month_text}'")

        if selected_month_text == "すべて表示":
            log_message("すべて表示が選択されました")
            self.refresh_data()
            return

        # 現在選択されているアイテムのデータを取得
        current_index = self.payment_month_filter.currentIndex()
        selected_month = self.payment_month_filter.itemData(current_index)

        log_message(
            f"月フィルタ: インデックス={current_index}, データ='{selected_month}'"
        )

        # データが取得できない場合は、テキストから年月を抽出
        if (
            not selected_month
            and "年" in selected_month_text
            and "月" in selected_month_text
        ):
            try:
                # 2024年03月 → 2024-03 の形式に変換
                parts = selected_month_text.replace("年", "-").replace("月", "")
                year_month = parts.split("-")
                if len(year_month) == 2:
                    selected_month = f"{year_month[0]}-{year_month[1].zfill(2)}"
                    log_message(f"テキストから抽出した月: {selected_month}")
            except Exception as e:
                log_message(f"月の抽出エラー: {e}")
                return

        if not selected_month:
            log_message("選択された月のデータが取得できませんでした")
            return

        # 選択された年月でデータを絞り込み
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_manager.expenses_db)
            cursor = conn.cursor()

            log_message(f"フィルタリング実行: 対象月='{selected_month}'")

            # 指定した年月のデータを取得
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_date, status
                FROM expenses 
                WHERE substr(payment_date, 1, 7) = ?
                ORDER BY payment_date DESC
                """,
                (selected_month,),
            )

            expense_rows = cursor.fetchall()
            log_message(f"フィルタリング結果: {len(expense_rows)}件")

            # 照合済み件数を取得
            cursor.execute(
                """
                SELECT COUNT(*) FROM expenses
                WHERE status = '照合済' AND substr(payment_date, 1, 7) = ?
                """,
                (selected_month,),
            )

            matched_count = cursor.fetchone()[0]
            conn.close()

            # ツリーのクリア
            self.tree.clear()

            # ツリーウィジェットにデータを追加
            for row in expense_rows:
                item = QTreeWidgetItem()

                # 値を設定
                item.setText(0, str(row[0]))  # ID
                item.setText(1, row[1])  # 案件名
                item.setText(2, row[2])  # 支払い先
                item.setText(3, row[3] if row[3] else "")  # 支払い先コード
                item.setText(4, format_amount(row[4]))  # 金額（整形）
                item.setText(5, row[5])  # 支払日
                item.setText(6, row[6])  # 状態

                # 状態に応じた背景色を適用
                status = row[6]
                self.apply_row_colors(item, status, 7)

                self.tree.addTopLevelItem(item)

            # 状態表示の更新
            self.app.status_label.setText(
                f"{selected_month_text}の費用データ: {len(expense_rows)}件、照合済み: {matched_count}件"
            )

            log_message(
                f"月フィルタ完了: {selected_month_text} - {len(expense_rows)}件表示"
            )

        except Exception as e:
            log_message(f"支払い月フィルタリング中にエラーが発生: {e}")
            import traceback

            log_message(f"エラー詳細: {traceback.format_exc()}")
            self.app.status_label.setText(
                f"エラー: データのフィルタリングに失敗しました"
            )

    def reset_search(self):
        """検索とフィルタをリセットしてすべてのデータを表示（改善版）"""
        # 検索フィールドをクリア
        self.search_entry.clear()

        # 支払い月フィルタをリセット
        if hasattr(self, "payment_month_filter"):
            self.payment_month_filter.blockSignals(True)
            self.payment_month_filter.setCurrentText("すべて表示")
            self.payment_month_filter.blockSignals(False)

        # 状態フィルタをリセット
        if hasattr(self, "status_filter"):
            self.status_filter.blockSignals(True)
            self.status_filter.setCurrentText("すべて")
            self.status_filter.blockSignals(False)

        # データを再読み込み
        self.refresh_data()

        log_message("検索とフィルタをリセットしました")

    def refresh_data(self):
        """費用データを更新（改善版）"""
        # ツリーのクリア
        self.tree.clear()

        try:
            # データベースからデータを読み込み
            expense_rows, matched_count = self.db_manager.get_expense_data()

            # ツリーウィジェットにデータを追加
            for row in expense_rows:
                item = QTreeWidgetItem()

                # 値を設定
                item.setText(0, str(row[0]))  # ID
                item.setText(1, row[1])  # 案件名
                item.setText(2, row[2])  # 支払い先
                item.setText(3, row[3] if row[3] else "")  # 支払い先コード
                item.setText(4, format_amount(row[4]))  # 金額（整形）
                item.setText(5, row[5])  # 支払日
                item.setText(6, row[6])  # 状態

                # 状態に応じた背景色を適用
                status = row[6]
                self.apply_row_colors(item, status, 7)

                self.tree.addTopLevelItem(item)

            # 状態表示の更新
            total_count = len(expense_rows)
            unprocessed_count = sum(1 for row in expense_rows if row[6] == "未処理")
            processing_count = sum(1 for row in expense_rows if row[6] == "処理中")
            completed_count = sum(1 for row in expense_rows if row[6] == "完了")

            self.app.status_label.setText(
                f"費用データ: 全{total_count}件 "
                f"(未処理:{unprocessed_count}件, 処理中:{processing_count}件, "
                f"照合済み:{matched_count}件, 完了:{completed_count}件)"
            )

            # 最終更新時刻の更新
            from datetime import datetime

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.app.last_update_label.setText(f"最終更新: {current_time}")

            # 保存されているソート状態を適用
            if self.sort_info["column"]:
                self.sort_tree_widget(
                    self.sort_info["column"], self.sort_info["reverse"]
                )

                # ソート状態を視覚的に表示
                for i in range(self.tree.columnCount()):
                    header_text = self.tree.headerItem().text(i).split(" ")[0]
                    if header_text == self.sort_info["column"]:
                        direction = " 🔽" if self.sort_info["reverse"] else " 🔼"
                        self.tree.headerItem().setText(
                            i, self.sort_info["column"] + direction
                        )
                        break

            # 支払い月フィルタを更新（データ更新後）← この位置に移動
            self.update_payment_month_filter()

            # 支払い先のオートコンプリーターを更新
            payee_widget = self.edit_entries.get("payee")
            if isinstance(payee_widget, PayeeLineEdit):
                payee_widget.setup_completer()

            log_message("費用データの更新が完了しました")

        except Exception as e:
            log_message(f"費用データ読み込み中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            self.app.status_label.setText(f"エラー: 費用データ読み込みに失敗しました")

    def on_tree_select_for_edit(self):
        """ツリーウィジェットの行選択時に編集フォームを表示"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            self.edit_frame.hide()
            return

        # 選択行のデータを取得
        selected_item = selected_items[0]
        expense_id = selected_item.text(0)

        try:
            # データベースから詳細情報を取得
            row = self.db_manager.get_expense_by_id(expense_id)

            if not row:
                return

            # 編集フォームに値を設定
            field_names = [
                "id",
                "project_name",
                "payee",
                "payee_code",
                "amount",
                "payment_date",
                "status",
            ]

            for i, field in enumerate(field_names):
                if field == "id":
                    # IDフィールド
                    self.edit_entries[field].setText(str(row[i]))
                elif field == "status":
                    # 状態コンボボックス
                    index = self.edit_entries[field].findText(row[i])
                    if index >= 0:
                        self.edit_entries[field].setCurrentIndex(index)
                elif field == "payment_date":
                    # 日付フィールド
                    try:
                        parts = row[i].split("-")
                        if len(parts) >= 3:
                            qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                            self.edit_entries[field].setDate(qdate)
                    except (ValueError, IndexError):
                        self.edit_entries[field].setDate(QDate.currentDate())
                else:
                    # 通常のテキストフィールド
                    self.edit_entries[field].setText(str(row[i]))

            # 編集フォームを表示
            self.edit_frame.show()

        except Exception as e:
            log_message(f"費用データ編集フォーム表示中にエラーが発生: {e}")

    def save_direct_edit(self):
        """費用テーブルの直接編集を保存（新規作成対応・コード0埋め対応）"""
        try:
            # utils.pyから関数をインポート
            from utils import format_payee_code

            # 入力値を取得
            expense_id = self.edit_entries["id"].text()
            project_name = self.edit_entries["project_name"].text()
            payee = self.edit_entries["payee"].text()
            payee_code = self.edit_entries["payee_code"].text()
            # 【追加開始】
            from utils import format_payee_code

            if payee_code:
                payee_code = format_payee_code(payee_code)
                self.edit_entries["payee_code"].setText(payee_code)
            # 【追加終了】
            amount_str = self.edit_entries["amount"].text()

            # 【追加】支払い先コードの0埋め処理
            if payee_code:
                payee_code = format_payee_code(payee_code)
                # 画面上のフィールドも更新
                self.edit_entries["payee_code"].setText(payee_code)

            # 日付はQDateEditから取得
            date = self.edit_entries["payment_date"].date()
            payment_date = f"{date.year()}-{date.month():02d}-{date.day():02d}"

            # コンボボックスから状態を取得
            status = self.edit_entries["status"].currentText()

            # 入力チェック
            if not project_name or not payee or not amount_str or not payment_date:
                QMessageBox.critical(self, "エラー", "必須項目を入力してください")
                return

            # 金額の変換
            try:
                amount_str = amount_str.replace(",", "").replace("円", "").strip()
                amount = float(amount_str)
            except ValueError:
                QMessageBox.critical(self, "エラー", "金額は数値で入力してください")
                return

            # データの設定
            is_new = expense_id == "新規"
            data = {
                "project_name": project_name,
                "payee": payee,
                "payee_code": payee_code,
                "amount": amount,
                "payment_date": payment_date,
                "status": status,
            }

            if not is_new:
                data["id"] = expense_id

            # データベースに保存
            expense_id = self.db_manager.save_expense(data, is_new)

            # 更新完了メッセージ
            if is_new:
                message = f"新しい費用データを作成しました（ID: {expense_id}）"
            else:
                message = f"費用データ ID: {expense_id} を更新しました"

            log_message(message)
            self.app.status_label.setText(message)

            # テーブルを更新
            self.refresh_data()

            # 編集フォームを非表示
            self.edit_frame.hide()

        except Exception as e:
            log_message(f"費用データ保存中にエラー: {e}")
            QMessageBox.critical(self, "エラー", f"費用データの保存に失敗しました: {e}")

    def cancel_direct_edit(self):
        """費用テーブルの直接編集をキャンセル"""
        self.edit_frame.hide()

    def create_record(self):
        """新しい費用レコードを作成するためのダイアログを表示"""
        try:
            # 選択解除
            self.tree.clearSelection()

            # 編集フォームの表示
            self.edit_frame.show()

            # フォームのクリア
            for field, widget in self.edit_entries.items():
                if field == "id":
                    widget.setText("新規")
                elif field == "status":
                    index = widget.findText("未処理")
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif field == "payment_date":
                    widget.setDate(QDate.currentDate())
                else:
                    widget.setText("")

        except Exception as e:
            log_message(f"新規費用レコード作成フォーム表示中にエラー: {e}")
            QMessageBox.critical(self, "エラー", f"フォーム表示に失敗しました: {e}")

    def delete_record(self):
        """選択された費用レコードを削除"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "情報", "削除する費用データを選択してください"
            )
            return

        # 選択項目の値を取得
        selected_item = selected_items[0]
        expense_id = selected_item.text(0)
        project_name = selected_item.text(1)

        # 確認ダイアログを表示
        reply = QMessageBox.question(
            self,
            "確認",
            f"費用データ「{project_name}（ID: {expense_id}）」を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # データを削除
            self.db_manager.delete_expense(expense_id)

            message = f"費用データ ID: {expense_id} を削除しました"
            log_message(message)
            self.refresh_data()
            self.app.status_label.setText(message)

        except Exception as e:
            log_message(f"費用データ削除中にエラーが発生: {e}")
            QMessageBox.critical(self, "エラー", f"費用データの削除に失敗しました: {e}")

    def duplicate_record(self):
        """選択された費用レコードを複製"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "情報", "複製する費用データを選択してください"
            )
            return

        # 選択項目の値を取得
        selected_item = selected_items[0]
        expense_id = selected_item.text(0)
        project_name = selected_item.text(1)

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"費用データ「{project_name}（ID: {expense_id}）」を複製しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # データを複製
            new_id = self.db_manager.duplicate_expense(expense_id)

            if new_id:
                message = f"費用データを複製しました（新ID: {new_id}）"
                log_message(
                    f"費用データ ID: {expense_id} を複製しました（新ID: {new_id}）"
                )
                self.refresh_data()
                self.app.status_label.setText(message)

                QMessageBox.information(self, "複製完了", message)
            else:
                QMessageBox.critical(self, "エラー", "選択されたデータが見つかりません")

        except Exception as e:
            log_message(f"費用データ複製中にエラーが発生: {e}")
            QMessageBox.critical(self, "エラー", f"費用データの複製に失敗しました: {e}")

    def match_with_payments(self):
        """費用テーブルと支払いテーブルを照合し、一致するものをマークする"""
        try:
            # 確認ダイアログ
            reply = QMessageBox.question(
                self,
                "確認",
                "費用データと支払いデータの照合を実行しますか？\n\n"
                "この処理により、金額・支払先コード・支払月が一致するデータが自動的に照合済みとしてマークされます。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply != QMessageBox.Yes:
                return

            # 照合処理を実行
            self.app.status_label.setText("照合処理を実行中...")
            matched_count, not_matched_count = (
                self.db_manager.match_expenses_with_payments()
            )

            if matched_count == 0 and not_matched_count == 0:
                QMessageBox.information(self, "情報", "照合対象のデータがありません")
                return

            # データを更新表示
            self.refresh_data()  # 費用データを更新
            self.app.payment_tab.refresh_data()  # 支払いデータも更新

            # 結果メッセージ
            result_msg = f"照合処理完了\n\n✅ 照合成功: {matched_count}件\n❌ 照合失敗: {not_matched_count}件"

            self.app.status_label.setText(
                f"照合完了: {matched_count}件一致、{not_matched_count}件不一致"
            )

            QMessageBox.information(self, "照合完了", result_msg)

            log_message(
                f"費用と支払いの照合: {matched_count}件一致、{not_matched_count}件不一致"
            )

        except Exception as e:
            log_message(f"照合処理中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"照合処理に失敗しました: {e}")

    def export_to_csv(self):
        """費用データをCSVファイルにエクスポート"""
        try:
            # データベースから全データを取得
            expense_rows, _ = self.db_manager.get_expense_data()

            if not expense_rows:
                QMessageBox.information(
                    self, "情報", "エクスポートするデータがありません"
                )
                return

            # 保存先のファイルを選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "費用データの保存先を選択",
                f"費用データ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSVファイル (*.csv)",
            )

            if not file_path:
                return  # キャンセルされた場合

            # CSVファイルに書き込み
            with open(file_path, "w", newline="", encoding="shift_jis") as file:
                writer = csv.writer(file)

                # ヘッダー行を書き込み
                writer.writerow(
                    [
                        "ID",
                        "案件名",
                        "支払い先",
                        "支払い先コード",
                        "金額",
                        "支払日",
                        "状態",
                    ]
                )

                # データ行を書き込み
                for row in expense_rows:
                    writer.writerow(row)

            log_message(f"費用データを{file_path}にエクスポートしました")
            self.app.status_label.setText(
                f"費用データを{os.path.basename(file_path)}にエクスポートしました"
            )

            # エクスポート後に確認メッセージを表示
            QMessageBox.information(
                self,
                "エクスポート完了",
                f"{len(expense_rows)}件のデータを\n{os.path.basename(file_path)}\nにエクスポートしました",
            )

        except Exception as e:
            log_message(f"費用データのエクスポート中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            QMessageBox.critical(
                self, "エラー", f"費用データのエクスポートに失敗しました: {e}"
            )

    def import_from_csv(self):
        """CSVファイルから費用データをインポート（支払いコード0埋め対応）"""
        try:
            from utils import format_payee_code  # 追加

            # インポートするCSVファイルを選択
            file_path, _ = QFileDialog.getOpenFileName(
                self, "インポートするCSVファイルを選択", "", "CSVファイル (*.csv)"
            )

            if not file_path:
                return  # キャンセルされた場合

            # 確認ダイアログを表示 - デフォルトでは「追加」を選択
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Question)
            message_box.setText(
                "データを追加しますか？\n「いいえ」を選択すると、既存のデータを上書きします。"
            )
            message_box.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            message_box.setDefaultButton(QMessageBox.Yes)

            result = message_box.exec_()

            if result == QMessageBox.Cancel:
                return

            # 追加モード (既存データを保持)
            if result == QMessageBox.Yes:
                clear_existing = False
                operation_text = "追加"
            else:
                # 上書きモード (既存データを削除) - 再確認
                warning_box = QMessageBox()
                warning_box.setIcon(QMessageBox.Warning)
                warning_box.setText(
                    "既存のデータがすべて削除されます。本当に上書きしますか？"
                )
                warning_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                warning_box.setDefaultButton(QMessageBox.No)

                if warning_box.exec_() != QMessageBox.Yes:
                    return  # キャンセル

                clear_existing = True
                operation_text = "上書き"

            # CSVファイルを読み込む
            imported_rows = []
            with open(file_path, "r", encoding="shift_jis", errors="replace") as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)  # ヘッダー行をスキップ

                for row in csv_reader:
                    if not row:  # 空行はスキップ
                        continue

                    # 最低限のデータチェック
                    if len(row) < 6:
                        continue

                    try:
                        # ID列は無視し、データベースで自動生成する場合
                        project_name = row[1]
                        payee = row[2]
                        payee_code = row[3]

                        # 【追加】支払い先コードの0埋め処理
                        if payee_code:
                            payee_code = format_payee_code(payee_code)

                        # 金額の変換
                        amount_str = row[4].replace(",", "").replace("円", "").strip()
                        amount = float(amount_str) if amount_str else 0

                        payment_date = row[5]
                        status = row[6] if len(row) > 6 else "未処理"

                        imported_rows.append(
                            (
                                project_name,
                                payee,
                                payee_code,
                                amount,
                                payment_date,
                                status,
                            )
                        )
                    except (ValueError, IndexError) as e:
                        log_message(f"行の解析中にエラー: {e} - {row}")

            if not imported_rows:
                QMessageBox.information(
                    self, "情報", "インポートできるデータがありませんでした"
                )
                return

            # データベースに反映
            conn = sqlite3.connect(self.db_manager.expenses_db)
            cursor = conn.cursor()

            # 既存のデータをクリアする場合
            if clear_existing:
                cursor.execute("DELETE FROM expenses")

            # データを挿入
            for row in imported_rows:
                cursor.execute(
                    """
                    INSERT INTO expenses (project_name, payee, payee_code, amount, payment_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    row,
                )

            conn.commit()
            conn.close()

            log_message(f"{len(imported_rows)}件のデータを{operation_text}しました")
            self.refresh_data()
            self.app.status_label.setText(
                f"{len(imported_rows)}件のデータを{operation_text}しました"
            )

            # インポート後に確認メッセージを表示
            QMessageBox.information(
                self,
                "インポート完了",
                f"{len(imported_rows)}件のデータを{operation_text}しました",
            )

        except Exception as e:
            log_message(f"費用データのインポート中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            QMessageBox.critical(
                self, "エラー", f"費用データのインポートに失敗しました: {e}"
            )

    # ファイル終了確認用のコメント - expense_tab.py完了
