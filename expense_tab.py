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
    QDialog,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, pyqtSlot, QStringListModel
from PyQt5.QtGui import QColor, QFont, QBrush
import csv
import os
from datetime import datetime, timedelta
from utils import format_amount, log_message
from matching_utils import MatchingLogic, get_matching_logic

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

        # 動的フォントサイズを取得
        self.font_size = app.base_font_size
        self.title_font_size = app.title_font_size
        
        # 動的サイズ計算（統一版）
        self.widget_min_width = max(80, int(self.font_size * 8))  # ドロップダウン対応
        self.button_min_width = max(70, int(self.font_size * 7))  # 文字+パディング余裕
        self.search_min_width = max(150, int(self.font_size * 15))  # 検索フィールド
        self.button_min_height = max(20, int(self.font_size * 1.8))  # app.pyと統一
        self.detail_label_width = max(100, int(self.font_size * 10))  # 詳細ラベル

        # ソート情報
        self.sort_info = {"column": None, "reverse": False}

        # 色分け設定（より明確な色を使用）
        self.matched_color = QColor(144, 238, 144)  # ライトグリーン（照合済み）
        self.processing_color = QColor(255, 255, 153)  # 薄い黄色（処理中）
        self.unprocessed_color = QColor(248, 248, 248)  # オフホワイト（未処理）
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
        self.payment_month_filter.setMinimumWidth(self.widget_min_width + 20)
        self.payment_month_filter.currentTextChanged.connect(self.filter_by_month)
        search_layout.addWidget(self.payment_month_filter)

        # 状態フィルタ
        search_layout.addWidget(QLabel("📊 状態:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["すべて", "未処理", "処理中", "照合済", "完了"])
        self.status_filter.setMinimumWidth(self.widget_min_width)
        self.status_filter.currentTextChanged.connect(self.filter_by_status)
        search_layout.addWidget(self.status_filter)

        # 検索フィールド
        search_layout.addWidget(QLabel("🔍 検索:"))
        self.search_entry = QLineEdit()
        self.search_entry.setMinimumWidth(self.search_min_width)
        self.search_entry.setPlaceholderText("案件名、支払い先で検索...")
        self.search_entry.returnPressed.connect(self.search_records)  # Enterキーで検索
        search_layout.addWidget(self.search_entry)

        # 検索ボタン
        search_button = QPushButton("検索")
        search_button.setMinimumSize(self.button_min_width, self.button_min_height)
        search_button.clicked.connect(self.search_records)
        search_layout.addWidget(search_button)

        # リセットボタン
        reset_button = QPushButton("リセット")
        reset_button.setMinimumSize(self.button_min_width, self.button_min_height)
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
        self.target_year_combo.setMinimumWidth(max(50, int(self.font_size * 3.5)))
        master_group_layout.addWidget(self.target_year_combo)

        master_group_layout.addWidget(QLabel("年"))

        self.target_month_combo = QComboBox()
        for month in range(1, 13):
            self.target_month_combo.addItem(f"{month:02d}")
        current_month = datetime.now().month
        self.target_month_combo.setCurrentText(f"{current_month:02d}")
        self.target_month_combo.setMinimumWidth(max(40, int(self.font_size * 3)))
        master_group_layout.addWidget(self.target_month_combo)

        master_group_layout.addWidget(QLabel("月"))

        # マスター生成ボタン
        reflect_new_button = QPushButton("🆕 新規マスター項目を今月反映")
        reflect_new_button.setMinimumHeight(self.button_min_height)
        reflect_new_button.clicked.connect(self.reflect_new_master_to_current_month)
        master_group_layout.addWidget(reflect_new_button)

        generate_next_button = QPushButton("➡️ 来月分生成")
        generate_next_button.setMinimumHeight(self.button_min_height)
        generate_next_button.clicked.connect(self.generate_next_month_expenses)
        master_group_layout.addWidget(generate_next_button)

        generate_button = QPushButton("📋 選択月生成")
        generate_button.setMinimumHeight(self.button_min_height)
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
        create_button.setMinimumSize(self.button_min_width, self.button_min_height)
        create_button.clicked.connect(self.create_record)
        record_group_layout.addWidget(create_button)

        delete_button = QPushButton("🗑️ 選択削除")
        delete_button.setMinimumSize(self.button_min_width, self.button_min_height)
        delete_button.clicked.connect(self.delete_record)
        record_group_layout.addWidget(delete_button)

        duplicate_button = QPushButton("📄 複製")
        duplicate_button.setMinimumSize(self.button_min_width, self.button_min_height)
        duplicate_button.clicked.connect(self.duplicate_record)
        record_group_layout.addWidget(duplicate_button)

        # 照合操作グループ
        match_group = QGroupBox("🔄 照合・データ操作")
        match_group_layout = QHBoxLayout(match_group)
        match_group_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.addWidget(match_group)

        match_button = QPushButton("💰 支払いと照合")
        match_button.setMinimumSize(self.button_min_width, self.button_min_height)
        match_button.clicked.connect(self.match_with_payments)
        match_group_layout.addWidget(match_button)
        
        compare_all_button = QPushButton("📊 全体比較確認")
        compare_all_button.setMinimumHeight(self.button_min_height)
        compare_all_button.clicked.connect(self.show_payment_comparison_all)
        match_group_layout.addWidget(compare_all_button)

        export_button = QPushButton("📤 CSVエクスポート")
        export_button.setMinimumHeight(self.button_min_height)
        export_button.clicked.connect(self.export_to_csv)
        match_group_layout.addWidget(export_button)

        import_button = QPushButton("📥 CSVインポート")
        import_button.setMinimumHeight(self.button_min_height)
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
        table_title.setFont(QFont("", self.title_font_size, QFont.Bold))
        table_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        table_layout.addWidget(table_title)

        # ツリーウィジェットの作成（スタイルシートでフォントサイズ設定されるため重複削除）
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["ID", "案件名", "支払い先", "コード", "金額", "支払日", "状態"]
        )
        # 複数選択を有効化
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
        
        # ソート機能を有効化
        self.tree.setSortingEnabled(True)
        self.tree.header().setSectionsMovable(False)

        # 選択時イベント
        self.tree.itemSelectionChanged.connect(self.on_tree_select_for_edit)
        
        # 右クリックメニュー
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # 下部：レコード編集エリア（高さを拡張）
        edit_frame = QFrame()
        edit_frame.setFrameStyle(QFrame.StyledPanel)
        edit_frame.setMaximumHeight(400)  # 案件情報対応のため高さ拡張
        edit_layout = QVBoxLayout(edit_frame)
        edit_layout.setContentsMargins(8, 8, 8, 8)
        content_splitter.addWidget(edit_frame)

        # 編集エリアタイトル
        edit_title = QLabel("✏️ レコード編集")
        edit_title.setFont(QFont("", self.title_font_size, QFont.Bold))
        edit_title.setStyleSheet("color: #2c3e50; margin-bottom: 8px;")
        edit_layout.addWidget(edit_title)

        # スクロールエリアの作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        edit_layout.addWidget(scroll_area)

        # スクロール可能なウィジェット
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setSpacing(12)
        scroll_area.setWidget(scroll_widget)

        # 編集フィールドの作成
        self.edit_entries = {}

        # 基本情報グループ
        basic_group = QGroupBox("📋 基本情報")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(8)
        scroll_layout.addWidget(basic_group)

        basic_fields = [
            ("ID:", "id", 0, 0, True),
            ("案件名:", "project_name", 0, 2, False),
            ("支払い先:", "payee", 1, 0, False),
            ("支払い先コード:", "payee_code", 1, 2, False),
            ("金額:", "amount", 2, 0, False),
            ("支払日:", "payment_date", 2, 2, False),
            ("状態:", "status", 3, 0, False),
        ]

        for label_text, field_key, row, col, read_only in basic_fields:
            # ラベル
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            basic_layout.addWidget(label, row, col)

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

            widget.setMinimumWidth(self.detail_label_width)
            basic_layout.addWidget(widget, row, col + 1)
            self.edit_entries[field_key] = widget

        # 案件情報グループ
        project_group = QGroupBox("🏢 案件情報")
        project_layout = QGridLayout(project_group)
        project_layout.setSpacing(8)
        scroll_layout.addWidget(project_group)

        project_fields = [
            ("クライアント:", "client_name", 0, 0, False),
            ("担当部門:", "department", 0, 2, False),
            ("案件状況:", "project_status", 1, 0, False),
            ("緊急度:", "urgency_level", 1, 2, False),
            ("開始日:", "project_start_date", 2, 0, False),
            ("完了予定日:", "project_end_date", 2, 2, False),
            ("予算:", "budget", 3, 0, False),
            ("承認者:", "approver", 3, 2, False),
        ]

        for label_text, field_key, row, col, read_only in project_fields:
            # ラベル
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            project_layout.addWidget(label, row, col)

            # 入力ウィジェット
            if field_key == "department":
                widget = QComboBox()
                widget.setEditable(True)
                widget.addItems(["", "営業部", "マーケティング部", "総務部", "企画部", "制作部"])
            elif field_key == "project_status":
                widget = QComboBox()
                widget.addItems(["進行中", "完了", "中止", "保留"])
            elif field_key == "urgency_level":
                widget = QComboBox()
                widget.addItems(["通常", "重要", "緊急"])
            elif field_key in ["project_start_date", "project_end_date"]:
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                widget.setSpecialValueText("未設定")
            elif field_key == "budget":
                widget = QLineEdit()
                widget.setPlaceholderText("0")
            else:
                widget = QLineEdit()

            widget.setMinimumWidth(self.detail_label_width)
            project_layout.addWidget(widget, row, col + 1)
            self.edit_entries[field_key] = widget

        # 支払い先と支払い先コードの連動を設定
        payee_widget = self.edit_entries.get("payee")
        payee_code_widget = self.edit_entries.get("payee_code")
        if isinstance(payee_widget, PayeeLineEdit) and payee_code_widget:
            payee_widget.code_field = payee_code_widget

        # 編集ボタンエリア
        button_group = QGroupBox("💾 操作")
        button_layout = QHBoxLayout(button_group)
        button_layout.setSpacing(8)
        scroll_layout.addWidget(button_group)

        # 請求書催促管理ボタン
        view_payments_button = QPushButton("📋 請求書確認")
        view_payments_button.setMinimumSize(self.button_min_width, self.button_min_height)
        view_payments_button.clicked.connect(self.show_related_payments)
        button_layout.addWidget(view_payments_button)
        
        # 同じ月・同じ支払い先の比較確認ボタン
        compare_button = QPushButton("🔍 同月同支払い先比較")
        # 長いテキストのボタンは特別に幅を広げる
        compare_button.setMinimumSize(max(120, int(self.font_size * 12)), self.button_min_height)
        compare_button.clicked.connect(self.show_payment_comparison)
        button_layout.addWidget(compare_button)
        
        button_layout.addStretch()

        cancel_button = QPushButton("❌ キャンセル")
        cancel_button.setMinimumSize(self.button_min_width, self.button_min_height)
        cancel_button.clicked.connect(self.cancel_direct_edit)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("💾 保存")
        save_button.setMinimumSize(self.button_min_width, self.button_min_height)
        save_button.clicked.connect(self.save_direct_edit)
        button_layout.addWidget(save_button)

        # 編集フィールドにEnterキーイベントを追加
        for field_key, widget in self.edit_entries.items():
            if hasattr(widget, 'returnPressed'):
                widget.returnPressed.connect(self.save_direct_edit)

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
        
        # 明示的にテキスト色を黒に設定
        text_brush = QBrush(QColor(0, 0, 0))  # 黒色

        for i in range(column_count):
            item.setBackground(i, brush)
            item.setForeground(i, text_brush)  # テキスト色を明示的に設定
            # さらに確実にするため、データも設定
            item.setData(i, Qt.BackgroundRole, background_color)
            item.setData(i, Qt.ForegroundRole, QColor(0, 0, 0))

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
            # すべて表示する場合は、他のフィルタも適用されるよう改善
            self.apply_all_filters()
            return

        # 現在表示されている項目をフィルタリング
        root = self.tree.invisibleRootItem()
        visible_count = 0
        for i in range(root.childCount()):
            item = root.child(i)
            status = item.text(6)  # 状態列
            should_show = (status == selected_status)
            item.setHidden(not should_show)
            if should_show:
                visible_count += 1

        # 表示件数を更新
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

            # フィルター状態を保持してデータを更新
            self.refresh_data_with_filters()

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

            # フィルター状態を保持してデータを更新
            self.refresh_data_with_filters()

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

            # 支払日から年月を抽出 (YYYY-MM形式、複数フォーマット対応)
            cursor.execute(
                """
                SELECT DISTINCT 
                    CASE 
                        WHEN payment_date LIKE '%/%' THEN substr(replace(payment_date, '/', '-'), 1, 7)
                        ELSE substr(payment_date, 1, 7)
                    END as month
                FROM expenses
                WHERE payment_date IS NOT NULL 
                AND payment_date != '' 
                AND length(payment_date) >= 7
                AND (
                    (payment_date LIKE '____-__-%' OR payment_date LIKE '____/__/__')
                )
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
            self.apply_all_filters()
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

        # 月フィルタを適用
        self.apply_month_filter(selected_month, selected_month_text)

    def apply_month_filter(self, selected_month, selected_month_text):
        """指定された月でフィルタリングを実行"""
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_manager.expenses_db)
            cursor = conn.cursor()

            log_message(f"フィルタリング実行: 対象月='{selected_month}'")

            # 指定した年月のデータを取得（複数の日付フォーマットに対応）
            cursor.execute(
                """
                SELECT id, project_name, payee, payee_code, amount, payment_date, status
                FROM expenses 
                WHERE (
                    substr(payment_date, 1, 7) = ? OR
                    substr(replace(payment_date, '/', '-'), 1, 7) = ? OR
                    (payment_date LIKE ? || '/%') OR
                    (payment_date LIKE ? || '-%')
                )
                ORDER BY payment_date DESC
                """,
                (selected_month, selected_month, selected_month, selected_month),
            )

            expense_rows = cursor.fetchall()
            log_message(f"フィルタリング結果: {len(expense_rows)}件")

            # 照合済み件数を取得（複数の日付フォーマットに対応）
            cursor.execute(
                """
                SELECT COUNT(*) FROM expenses
                WHERE status = '照合済' AND (
                    substr(payment_date, 1, 7) = ? OR
                    substr(replace(payment_date, '/', '-'), 1, 7) = ? OR
                    (payment_date LIKE ? || '/%') OR
                    (payment_date LIKE ? || '-%')
                )
                """,
                (selected_month, selected_month, selected_month, selected_month),
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

            # 状態フィルタを追加適用
            status_filter = self.status_filter.currentText()
            if status_filter and status_filter != "すべて":
                root = self.tree.invisibleRootItem()
                visible_count = 0
                for i in range(root.childCount()):
                    item = root.child(i)
                    status = item.text(6)  # 状態列
                    should_show = (status == status_filter)
                    item.setHidden(not should_show)
                    if should_show:
                        visible_count += 1
                
                # 状態表示の更新
                self.app.status_label.setText(
                    f"{selected_month_text}の{status_filter}費用データ: {visible_count}件"
                )
            else:
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

    def apply_all_filters(self):
        """すべてのフィルタを適用（検索、月、状態）"""
        search_term = self.search_entry.text().strip()
        selected_month_text = self.payment_month_filter.currentText()
        selected_status = self.status_filter.currentText()

        # まずデータをリフレッシュ
        self.refresh_data()

        # 検索フィルタを適用
        if search_term:
            self.search_records()
            return

        # 月フィルタを適用
        if selected_month_text and selected_month_text != "すべて表示":
            current_index = self.payment_month_filter.currentIndex()
            selected_month = self.payment_month_filter.itemData(current_index)
            
            if not selected_month and "年" in selected_month_text and "月" in selected_month_text:
                try:
                    parts = selected_month_text.replace("年", "-").replace("月", "")
                    year_month = parts.split("-")
                    if len(year_month) == 2:
                        selected_month = f"{year_month[0]}-{year_month[1].zfill(2)}"
                except:
                    pass
            
            if selected_month:
                self.apply_month_filter(selected_month, selected_month_text)
                return

        # 状態フィルタを適用
        if selected_status and selected_status != "すべて":
            self.filter_by_status()

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

    def refresh_data_with_filters(self):
        """フィルター状態を保持してデータを更新"""
        try:
            # 現在のフィルター状態を保存
            current_search = self.search_entry.text()
            current_status = self.status_filter.currentText()
            current_month_index = self.payment_month_filter.currentIndex()
            current_month_text = self.payment_month_filter.currentText()
            
            log_message(f"フィルター状態保存: 検索='{current_search}', 状態='{current_status}', 月='{current_month_text}'")
            
            # データを更新
            self.refresh_data()
            
            # フィルター状態を復元
            if current_search:
                self.search_entry.setText(current_search)
            
            if current_status != "すべて":
                self.status_filter.setCurrentText(current_status)
            
            # 月フィルターの復元（インデックスベース）
            if current_month_text != "すべて表示" and current_month_index > 0:
                # まず同じテキストがあるかチェック
                month_index = self.payment_month_filter.findText(current_month_text)
                if month_index >= 0:
                    self.payment_month_filter.setCurrentIndex(month_index)
                    log_message(f"月フィルター復元: {current_month_text}")
            
            # フィルターを再適用
            if current_search:
                self.search_records()
            elif current_month_text != "すべて表示" and current_month_index > 0:
                self.filter_by_month()
            elif current_status != "すべて":
                self.filter_by_status()
                
            log_message("フィルター状態の復元が完了しました")
            
        except Exception as e:
            log_message(f"フィルター状態復元中にエラー: {e}")
            # エラーが発生した場合は通常のrefresh_dataにフォールバック
            self.refresh_data()

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

            # 編集フォームに値を設定（案件情報含む）
            field_mapping = {
                0: "id",
                1: "project_name", 
                2: "payee",
                3: "payee_code",
                4: "amount",
                5: "payment_date",
                6: "status",
                7: "client_name",
                8: "department", 
                9: "project_status",
                10: "project_start_date",
                11: "project_end_date",
                12: "budget",
                13: "approver",
                14: "urgency_level"
            }

            for i, field in field_mapping.items():
                if i >= len(row) or field not in self.edit_entries:
                    continue
                    
                widget = self.edit_entries[field]
                value = row[i] if row[i] is not None else ""
                
                if field == "id":
                    # IDフィールド
                    widget.setText(str(value))
                elif field in ["status", "project_status", "urgency_level"]:
                    # コンボボックス
                    if hasattr(widget, 'findText'):
                        index = widget.findText(str(value))
                        if index >= 0:
                            widget.setCurrentIndex(index)
                elif field == "department":
                    # 編集可能コンボボックス
                    if hasattr(widget, 'setCurrentText'):
                        widget.setCurrentText(str(value))
                elif field in ["payment_date", "project_start_date", "project_end_date"]:
                    # 日付フィールド
                    try:
                        if str(value) and str(value) != "":
                            parts = str(value).split("-")
                            if len(parts) >= 3:
                                qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                                widget.setDate(qdate)
                            else:
                                widget.setDate(QDate.currentDate())
                        else:
                            widget.setDate(QDate.currentDate())
                    except (ValueError, IndexError):
                        widget.setDate(QDate.currentDate())
                else:
                    # 通常のテキストフィールド
                    widget.setText(str(value))

            # 編集フォームを表示
            self.edit_frame.show()

        except Exception as e:
            log_message(f"費用データ編集フォーム表示中にエラーが発生: {e}")

    def save_direct_edit(self):
        """費用テーブルの直接編集を保存（新規作成対応・コード0埋め対応）"""
        try:
            # utils.pyから関数をインポート
            from utils import format_payee_code

            # 基本情報の入力値を取得
            expense_id = self.edit_entries["id"].text()
            project_name = self.edit_entries["project_name"].text()
            payee = self.edit_entries["payee"].text()
            payee_code = self.edit_entries["payee_code"].text()
            amount_str = self.edit_entries["amount"].text()
            status = self.edit_entries["status"].currentText()

            # 支払い先コードの0埋め処理
            if payee_code:
                payee_code = format_payee_code(payee_code)
                self.edit_entries["payee_code"].setText(payee_code)

            # 日付の取得
            date = self.edit_entries["payment_date"].date()
            payment_date = f"{date.year()}-{date.month():02d}-{date.day():02d}"

            # 案件情報の入力値を取得
            client_name = self.edit_entries["client_name"].text()
            department = self.edit_entries["department"].currentText() if hasattr(self.edit_entries["department"], 'currentText') else ""
            project_status = self.edit_entries["project_status"].currentText()
            urgency_level = self.edit_entries["urgency_level"].currentText()
            
            # 案件日付の取得
            project_start_date = ""
            project_end_date = ""
            if "project_start_date" in self.edit_entries:
                start_date = self.edit_entries["project_start_date"].date()
                project_start_date = f"{start_date.year()}-{start_date.month():02d}-{start_date.day():02d}"
            
            if "project_end_date" in self.edit_entries:
                end_date = self.edit_entries["project_end_date"].date()
                project_end_date = f"{end_date.year()}-{end_date.month():02d}-{end_date.day():02d}"

            budget_str = self.edit_entries["budget"].text()
            approver = self.edit_entries["approver"].text()

            # 入力チェック
            if not project_name or not payee or not amount_str or not payment_date:
                QMessageBox.critical(self, "エラー", "必須項目（案件名、支払先、金額、支払日）を入力してください")
                return

            # 金額と予算の変換
            try:
                amount_str = amount_str.replace(",", "").replace("円", "").strip()
                amount = float(amount_str)
            except ValueError:
                QMessageBox.critical(self, "エラー", "金額は数値で入力してください")
                return

            try:
                budget = float(budget_str.replace(",", "").replace("円", "").strip()) if budget_str else 0
            except ValueError:
                budget = 0

            # データの設定（案件情報含む）
            is_new = expense_id == "新規"
            data = {
                "project_name": project_name,
                "payee": payee,
                "payee_code": payee_code,
                "amount": amount,
                "payment_date": payment_date,
                "status": status,
                "client_name": client_name,
                "department": department,
                "project_status": project_status,
                "project_start_date": project_start_date,
                "project_end_date": project_end_date,
                "budget": budget,
                "approver": approver,
                "urgency_level": urgency_level,
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

            # フィルター状態を保持してテーブルを更新
            self.refresh_data_with_filters()

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
                elif isinstance(widget, QComboBox):
                    # ComboBoxの場合は空のテキストを設定または最初の項目を選択
                    if widget.isEditable():
                        widget.setCurrentText("")
                    else:
                        widget.setCurrentIndex(0)
                elif isinstance(widget, QDateEdit):
                    # DateEditの場合は現在の日付を設定
                    widget.setDate(QDate.currentDate())
                else:
                    # LineEditなどテキスト入力ウィジェットの場合
                    widget.setText("")

        except Exception as e:
            log_message(f"新規費用レコード作成フォーム表示中にエラー: {e}")
            QMessageBox.critical(self, "エラー", f"フォーム表示に失敗しました: {e}")

    def delete_record(self):
        """選択された費用レコードを削除（複数選択対応）"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "情報", "削除する費用データを選択してください"
            )
            return

        # 複数選択の場合の確認ダイアログ
        item_count = len(selected_items)
        if item_count == 1:
            # 単一選択の場合
            selected_item = selected_items[0]
            expense_id = selected_item.text(0)
            project_name = selected_item.text(1)

            reply = QMessageBox.question(
                self,
                "確認",
                f"費用データ「{project_name}（ID: {expense_id}）」を削除しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
        else:
            # 複数選択の場合
            project_names = [item.text(1) for item in selected_items[:3]]  # 最初の3件を表示
            preview = "、".join(project_names)
            if item_count > 3:
                preview += f"...他{item_count - 3}件"

            reply = QMessageBox.question(
                self,
                "確認",
                f"{item_count}件の費用データを削除しますか？\n\n対象項目：{preview}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

        if reply != QMessageBox.Yes:
            return

        try:
            # 削除対象のIDリストを作成
            expense_ids = [item.text(0) for item in selected_items]

            # データを削除（バッチ処理）
            deleted_count = 0
            for expense_id in expense_ids:
                self.db_manager.delete_expense(expense_id)
                deleted_count += 1

            message = f"{deleted_count}件の費用データを削除しました"
            log_message(message)
            self.refresh_data_with_filters()
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
                self.refresh_data_with_filters()
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
            # 現在のフィルター状態を保存
            current_month = self.payment_month_filter.currentText()
            current_status = self.status_filter.currentText()
            
            # 照合処理を実行
            self.app.status_label.setText("照合処理を実行中...")
            matched_count, not_matched_count = (
                self.db_manager.match_expenses_with_payments()
            )

            # フィルター状態を保持してデータを更新
            self.refresh_data_with_filters()  # 費用データを更新
            self.app.payment_tab.refresh_data()  # 支払いデータも更新
            
            # フィルター状態を復元
            if current_month:
                self.payment_month_filter.setCurrentText(current_month)
            if current_status:
                self.status_filter.setCurrentText(current_status)
            
            # フィルターを再適用
            self.apply_all_filters()

            self.app.status_label.setText(
                f"照合完了: {matched_count}件一致、{not_matched_count}件不一致"
            )

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
            self.refresh_data_with_filters()
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

    def show_context_menu(self, position):
        """右クリックメニューを表示"""
        item = self.tree.itemAt(position)
        if not item:
            return
            
        menu = QWidget()
        menu.setWindowFlags(Qt.Popup)
        menu.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        
        layout = QVBoxLayout(menu)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 関連支払いデータを表示
        view_payments_btn = QPushButton("👁️ 同じ支払い先の支払いデータを表示")
        view_payments_btn.clicked.connect(lambda: self.show_related_payments_for_item(item))
        layout.addWidget(view_payments_btn)
        
        # 同月同支払い先比較
        compare_btn = QPushButton("🔍 同月同支払い先比較")
        compare_btn.clicked.connect(lambda: self.show_payment_comparison_dialog(item))
        layout.addWidget(compare_btn)
        
        # 支払いタブに移動してフィルタ
        goto_payments_btn = QPushButton("🔗 支払いタブで同じ支払い先を表示")
        goto_payments_btn.clicked.connect(lambda: self.goto_payments_tab_filtered(item))
        layout.addWidget(goto_payments_btn)
        
        # メニューを表示
        global_position = self.tree.mapToGlobal(position)
        menu.move(global_position)
        menu.show()
        
        # メニューの外をクリックしたら閉じる
        def close_menu():
            menu.close()
        
        menu.mousePressEvent = lambda event: close_menu() if not menu.rect().contains(event.pos()) else None

    def show_related_payments(self):
        """編集中の費用データの関連支払いデータを表示"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "情報", "費用データを選択してください")
            return
        
        self.show_related_payments_for_item(current_item)

    def show_related_payments_for_item(self, item):
        """指定された費用データの関連支払いデータを表示"""
        try:
            payee = item.text(2)  # 支払い先
            payee_code = item.text(3)  # 支払い先コード
            payment_date = item.text(5)  # 支払日
            amount = item.text(4)  # 金額
            
            if not payee and not payee_code:
                QMessageBox.information(self, "情報", "支払い先情報が不足しています")
                return
            
            # 同じ月の支払いデータを検索
            payment_month = payment_date[:7] if len(payment_date) >= 7 else ""
            
            # データベースから関連支払いデータを取得
            conn = sqlite3.connect('billing.db')
            cursor = conn.cursor()
            
            query = """
                SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                WHERE (payee = ? OR payee_code = ?)
            """
            params = [payee, payee_code]
            
            if payment_month:
                query += " AND substr(payment_date, 1, 7) = ?"
                params.append(payment_month)
                
            query += " ORDER BY payment_date DESC, amount DESC"
            
            cursor.execute(query, params)
            payment_rows = cursor.fetchall()
            conn.close()
            
            if not payment_rows:
                QMessageBox.information(self, "情報", 
                    f"支払い先「{payee}」({payee_code})の関連支払いデータが見つかりません")
                return
            
            # 関連支払いデータ表示ダイアログ
            self.show_related_payments_dialog(payee, payee_code, payment_month, amount, payment_rows)
            
        except Exception as e:
            log_message(f"関連支払いデータ表示エラー: {e}")
            QMessageBox.critical(self, "エラー", f"関連支払いデータの表示に失敗しました: {e}")

    def show_related_payments_dialog(self, payee, payee_code, payment_month, selected_amount, payment_rows):
        """請求書催促管理用の比較ダイアログ"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📋 請求書確認・催促管理 - {payee}")
        dialog.setModal(True)
        dialog.resize(1000, 600)
        
        layout = QVBoxLayout(dialog)
        
        # ヘッダー情報
        header = QFrame()
        header.setStyleSheet("background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin-bottom: 10px;")
        header_layout = QVBoxLayout(header)
        
        title_label = QLabel(f"📋 請求書確認・催促管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; margin-bottom: 5px;")
        header_layout.addWidget(title_label)
        
        info_label = QLabel(f"💼 支払い先: {payee} ({payee_code})　|　📅 対象月: {payment_month}　|　💰 費用金額: {selected_amount}")
        info_label.setStyleSheet("font-size: 12px; color: #424242;")
        header_layout.addWidget(info_label)
        
        layout.addWidget(header)
        
        # メインエリア - 左右分割
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左側：支払いデータ一覧
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        
        left_title = QLabel("📄 同じ支払い先の支払いデータ")
        left_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        left_layout.addWidget(left_title)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["金額", "支払日", "状態", "件名", "案件名"])
        tree.setAlternatingRowColors(True)
        left_layout.addWidget(tree)
        
        # 右側：催促管理エリア
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        right_title = QLabel("📞 催促管理")
        right_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        right_layout.addWidget(right_title)
        
        # 催促状況の判定と表示
        催促_info = self.analyze_payment_status(selected_amount, payment_rows)
        status_label = QLabel(催促_info["message"])
        status_label.setStyleSheet(f"padding: 10px; background-color: {催促_info['color']}; border-radius: 4px; margin-bottom: 10px;")
        status_label.setWordWrap(True)
        right_layout.addWidget(status_label)
        
        # メモエリア
        memo_label = QLabel("📝 催促メモ:")
        memo_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(memo_label)
        
        memo_text = QTextEdit()
        memo_text.setMaximumHeight(150)
        memo_text.setPlaceholderText("催促の進捗や連絡内容をメモしてください...")
        right_layout.addWidget(memo_text)
        
        # 催促アクションボタン
        action_layout = QHBoxLayout()
        
        if 催促_info["needs_followup"]:
            followup_button = QPushButton("📞 催促要")
            followup_button.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
        else:
            followup_button = QPushButton("✅ 請求済み")
            followup_button.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px;")
        
        action_layout.addWidget(followup_button)
        right_layout.addLayout(action_layout)
        
        right_layout.addStretch()
        
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setSizes([600, 400])
        
        # データを追加（金額順にソート）
        sorted_rows = sorted(payment_rows, key=lambda x: float(str(x[4]).replace("¥", "").replace(",", "")) if x[4] else 0, reverse=True)
        
        selected_amount_float = 0
        try:
            selected_amount_float = float(selected_amount.replace("¥", "").replace(",", ""))
        except:
            pass
        
        for row in sorted_rows:
            item = QTreeWidgetItem()
            # 金額、支払日、状態、件名、案件名の順
            item.setText(0, format_amount(row[4]) if row[4] else "")  # 金額
            item.setText(1, str(row[5]) if row[5] else "")  # 支払日
            item.setText(2, str(row[6]) if row[6] else "")  # 状態
            item.setText(3, str(row[0]) if row[0] else "")  # 件名
            item.setText(4, str(row[1]) if row[1] else "")  # 案件名
            
            # 金額による色分け
            try:
                row_amount = float(str(row[4]).replace("¥", "").replace(",", ""))
                diff = abs(row_amount - selected_amount_float)
                
                if diff == 0:
                    # 完全一致 - 緑
                    item.setBackground(0, QColor("#c8e6c9"))
                    item.setBackground(1, QColor("#c8e6c9"))
                elif diff <= 1000:
                    # 1000円以内の差 - 黄
                    item.setBackground(0, QColor("#fff9c4"))
                    item.setBackground(1, QColor("#fff9c4"))
                elif diff <= 5000:
                    # 5000円以内の差 - オレンジ
                    item.setBackground(0, QColor("#ffe0b2"))
                    item.setBackground(1, QColor("#ffe0b2"))
                
                # 金額を太字で強調
                font = QFont()
                font.setBold(True)
                item.setFont(0, font)
                
            except:
                pass
                
            tree.addTopLevelItem(item)
        
        # 列幅調整
        tree.resizeColumnToContents(0)  # 金額
        tree.resizeColumnToContents(1)  # 支払日
        tree.resizeColumnToContents(2)  # 状態
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        goto_button = QPushButton("🔗 支払いタブで詳細確認")
        goto_button.clicked.connect(lambda: self.goto_payments_tab_with_filter(payee, payee_code, payment_month))
        button_layout.addWidget(goto_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def analyze_payment_status(self, selected_amount, payment_rows):
        """請求状況を分析して催促の必要性を判定"""
        try:
            selected_amount_float = float(selected_amount.replace("¥", "").replace(",", ""))
        except:
            return {
                "message": "❓ 金額の解析ができませんでした",
                "color": "#f5f5f5",
                "needs_followup": True
            }
        
        if not payment_rows:
            return {
                "message": "⚠️ 請求書未着\n同じ支払い先からの請求が見つかりません。\n催促が必要です。",
                "color": "#ffebee",
                "needs_followup": True
            }
        
        # 完全一致チェック
        exact_matches = []
        close_matches = []  # 1000円以内
        
        for row in payment_rows:
            try:
                row_amount = float(str(row[4]).replace("¥", "").replace(",", ""))
                diff = abs(row_amount - selected_amount_float)
                
                if diff == 0:
                    exact_matches.append(row)
                elif diff <= 1000:
                    close_matches.append(row)
            except:
                continue
        
        if exact_matches:
            return {
                "message": f"✅ 請求書到着済み\n同じ金額（{selected_amount}）の請求が{len(exact_matches)}件見つかりました。\n催促は不要です。",
                "color": "#e8f5e8",
                "needs_followup": False
            }
        elif close_matches:
            amounts = [format_amount(row[4]) for row in close_matches]
            return {
                "message": f"⚡ 金額変更の可能性\n近い金額の請求が見つかりました：{', '.join(amounts)}\n金額変更について確認が必要です。",
                "color": "#fff8e1",
                "needs_followup": True
            }
        else:
            return {
                "message": f"📞 催促要\n同じ支払い先から{len(payment_rows)}件の請求がありますが、\n該当金額（{selected_amount}）の請求が見つかりません。\n催促が必要です。",
                "color": "#ffebee",
                "needs_followup": True
            }

    def goto_payments_tab_filtered(self, item):
        """支払いタブに移動して同じ支払い先でフィルタ"""
        payee = item.text(2)  # 支払い先
        payee_code = item.text(3)  # 支払い先コード
        payment_date = item.text(5)  # 支払日
        payment_month = payment_date[:7] if len(payment_date) >= 7 else ""
        
        self.goto_payments_tab_with_filter(payee, payee_code, payment_month)

    def goto_payments_tab_with_filter(self, payee, payee_code, payment_month):
        """支払いタブに移動してフィルタを適用"""
        try:
            # 支払いタブに切り替え
            self.app.tab_control.setCurrentWidget(self.app.payment_tab)
            
            # 検索条件を設定
            if payee:
                self.app.payment_tab.search_entry.setText(payee)
            elif payee_code:
                self.app.payment_tab.search_entry.setText(payee_code)
            
            # 検索実行
            self.app.payment_tab.search_records()
            
            # 確認メッセージ
            self.app.status_label.setText(f"支払いタブに移動しました: {payee} ({payee_code})")
            
        except Exception as e:
            log_message(f"支払いタブへの移動エラー: {e}")
            QMessageBox.critical(self, "エラー", f"支払いタブへの移動に失敗しました: {e}")

    def show_payment_comparison(self):
        """同月同支払い先比較モーダルを表示"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "情報", "費用データを選択してください")
            return
        
        self.show_payment_comparison_dialog(current_item)

    def show_payment_comparison_dialog(self, item):
        """同月同支払い先比較ダイアログ（2つのリスト表示版）"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QTreeWidget, QTreeWidgetItem, 
                                   QFrame, QSplitter, QGroupBox)
        
        payee = item.text(2)  # 支払い先
        payee_code = item.text(3)  # 支払い先コード
        payment_date = item.text(5)  # 支払日
        amount = item.text(4)  # 金額
        project_name = item.text(1)  # 案件名
        
        if not payee and not payee_code:
            QMessageBox.information(self, "情報", "支払い先情報が不足しています")
            return
        
        # 同じ月の検索条件（日付フォーマットを統一）
        payment_month = payment_date[:7] if len(payment_date) >= 7 else ""
        # 支払いデータ用の月フォーマット（2025/04形式）
        payment_month_slash = payment_month.replace("-", "/") if payment_month else ""
        
        try:
            # 支払いデータを取得（billing.db）
            payment_conn = sqlite3.connect('billing.db')
            payment_cursor = payment_conn.cursor()
            
            if payee_code and payee_code.strip():
                # 支払いテーブル検索（支払い先コード優先）- 日付フォーマット2025/04/30
                payment_cursor.execute("""
                    SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                    FROM payments
                    WHERE payee_code = ? AND substr(payment_date, 1, 7) = ?
                    ORDER BY amount DESC, payment_date DESC
                """, (payee_code.strip(), payment_month_slash))
                payment_rows = payment_cursor.fetchall()
            else:
                # 支払いテーブル検索（支払い先名）- 日付フォーマット2025/04/30
                payment_cursor.execute("""
                    SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                    FROM payments
                    WHERE payee LIKE ? AND substr(payment_date, 1, 7) = ?
                    ORDER BY amount DESC, payment_date DESC
                """, (f"%{payee.strip()}%", payment_month_slash))
                payment_rows = payment_cursor.fetchall()
            
            payment_conn.close()
            
            # 費用データを取得（expenses.db）
            expense_conn = sqlite3.connect('expenses.db')
            expense_cursor = expense_conn.cursor()
            
            if payee_code and payee_code.strip():
                # 費用テーブル検索（支払い先コード優先）
                expense_cursor.execute("""
                    SELECT id, project_name, payee, payee_code, amount, payment_date, status
                    FROM expenses
                    WHERE payee_code = ? AND substr(payment_date, 1, 7) = ?
                    ORDER BY amount DESC, payment_date DESC
                """, (payee_code.strip(), payment_month))
                expense_rows = expense_cursor.fetchall()
            else:
                # 費用テーブル検索（支払い先名）
                expense_cursor.execute("""
                    SELECT id, project_name, payee, payee_code, amount, payment_date, status
                    FROM expenses
                    WHERE payee LIKE ? AND substr(payment_date, 1, 7) = ?
                    ORDER BY amount DESC, payment_date DESC
                """, (f"%{payee.strip()}%", payment_month))
                expense_rows = expense_cursor.fetchall()
            
            expense_conn.close()
            
            # ダイアログ作成
            dialog = QDialog(self)
            dialog.setWindowTitle(f"🔍 同月同支払い先比較 - {payee}")
            dialog.setModal(True)
            dialog.resize(1400, 700)
            
            layout = QVBoxLayout(dialog)
            
            # シンプルなヘッダー情報
            header = QFrame()
            header.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 5px;")
            header_layout = QHBoxLayout(header)

            title_label = QLabel(f"🔍 {payee} ({payment_month})")
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
            header_layout.addWidget(title_label)

            header_layout.addStretch()

            result_label = QLabel(f"支払い{len(payment_rows)}件 | 費用{len(expense_rows)}件")
            result_label.setStyleSheet("font-size: 12px; color: #666;")
            header_layout.addWidget(result_label)

            layout.addWidget(header)
            
            # メインエリア（左右分割）
            splitter = QSplitter(Qt.Horizontal)
            layout.addWidget(splitter)

            # 左側：支払いテーブル
            payment_frame = QFrame()
            payment_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
            payment_layout = QVBoxLayout(payment_frame)
            payment_layout.setContentsMargins(5, 5, 5, 5)

            payment_header = QLabel("💳 支払いテーブル")
            payment_header.setStyleSheet("font-weight: bold; color: #1976d2; padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
            payment_layout.addWidget(payment_header)

            payment_tree = QTreeWidget()
            payment_tree.setHeaderLabels(["金額", "支払日", "案件名", "状態"])
            payment_tree.setAlternatingRowColors(True)
            payment_tree.setRootIsDecorated(False)
            payment_layout.addWidget(payment_tree)

            # 右側：費用テーブル
            expense_frame = QFrame()
            expense_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
            expense_layout = QVBoxLayout(expense_frame)
            expense_layout.setContentsMargins(5, 5, 5, 5)

            expense_header = QLabel("💰 費用テーブル")
            expense_header.setStyleSheet("font-weight: bold; color: #d32f2f; padding: 5px; background-color: #ffebee; border-radius: 3px;")
            expense_layout.addWidget(expense_header)

            expense_tree = QTreeWidget()
            expense_tree.setHeaderLabels(["金額", "支払日", "案件名", "状態"])
            expense_tree.setAlternatingRowColors(True)
            expense_tree.setRootIsDecorated(False)
            expense_layout.addWidget(expense_tree)

            # 費用テーブル用の編集ボタン
            expense_button_layout = QHBoxLayout()
            edit_expense_button = QPushButton("✏️ 選択項目を編集")
            edit_expense_button.setMinimumSize(120, 28)
            edit_expense_button.clicked.connect(lambda: self.edit_expense_from_comparison(expense_tree, dialog))
            expense_button_layout.addWidget(edit_expense_button)
            expense_button_layout.addStretch()
            expense_layout.addLayout(expense_button_layout)

            # スプリッターに追加
            splitter.addWidget(payment_frame)
            splitter.addWidget(expense_frame)
            splitter.setSizes([700, 700])  # 左右同じサイズ
            
            # 選択された費用の金額（比較用）
            selected_amount_float = 0
            try:
                selected_amount_float = float(amount.replace("¥", "").replace(",", ""))
            except:
                pass
            
            # 支払いデータを追加
            for row in payment_rows:
                payment_item = QTreeWidgetItem()

                row_amount_str = format_amount(row[4]) if row[4] else ""
                payment_item.setText(0, row_amount_str)  # 金額
                payment_item.setText(1, str(row[5]) if row[5] else "")  # 支払日
                payment_item.setText(2, str(row[1]) if row[1] else "")  # 案件名
                payment_item.setText(3, str(row[6]) if row[6] else "")  # 状態

                # 金額による色分け
                try:
                    row_amount = float(str(row[4]).replace("¥", "").replace(",", ""))
                    diff = abs(row_amount - selected_amount_float)

                    if diff == 0:
                        # 完全一致 - 緑
                        for i in range(4):
                            payment_item.setBackground(i, QColor("#c8e6c9"))
                    elif diff <= 1000:
                        # 1000円以内の差 - 黄
                        for i in range(4):
                            payment_item.setBackground(i, QColor("#fff9c4"))
                except:
                    pass

                payment_tree.addTopLevelItem(payment_item)
            
            # 費用データを追加
            for row in expense_rows:
                expense_item = QTreeWidgetItem()

                row_amount_str = format_amount(row[4]) if row[4] else ""
                expense_item.setText(0, row_amount_str)  # 金額
                expense_item.setText(1, str(row[5]) if row[5] else "")  # 支払日
                expense_item.setText(2, str(row[1]) if row[1] else "")  # 案件名
                expense_item.setText(3, str(row[6]) if row[6] else "")  # 状態

                # データベースのIDを隠しデータとして保存
                expense_item.setData(0, Qt.UserRole, str(row[0]))  # ID

                # 選択された項目を強調表示
                if (str(row[1]) == project_name and
                    str(row[3]) == payee_code and
                    str(row[5]) == payment_date):
                    for i in range(4):
                        expense_item.setBackground(i, QColor("#ffeb3b"))  # 選択項目は黄色
                    font = QFont()
                    font.setBold(True)
                    for i in range(4):
                        expense_item.setFont(i, font)

                expense_tree.addTopLevelItem(expense_item)
            
            # 列幅調整
            for tree in [payment_tree, expense_tree]:
                for i in range(tree.columnCount()):
                    tree.resizeColumnToContents(i)
            
            # ボタンエリア
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(5, 10, 5, 5)

            close_button = QPushButton("閉じる")
            close_button.setMinimumSize(80, 32)
            close_button.clicked.connect(dialog.accept)
            button_layout.addStretch()
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            log_message(f"同月同支払い先比較エラー: {e}")
            QMessageBox.critical(self, "エラー", f"同月同支払い先比較の表示に失敗しました: {e}")

    def edit_expense_from_comparison(self, expense_tree, parent_dialog):
        """比較画面から費用項目を編集"""
        try:
            selected_items = expense_tree.selectedItems()
            if not selected_items:
                QMessageBox.information(parent_dialog, "情報", "編集する費用項目を選択してください")
                return

            selected_item = selected_items[0]
            expense_id = selected_item.data(0, Qt.UserRole)

            if not expense_id:
                QMessageBox.warning(parent_dialog, "警告", "選択された項目のIDが取得できません")
                return

            # 比較ダイアログを閉じる
            parent_dialog.accept()

            # メインの費用テーブルで該当項目を選択して編集
            self.select_and_edit_expense_by_id(expense_id)

        except Exception as e:
            log_message(f"比較画面からの費用編集エラー: {e}")
            QMessageBox.critical(parent_dialog, "エラー", f"費用編集に失敗しました: {e}")

    def select_and_edit_expense_by_id(self, expense_id):
        """指定されたIDの費用項目を選択して編集"""
        try:
            # メインの費用テーブルから該当項目を検索
            root = self.tree.invisibleRootItem()
            target_item = None

            for i in range(root.childCount()):
                item = root.child(i)
                if item.text(0) == str(expense_id):  # IDで一致確認
                    target_item = item
                    break

            if target_item:
                # 項目を選択
                self.tree.clearSelection()
                self.tree.setCurrentItem(target_item)
                target_item.setSelected(True)

                # 編集ダイアログを開く
                self.on_tree_select_for_edit()
            else:
                # 該当項目が見つからない場合はデータを再読み込み
                self.refresh_data_with_filters()
                QMessageBox.information(self, "情報", "項目が見つからないため、データを再読み込みしました。再度お試しください。")

        except Exception as e:
            log_message(f"ID指定での費用項目選択エラー: {e}")
            QMessageBox.critical(self, "エラー", f"項目の選択に失敗しました: {e}")

    def analyze_missing_invoice(self, selected_amount, payment_rows):
        """請求書未着を分析"""
        try:
            selected_amount_float = float(selected_amount.replace("¥", "").replace(",", ""))
        except:
            return {
                "message": "❓ 金額の解析ができませんでした",
                "color": "#f5f5f5",
                "is_missing": True
            }
        
        if not payment_rows:
            return {
                "message": "❌ 請求書未着\n同じ支払い先・同じ月の支払いデータが見つかりません。\n催促が必要です。",
                "color": "#f8d7da",
                "is_missing": True
            }
        
        # 完全一致チェック
        exact_matches = []
        close_matches = []  # 1000円以内
        
        for row in payment_rows:
            try:
                row_amount = float(str(row[4]).replace("¥", "").replace(",", ""))
                diff = abs(row_amount - selected_amount_float)
                
                if diff == 0:
                    exact_matches.append(row)
                elif diff <= 1000:
                    close_matches.append(row)
            except:
                continue
        
        if exact_matches:
            return {
                "message": f"✅ 請求書到着済み\n同じ金額（{selected_amount}）の請求が{len(exact_matches)}件見つかりました。\n催促は不要です。",
                "color": "#d4edda",
                "is_missing": False
            }
        elif close_matches:
            amounts = [format_amount(row[4]) for row in close_matches]
            return {
                "message": f"⚡ 金額変更の可能性\n近い金額の請求が見つかりました：{', '.join(amounts)}\n金額変更について確認が必要です。",
                "color": "#fff3cd",
                "is_missing": True
            }
        else:
            return {
                "message": f"❌ 請求書未着\n同じ支払い先から{len(payment_rows)}件の請求がありますが、\n該当金額（{selected_amount}）の請求が見つかりません。\n催促が必要です。",
                "color": "#f8d7da",
                "is_missing": True
            }

    def show_missing_invoice_check_all(self):
        """未処理項目の請求書未着確認一括表示"""
        try:
            # 未処理の費用データを取得
            expense_rows, _ = self.db_manager.get_expense_data()
            unprocessed_items = [row for row in expense_rows if row[6] == "未処理"]
            
            if not unprocessed_items:
                QMessageBox.information(self, "情報", "未処理の費用データがありません")
                return
            
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QScrollArea, QFrame
            
            # ダイアログ作成
            dialog = QDialog(self)
            dialog.setWindowTitle("🔍 未処理項目の請求書未着確認")
            dialog.setModal(True)
            dialog.resize(1400, 800)
            
            layout = QVBoxLayout(dialog)
            
            # ヘッダー情報
            header = QFrame()
            header.setStyleSheet("background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #ffc107;")
            header_layout = QVBoxLayout(header)
            
            title_label = QLabel("🔍 未処理項目の請求書未着確認（一括確認）")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #856404; margin-bottom: 5px;")
            header_layout.addWidget(title_label)
            
            info_label = QLabel(f"📊 対象: {len(unprocessed_items)}件の未処理費用データ")
            info_label.setStyleSheet("font-size: 12px; color: #856404;")
            header_layout.addWidget(info_label)
            
            layout.addWidget(header)
            
            # 一覧表示
            tree = QTreeWidget()
            tree.setHeaderLabels([
                "判定", "案件名", "支払い先", "金額", "支払日", 
                "一致件数", "近似件数", "対応状況"
            ])
            tree.setAlternatingRowColors(True)
            layout.addWidget(tree)
            
            # 未着分析結果の統計
            missing_count = 0
            confirmed_count = 0
            need_check_count = 0
            
            # 各未処理項目を分析
            for expense_row in unprocessed_items:
                payee = expense_row[2]  # 支払い先
                payee_code = expense_row[3]  # 支払い先コード
                amount = expense_row[4]  # 金額
                payment_date = expense_row[5]  # 支払日
                payment_month = payment_date[:7] if len(payment_date) >= 7 else ""
                
                # 関連支払いデータを取得（直接データベース検索）
                conn = sqlite3.connect('billing.db')
                cursor = conn.cursor()
                
                search_conditions = []
                params = []
                
                # 支払い先コードがある場合は優先
                if payee_code and str(payee_code).strip():
                    search_conditions.append("payee_code = ?")
                    params.append(str(payee_code).strip())
                
                # 支払い先名でも検索
                if payee and str(payee).strip():
                    search_conditions.append("payee LIKE ?")
                    params.append(f"%{str(payee).strip()}%")
                
                if not search_conditions:
                    payment_rows = []
                else:
                    query = """
                        SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                        FROM payments
                        WHERE ({})
                    """.format(" OR ".join(search_conditions))
                    
                    # 月フィルタを追加
                    if payment_month:
                        query += " AND substr(payment_date, 1, 7) = ?"
                        params.append(payment_month)
                    
                    query += " ORDER BY amount DESC, payment_date DESC"
                    
                    cursor.execute(query, params)
                    payment_rows = cursor.fetchall()
                
                conn.close()
                
                # 分析
                analysis = self.analyze_missing_invoice(format_amount(amount), payment_rows)
                
                # 統計を更新
                if analysis["is_missing"]:
                    if not payment_rows:
                        missing_count += 1
                    else:
                        need_check_count += 1
                else:
                    confirmed_count += 1
                
                # 一致件数と近似件数をカウント
                exact_matches = 0
                close_matches = 0
                
                try:
                    amount_float = float(str(amount))
                    for payment_row in payment_rows:
                        try:
                            payment_amount = float(str(payment_row[4]).replace("¥", "").replace(",", ""))
                            diff = abs(payment_amount - amount_float)
                            if diff == 0:
                                exact_matches += 1
                            elif diff <= 1000:
                                close_matches += 1
                        except:
                            continue
                except:
                    pass
                
                # ツリーアイテム作成
                item = QTreeWidgetItem()
                
                # 判定結果
                if analysis["is_missing"]:
                    if not payment_rows:
                        item.setText(0, "❌ 未着")
                        item.setBackground(0, QColor("#f8d7da"))
                        item.setText(7, "催促要")
                    else:
                        item.setText(0, "⚡ 要確認")
                        item.setBackground(0, QColor("#fff3cd"))
                        item.setText(7, "金額確認要")
                else:
                    item.setText(0, "✅ 到着済み")
                    item.setBackground(0, QColor("#d4edda"))
                    item.setText(7, "対応不要")
                
                # 基本情報
                item.setText(1, expense_row[1])  # 案件名
                item.setText(2, payee)  # 支払い先
                item.setText(3, format_amount(amount))  # 金額
                item.setText(4, payment_date)  # 支払日
                item.setText(5, str(exact_matches))  # 一致件数
                item.setText(6, str(close_matches))  # 近似件数
                
                # データを保存（ダブルクリック用）
                item.setData(0, Qt.UserRole, expense_row)
                
                tree.addTopLevelItem(item)
            
            # 列幅調整
            for i in range(tree.columnCount()):
                tree.resizeColumnToContents(i)
            
            # 統計情報
            stats_frame = QFrame()
            stats_frame.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px;")
            stats_layout = QHBoxLayout(stats_frame)
            
            stats_layout.addWidget(QLabel(f"❌ 未着・催促要: {missing_count}件"))
            stats_layout.addWidget(QLabel(f"⚡ 金額確認要: {need_check_count}件"))
            stats_layout.addWidget(QLabel(f"✅ 到着済み: {confirmed_count}件"))
            stats_layout.addStretch()
            
            layout.addWidget(stats_frame)
            
            # ダブルクリックで詳細表示
            def on_double_click(item, column):
                expense_row = item.data(0, Qt.UserRole)
                if expense_row:
                    # 詳細ダイアログを表示
                    temp_item = QTreeWidgetItem()
                    temp_item.setText(1, expense_row[1])  # 案件名
                    temp_item.setText(2, expense_row[2])  # 支払い先
                    temp_item.setText(3, expense_row[3])  # 支払い先コード
                    temp_item.setText(4, format_amount(expense_row[4]))  # 金額
                    temp_item.setText(5, expense_row[5])  # 支払日
                    temp_item.setText(6, expense_row[6])  # 状態
                    
                    self.show_missing_invoice_dialog(temp_item)
            
            tree.itemDoubleClicked.connect(on_double_click)
            
            # 説明
            help_label = QLabel("💡 ダブルクリックで詳細確認ができます")
            help_label.setStyleSheet("font-size: 11px; color: #666; margin-top: 5px;")
            layout.addWidget(help_label)
            
            # ボタンエリア
            button_layout = QHBoxLayout()
            
            close_button = QPushButton("閉じる")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            log_message(f"一括請求書未着確認エラー: {e}")
            QMessageBox.critical(self, "エラー", f"一括請求書未着確認の表示に失敗しました: {e}")

    def show_payment_comparison_all(self):
        """全費用データの支払い比較を表示"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QFrame, QProgressBar, QApplication
        from PyQt5.QtCore import Qt
        
        try:
            # 現在の表示データを取得
            expense_data = []
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item:
                    expense_data.append({
                        'subject': item.text(0),
                        'project_name': item.text(1),
                        'payee': item.text(2),
                        'payee_code': item.text(3),
                        'amount': item.text(4),
                        'payment_date': item.text(5),
                        'status': item.text(6)
                    })
            
            if not expense_data:
                QMessageBox.information(self, "情報", "表示される費用データがありません")
                return
            
            # ダイアログ作成
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 全体支払い比較確認")
            dialog.setModal(True)
            dialog.resize(1200, 700)
            
            layout = QVBoxLayout(dialog)
            
            # ヘッダー情報
            header = QFrame()
            header.setStyleSheet("background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4caf50;")
            header_layout = QVBoxLayout(header)
            
            title_label = QLabel("📊 全体支払い比較確認")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e7d32; margin-bottom: 5px;")
            header_layout.addWidget(title_label)
            
            info_label = QLabel(f"📋 対象件数: {len(expense_data)}件の費用データを分析中...")
            info_label.setStyleSheet("font-size: 12px; color: #2e7d32;")
            header_layout.addWidget(info_label)
            
            layout.addWidget(header)
            
            # プログレスバー
            progress = QProgressBar()
            progress.setMaximum(len(expense_data))
            progress.setValue(0)
            layout.addWidget(progress)
            
            # 結果表示ツリー
            tree = QTreeWidget()
            tree.setHeaderLabels(["件名", "案件名", "支払い先", "金額", "支払日", "状態", "比較結果", "同月件数"])
            tree.setAlternatingRowColors(True)
            layout.addWidget(tree)
            
            # データベース接続
            conn = sqlite3.connect('billing.db')
            cursor = conn.cursor()
            
            # 各費用データに対して支払い比較を実行
            for idx, expense in enumerate(expense_data):
                QApplication.processEvents()  # UIの応答性を維持
                progress.setValue(idx + 1)
                
                payee = expense['payee']
                payee_code = expense['payee_code']
                payment_date = expense['payment_date']
                amount = expense['amount']
                
                # 同じ月の支払いデータを検索
                payment_month = payment_date[:7] if len(payment_date) >= 7 else ""
                
                try:
                    # 支払い先コードを優先して検索
                    if payee_code and payee_code.strip():
                        cursor.execute("""
                            SELECT COUNT(*) as count, 
                                   GROUP_CONCAT(DISTINCT amount) as amounts,
                                   GROUP_CONCAT(DISTINCT status) as statuses
                            FROM payments
                            WHERE payee_code = ? AND substr(payment_date, 1, 7) = ?
                        """, (payee_code.strip(), payment_month))
                    else:
                        cursor.execute("""
                            SELECT COUNT(*) as count,
                                   GROUP_CONCAT(DISTINCT amount) as amounts,
                                   GROUP_CONCAT(DISTINCT status) as statuses
                            FROM payments
                            WHERE payee LIKE ? AND substr(payment_date, 1, 7) = ?
                        """, (f"%{payee.strip()}%", payment_month))
                    
                    result = cursor.fetchone()
                    payment_count = result[0] if result else 0
                    payment_amounts = result[1] if result and result[1] else ""
                    payment_statuses = result[2] if result and result[2] else ""
                    
                    # 比較結果を判定
                    if payment_count == 0:
                        comparison_result = "❌ 支払いデータなし"
                        item_color = "#ffebee"
                    elif payment_count == 1:
                        comparison_result = "✅ 1件一致"
                        item_color = "#e8f5e8"
                    else:
                        comparison_result = f"⚠️ {payment_count}件存在"
                        item_color = "#fff3e0"
                    
                    # ツリーアイテムを作成
                    tree_item = QTreeWidgetItem()
                    tree_item.setText(0, expense['subject'])
                    tree_item.setText(1, expense['project_name'])
                    tree_item.setText(2, expense['payee'])
                    tree_item.setText(3, expense['amount'])
                    tree_item.setText(4, expense['payment_date'])
                    tree_item.setText(5, expense['status'])
                    tree_item.setText(6, comparison_result)
                    tree_item.setText(7, str(payment_count))
                    
                    # 背景色を設定
                    for col in range(8):
                        tree_item.setBackground(col, QColor(item_color))
                    
                    # 元のデータを保存（ダブルクリック用）
                    tree_item.setData(0, Qt.UserRole, expense)
                    
                    tree.addTopLevelItem(tree_item)
                    
                except Exception as e:
                    log_message(f"支払い比較エラー ({expense['subject']}): {e}")
                    continue
            
            conn.close()
            
            # プログレスバーを非表示
            progress.hide()
            
            # 統計情報を更新
            total_items = tree.topLevelItemCount()
            no_payment_count = 0
            single_match_count = 0
            multiple_match_count = 0
            
            for i in range(total_items):
                item = tree.topLevelItem(i)
                result_text = item.text(6)
                if "支払いデータなし" in result_text:
                    no_payment_count += 1
                elif "1件一致" in result_text:
                    single_match_count += 1
                elif "件存在" in result_text:
                    multiple_match_count += 1
            
            # 統計情報を表示
            stats_frame = QFrame()
            stats_frame.setStyleSheet("background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin-top: 10px;")
            stats_layout = QHBoxLayout(stats_frame)
            
            stats_label = QLabel(f"📊 統計: 総件数 {total_items}件 | ✅ 一致 {single_match_count}件 | ❌ 未払い {no_payment_count}件 | ⚠️ 複数 {multiple_match_count}件")
            stats_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            stats_layout.addWidget(stats_label)
            
            layout.addWidget(stats_frame)
            
            # ダブルクリックで詳細表示
            def on_double_click(item, column):
                expense_data = item.data(0, Qt.UserRole)
                if expense_data:
                    # 詳細比較ダイアログを表示
                    temp_item = QTreeWidgetItem()
                    temp_item.setText(0, expense_data['subject'])
                    temp_item.setText(1, expense_data['project_name'])
                    temp_item.setText(2, expense_data['payee'])
                    temp_item.setText(3, expense_data['payee_code'])
                    temp_item.setText(4, expense_data['amount'])
                    temp_item.setText(5, expense_data['payment_date'])
                    temp_item.setText(6, expense_data['status'])
                    
                    self.show_payment_comparison_dialog(temp_item)
            
            tree.itemDoubleClicked.connect(on_double_click)
            
            # 説明
            help_label = QLabel("💡 ダブルクリックで個別の詳細比較を表示できます | ❌赤: 支払いなし | ✅緑: 正常 | ⚠️オレンジ: 複数支払い")
            help_label.setStyleSheet("font-size: 11px; color: #666; margin-top: 5px;")
            layout.addWidget(help_label)
            
            # ボタンエリア
            button_layout = QHBoxLayout()
            
            # CSVエクスポートボタン
            export_button = QPushButton("📤 結果をCSVエクスポート")
            export_button.clicked.connect(lambda: self.export_comparison_results(tree))
            button_layout.addWidget(export_button)
            
            button_layout.addStretch()
            
            close_button = QPushButton("閉じる")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            log_message(f"全体支払い比較エラー: {e}")
            QMessageBox.critical(self, "エラー", f"全体支払い比較の表示に失敗しました: {e}")

    def export_comparison_results(self, tree):
        """比較結果をCSVにエクスポート"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            from datetime import datetime
            
            # ファイル保存ダイアログ
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "比較結果をCSVで保存",
                f"payment_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # ヘッダーを書き込み
                    headers = []
                    for col in range(tree.columnCount()):
                        headers.append(tree.headerItem().text(col))
                    writer.writerow(headers)
                    
                    # データを書き込み
                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        row_data = []
                        for col in range(tree.columnCount()):
                            row_data.append(item.text(col))
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "完了", f"比較結果を保存しました:\n{filename}")
                
        except Exception as e:
            log_message(f"比較結果エクスポートエラー: {e}")
            QMessageBox.critical(self, "エラー", f"比較結果のエクスポートに失敗しました: {e}")

    # ===== メニューバー/ツールバー用の共通アクション =====
    def export_csv(self):
        """CSV出力（メニュー/ツールバー用）"""
        self.export_to_csv()
    
    def create_new_entry(self):
        """新規エントリ作成（メニュー/ツールバー用）"""
        # 新規レコード追加ダイアログを表示
        try:
            from PyQt5.QtWidgets import QInputDialog, QComboBox
            
            # 現在選択されているタブに応じて適切な新規作成を実行
            current_tab = self.tab_control.currentIndex()
            
            if current_tab == 0:  # 支出情報タブ
                # 新規支出レコードを作成
                self.add_new_record()
            else:
                QMessageBox.information(self, "新規作成", "現在のサブタブでは新規作成は利用できません。")
                
        except Exception as e:
            log_message(f"新規作成エラー: {e}")
            QMessageBox.critical(self, "エラー", f"新規作成に失敗しました: {e}")
    
    def delete_selected(self):
        """選択項目削除（メニュー/ツールバー用）"""
        self.delete_record()
    
    def show_search(self):
        """検索表示（メニュー/ツールバー用）"""
        self.search_records()
    
    def reset_filters(self):
        """フィルターリセット（メニュー/ツールバー用）"""
        self.reset_search()
    
    def toggle_filter_panel(self, visible):
        """フィルターパネル表示切り替え"""
        try:
            if hasattr(self, 'search_frame'):
                self.search_frame.setVisible(visible)
        except Exception as e:
            log_message(f"フィルターパネル切り替えエラー: {e}")
    
    def run_matching(self):
        """照合実行（メニュー/ツールバー用）"""
        try:
            # 現在のタブに応じて適切な照合処理を実行
            current_tab = self.tab_control.currentIndex()
            
            if current_tab == 2:  # 支払い照合タブ
                # 照合処理を実行
                self.comparison_results_label.setText("照合処理を実行中...")
                self.compare_payments()
                QMessageBox.information(self, "照合実行", "照合処理が完了しました。")
            else:
                QMessageBox.information(self, "照合実行", "支払い照合タブで照合機能を使用してください。")
                
        except Exception as e:
            log_message(f"照合実行エラー: {e}")
            QMessageBox.critical(self, "エラー", f"照合実行に失敗しました: {e}")

    # ファイル終了確認用のコメント - expense_tab.py完了
