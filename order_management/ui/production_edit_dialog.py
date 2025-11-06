"""番組・イベント編集ダイアログ（出演者マスタ連携版）"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QMessageBox, QLabel,
    QRadioButton, QButtonGroup, QCheckBox, QListWidget, QComboBox, QWidget,
    QSizePolicy, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QDate, QTime
from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_list_item
from order_management.ui.cast_edit_dialog import CastEditDialog
from order_management.ui.producer_select_dialog import ProducerSelectDialog
from order_management.ui.expense_edit_dialog import ExpenseEditDialog


class ProductionEditDialog(QDialog):
    """番組・イベント編集ダイアログ"""

    def __init__(self, parent=None, production=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.production = production
        self.is_edit = production is not None

        self.setWindowTitle("番組・イベント編集" if self.is_edit else "新規登録")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        self._setup_ui()

        if self.is_edit:
            self._load_production_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        # フォーム
        form_layout = QFormLayout()
        # フィールドが必要に応じて拡大するように設定
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        # 行間のスペーシングを調整
        form_layout.setVerticalSpacing(12)
        # ラベルとフィールドの配置を調整
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 番組・イベント名
        self.name_edit = QLineEdit()
        form_layout.addRow("番組・イベント名 *:", self.name_edit)

        # 種別
        production_type_layout = QHBoxLayout()
        production_type_layout.setContentsMargins(0, 0, 0, 0)
        self.production_type_group = QButtonGroup()
        self.type_regular = QRadioButton("レギュラー番組")
        self.type_special = QRadioButton("特別番組")
        self.type_event = QRadioButton("イベント")
        self.type_public_broadcast = QRadioButton("公開放送")
        self.type_public_recording = QRadioButton("公開収録")
        self.type_special_project = QRadioButton("特別企画")
        self.type_regular.setMinimumWidth(120)
        self.type_special.setMinimumWidth(90)
        self.type_event.setMinimumWidth(90)
        self.type_public_broadcast.setMinimumWidth(90)
        self.type_public_recording.setMinimumWidth(90)
        self.type_special_project.setMinimumWidth(90)
        self.production_type_group.addButton(self.type_regular)
        self.production_type_group.addButton(self.type_special)
        self.production_type_group.addButton(self.type_event)
        self.production_type_group.addButton(self.type_public_broadcast)
        self.production_type_group.addButton(self.type_public_recording)
        self.production_type_group.addButton(self.type_special_project)
        self.type_regular.setChecked(True)
        self.type_regular.toggled.connect(self.on_production_type_changed)
        production_type_layout.addWidget(self.type_regular)
        production_type_layout.addWidget(self.type_special)
        production_type_layout.addWidget(self.type_event)
        production_type_layout.addWidget(self.type_public_broadcast)
        production_type_layout.addWidget(self.type_public_recording)
        production_type_layout.addWidget(self.type_special_project)
        production_type_layout.addStretch()

        production_type_widget = QWidget()
        production_type_widget.setLayout(production_type_layout)
        production_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        production_type_widget.setMinimumHeight(40)
        form_layout.addRow("種別:", production_type_widget)

        # 親制作物（特別番組等の場合のみ表示）
        self.parent_production_combo = QComboBox()
        self.parent_production_combo.setMinimumWidth(300)
        self.load_parent_productions()
        form_layout.addRow("親制作物:", self.parent_production_combo)
        self.parent_production_label = form_layout.labelForField(self.parent_production_combo)
        # 初期状態では非表示
        self.parent_production_combo.setVisible(False)
        self.parent_production_label.setVisible(False)

        # 備考
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("備考:", self.description_edit)

        # 開始日
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("開始日:", self.start_date_edit)

        # 終了日
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("終了日:", self.end_date_edit)

        # 実施開始時間（レギュラー以外用）
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(0, 0))
        form_layout.addRow("実施開始時間:", self.start_time_edit)
        self.start_time_label = form_layout.labelForField(self.start_time_edit)
        # 初期状態では非表示
        self.start_time_edit.setVisible(False)
        self.start_time_label.setVisible(False)

        # 実施終了時間（レギュラー以外用）
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(0, 0))
        form_layout.addRow("実施終了時間:", self.end_time_edit)
        self.end_time_label = form_layout.labelForField(self.end_time_edit)
        # 初期状態では非表示
        self.end_time_edit.setVisible(False)
        self.end_time_label.setVisible(False)

        # 放送時間（レギュラー番組用）
        self.broadcast_time_edit = QLineEdit()
        self.broadcast_time_edit.setPlaceholderText("例: 23:00-24:00")
        form_layout.addRow("放送時間:", self.broadcast_time_edit)
        self.broadcast_time_label = form_layout.labelForField(self.broadcast_time_edit)

        # 放送曜日（レギュラー番組用）
        broadcast_days_layout = QHBoxLayout()
        broadcast_days_layout.setContentsMargins(0, 0, 0, 0)
        self.day_checkboxes = {}
        for day in ["月", "火", "水", "木", "金", "土", "日"]:
            checkbox = QCheckBox(day)
            checkbox.setMinimumWidth(50)  # 最小幅を設定して切れないようにする
            self.day_checkboxes[day] = checkbox
            broadcast_days_layout.addWidget(checkbox)
        broadcast_days_layout.addStretch()

        broadcast_days_widget = QWidget()
        broadcast_days_widget.setLayout(broadcast_days_layout)
        broadcast_days_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        broadcast_days_widget.setMinimumHeight(40)
        form_layout.addRow("放送曜日:", broadcast_days_widget)
        self.broadcast_days_label = form_layout.labelForField(broadcast_days_widget)

        # ステータス
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_group = QButtonGroup()
        self.status_broadcasting = QRadioButton("放送中")
        self.status_ended = QRadioButton("終了")
        self.status_broadcasting.setMinimumWidth(80)  # 最小幅を設定
        self.status_ended.setMinimumWidth(80)  # 最小幅を設定
        self.status_group.addButton(self.status_broadcasting)
        self.status_group.addButton(self.status_ended)
        self.status_broadcasting.setChecked(True)
        status_layout.addWidget(self.status_broadcasting)
        status_layout.addWidget(self.status_ended)
        status_layout.addStretch()

        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        status_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_widget.setMinimumHeight(40)
        form_layout.addRow("ステータス:", status_widget)

        layout.addLayout(form_layout)

        # 出演者セクション
        cast_label = QLabel("出演者:")
        cast_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(cast_label)

        self.cast_list = QListWidget()
        self.cast_list.setMaximumHeight(120)
        layout.addWidget(self.cast_list)

        cast_button_layout = QHBoxLayout()
        self.add_cast_button = QPushButton("出演者追加")
        self.delete_cast_button = QPushButton("出演者削除")
        self.new_cast_button = QPushButton("新規出演者登録")
        self.add_cast_button.clicked.connect(self.add_cast)
        self.delete_cast_button.clicked.connect(self.delete_cast)
        self.new_cast_button.clicked.connect(self.create_new_cast)
        cast_button_layout.addWidget(self.add_cast_button)
        cast_button_layout.addWidget(self.delete_cast_button)
        cast_button_layout.addWidget(self.new_cast_button)
        cast_button_layout.addStretch()
        layout.addLayout(cast_button_layout)

        # 制作会社セクション
        producer_label = QLabel("制作会社:")
        producer_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(producer_label)

        self.producer_list = QListWidget()
        self.producer_list.setMaximumHeight(120)
        layout.addWidget(self.producer_list)

        producer_button_layout = QHBoxLayout()
        self.add_producer_button = QPushButton("制作会社追加")
        self.delete_producer_button = QPushButton("制作会社削除")
        self.add_producer_button.clicked.connect(self.add_producer)
        self.delete_producer_button.clicked.connect(self.delete_producer)
        producer_button_layout.addWidget(self.add_producer_button)
        producer_button_layout.addWidget(self.delete_producer_button)
        producer_button_layout.addStretch()
        layout.addLayout(producer_button_layout)

        # 費用項目セクション
        expense_label = QLabel("費用項目:")
        expense_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(expense_label)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(6)
        self.expense_table.setHorizontalHeaderLabels([
            "項目名", "金額（円）", "発注先", "ステータス", "実施日", "支払予定日"
        ])
        self.expense_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.expense_table.setMaximumHeight(150)
        self.expense_table.doubleClicked.connect(self.edit_expense)

        # カラム幅の設定
        header = self.expense_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 項目名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 発注先
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ステータス
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 実施日
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 支払予定日

        layout.addWidget(self.expense_table)

        expense_button_layout = QHBoxLayout()
        self.add_expense_button = QPushButton("費用項目を追加")
        self.edit_expense_button = QPushButton("編集")
        self.delete_expense_button = QPushButton("削除")
        self.add_expense_button.clicked.connect(self.add_expense)
        self.edit_expense_button.clicked.connect(self.edit_expense)
        self.delete_expense_button.clicked.connect(self.delete_expense)
        expense_button_layout.addWidget(self.add_expense_button)
        expense_button_layout.addWidget(self.edit_expense_button)
        expense_button_layout.addWidget(self.delete_expense_button)
        expense_button_layout.addStretch()
        layout.addLayout(expense_button_layout)

        # ボタン
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("キャンセル")
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # データ保持
        self.cast_data = []  # [{'cast_id': 1, 'role': 'MC'}, ...]
        self.producer_data = []  # [{'id': partner_id, 'name': '会社名'}, ...]
        self.expense_data = []  # [{'id': expense_id, 'item_name': '制作費', ...}, ...]

    def on_production_type_changed(self):
        """種別変更時の処理"""
        is_regular = self.type_regular.isChecked()

        # レギュラー番組の場合は放送時間・放送曜日を表示
        self.broadcast_time_edit.setVisible(is_regular)
        self.broadcast_time_label.setVisible(is_regular)
        for checkbox in self.day_checkboxes.values():
            checkbox.setVisible(is_regular)
        self.broadcast_days_label.setVisible(is_regular)

        # レギュラー番組以外の場合は実施時間を表示
        self.start_time_edit.setVisible(not is_regular)
        self.start_time_label.setVisible(not is_regular)
        self.end_time_edit.setVisible(not is_regular)
        self.end_time_label.setVisible(not is_regular)

        # 特別番組等の場合は親制作物を表示
        show_parent = not is_regular
        self.parent_production_combo.setVisible(show_parent)
        self.parent_production_label.setVisible(show_parent)

    def load_parent_productions(self):
        """親制作物一覧を読み込み（レギュラー番組のみ親になれる）"""
        productions = self.db.get_productions_with_hierarchy(include_children=False)
        self.parent_production_combo.clear()
        self.parent_production_combo.addItem("（親制作物なし）", None)

        for production in productions:
            # production: (id, name, description, production_type, start_date, end_date,
            #              start_time, end_time, broadcast_time, broadcast_days, status, parent_production_id)
            production_type = production[3] if len(production) > 3 else "レギュラー番組"

            # 自分自身を除外（編集時）
            if self.is_edit and production[0] == self.production[0]:
                continue

            # レギュラー番組のみ親になれる
            if production_type != "レギュラー番組":
                continue

            self.parent_production_combo.addItem(production[1], production[0])

    def _load_production_data(self):
        """制作物データを読み込み"""
        if not self.production:
            return

        # get_production_by_id returns: (id, name, description, production_type, start_date, end_date,
        #                                 start_time, end_time, broadcast_time, broadcast_days, status, parent_production_id)
        self.name_edit.setText(self.production[1] or "")
        self.description_edit.setPlainText(self.production[2] or "")

        # 種別を設定（インデックス3: production_type）
        if len(self.production) > 3 and self.production[3]:
            production_type = self.production[3]
            if production_type == "特別番組":
                self.type_special.setChecked(True)
            elif production_type == "イベント":
                self.type_event.setChecked(True)
            elif production_type == "公開放送":
                self.type_public_broadcast.setChecked(True)
            elif production_type == "公開収録":
                self.type_public_recording.setChecked(True)
            elif production_type == "特別企画":
                self.type_special_project.setChecked(True)
            else:
                self.type_regular.setChecked(True)

        # 開始日・終了日を設定（インデックス4, 5）
        if len(self.production) > 4 and self.production[4]:
            self.start_date_edit.setDate(QDate.fromString(self.production[4], "yyyy-MM-dd"))
        if len(self.production) > 5 and self.production[5]:
            self.end_date_edit.setDate(QDate.fromString(self.production[5], "yyyy-MM-dd"))

        # 実施時間を設定（インデックス6, 7: start_time, end_time）
        if len(self.production) > 6 and self.production[6]:
            self.start_time_edit.setTime(QTime.fromString(self.production[6], "HH:mm:ss"))
        if len(self.production) > 7 and self.production[7]:
            self.end_time_edit.setTime(QTime.fromString(self.production[7], "HH:mm:ss"))

        # 放送時間を設定（インデックス8: broadcast_time）
        if len(self.production) > 8:
            self.broadcast_time_edit.setText(self.production[8] or "")

        # 放送曜日を設定（インデックス9: broadcast_days）
        if len(self.production) > 9:
            broadcast_days = self.production[9] or ""
            if broadcast_days:
                for day in broadcast_days.split(","):
                    if day in self.day_checkboxes:
                        self.day_checkboxes[day].setChecked(True)

        # ステータスを設定（インデックス10: status）
        if len(self.production) > 10 and self.production[10] == "終了":
            self.status_ended.setChecked(True)

        # 親制作物を設定（インデックス11: parent_production_id）
        if len(self.production) > 11 and self.production[11]:
            parent_production_id = self.production[11]
            for i in range(self.parent_production_combo.count()):
                if self.parent_production_combo.itemData(i) == parent_production_id:
                    self.parent_production_combo.setCurrentIndex(i)
                    break

        # 出演者を読み込み
        production_id = self.production[0]
        cast_list = self.db.get_production_cast(production_id)
        for cast in cast_list:
            # cast: (production_cast.id, cast_id, cast_name, partner_name, role)
            cast_data = {'cast_id': cast[1], 'role': cast[4] or ""}
            self.cast_data.append(cast_data)
            display_text = f"{cast[2]} ({cast[3]})"
            if cast[4]:
                display_text += f" - {cast[4]}"
            item = create_list_item(display_text, cast_data)
            self.cast_list.addItem(item)

        # 制作会社を読み込み
        producer_list = self.db.get_production_producers(production_id)
        for producer in producer_list:
            producer_data = {'id': producer[1], 'name': producer[2]}
            self.producer_data.append(producer_data)
            item = create_list_item(producer_data['name'], producer_data)
            self.producer_list.addItem(item)

        # 費用項目を読み込み
        self._load_expenses()

    def add_cast(self):
        """出演者追加（出演者マスタから選択）"""
        dialog = CastSelectDialog(self)
        if dialog.exec_():
            selected_casts = dialog.get_selected_casts()
            for cast in selected_casts:
                # 既に追加済みかチェック
                already_added = any(c['cast_id'] == cast['id'] for c in self.cast_data)
                if already_added:
                    continue

                # 役割を入力
                from PyQt5.QtWidgets import QInputDialog
                role, ok = QInputDialog.getText(self, "役割入力", f"{cast['name']}の役割（任意）:")

                cast_data = {'cast_id': cast['id'], 'role': role if ok else ""}
                self.cast_data.append(cast_data)

                display_text = f"{cast['name']} ({cast['partner_name']})"
                if role and ok:
                    display_text += f" - {role}"
                item = create_list_item(display_text, cast_data)
                self.cast_list.addItem(item)

    def delete_cast(self):
        """出演者削除"""
        current_item = self.cast_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "削除する出演者を選択してください")
            return

        cast_data = current_item.data(Qt.UserRole)
        row = self.cast_list.row(current_item)
        self.cast_list.takeItem(row)
        self.cast_data.remove(cast_data)

    def create_new_cast(self):
        """新規出演者登録"""
        dialog = CastEditDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "完了", "出演者を登録しました。「出演者追加」から選択してください。")

    def add_producer(self):
        """制作会社追加"""
        dialog = ProducerSelectDialog(self)
        if dialog.exec_():
            selected_partners = dialog.get_selected_partners()
            for partner in selected_partners:
                already_added = any(p['id'] == partner['id'] for p in self.producer_data)
                if not already_added:
                    self.producer_data.append(partner)
                    item = create_list_item(partner['name'], partner)
                    self.producer_list.addItem(item)

    def delete_producer(self):
        """制作会社削除"""
        selected_items = self.producer_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "削除する制作会社を選択してください")
            return

        for item in selected_items:
            producer_data = item.data(Qt.UserRole)
            row = self.producer_list.row(item)
            self.producer_list.takeItem(row)
            self.producer_data.remove(producer_data)

    def _load_expenses(self):
        """費用項目を読み込んでテーブルに表示"""
        if not self.is_edit:
            return

        production_id = self.production[0]
        expenses = self.db.get_expenses_by_production(production_id)

        self.expense_data = []
        self.expense_table.setRowCount(0)

        for expense in expenses:
            # expense: (id, production_id, item_name, amount, supplier_id, contact_person,
            #          status, order_number, implementation_date, invoice_received_date)
            expense_id = expense[0]

            # 詳細情報を取得
            expense_detail = self.db.get_expense_order_by_id(expense_id)
            if not expense_detail:
                continue

            # 発注先名を取得
            supplier_name = ""
            if expense_detail[4]:  # supplier_id
                supplier = self.db.get_partner_by_id(expense_detail[4])
                if supplier:
                    supplier_name = supplier[1]

            expense_data = {
                'id': expense_id,
                'item_name': expense_detail[2] or "",
                'amount': expense_detail[3] or 0,
                'supplier_id': expense_detail[4],
                'supplier_name': supplier_name,
                'contact_person': expense_detail[5] or "",
                'status': expense_detail[6] or "",
                'implementation_date': expense_detail[9] or "",
                'payment_scheduled_date': expense_detail[11] or "",
                'notes': expense_detail[16] or ""
            }
            self.expense_data.append(expense_data)
            self._add_expense_to_table(expense_data)

    def _add_expense_to_table(self, expense_data):
        """テーブルに費用項目を追加"""
        row = self.expense_table.rowCount()
        self.expense_table.insertRow(row)

        self.expense_table.setItem(row, 0, QTableWidgetItem(expense_data['item_name']))
        self.expense_table.setItem(row, 1, QTableWidgetItem(f"{expense_data['amount']:,.0f}"))
        self.expense_table.setItem(row, 2, QTableWidgetItem(expense_data['supplier_name']))
        self.expense_table.setItem(row, 3, QTableWidgetItem(expense_data['status']))
        self.expense_table.setItem(row, 4, QTableWidgetItem(expense_data['implementation_date']))
        self.expense_table.setItem(row, 5, QTableWidgetItem(expense_data['payment_scheduled_date']))

        # 行にデータを保存
        for col in range(6):
            item = self.expense_table.item(row, col)
            if item:
                item.setData(Qt.UserRole, expense_data)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def add_expense(self):
        """費用項目を追加"""
        if not self.is_edit:
            QMessageBox.warning(self, "警告", "番組を保存してから費用項目を追加してください")
            return

        production_id = self.production[0]
        dialog = ExpenseEditDialog(self, production_id=production_id)
        if dialog.exec_():
            # データを保存
            expense_input = dialog.get_data()
            try:
                expense_id = self.db.save_expense_order(expense_input, is_new=True)

                # テーブルに追加
                expense_detail = self.db.get_expense_order_by_id(expense_id)
                if expense_detail:
                    supplier_name = ""
                    if expense_detail[4]:
                        supplier = self.db.get_partner_by_id(expense_detail[4])
                        if supplier:
                            supplier_name = supplier[1]

                    expense_data = {
                        'id': expense_id,
                        'item_name': expense_detail[2] or "",
                        'amount': expense_detail[3] or 0,
                        'supplier_id': expense_detail[4],
                        'supplier_name': supplier_name,
                        'contact_person': expense_detail[5] or "",
                        'status': expense_detail[6] or "",
                        'implementation_date': expense_detail[9] or "",
                        'payment_scheduled_date': expense_detail[11] or "",
                        'notes': expense_detail[16] or ""
                    }
                    self.expense_data.append(expense_data)
                    self._add_expense_to_table(expense_data)

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"費用項目の追加に失敗しました:\n{str(e)}")

    def edit_expense(self):
        """費用項目を編集"""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する費用項目を選択してください")
            return

        item = self.expense_table.item(current_row, 0)
        if not item:
            return

        expense_data = item.data(Qt.UserRole)
        expense_id = expense_data['id']

        dialog = ExpenseEditDialog(self, expense_id=expense_id)
        if dialog.exec_():
            # データを保存
            expense_input = dialog.get_data()
            try:
                self.db.save_expense_order(expense_input, is_new=False)
                # データを再読み込み
                self._load_expenses()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"費用項目の更新に失敗しました:\n{str(e)}")

    def delete_expense(self):
        """費用項目を削除"""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する費用項目を選択してください")
            return

        item = self.expense_table.item(current_row, 0)
        if not item:
            return

        expense_data = item.data(Qt.UserRole)
        expense_id = expense_data['id']
        item_name = expense_data['item_name']

        reply = QMessageBox.question(
            self, "確認",
            f"費用項目「{item_name}」を削除してもよろしいですか？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_expense_order(expense_id)
                self.expense_table.removeRow(current_row)
                self.expense_data = [e for e in self.expense_data if e['id'] != expense_id]
                QMessageBox.information(self, "成功", "費用項目を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")

    def save(self):
        """保存"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "番組・イベント名は必須です")
            return

        selected_days = [day for day, cb in self.day_checkboxes.items() if cb.isChecked()]
        status = "放送中" if self.status_broadcasting.isChecked() else "終了"

        # 種別を決定
        if self.type_special.isChecked():
            production_type = "特別番組"
        elif self.type_event.isChecked():
            production_type = "イベント"
        elif self.type_public_broadcast.isChecked():
            production_type = "公開放送"
        elif self.type_public_recording.isChecked():
            production_type = "公開収録"
        elif self.type_special_project.isChecked():
            production_type = "特別企画"
        else:
            production_type = "レギュラー番組"

        # 親制作物IDを取得
        parent_production_id = self.parent_production_combo.currentData()

        production_data = {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'production_type': production_type,
            'start_date': self.start_date_edit.date().toString("yyyy-MM-dd") if self.start_date_edit.date().isValid() else None,
            'end_date': self.end_date_edit.date().toString("yyyy-MM-dd") if self.end_date_edit.date().isValid() else None,
            'start_time': self.start_time_edit.time().toString("HH:mm:ss") if not self.type_regular.isChecked() else None,
            'end_time': self.end_time_edit.time().toString("HH:mm:ss") if not self.type_regular.isChecked() else None,
            'broadcast_time': self.broadcast_time_edit.text().strip() if self.type_regular.isChecked() else None,
            'broadcast_days': ",".join(selected_days) if self.type_regular.isChecked() else None,
            'status': status,
            'parent_production_id': parent_production_id
        }

        if self.is_edit:
            production_data['id'] = self.production[0]

        try:
            production_id = self.db.save_production(production_data, is_new=not self.is_edit)

            # 出演者を保存
            self.db.save_production_cast(production_id, self.cast_data)

            # 制作会社を保存
            producer_ids = [p['id'] for p in self.producer_data]
            self.db.save_production_producers(production_id, producer_ids)

            self.accept()
        except Exception as e:
            error_msg = str(e)
            # UNIQUE constraint違反の場合
            if 'UNIQUE constraint failed' in error_msg or 'UNIQUE' in error_msg:
                QMessageBox.warning(
                    self, "名前が重複",
                    f"番組・イベント名「{production_data['name']}」は既に登録されています。\n"
                    f"別の名前を使用してください。"
                )
            else:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {error_msg}")

    def get_data(self):
        """データ取得（互換性のため）"""
        return {}


class CastSelectDialog(QDialog):
    """出演者選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()

        self.setWindowTitle("出演者選択")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_casts()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._load_casts)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # リスト
        self.cast_list = QListWidget()
        self.cast_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.cast_list)

        # ボタン
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("選択")
        self.cancel_button = QPushButton("キャンセル")
        self.select_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _load_casts(self):
        """出演者を読み込み"""
        search_term = self.search_edit.text()
        casts = self.db.get_casts(search_term)

        self.cast_list.clear()
        for cast in casts:
            # cast: (id, name, partner_name, partner_code, notes)
            display_text = f"{cast[1]} ({cast[2]})"
            cast_data = {'id': cast[0], 'name': cast[1], 'partner_name': cast[2]}
            item = create_list_item(display_text, cast_data)
            self.cast_list.addItem(item)

    def get_selected_casts(self):
        """選択された出演者を取得"""
        selected_items = self.cast_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items]
