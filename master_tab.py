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
    QCheckBox,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QFont, QBrush
import csv
import os
from datetime import datetime
from utils import format_amount, log_message

# 不要なインポートを削除


class MasterTab(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db_manager = app.db_manager
        self.status_label = app.status_label

        # 動的フォントサイズを取得
        self.font_size = app.base_font_size
        self.title_font_size = app.title_font_size
        
        # 動的サイズ計算（コンパクト版）
        self.widget_min_width = max(70, int(self.font_size * 5))
        self.button_min_width = max(50, int(self.font_size * 4))
        self.search_min_width = max(130, int(self.font_size * 10))
        self.button_min_size = max(20, int(self.font_size * 1.6))

        # ソート情報
        self.sort_info = {"column": None, "reverse": False}

        # 色分け設定
        self.monthly_color = QColor(173, 216, 230)  # ライトブルー（月額固定）
        self.count_based_color = QColor(255, 182, 193)  # ライトピンク（回数ベース）
        self.default_color = QColor(248, 248, 248)  # オフホワイト（デフォルト）

        # レイアウト設定
        self.setup_ui()

    def setup_ui(self):
        # メインレイアウト
        main_layout = QVBoxLayout(self)

        # 凡例エリア（種別の色分け説明）
        legend_frame = QFrame()
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.addWidget(legend_frame)

        legend_layout.addWidget(QLabel("🎨 種別色分け:"))

        # 各種別の色見本を表示
        legend_items = [
            ("月額固定", self.monthly_color),
            ("回数ベース", self.count_based_color),
        ]

        for payment_type, color in legend_items:
            color_label = QLabel(f" {payment_type} ")
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

        # 検索・フィルタフレーム
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.addWidget(search_frame)

        # 種別フィルタ
        search_layout.addWidget(QLabel("📊 種別:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["すべて", "月額固定", "回数ベース"])
        self.type_filter.setMinimumWidth(self.widget_min_width + 20)
        self.type_filter.currentTextChanged.connect(self.filter_by_type)
        search_layout.addWidget(self.type_filter)

        # 検索フィールド
        search_layout.addWidget(QLabel("🔍 検索:"))
        self.search_entry = QLineEdit()
        self.search_entry.setMinimumWidth(self.search_min_width)
        self.search_entry.setPlaceholderText("案件名、支払い先で検索...")
        self.search_entry.returnPressed.connect(self.search_records)
        search_layout.addWidget(self.search_entry)

        search_button = QPushButton("検索")
        search_button.clicked.connect(self.search_records)
        search_layout.addWidget(search_button)

        reset_button = QPushButton("リセット")
        reset_button.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_button)

        search_layout.addStretch()

        # 上部のボタンフレーム
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.addWidget(button_frame)

        # レコード操作グループ
        record_group = QGroupBox("📝 レコード操作")
        record_group_layout = QHBoxLayout(record_group)
        button_layout.addWidget(record_group)

        create_button = QPushButton("➕ 新規作成")
        create_button.clicked.connect(self.create_record)
        record_group_layout.addWidget(create_button)

        delete_button = QPushButton("🗑️ 削除")
        delete_button.clicked.connect(self.delete_record)
        record_group_layout.addWidget(delete_button)

        duplicate_button = QPushButton("📄 複製")
        duplicate_button.clicked.connect(self.duplicate_record)
        record_group_layout.addWidget(duplicate_button)

        # データ操作グループ
        data_group = QGroupBox("💾 データ操作")
        data_group_layout = QHBoxLayout(data_group)
        button_layout.addWidget(data_group)

        export_button = QPushButton("📤 CSVエクスポート")
        export_button.clicked.connect(self.export_to_csv)
        data_group_layout.addWidget(export_button)

        import_button = QPushButton("📥 CSVインポート")
        import_button.clicked.connect(self.import_from_csv)
        data_group_layout.addWidget(import_button)

        # ツリーウィジェットのフレーム
        tree_frame = QFrame()
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.addWidget(tree_frame)

        # テーブルタイトル
        table_title = QLabel("🏗️ 費用マスター一覧")
        table_title.setFont(QFont("", self.title_font_size, QFont.Bold))
        table_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        tree_layout.addWidget(table_title)

        # ツリーウィジェットの作成（スタイルシートでフォントサイズ設定されるため重複削除）
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [
                "ID",
                "案件名",
                "支払い先",
                "コード",
                "金額",
                "種別",
                "開始日",
                "終了日",
                "放送曜日",
            ]
        )
        tree_layout.addWidget(self.tree)

        # 列の設定
        self.tree.setColumnHidden(0, True)  # ID非表示
        self.tree.setColumnHidden(6, True)  # 開始日非表示
        self.tree.setColumnHidden(7, True)  # 終了日非表示

        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)  # 案件名
        self.tree.header().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )  # 支払い先
        self.tree.header().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )  # コード
        self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 金額
        self.tree.header().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 種別
        self.tree.header().setSectionResizeMode(
            8, QHeaderView.ResizeToContents
        )  # 放送曜日

        # 複数選択を可能に
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setAlternatingRowColors(False)  # 交互背景色を無効化（色分けのため）
        
        # ソート機能を有効化
        self.tree.setSortingEnabled(True)

        # ヘッダークリックでソート機能（PyQt5バージョン互換対応）
        self.tree.header().sectionClicked.connect(self.on_header_clicked)
        # PyQt5バージョン互換性対応
        try:
            # PyQt5の新しいバージョン
            self.tree.header().setSectionsClickable(True)
        except AttributeError:
            # PyQt5の古いバージョン
            self.tree.header().setClickable(True)

        # 選択時イベント
        self.tree.itemSelectionChanged.connect(self.on_tree_select_for_edit)

        # 編集フォームの作成
        self.edit_frame = QGroupBox("✏️ マスターレコード編集")
        edit_layout = QVBoxLayout(self.edit_frame)
        main_layout.addWidget(self.edit_frame)

        # 編集フォームの内部レイアウト
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setContentsMargins(5, 5, 5, 5)
        edit_layout.addWidget(form_widget)

        # 編集フォームのフィールド定義
        master_fields = [
            ("ID", "id", 5),
            ("案件名", "project_name", 20),
            ("支払い先", "payee", 15),
            ("支払い先コード", "payee_code", 10),
            ("金額", "amount", 10),
            ("種別", "payment_type", 10),
            ("開始日", "start_date", 10),
            ("終了日", "end_date", 10),
        ]

        # 編集フィールドの作成
        self.edit_entries = {}

        # フィールドを3列で配置
        for i, (label_text, field_name, width) in enumerate(master_fields):
            row = i // 3
            col = (i % 3) * 2

            # ラベル
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            form_layout.addWidget(label, row, col)

            # 入力ウィジェット（動的幅コンパクト版）
            dynamic_width = max(70, int(self.font_size * width * 0.8))
            if field_name == "id":
                # IDは読み取り専用
                entry = QLineEdit()
                entry.setMinimumWidth(dynamic_width)
                entry.setReadOnly(True)
                entry.setStyleSheet("background-color: #f8f9fa;")
            elif field_name == "payment_type":
                # 種別はドロップダウン
                entry = QComboBox()
                entry.addItems(["月額固定", "回数ベース"])
                entry.setMinimumWidth(dynamic_width)
                entry.currentIndexChanged.connect(self.on_payment_type_change)
            elif field_name in ["start_date", "end_date"]:
                # 日付選択
                entry = QDateEdit()
                entry.setCalendarPopup(True)
                entry.setMinimumWidth(dynamic_width)
                entry.setDate(QDate.currentDate())
            else:
                # 通常のテキスト入力
                entry = QLineEdit()
                entry.setMinimumWidth(dynamic_width)

            form_layout.addWidget(entry, row, col + 1)
            self.edit_entries[field_name] = entry

        # 放送曜日チェックボックス
        broadcast_frame = QGroupBox("📅 放送曜日")
        broadcast_layout = QHBoxLayout(broadcast_frame)
        edit_layout.addWidget(broadcast_frame)

        self.weekday_vars = {}
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]

        for day in weekdays:
            checkbox = QCheckBox(day)
            broadcast_layout.addWidget(checkbox)
            self.weekday_vars[day] = checkbox

        # 非表示の放送曜日フィールド（データ保存用）
        self.edit_entries["broadcast_days"] = QLineEdit()
        self.edit_entries["broadcast_days"].hide()

        # ボタンフレーム
        button_widget = QWidget()
        button_box_layout = QHBoxLayout(button_widget)
        edit_layout.addWidget(button_widget)

        # 保存/キャンセルボタン
        button_box_layout.addStretch()

        cancel_button = QPushButton("❌ キャンセル")
        button_width = max(70, int(self.font_size * 5))
        cancel_button.setMinimumSize(button_width, self.button_min_size)
        cancel_button.clicked.connect(self.cancel_direct_edit)
        button_box_layout.addWidget(cancel_button)

        save_button = QPushButton("💾 保存")
        save_button.setMinimumSize(button_width, self.button_min_size)
        save_button.clicked.connect(self.save_direct_edit)
        button_box_layout.addWidget(save_button)

        # 編集フィールドにEnterキーイベントを追加
        for field_key, widget in self.edit_entries.items():
            if hasattr(widget, 'returnPressed'):
                widget.returnPressed.connect(self.save_direct_edit)

        # 初期状態では編集フォームを非表示
        self.edit_frame.hide()

    def get_color_for_payment_type(self, payment_type):
        """種別に応じた背景色を返す"""
        color_map = {
            "月額固定": self.monthly_color,
            "回数ベース": self.count_based_color,
        }
        return color_map.get(payment_type, self.default_color)

    def apply_row_colors(self, item, payment_type, column_count=9):
        """行に色を適用する共通メソッド"""
        background_color = self.get_color_for_payment_type(payment_type)
        brush = QBrush(background_color)
        
        # 明示的にテキスト色を黒に設定
        text_brush = QBrush(QColor(0, 0, 0))  # 黒色

        for i in range(column_count):
            item.setBackground(i, brush)
            item.setForeground(i, text_brush)  # テキスト色を明示的に設定
            # さらに確実にするため、データも設定
            item.setData(i, Qt.BackgroundRole, background_color)
            item.setData(i, Qt.ForegroundRole, QColor(0, 0, 0))

    def filter_by_type(self):
        """種別でフィルタリング"""
        selected_type = self.type_filter.currentText()

        if selected_type == "すべて":
            self.refresh_data()
            return

        # 現在表示されている項目をフィルタリング
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            payment_type = item.text(5)  # 種別列
            item.setHidden(payment_type != selected_type)

        # 表示件数を更新
        visible_count = sum(
            1 for i in range(root.childCount()) if not root.child(i).isHidden()
        )
        self.app.status_label.setText(
            f"{selected_type}のマスターデータ: {visible_count}件"
        )

    def search_records(self):
        """マスターレコードの検索"""
        search_term = self.search_entry.text().strip()
        if not search_term:
            self.refresh_data()
            return

        # ツリーのクリア
        self.tree.clear()

        try:
            # データベースから検索
            master_rows = self.db_manager.get_master_data(search_term)

            # 検索結果をツリーウィジェットに追加
            for row in master_rows:
                item = QTreeWidgetItem()

                # 新しいフィールドがない古いデータの場合は、デフォルト値を使用
                payment_type = row[5] if len(row) > 5 else "月額固定"
                broadcast_days = row[6] if len(row) > 6 else ""
                start_date = row[7] if len(row) > 7 else ""
                end_date = row[8] if len(row) > 8 else ""

                # 値を設定
                item.setText(0, str(row[0]))  # ID
                item.setText(1, row[1])  # 案件名
                item.setText(2, row[2])  # 支払い先
                item.setText(3, row[3] if row[3] else "")  # 支払い先コード
                item.setText(4, format_amount(row[4]))  # 金額（整形）
                item.setText(5, payment_type)  # 種別
                item.setText(6, start_date)  # 開始日
                item.setText(7, end_date)  # 終了日
                item.setText(8, broadcast_days)  # 放送曜日

                # 種別に応じた背景色を適用
                self.apply_row_colors(item, payment_type, 9)

                self.tree.addTopLevelItem(item)

            # 状態表示の更新
            self.app.status_label.setText(
                f"「{search_term}」の検索結果: {len(master_rows)}件"
            )

        except Exception as e:
            log_message(f"マスターデータ検索中にエラーが発生: {e}")
            self.app.status_label.setText(f"エラー: マスターデータ検索に失敗しました")

    def reset_search(self):
        """検索をリセット"""
        self.search_entry.clear()
        self.type_filter.setCurrentText("すべて")
        self.refresh_data()

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
            if column_name in ["金額", "ID"]:
                # 金額は円マークとカンマを取り除いて数値としてソート
                try:
                    value = value.replace(",", "").replace("円", "").strip()
                    return float(value) if value else 0
                except (ValueError, TypeError):
                    return 0
            elif column_name in ["開始日", "終了日"]:
                # 日付は文字列としてソート（YYYY-MM-DD形式想定）
                return value if value else "0000-00-00"
            elif column_name in ["種別"]:
                # 種別は優先順位でソート
                type_priority = {"月額固定": 1, "回数ベース": 2}
                return type_priority.get(value, 0)
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

    def refresh_data(self):
        """費用マスターデータを更新（改善版）"""
        # ツリーのクリア
        self.tree.clear()

        try:
            # データベースからデータを読み込み
            master_rows = self.db_manager.get_master_data()

            # ツリーウィジェットにデータを追加
            monthly_count = 0
            count_based_count = 0

            for row in master_rows:
                item = QTreeWidgetItem()

                # 新しいフィールドがない古いデータの場合は、デフォルト値を使用
                payment_type = row[5] if len(row) > 5 else "月額固定"
                broadcast_days = row[6] if len(row) > 6 else ""
                start_date = row[7] if len(row) > 7 else ""
                end_date = row[8] if len(row) > 8 else ""

                # 値を設定
                item.setText(0, str(row[0]))  # ID
                item.setText(1, row[1])  # 案件名
                item.setText(2, row[2])  # 支払い先
                item.setText(3, row[3] if row[3] else "")  # 支払い先コード
                item.setText(4, format_amount(row[4]))  # 金額（整形）
                item.setText(5, payment_type)  # 種別
                item.setText(6, start_date)  # 開始日
                item.setText(7, end_date)  # 終了日
                item.setText(8, broadcast_days)  # 放送曜日

                # 種別に応じた背景色を適用
                self.apply_row_colors(item, payment_type, 9)

                # 種別カウント
                if payment_type == "月額固定":
                    monthly_count += 1
                elif payment_type == "回数ベース":
                    count_based_count += 1

                self.tree.addTopLevelItem(item)

            # 状態表示の更新（改善版）
            total_count = len(master_rows)
            self.app.status_label.setText(
                f"費用マスターデータ: 全{total_count}件 "
                f"(月額固定:{monthly_count}件, 回数ベース:{count_based_count}件)"
            )

            # 最終更新時刻の更新
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

            log_message("費用マスターデータの更新が完了しました")

        except Exception as e:
            log_message(f"費用マスターデータ読み込み中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            self.app.status_label.setText(
                f"エラー: 費用マスターデータ読み込みに失敗しました"
            )

    def on_tree_select_for_edit(self):
        """ツリーウィジェットの行選択時に編集フォームを表示"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            self.edit_frame.hide()
            return

        # 選択行のデータを取得
        selected_item = selected_items[0]
        master_id = selected_item.text(0)

        try:
            # データベースから詳細情報を取得
            row = self.db_manager.get_master_by_id(master_id)

            if not row:
                return

            # 編集フォームに値を設定
            field_names = [
                "id",
                "project_name",
                "payee",
                "payee_code",
                "amount",
                "payment_type",
                "start_date",
                "end_date",
            ]

            for i, field in enumerate(field_names):
                if field == "id":
                    # IDフィールド
                    self.edit_entries[field].setText(str(row[i]))
                elif field == "payment_type":
                    # 種別コンボボックス
                    index = self.edit_entries[field].findText(
                        row[i] if i < len(row) else "月額固定"
                    )
                    if index >= 0:
                        self.edit_entries[field].setCurrentIndex(index)
                elif field in ["start_date", "end_date"]:
                    # 日付フィールド
                    date_value = row[i] if i < len(row) else ""
                    try:
                        parts = date_value.split("-")
                        if len(parts) >= 3:
                            qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                            self.edit_entries[field].setDate(qdate)
                        else:
                            self.edit_entries[field].setDate(QDate.currentDate())
                    except (ValueError, IndexError, AttributeError):
                        self.edit_entries[field].setDate(QDate.currentDate())
                else:
                    # 通常のテキストフィールド
                    self.edit_entries[field].setText(
                        str(row[i]) if i < len(row) else ""
                    )

            # 放送曜日チェックボックスの設定
            broadcast_days_str = row[6] if len(row) > 6 else ""
            selected_days = [
                day.strip() for day in broadcast_days_str.split(",") if day.strip()
            ]

            # すべてチェックを外す
            for day, checkbox in self.weekday_vars.items():
                checkbox.setChecked(False)

            # 選択された曜日をチェック
            for day in selected_days:
                if day in self.weekday_vars:
                    self.weekday_vars[day].setChecked(True)

            # 非表示フィールドにも設定
            self.edit_entries["broadcast_days"].setText(broadcast_days_str)

            # 編集フォームを表示
            self.edit_frame.show()

        except Exception as e:
            log_message(f"費用マスターデータ編集フォーム表示中にエラーが発生: {e}")

    def on_payment_type_change(self, index):
        """種別変更時のチェック（直接編集フォーム用）"""
        # 種別に応じた処理を追加する場合はここに記述
        pass

    def save_direct_edit(self):
        """費用マスターテーブルの直接編集を保存（新規作成対応・コード0埋め対応）"""
        try:
            # utils.pyから関数をインポート
            from utils import format_payee_code

            # 入力値を取得
            master_id = self.edit_entries["id"].text()
            project_name = self.edit_entries["project_name"].text()
            payee = self.edit_entries["payee"].text()
            payee_code = self.edit_entries["payee_code"].text()
            amount_str = self.edit_entries["amount"].text()
            payment_type = self.edit_entries["payment_type"].currentText()

            # 【修正】支払い先コードの0埋め処理（1回のみ）
            if payee_code:
                payee_code = format_payee_code(payee_code)
                # 画面上のフィールドも更新
                self.edit_entries["payee_code"].setText(payee_code)

            # 日付はQDateEditから取得
            start_date = self.edit_entries["start_date"].date()
            start_date_str = (
                f"{start_date.year()}-{start_date.month():02d}-{start_date.day():02d}"
            )

            end_date = self.edit_entries["end_date"].date()
            end_date_str = (
                f"{end_date.year()}-{end_date.month():02d}-{end_date.day():02d}"
            )

            # 放送曜日を取得
            selected_days = [
                day
                for day, checkbox in self.weekday_vars.items()
                if checkbox.isChecked()
            ]
            broadcast_days = ",".join(selected_days)

            # 入力チェック
            if not project_name or not payee or not amount_str:
                QMessageBox.critical(self, "エラー", "必須項目を入力してください")
                return

            # 種別が回数ベースの場合は放送曜日を必須に
            if payment_type == "回数ベース" and not broadcast_days:
                QMessageBox.critical(
                    self, "エラー", "回数ベースの場合は放送曜日を選択してください"
                )
                return

            # 金額の変換
            try:
                amount_str = amount_str.replace(",", "").replace("円", "").strip()
                amount = float(amount_str)
            except ValueError:
                QMessageBox.critical(self, "エラー", "金額は数値で入力してください")
                return

            # データの設定
            is_new = master_id == "新規"
            data = {
                "project_name": project_name,
                "payee": payee,
                "payee_code": payee_code,
                "amount": amount,
                "payment_type": payment_type,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "broadcast_days": broadcast_days,
            }

            if not is_new:
                data["id"] = master_id

            # データベースに保存
            master_id = self.db_manager.save_master(data, is_new)

            # 更新完了メッセージ
            if is_new:
                message = f"新しい費用マスターデータを作成しました（ID: {master_id}）"
            else:
                message = f"費用マスターデータ ID: {master_id} を更新しました"

            log_message(message)
            self.app.status_label.setText(message)

            # テーブルを更新
            self.refresh_data()

            # 編集フォームを非表示
            self.edit_frame.hide()

        except Exception as e:
            log_message(f"費用マスターデータ保存中にエラー: {e}")
            QMessageBox.critical(
                self, "エラー", f"費用マスターデータの保存に失敗しました: {e}"
            )

    def cancel_direct_edit(self):
        """費用マスターテーブルの直接編集をキャンセル"""
        self.edit_frame.hide()

    def create_record(self):
        """新しい費用マスターレコードを直接編集フォームで作成"""
        try:
            # 選択解除
            self.tree.clearSelection()

            # 編集フォームの表示
            self.edit_frame.show()

            # フォームのクリア
            for field, widget in self.edit_entries.items():
                if field == "id":
                    widget.setText("新規")
                elif field == "payment_type":
                    index = widget.findText("月額固定")
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif field in ["start_date", "end_date"]:
                    widget.setDate(QDate.currentDate())
                else:
                    widget.setText("")

            # 放送曜日のチェックをクリア
            for day, checkbox in self.weekday_vars.items():
                checkbox.setChecked(False)

        except Exception as e:
            log_message(f"新規費用マスターレコード作成フォーム表示中にエラー: {e}")
            QMessageBox.critical(self, "エラー", f"フォーム表示に失敗しました: {e}")

    def delete_record(self):
        """選択された費用マスターレコード（複数可能）を削除"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "情報", "削除する費用マスターデータを選択してください"
            )
            return

        # 複数選択の場合の確認メッセージ
        if len(selected_items) == 1:
            master_id = selected_items[0].text(0)
            project_name = selected_items[0].text(1)
            confirm_message = f"費用マスターデータ「{project_name}（ID: {master_id}）」を削除しますか？"
        else:
            confirm_message = (
                f"選択された{len(selected_items)}件の費用マスターデータを削除しますか？"
            )

        # 確認ダイアログを表示
        reply = QMessageBox.question(
            self,
            "確認",
            confirm_message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 削除対象のID一覧
            deleted_ids = []

            # 選択された各項目を削除
            for item in selected_items:
                master_id = item.text(0)
                self.db_manager.delete_master(master_id)
                deleted_ids.append(master_id)

            deleted_count = len(deleted_ids)
            log_message(f"{deleted_count}件の費用マスターデータを削除しました")
            self.refresh_data()

            # 状態表示の更新
            if deleted_count == 1:
                self.app.status_label.setText(
                    f"費用マスターデータ ID: {deleted_ids[0]} を削除しました"
                )
            else:
                self.app.status_label.setText(
                    f"{deleted_count}件の費用マスターデータを削除しました"
                )

        except Exception as e:
            log_message(f"費用マスターデータ削除中にエラーが発生: {e}")
            QMessageBox.critical(
                self, "エラー", f"費用マスターデータの削除に失敗しました: {e}"
            )

    def duplicate_record(self):
        """選択された費用マスターレコードを複製"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "情報", "複製する費用マスターデータを選択してください"
            )
            return

        # 選択項目の値を取得
        selected_item = selected_items[0]
        master_id = selected_item.text(0)
        project_name = selected_item.text(1)

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"費用マスターデータ「{project_name}（ID: {master_id}）」を複製しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # データを複製
            new_id = self.db_manager.duplicate_master(master_id)

            if new_id:
                message = f"費用マスターデータを複製しました（新ID: {new_id}）"
                log_message(
                    f"費用マスターデータ ID: {master_id} を複製しました（新ID: {new_id}）"
                )
                self.refresh_data()
                self.app.status_label.setText(message)

                QMessageBox.information(self, "複製完了", message)
            else:
                QMessageBox.critical(self, "エラー", "選択されたデータが見つかりません")

        except Exception as e:
            log_message(f"費用マスターデータ複製中にエラーが発生: {e}")
            QMessageBox.critical(
                self, "エラー", f"費用マスターデータの複製に失敗しました: {e}"
            )

    def export_to_csv(self):
        """費用マスターデータをCSVファイルにエクスポート"""
        try:
            # データベースから全データを取得
            master_rows = self.db_manager.get_master_data()

            if not master_rows:
                QMessageBox.information(
                    self, "情報", "エクスポートするデータがありません"
                )
                return

            # 保存先のファイルを選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "費用マスターデータの保存先を選択",
                f"費用マスター_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
                        "種別",
                        "開始日",
                        "終了日",
                        "放送曜日",
                    ]
                )

                # データ行を書き込み
                for row in master_rows:
                    # 新しいフィールドがない古いデータの場合は、デフォルト値を使用
                    full_row = list(row)
                    if len(full_row) < 9:
                        full_row.extend(["月額固定", "", "", ""] * (9 - len(full_row)))
                    writer.writerow(full_row)

            log_message(f"費用マスターデータを{file_path}にエクスポートしました")
            self.app.status_label.setText(
                f"費用マスターデータを{os.path.basename(file_path)}にエクスポートしました"
            )

            # エクスポート後に確認メッセージを表示
            QMessageBox.information(
                self,
                "エクスポート完了",
                f"{len(master_rows)}件のデータを\n{os.path.basename(file_path)}\nにエクスポートしました",
            )

        except Exception as e:
            log_message(f"費用マスターデータのエクスポート中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            QMessageBox.critical(
                self, "エラー", f"費用マスターデータのエクスポートに失敗しました: {e}"
            )

    def import_from_csv(self):
        """CSVファイルから費用マスターデータをインポート（支払いコード0埋め対応）"""
        try:
            from utils import format_payee_code  # 追加

            # インポートするCSVファイルを選択
            file_path, _ = QFileDialog.getOpenFileName(
                self, "インポートするCSVファイルを選択", "", "CSVファイル (*.csv)"
            )

            if not file_path:
                return  # キャンセルされた場合

            # 確認ダイアログを表示
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

            # 追加/上書きモードの設定
            if result == QMessageBox.Yes:
                clear_existing = False
                operation_text = "追加"
            else:
                # 上書きモード - 再確認
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
                        # 基本データの取得
                        project_name = row[1]
                        payee = row[2]
                        payee_code = row[3]

                        # 【追加】支払い先コードの0埋め処理
                        if payee_code:
                            payee_code = format_payee_code(payee_code)

                        # 金額の変換
                        amount_str = row[4].replace(",", "").replace("円", "").strip()
                        amount = float(amount_str) if amount_str else 0

                        # 拡張データの取得
                        payment_type = row[5] if len(row) > 5 else "月額固定"
                        start_date = row[6] if len(row) > 6 else ""
                        end_date = row[7] if len(row) > 7 else ""
                        broadcast_days = row[8] if len(row) > 8 else ""

                        imported_rows.append(
                            (
                                project_name,
                                payee,
                                payee_code,
                                amount,
                                payment_type,
                                start_date,
                                end_date,
                                broadcast_days,
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
            import sqlite3

            conn = sqlite3.connect(self.db_manager.expense_master_db)
            cursor = conn.cursor()

            # 既存のデータをクリアする場合
            if clear_existing:
                cursor.execute("DELETE FROM expense_master")

            # データを挿入
            for row in imported_rows:
                cursor.execute(
                    """
                    INSERT INTO expense_master (
                        project_name, payee, payee_code, amount, payment_type, 
                        start_date, end_date, broadcast_days, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '未処理')
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
            log_message(f"費用マスターデータのインポート中にエラーが発生: {e}")
            import traceback

            log_message(traceback.format_exc())
            QMessageBox.critical(
                self, "エラー", f"費用マスターデータのインポートに失敗しました: {e}"
            )


# ファイル終了確認用のコメント - master_tab.py完了
