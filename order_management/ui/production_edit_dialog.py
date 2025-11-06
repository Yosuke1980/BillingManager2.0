"""番組・イベント編集ダイアログ（タブ形式）"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QLabel,
    QRadioButton, QButtonGroup, QCheckBox, QListWidget, QComboBox, QWidget,
    QSizePolicy, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QTime
from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_list_item
from order_management.ui.custom_date_edit import ImprovedDateEdit
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
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)

        self._setup_ui()

        if self.is_edit:
            self._load_production_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        # タブウィジェット作成
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 各タブを作成
        self._create_basic_info_tab()
        self._create_cast_tab()
        self._create_producer_tab()
        self._create_expense_tab()

        # 保存・キャンセルボタン
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
        self.cast_data = []
        self.producer_data = []
        self.expense_data = []

    def _create_basic_info_tab(self):
        """基本情報タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

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
        self.start_date_edit = ImprovedDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("開始日:", self.start_date_edit)

        # 終了日
        self.end_date_edit = ImprovedDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
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
        layout.addStretch()

        # タブに追加
        self.tab_widget.addTab(tab, "📝 基本情報")

    def _create_cast_tab(self):
        """出演者タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 出演者テーブル（フル画面使用）
        self.cast_table = QTableWidget()
        self.cast_table.setColumnCount(7)
        self.cast_table.setHorizontalHeaderLabels([
            "出演者名", "役割", "事務所", "契約項目", "金額（円）", "ステータス", "支払サイト"
        ])
        self.cast_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cast_table.doubleClicked.connect(self.edit_cast_contract)

        # カラム幅の設定
        header = self.cast_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 出演者名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 役割
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 事務所
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 契約項目
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # ステータス
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 支払サイト

        layout.addWidget(self.cast_table)

        # ボタン
        cast_button_layout = QHBoxLayout()
        self.add_cast_button = QPushButton("出演者を追加")
        self.add_cast_contract_button = QPushButton("契約を追加")
        self.edit_cast_contract_button = QPushButton("編集")
        self.delete_cast_button = QPushButton("削除")
        self.new_cast_button = QPushButton("新規出演者登録")
        self.add_cast_button.clicked.connect(self.add_cast)
        self.add_cast_contract_button.clicked.connect(self.add_cast_contract)
        self.edit_cast_contract_button.clicked.connect(self.edit_cast_contract)
        self.delete_cast_button.clicked.connect(self.delete_cast)
        self.new_cast_button.clicked.connect(self.create_new_cast)
        cast_button_layout.addWidget(self.add_cast_button)
        cast_button_layout.addWidget(self.add_cast_contract_button)
        cast_button_layout.addWidget(self.edit_cast_contract_button)
        cast_button_layout.addWidget(self.delete_cast_button)
        cast_button_layout.addWidget(self.new_cast_button)
        cast_button_layout.addStretch()
        layout.addLayout(cast_button_layout)

        # タブに追加
        self.tab_widget.addTab(tab, "👥 出演者")

    def _create_producer_tab(self):
        """制作会社タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 制作会社テーブル（フル画面使用）
        self.producer_table = QTableWidget()
        self.producer_table.setColumnCount(6)
        self.producer_table.setHorizontalHeaderLabels([
            "制作会社名", "契約項目", "金額（円）", "ステータス", "支払サイト", "操作"
        ])
        self.producer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.producer_table.doubleClicked.connect(self.edit_producer_contract)

        # カラム幅の設定
        header = self.producer_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 制作会社名
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 契約項目
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ステータス
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 支払サイト
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 操作

        layout.addWidget(self.producer_table)

        # ボタン
        producer_button_layout = QHBoxLayout()
        self.add_producer_button = QPushButton("制作会社を追加")
        self.add_producer_contract_button = QPushButton("契約を追加")
        self.edit_producer_contract_button = QPushButton("編集")
        self.delete_producer_button = QPushButton("削除")
        self.add_producer_button.clicked.connect(self.add_producer)
        self.add_producer_contract_button.clicked.connect(self.add_producer_contract)
        self.edit_producer_contract_button.clicked.connect(self.edit_producer_contract)
        self.delete_producer_button.clicked.connect(self.delete_producer)
        producer_button_layout.addWidget(self.add_producer_button)
        producer_button_layout.addWidget(self.add_producer_contract_button)
        producer_button_layout.addWidget(self.edit_producer_contract_button)
        producer_button_layout.addWidget(self.delete_producer_button)
        producer_button_layout.addStretch()
        layout.addLayout(producer_button_layout)

        # タブに追加
        self.tab_widget.addTab(tab, "🏢 制作会社")

    def _create_expense_tab(self):
        """費用項目タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 費用項目テーブル（フル画面使用）
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(6)
        self.expense_table.setHorizontalHeaderLabels([
            "項目名", "金額（円）", "発注先", "ステータス", "実施日", "支払予定日"
        ])
        self.expense_table.setSelectionBehavior(QTableWidget.SelectRows)
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

        # 合計金額表示
        self.expense_total_label = QLabel("合計金額: ¥0")
        self.expense_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.expense_total_label)

        # ボタン
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

        # タブに追加
        self.tab_widget.addTab(tab, "💰 費用項目")

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
        self._load_cast_data()

        # 制作会社を読み込み
        self._load_producer_data()

        # 費用項目を読み込み
        self._load_expenses()

    def _load_cast_data(self):
        """出演者と契約情報を読み込んでテーブルに表示"""
        if not self.is_edit:
            return

        production_id = self.production[0]
        cast_with_contracts = self.db.get_production_cast_with_contracts(production_id)

        self.cast_data = []
        self.cast_table.setRowCount(0)

        # 出演者ごとにグループ化
        cast_groups = {}
        for row in cast_with_contracts:
            # row: (production_cast_id, cast_id, cast_name, role, partner_id, partner_name,
            #       contract_id, item_name, unit_price, order_status, payment_timing,
            #       contract_start_date, contract_end_date)
            production_cast_id = row[0]
            cast_id = row[1]
            cast_name = row[2]
            role = row[3] or ""
            partner_id = row[4]
            partner_name = row[5]
            contract_id = row[6]

            if cast_id not in cast_groups:
                cast_groups[cast_id] = {
                    'production_cast_id': production_cast_id,
                    'cast_id': cast_id,
                    'cast_name': cast_name,
                    'role': role,
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'contracts': []
                }
                # cast_data用のデータも保存
                self.cast_data.append({'cast_id': cast_id, 'role': role})

            # 契約情報を追加
            if contract_id:
                contract_info = {
                    'contract_id': contract_id,
                    'item_name': row[7] or "",
                    'unit_price': row[8] or 0,
                    'order_status': row[9] or "",
                    'payment_timing': row[10] or "",
                }
                cast_groups[cast_id]['contracts'].append(contract_info)

        # テーブルに表示
        for cast_id, cast_info in cast_groups.items():
            contracts = cast_info['contracts']
            if not contracts:
                # 契約がない場合
                row = self.cast_table.rowCount()
                self.cast_table.insertRow(row)
                self.cast_table.setItem(row, 0, QTableWidgetItem(cast_info['cast_name']))
                self.cast_table.setItem(row, 1, QTableWidgetItem(cast_info['role']))
                self.cast_table.setItem(row, 2, QTableWidgetItem(cast_info['partner_name']))
                self.cast_table.setItem(row, 3, QTableWidgetItem("(契約なし)"))
                self.cast_table.setItem(row, 4, QTableWidgetItem(""))
                self.cast_table.setItem(row, 5, QTableWidgetItem(""))
                self.cast_table.setItem(row, 6, QTableWidgetItem(""))

                # データを保存
                for col in range(7):
                    item = self.cast_table.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, {
                            'production_cast_id': cast_info['production_cast_id'],
                            'cast_id': cast_info['cast_id'],
                            'partner_id': cast_info['partner_id'],
                            'contract_id': None
                        })
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                # 契約がある場合
                start_row = self.cast_table.rowCount()
                for i, contract in enumerate(contracts):
                    row = self.cast_table.rowCount()
                    self.cast_table.insertRow(row)

                    # すべての行に出演者情報を設定（rowSpanで表示は統合される）
                    self.cast_table.setItem(row, 0, QTableWidgetItem(cast_info['cast_name']))
                    self.cast_table.setItem(row, 1, QTableWidgetItem(cast_info['role']))
                    self.cast_table.setItem(row, 2, QTableWidgetItem(cast_info['partner_name']))

                    # 契約情報を表示
                    self.cast_table.setItem(row, 3, QTableWidgetItem(contract['item_name']))
                    self.cast_table.setItem(row, 4, QTableWidgetItem(f"{contract['unit_price']:,.0f}"))
                    self.cast_table.setItem(row, 5, QTableWidgetItem(contract['order_status']))
                    self.cast_table.setItem(row, 6, QTableWidgetItem(contract['payment_timing']))

                    # データを保存
                    for col in range(7):
                        item = self.cast_table.item(row, col)
                        if item:
                            item.setData(Qt.UserRole, {
                                'production_cast_id': cast_info['production_cast_id'],
                                'cast_id': cast_info['cast_id'],
                                'partner_id': cast_info['partner_id'],
                                'contract_id': contract['contract_id']
                            })
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                # rowSpanでマージ（表示上は統合されるが、データはすべての行に保存されている）
                if len(contracts) > 1:
                    self.cast_table.setSpan(start_row, 0, len(contracts), 1)  # 出演者名
                    self.cast_table.setSpan(start_row, 1, len(contracts), 1)  # 役割
                    self.cast_table.setSpan(start_row, 2, len(contracts), 1)  # 事務所

    def add_cast(self):
        """出演者追加（出演者マスタから選択）"""
        if not self.is_edit:
            QMessageBox.warning(self, "警告", "番組を保存してから出演者を追加してください")
            return

        dialog = CastSelectDialog(self)
        if dialog.exec_():
            selected_casts = dialog.get_selected_casts()
            for cast in selected_casts:
                # 既に追加済みかチェック
                already_added = any(c['cast_id'] == cast['id'] for c in self.cast_data)
                if already_added:
                    QMessageBox.warning(self, "警告", f"{cast['name']}は既に追加されています")
                    continue

                # 役割を入力
                from PyQt5.QtWidgets import QInputDialog
                role, ok = QInputDialog.getText(self, "役割入力", f"{cast['name']}の役割（任意）:")
                if not ok:
                    continue

                # 出演者を保存
                cast_data = {'cast_id': cast['id'], 'role': role}
                self.cast_data.append(cast_data)
                production_id = self.production[0]
                self.db.save_production_cast(production_id, self.cast_data)

                # 契約作成確認
                reply = QMessageBox.question(
                    self, "契約の作成",
                    f"出演者「{cast['name']}」を追加しました。\n\nこの出演者の契約も作成しますか？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )

                if reply == QMessageBox.Yes:
                    # 契約編集ダイアログを開く
                    from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
                    # 出演者の事務所（partner_id）を取得
                    cast_info = self.db.get_cast_by_id(cast['id'])
                    if cast_info:
                        partner_id = cast_info[2]  # cast: (id, name, partner_id, notes, created_at, updated_at)
                        contract_dialog = OrderContractEditDialog(
                            self,
                            production_id=production_id,
                            partner_id=partner_id,
                            work_type='出演'
                        )
                        if contract_dialog.exec_():
                            QMessageBox.information(self, "成功", "契約を作成しました")
                elif reply == QMessageBox.Cancel:
                    # キャンセルの場合、出演者も削除
                    self.cast_data.remove(cast_data)
                    self.db.save_production_cast(production_id, self.cast_data)
                    continue

                # データを再読み込み
                self._load_cast_data()
                # 費用項目も更新
                self._load_expenses()

    def _load_producer_data(self):
        """制作会社と契約情報を読み込んでテーブルに表示"""
        if not self.is_edit:
            return

        production_id = self.production[0]
        producer_with_contracts = self.db.get_production_producers_with_contracts(production_id)

        self.producer_data = []
        self.producer_table.setRowCount(0)

        # 制作会社ごとにグループ化
        producer_groups = {}
        for row in producer_with_contracts:
            # row: (production_producer_id, partner_id, partner_name,
            #       contract_id, item_name, unit_price, order_status, payment_timing,
            #       contract_start_date, contract_end_date)
            production_producer_id = row[0]
            partner_id = row[1]
            partner_name = row[2]
            contract_id = row[3]

            if partner_id not in producer_groups:
                producer_groups[partner_id] = {
                    'production_producer_id': production_producer_id,
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'contracts': []
                }
                # producer_data用のデータも保存
                self.producer_data.append({'id': partner_id, 'name': partner_name})

            # 契約情報を追加
            if contract_id:
                contract_info = {
                    'contract_id': contract_id,
                    'item_name': row[4] or "",
                    'unit_price': row[5] or 0,
                    'order_status': row[6] or "",
                    'payment_timing': row[7] or "",
                }
                producer_groups[partner_id]['contracts'].append(contract_info)

        # テーブルに表示
        for partner_id, producer_info in producer_groups.items():
            contracts = producer_info['contracts']
            if not contracts:
                # 契約がない場合
                row = self.producer_table.rowCount()
                self.producer_table.insertRow(row)
                self.producer_table.setItem(row, 0, QTableWidgetItem(producer_info['partner_name']))
                self.producer_table.setItem(row, 1, QTableWidgetItem("(契約なし)"))
                self.producer_table.setItem(row, 2, QTableWidgetItem(""))
                self.producer_table.setItem(row, 3, QTableWidgetItem(""))
                self.producer_table.setItem(row, 4, QTableWidgetItem(""))
                self.producer_table.setItem(row, 5, QTableWidgetItem(""))

                # データを保存
                for col in range(6):
                    item = self.producer_table.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, {
                            'production_producer_id': producer_info['production_producer_id'],
                            'partner_id': producer_info['partner_id'],
                            'contract_id': None
                        })
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                # 契約がある場合
                start_row = self.producer_table.rowCount()
                for i, contract in enumerate(contracts):
                    row = self.producer_table.rowCount()
                    self.producer_table.insertRow(row)

                    # すべての行に制作会社名を設定（rowSpanで表示は統合される）
                    self.producer_table.setItem(row, 0, QTableWidgetItem(producer_info['partner_name']))

                    # 契約情報を表示
                    self.producer_table.setItem(row, 1, QTableWidgetItem(contract['item_name']))
                    self.producer_table.setItem(row, 2, QTableWidgetItem(f"{contract['unit_price']:,.0f}"))
                    self.producer_table.setItem(row, 3, QTableWidgetItem(contract['order_status']))
                    self.producer_table.setItem(row, 4, QTableWidgetItem(contract['payment_timing']))
                    self.producer_table.setItem(row, 5, QTableWidgetItem(""))

                    # データを保存
                    for col in range(6):
                        item = self.producer_table.item(row, col)
                        if item:
                            item.setData(Qt.UserRole, {
                                'production_producer_id': producer_info['production_producer_id'],
                                'partner_id': producer_info['partner_id'],
                                'contract_id': contract['contract_id']
                            })
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                # rowSpanでマージ（表示上は統合されるが、データはすべての行に保存されている）
                if len(contracts) > 1:
                    self.producer_table.setSpan(start_row, 0, len(contracts), 1)  # 制作会社名

    def add_cast_contract(self):
        """選択された出演者に契約を追加"""
        if not self.is_edit:
            QMessageBox.warning(self, "警告", "番組を保存してから契約を追加してください")
            return

        current_row = self.cast_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "出演者を選択してください")
            return

        item = self.cast_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        production_id = self.production[0]
        partner_id = data['partner_id']

        # 契約編集ダイアログを開く
        from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
        contract_dialog = OrderContractEditDialog(
            self,
            production_id=production_id,
            partner_id=partner_id,
            work_type='出演'
        )
        if contract_dialog.exec_():
            QMessageBox.information(self, "成功", "契約を作成しました")
            # データを再読み込み
            self._load_cast_data()
            self._load_expenses()

    def edit_cast_contract(self):
        """選択された契約を編集"""
        current_row = self.cast_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する契約を選択してください")
            return

        item = self.cast_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        contract_id = data.get('contract_id')

        if not contract_id:
            QMessageBox.warning(self, "警告", "契約が選択されていません")
            return

        # 契約編集ダイアログを開く
        from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
        contract_dialog = OrderContractEditDialog(self, contract_id=contract_id)
        if contract_dialog.exec_():
            QMessageBox.information(self, "成功", "契約を更新しました")
            # データを再読み込み
            self._load_cast_data()
            self._load_expenses()

    def delete_cast(self):
        """出演者削除（契約も削除）"""
        if not self.is_edit:
            return

        current_row = self.cast_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する出演者を選択してください")
            return

        item = self.cast_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        production_cast_id = data['production_cast_id']
        production_id = self.production[0]
        partner_id = data['partner_id']

        # 関連する契約を取得
        contracts = self.db.get_contracts_by_production_and_partner(production_id, partner_id)

        # 確認ダイアログ
        cast_name = self.cast_table.item(current_row, 0).text() if self.cast_table.item(current_row, 0) else "この出演者"
        message = f"出演者「{cast_name}」を削除すると、"
        if contracts:
            message += "以下の契約も削除されます：\n\n"
            for contract in contracts:
                # contract: (contract_id, item_name, unit_price, order_status, payment_timing)
                message += f"・{contract[1]}: ¥{contract[2]:,.0f}\n"
        else:
            message += "契約はありません。\n"
        message += "\n本当に削除してもよろしいですか？"

        reply = QMessageBox.question(
            self, "確認",
            message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_cast_from_production(production_cast_id, production_id, partner_id)
                QMessageBox.information(self, "成功", "出演者と契約を削除しました")
                # データを再読み込み
                self._load_cast_data()
                self._load_expenses()
                # cast_dataも更新
                self.cast_data = [c for c in self.cast_data if c['cast_id'] != data['cast_id']]
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")

    def create_new_cast(self):
        """新規出演者登録"""
        dialog = CastEditDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "完了", "出演者を登録しました。「出演者追加」から選択してください。")

    def add_producer(self):
        """制作会社追加"""
        if not self.is_edit:
            QMessageBox.warning(self, "警告", "番組を保存してから制作会社を追加してください")
            return

        dialog = ProducerSelectDialog(self)
        if dialog.exec_():
            selected_partners = dialog.get_selected_partners()
            for partner in selected_partners:
                already_added = any(p['id'] == partner['id'] for p in self.producer_data)
                if already_added:
                    QMessageBox.warning(self, "警告", f"{partner['name']}は既に追加されています")
                    continue

                # 制作会社を保存
                self.producer_data.append(partner)
                production_id = self.production[0]
                producer_ids = [p['id'] for p in self.producer_data]
                self.db.save_production_producers(production_id, producer_ids)

                # 契約作成確認
                reply = QMessageBox.question(
                    self, "契約の作成",
                    f"制作会社「{partner['name']}」を追加しました。\n\nこの制作会社の契約も作成しますか？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )

                if reply == QMessageBox.Yes:
                    # 契約編集ダイアログを開く
                    from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
                    contract_dialog = OrderContractEditDialog(
                        self,
                        production_id=production_id,
                        partner_id=partner['id'],
                        work_type='制作'
                    )
                    if contract_dialog.exec_():
                        QMessageBox.information(self, "成功", "契約を作成しました")
                elif reply == QMessageBox.Cancel:
                    # キャンセルの場合、制作会社も削除
                    self.producer_data.remove(partner)
                    producer_ids = [p['id'] for p in self.producer_data]
                    self.db.save_production_producers(production_id, producer_ids)
                    continue

                # データを再読み込み
                self._load_producer_data()
                self._load_expenses()

    def add_producer_contract(self):
        """選択された制作会社に契約を追加"""
        if not self.is_edit:
            QMessageBox.warning(self, "警告", "番組を保存してから契約を追加してください")
            return

        current_row = self.producer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "制作会社を選択してください")
            return

        item = self.producer_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        production_id = self.production[0]
        partner_id = data['partner_id']

        # 契約編集ダイアログを開く
        from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
        contract_dialog = OrderContractEditDialog(
            self,
            production_id=production_id,
            partner_id=partner_id,
            work_type='制作'
        )
        if contract_dialog.exec_():
            QMessageBox.information(self, "成功", "契約を作成しました")
            # データを再読み込み
            self._load_producer_data()
            self._load_expenses()

    def edit_producer_contract(self):
        """選択された契約を編集"""
        current_row = self.producer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する契約を選択してください")
            return

        item = self.producer_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        contract_id = data.get('contract_id')

        if not contract_id:
            QMessageBox.warning(self, "警告", "契約が選択されていません")
            return

        # 契約編集ダイアログを開く
        from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
        contract_dialog = OrderContractEditDialog(self, contract_id=contract_id)
        if contract_dialog.exec_():
            QMessageBox.information(self, "成功", "契約を更新しました")
            # データを再読み込み
            self._load_producer_data()
            self._load_expenses()

    def delete_producer(self):
        """制作会社削除（契約も削除）"""
        if not self.is_edit:
            return

        current_row = self.producer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する制作会社を選択してください")
            return

        item = self.producer_table.item(current_row, 0)
        if not item:
            return

        data = item.data(Qt.UserRole)
        production_producer_id = data['production_producer_id']
        production_id = self.production[0]
        partner_id = data['partner_id']

        # 関連する契約を取得
        contracts = self.db.get_contracts_by_production_and_partner(production_id, partner_id)

        # 確認ダイアログ
        producer_name = self.producer_table.item(current_row, 0).text() if self.producer_table.item(current_row, 0) else "この制作会社"
        message = f"制作会社「{producer_name}」を削除すると、"
        if contracts:
            message += "以下の契約も削除されます：\n\n"
            for contract in contracts:
                # contract: (contract_id, item_name, unit_price, order_status, payment_timing)
                message += f"・{contract[1]}: ¥{contract[2]:,.0f}\n"
        else:
            message += "契約はありません。\n"
        message += "\n本当に削除してもよろしいですか？"

        reply = QMessageBox.question(
            self, "確認",
            message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_producer_from_production(production_producer_id, production_id, partner_id)
                QMessageBox.information(self, "成功", "制作会社と契約を削除しました")
                # データを再読み込み
                self._load_producer_data()
                self._load_expenses()
                # producer_dataも更新
                self.producer_data = [p for p in self.producer_data if p['id'] != partner_id]
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")

    def _load_expenses(self):
        """費用項目を読み込んでテーブルに表示（契約由来 + 手動追加）"""
        if not self.is_edit:
            return

        production_id = self.production[0]
        self.expense_data = []
        self.expense_table.setRowCount(0)

        # 1. 契約由来の費用項目を取得して表示
        # 出演者の契約
        cast_contracts = self.db.get_production_cast_with_contracts(production_id)
        for row in cast_contracts:
            contract_id = row[6]
            if contract_id:
                item_name = row[7] or ""
                unit_price = row[8] or 0
                order_status = row[9] or ""
                payment_timing = row[10] or ""
                partner_name = row[5]

                expense_data = {
                    'source': 'contract',  # 契約由来マーク
                    'contract_id': contract_id,
                    'item_name': f"🔗 {item_name}",
                    'amount': unit_price,
                    'supplier_name': partner_name,
                    'status': order_status,
                    'implementation_date': "",
                    'payment_scheduled_date': payment_timing
                }
                self.expense_data.append(expense_data)
                self._add_expense_to_table(expense_data, is_contract=True)

        # 制作会社の契約
        producer_contracts = self.db.get_production_producers_with_contracts(production_id)
        for row in producer_contracts:
            contract_id = row[3]
            if contract_id:
                item_name = row[4] or ""
                unit_price = row[5] or 0
                order_status = row[6] or ""
                payment_timing = row[7] or ""
                partner_name = row[2]

                expense_data = {
                    'source': 'contract',  # 契約由来マーク
                    'contract_id': contract_id,
                    'item_name': f"🔗 {item_name}",
                    'amount': unit_price,
                    'supplier_name': partner_name,
                    'status': order_status,
                    'implementation_date': "",
                    'payment_scheduled_date': payment_timing
                }
                self.expense_data.append(expense_data)
                self._add_expense_to_table(expense_data, is_contract=True)

        # 2. 手動追加の費用項目を取得して表示
        expenses = self.db.get_expenses_by_production(production_id)
        for expense in expenses:
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
                'source': 'manual',  # 手動追加
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
            self._add_expense_to_table(expense_data, is_contract=False)

    def _add_expense_to_table(self, expense_data, is_contract=False):
        """テーブルに費用項目を追加

        Args:
            expense_data: 費用項目データ
            is_contract: 契約由来の場合True（編集・削除不可）
        """
        row = self.expense_table.rowCount()
        self.expense_table.insertRow(row)

        self.expense_table.setItem(row, 0, QTableWidgetItem(expense_data['item_name']))
        self.expense_table.setItem(row, 1, QTableWidgetItem(f"{expense_data['amount']:,.0f}"))
        self.expense_table.setItem(row, 2, QTableWidgetItem(expense_data['supplier_name']))
        self.expense_table.setItem(row, 3, QTableWidgetItem(expense_data['status']))
        self.expense_table.setItem(row, 4, QTableWidgetItem(expense_data.get('implementation_date', '')))
        self.expense_table.setItem(row, 5, QTableWidgetItem(expense_data.get('payment_scheduled_date', '')))

        # 行にデータを保存
        for col in range(6):
            item = self.expense_table.item(row, col)
            if item:
                item.setData(Qt.UserRole, expense_data)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                # 契約由来の項目は背景色を変える
                if is_contract:
                    from PyQt5.QtGui import QColor
                    item.setBackground(QColor(240, 248, 255))  # 薄い青色

        # 合計金額を更新
        self._update_expense_total()

    def _update_expense_total(self):
        """費用項目の合計金額を更新"""
        total = sum(expense['amount'] for expense in self.expense_data)
        self.expense_total_label.setText(f"合計金額: ¥{total:,.0f}")

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
        """費用項目を編集（契約由来の項目は編集不可）"""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する費用項目を選択してください")
            return

        item = self.expense_table.item(current_row, 0)
        if not item:
            return

        expense_data = item.data(Qt.UserRole)

        # 契約由来の項目は編集不可
        if expense_data.get('source') == 'contract':
            QMessageBox.warning(
                self, "編集不可",
                "契約由来の費用項目は直接編集できません。\n"
                "出演者タブまたは制作会社タブから契約を編集してください。"
            )
            return

        expense_id = expense_data.get('id')
        if not expense_id:
            return

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
        """費用項目を削除（契約由来の項目は削除不可）"""
        current_row = self.expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する費用項目を選択してください")
            return

        item = self.expense_table.item(current_row, 0)
        if not item:
            return

        expense_data = item.data(Qt.UserRole)

        # 契約由来の項目は削除不可
        if expense_data.get('source') == 'contract':
            QMessageBox.warning(
                self, "削除不可",
                "契約由来の費用項目は直接削除できません。\n"
                "出演者タブまたは制作会社タブから契約を削除してください。"
            )
            return

        expense_id = expense_data.get('id')
        item_name = expense_data.get('item_name', '')

        if not expense_id:
            return

        reply = QMessageBox.question(
            self, "確認",
            f"費用項目「{item_name}」を削除してもよろしいですか？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_expense_order(expense_id)
                self.expense_table.removeRow(current_row)
                self.expense_data = [e for e in self.expense_data if e.get('id') != expense_id]
                self._update_expense_total()
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
