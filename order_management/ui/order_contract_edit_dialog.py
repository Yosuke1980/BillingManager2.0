"""発注書編集ダイアログ

発注書の登録・編集を行います。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel,
                             QDateEdit, QTextEdit, QFileDialog, QMessageBox, QWidget,
                             QRadioButton, QButtonGroup, QScrollArea, QApplication, QGroupBox,
                             QSizePolicy)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.program_edit_dialog import ProgramEditDialog
from order_management.ui.partner_master_widget import PartnerEditDialog
from partner_manager import PartnerManager


class OrderContractEditDialog(QDialog):
    """発注書編集ダイアログ"""

    def __init__(self, parent=None, contract_id=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.pm = PartnerManager()
        self.contract_id = contract_id
        self.pdf_file_path = ""
        self.pdf_dir = "order_pdfs"

        self.setWindowTitle("発注書編集" if contract_id else "新規発注書")

        # 画面サイズを取得して適切なダイアログサイズを設定
        screen = QApplication.primaryScreen().geometry()
        dialog_height = min(800, int(screen.height() * 0.8))  # 画面の80%または800pxの小さい方
        self.setMinimumSize(650, 600)
        self.resize(700, dialog_height)

        self.init_ui()

        if contract_id:
            self.load_contract_data()

    def init_ui(self):
        """UIの初期化（グループボックスでセクション分け）"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ===== セクション1: 基本情報 =====
        basic_group = QGroupBox("基本情報")
        basic_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        basic_layout = QFormLayout()
        basic_layout.setVerticalSpacing(12)
        basic_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        basic_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 発注種別（レギュラー・単発）
        order_type_layout = QHBoxLayout()
        order_type_layout.setContentsMargins(0, 0, 0, 0)
        self.order_type_group = QButtonGroup()
        self.order_type_regular = QRadioButton("レギュラー")
        self.order_type_spot = QRadioButton("単発")
        self.order_type_regular.setMinimumWidth(100)
        self.order_type_spot.setMinimumWidth(80)
        self.order_type_group.addButton(self.order_type_regular)
        self.order_type_group.addButton(self.order_type_spot)
        self.order_type_regular.setChecked(True)
        order_type_layout.addWidget(self.order_type_regular)
        order_type_layout.addWidget(self.order_type_spot)
        order_type_layout.addStretch()

        order_type_widget = QWidget()
        order_type_widget.setLayout(order_type_layout)
        order_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        order_type_widget.setMinimumHeight(40)
        basic_layout.addRow("発注種別:", order_type_widget)

        # 書類タイプ（契約書・発注書・発注メール）
        doc_type_layout = QHBoxLayout()
        doc_type_layout.setContentsMargins(0, 0, 0, 0)
        self.doc_type_group = QButtonGroup()
        self.doc_type_contract = QRadioButton("契約書")
        self.doc_type_order = QRadioButton("発注書")
        self.doc_type_email = QRadioButton("発注メール")
        self.doc_type_contract.setMinimumWidth(80)
        self.doc_type_order.setMinimumWidth(80)
        self.doc_type_email.setMinimumWidth(100)
        self.doc_type_group.addButton(self.doc_type_contract)
        self.doc_type_group.addButton(self.doc_type_order)
        self.doc_type_group.addButton(self.doc_type_email)
        self.doc_type_order.setChecked(True)
        self.doc_type_email.toggled.connect(self.on_doc_type_changed)
        doc_type_layout.addWidget(self.doc_type_contract)
        doc_type_layout.addWidget(self.doc_type_order)
        doc_type_layout.addWidget(self.doc_type_email)
        doc_type_layout.addStretch()

        doc_type_widget = QWidget()
        doc_type_widget.setLayout(doc_type_layout)
        doc_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        doc_type_widget.setMinimumHeight(40)
        basic_layout.addRow("書類タイプ:", doc_type_widget)

        # ファイル選択（契約書タイプの直下）
        file_layout = QHBoxLayout()
        self.file_label = QLabel("(未選択)")
        file_layout.addWidget(self.file_label)
        file_btn = create_button("ファイル選択", self.select_file)
        file_layout.addWidget(file_btn)
        file_layout.addStretch()
        basic_layout.addRow("ファイル:", file_layout)
        self.file_layout_row = basic_layout.rowCount() - 1

        # 発注ステータス
        self.order_status_combo = QComboBox()
        self.order_status_combo.addItems(["未完了", "完了"])
        basic_layout.addRow("発注ステータス:", self.order_status_combo)

        basic_group.setLayout(basic_layout)

        # ===== セクション2: 番組・案件情報 =====
        program_group = QGroupBox("番組・案件情報 *")
        program_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        program_layout_main = QFormLayout()
        program_layout_main.setVerticalSpacing(8)

        # 番組選択
        program_layout = QHBoxLayout()
        self.program_combo = QComboBox()
        self.program_combo.setEditable(True)
        self.program_combo.setInsertPolicy(QComboBox.NoInsert)
        self.program_combo.setMinimumWidth(300)
        self.program_combo.completer().setCompletionMode(self.program_combo.completer().PopupCompletion)
        self.program_combo.completer().setFilterMode(Qt.MatchContains)
        self.program_combo.currentIndexChanged.connect(self.on_program_changed)
        self.load_programs()
        program_layout.addWidget(self.program_combo, 1)

        add_program_btn = create_button("新規番組追加", self.add_new_program)
        add_program_btn.setMinimumWidth(120)
        program_layout.addWidget(add_program_btn, 0)

        program_name_label = QLabel("<b>番組名 *:</b>")
        program_layout_main.addRow(program_name_label, program_layout)

        # 案件指定（ラジオボタン）
        project_type_layout = QHBoxLayout()
        self.rb_normal = QRadioButton("通常放送（レギュラー放送用）")
        self.rb_project = QRadioButton("特定案件（イベント・特番用）")
        self.rb_normal.setChecked(True)

        self.project_type_group = QButtonGroup()
        self.project_type_group.addButton(self.rb_normal)
        self.project_type_group.addButton(self.rb_project)
        self.rb_project.toggled.connect(self.on_project_type_changed)

        project_type_layout.addWidget(self.rb_normal)
        project_type_layout.addWidget(self.rb_project)
        project_type_layout.addStretch()
        program_layout_main.addRow("案件指定:", project_type_layout)

        # 案件選択コンボボックス（インデントして階層表示）
        project_select_widget = QWidget()
        project_select_layout = QHBoxLayout()
        project_select_layout.setContentsMargins(20, 0, 0, 0)  # 左に20pxインデント

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(280)
        self.project_combo.setEnabled(False)
        project_select_layout.addWidget(self.project_combo, 1)

        add_project_btn = create_button("新規案件追加", self.add_new_project)
        add_project_btn.setMinimumWidth(120)
        add_project_btn.setEnabled(False)
        self.add_project_btn = add_project_btn
        project_select_layout.addWidget(add_project_btn, 0)

        project_select_widget.setLayout(project_select_layout)
        program_layout_main.addRow("", project_select_widget)
        self.project_select_widget = project_select_widget
        self.project_select_widget.setVisible(False)

        # ヘルプテキスト
        help_label = QLabel("<i><font color='#666'>ヒント: 通常放送はレギュラー番組の定期発注、特定案件はイベントや特番などの単発発注です</font></i>")
        help_label.setWordWrap(True)
        program_layout_main.addRow("", help_label)

        # 費用項目
        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("例: 山田太郎出演料、制作費")
        item_name_label = QLabel("<b>費用項目 *:</b>")
        program_layout_main.addRow(item_name_label, self.item_name)

        program_group.setLayout(program_layout_main)

        # ===== セクション3: 取引先情報 =====
        partner_group = QGroupBox("取引先情報 *")
        partner_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        partner_layout_main = QFormLayout()
        partner_layout_main.setVerticalSpacing(8)

        partner_layout = QHBoxLayout()
        self.partner_combo = QComboBox()
        self.partner_combo.setEditable(True)
        self.partner_combo.setInsertPolicy(QComboBox.NoInsert)
        self.partner_combo.setMinimumWidth(300)
        self.partner_combo.completer().setCompletionMode(self.partner_combo.completer().PopupCompletion)
        self.partner_combo.completer().setFilterMode(Qt.MatchContains)
        self.load_partners()
        partner_layout.addWidget(self.partner_combo, 1)

        add_partner_btn = create_button("新規取引先追加", self.add_new_partner)
        add_partner_btn.setMinimumWidth(140)
        partner_layout.addWidget(add_partner_btn, 0)

        partner_name_label = QLabel("<b>取引先名 *:</b>")
        partner_layout_main.addRow(partner_name_label, partner_layout)

        partner_group.setLayout(partner_layout_main)

        # ===== セクション4: 契約条件 =====
        contract_group = QGroupBox("契約条件")
        contract_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        contract_layout = QFormLayout()
        contract_layout.setVerticalSpacing(8)

        # 契約期間
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.dateChanged.connect(self.on_start_date_changed)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("  〜  "))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addMonths(6))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()

        contract_layout.addRow("開始日 〜 終了日:", date_layout)

        # 期間タイプ
        self.period_type = QComboBox()
        self.period_type.addItems(["3ヶ月", "半年", "1年"])
        self.period_type.setCurrentText("半年")
        self.period_type.currentTextChanged.connect(self.on_period_type_changed)
        contract_layout.addRow("期間タイプ:", self.period_type)

        # 支払い方法と金額
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("支払い方法:"))
        self.payment_type = QComboBox()
        self.payment_type.addItems(["月額固定", "回数ベース"])
        self.payment_type.setCurrentText("月額固定")
        self.payment_type.currentTextChanged.connect(self.on_payment_type_changed)
        payment_layout.addWidget(self.payment_type)

        payment_layout.addWidget(QLabel("  金額:"))
        self.unit_price_label = QLabel("")
        self.unit_price = QLineEdit()
        self.unit_price.setPlaceholderText("例: 50000")
        self.unit_price.setMaximumWidth(150)
        payment_layout.addWidget(self.unit_price)
        payment_layout.addStretch()

        contract_layout.addRow("", payment_layout)

        # ヘルプテキスト
        payment_help = QLabel("<i><font color='#666'>ヒント: 月額固定は毎月同じ金額、回数ベースは放送回数×単価で計算</font></i>")
        payment_help.setWordWrap(True)
        contract_layout.addRow("", payment_help)

        # 支払いタイミング
        self.payment_timing = QComboBox()
        self.payment_timing.addItems(["翌月末払い", "当月末払い"])
        self.payment_timing.setCurrentText("翌月末払い")
        contract_layout.addRow("支払いタイミング:", self.payment_timing)

        contract_group.setLayout(contract_layout)

        # ===== セクション5: 確認情報（契約書・発注書の場合） =====
        self.confirm_group = QGroupBox("確認情報")
        self.confirm_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        confirm_layout = QFormLayout()
        confirm_layout.setVerticalSpacing(8)

        # 確認者
        self.confirmed_by = QLineEdit()
        confirm_layout.addRow("確認者:", self.confirmed_by)

        self.confirm_group.setLayout(confirm_layout)

        # ===== セクション6: メール送信情報（メール発注の場合） =====
        self.email_group = QGroupBox("メール送信情報（メール発注用）")
        self.email_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        email_layout = QFormLayout()
        email_layout.setVerticalSpacing(8)

        # メール件名
        self.email_subject = QLineEdit()
        self.email_subject.setPlaceholderText("例: 2025年度上期 番組制作委託のお願い")
        email_layout.addRow("件名:", self.email_subject)

        # メール送信先
        self.email_to = QLineEdit()
        self.email_to.setPlaceholderText("例: partner@example.com")
        email_layout.addRow("送信先:", self.email_to)

        # メール送信日
        self.email_sent_date = QDateEdit()
        self.email_sent_date.setCalendarPopup(True)
        self.email_sent_date.setDate(QDate.currentDate())
        email_layout.addRow("送信日:", self.email_sent_date)

        # メール本文
        self.email_body = QTextEdit()
        self.email_body.setMaximumHeight(150)
        self.email_body.setPlaceholderText("メール本文を入力...")
        email_layout.addRow("本文:", self.email_body)

        self.email_group.setLayout(email_layout)

        # ===== セクション7: その他 =====
        other_group = QGroupBox("その他")
        other_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        other_layout = QFormLayout()
        other_layout.setVerticalSpacing(8)

        # 備考
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        other_layout.addRow("備考:", self.notes)

        other_group.setLayout(other_layout)

        # ===== すべてのグループをメインレイアウトに追加 =====
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: white;")
        form_main_layout = QVBoxLayout()
        form_main_layout.setContentsMargins(10, 10, 10, 10)
        form_main_layout.setSpacing(10)

        form_main_layout.addWidget(basic_group)
        form_main_layout.addWidget(program_group)
        form_main_layout.addWidget(partner_group)
        form_main_layout.addWidget(contract_group)
        form_main_layout.addWidget(self.confirm_group)
        form_main_layout.addWidget(self.email_group)
        form_main_layout.addWidget(other_group)

        form_widget.setLayout(form_main_layout)

        # スクロールエリアに配置
        scroll_area = QScrollArea()
        scroll_area.setWidget(form_widget)
        scroll_area.setWidgetResizable(True)

        main_layout.addWidget(scroll_area, 1)

        # ボタン（スクロールエリアの外に配置）
        button_layout = QHBoxLayout()
        save_btn = create_button("保存", self.save)
        button_layout.addWidget(save_btn)

        cancel_btn = create_button("キャンセル", self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout, 0)

        self.setLayout(main_layout)

        # 初期表示：発注書モードでメールフィールドを非表示
        self.on_doc_type_changed()

    def on_payment_type_changed(self, payment_type):
        """支払タイプが変更されたときの処理"""
        # 既存の処理を維持
        pass

    def on_project_type_changed(self):
        """案件区分が変更されたときの処理"""
        is_project = self.rb_project.isChecked()
        self.project_select_widget.setVisible(is_project)
        self.project_combo.setEnabled(is_project)
        self.add_project_btn.setEnabled(is_project)

        if is_project:
            # 特定案件が選択された場合、現在選択されている番組の案件一覧を読み込む
            self.load_projects_for_program()

    def on_doc_type_changed(self):
        """書類タイプが変更されたときにフィールドの表示を切り替える"""
        is_email = self.doc_type_email.isChecked()

        # メール発注の場合：確認情報を非表示、メールグループを表示
        # 契約書 or 発注書の場合：確認情報を表示、メールグループを非表示
        self.confirm_group.setVisible(not is_email)
        self.email_group.setVisible(is_email)

    def select_file(self):
        """ファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "ファイルを選択",
            "",
            "PDFファイル (*.pdf);;すべてのファイル (*.*)"
        )

        if file_path:
            self.pdf_file_path = file_path
            self.file_label.setText(os.path.basename(file_path))

    def on_program_changed(self):
        """番組が変更されたときの処理"""
        # 特定案件モードの場合、案件一覧を更新
        if self.rb_project.isChecked():
            self.load_projects_for_program()

    def load_projects_for_program(self):
        """選択中の番組に紐づく案件一覧を読み込む"""
        program_id = self.program_combo.currentData()
        if not program_id:
            self.project_combo.clear()
            return

        projects = self.db.get_projects_by_program(program_id)
        self.project_combo.clear()
        self.project_combo.addItem("（案件を選択）", None)

        for project in projects:
            # project: (id, name, date, type, budget, parent_id,
            #          start_date, end_date, project_type, program_id, program_name)
            display_text = f"{project[1]}"
            if project[8]:  # project_type
                display_text += f" ({project[8]})"
            if project[6]:  # start_date
                display_text += f" [{project[6]}]"
            self.project_combo.addItem(display_text, project[0])

    def add_new_project(self):
        """新規案件を追加"""
        from order_management.ui.project_edit_dialog import ProjectEditDialog

        program_id = self.program_combo.currentData()
        dialog = ProjectEditDialog(self, program_id=program_id)
        if dialog.exec_():
            # 案件一覧を再読み込み
            self.load_projects_for_program()
            # 新しく追加された案件を選択
            # （最後に追加された案件が最新）
            if self.project_combo.count() > 1:
                self.project_combo.setCurrentIndex(self.project_combo.count() - 1)

    def load_programs(self):
        """番組一覧を読み込み"""
        programs = self.db.get_programs()
        self.program_dict = {}

        for program in programs:
            # program: (id, name, description, start_date, end_date, broadcast_time, broadcast_days, status)
            display_text = f"{program[1]} (ID: {program[0]})"
            self.program_combo.addItem(display_text, program[0])  # IDをデータとして保存
            self.program_dict[display_text] = program[0]

    def load_partners(self):
        """取引先一覧を読み込み"""
        partners = self.db.get_partners()
        self.partner_dict = {}

        for partner in partners:
            # partner: (id, name, code, contact_person, email, phone, address, partner_type, notes)
            display_text = f"{partner[1]}"
            if partner[2]:  # code
                display_text += f" ({partner[2]})"
            self.partner_combo.addItem(display_text, partner[0])  # IDをデータとして保存
            self.partner_dict[display_text] = partner[0]

    def load_projects(self):
        """案件一覧を読み込み"""
        projects = self.db.get_projects()
        self.project_dict = {}

        for project in projects:
            # project: (id, name, date, type, budget, parent_id, start_date, end_date, created_at, updated_at, program_id)
            display_text = f"{project[1]}"
            self.project_combo.addItem(display_text, project[0])  # IDをデータとして保存
            self.project_dict[display_text] = project[0]

    def load_contract_data(self):
        """発注書データを読み込み"""
        contract = self.db.get_order_contract_by_id(self.contract_id)

        if contract:
            # contract フィールド順序:
            # 0:id, 1:program_id, 2:program_name, 3:partner_id, 4:partner_name,
            # 5:contract_start_date, 6:contract_end_date, 7:contract_period_type,
            # 8:pdf_status, 9:pdf_distributed_date, 10:confirmed_by,
            # 11:pdf_file_path, 12:notes, 13:created_at, 14:updated_at,
            # 15:order_type, 16:order_status,
            # 17:email_subject, 18:email_body, 19:email_sent_date, 20:email_to,
            # 21:payment_type, 22:unit_price, 23:payment_timing,
            # 24:project_id, 25:project_name, 26:item_name

            # 番組選択
            for i in range(self.program_combo.count()):
                if self.program_dict[self.program_combo.itemText(i)] == contract[1]:
                    self.program_combo.setCurrentIndex(i)
                    break

            # 取引先選択
            for i in range(self.partner_combo.count()):
                if self.partner_dict[self.partner_combo.itemText(i)] == contract[3]:
                    self.partner_combo.setCurrentIndex(i)
                    break

            # 委託開始日
            if contract[5]:
                self.start_date.setDate(QDate.fromString(contract[5], "yyyy-MM-dd"))

            # 委託終了日
            if contract[6]:
                self.end_date.setDate(QDate.fromString(contract[6], "yyyy-MM-dd"))

            # 契約期間種別
            if contract[7]:
                self.period_type.setCurrentText(contract[7])

            # 確認者
            if contract[10]:
                self.confirmed_by.setText(contract[10])

            # ファイルパス
            if contract[11]:
                self.pdf_file_path = contract[11]
                self.file_label.setText(os.path.basename(self.pdf_file_path))

            # 備考
            if contract[12]:
                self.notes.setPlainText(contract[12])

            # 発注種別と書類タイプ（インデックス15）
            if contract[15]:
                # 旧データとの互換性のため、「契約書」「発注書」「メール発注」を変換
                if contract[15] == "契約書":
                    self.doc_type_contract.setChecked(True)
                elif contract[15] == "発注書":
                    self.doc_type_order.setChecked(True)
                elif contract[15] == "メール発注":
                    self.doc_type_email.setChecked(True)
                self.on_doc_type_changed()  # フィールド表示を更新

            # 発注ステータス（インデックス16）
            if contract[16]:
                self.order_status_combo.setCurrentText(contract[16])

            # メール件名（インデックス17）
            if contract[17]:
                self.email_subject.setText(contract[17])

            # メール本文（インデックス18）
            if contract[18]:
                self.email_body.setPlainText(contract[18])

            # メール送信日（インデックス19）
            if contract[19]:
                self.email_sent_date.setDate(QDate.fromString(contract[19], "yyyy-MM-dd"))

            # メール送信先（インデックス20）
            if contract[20]:
                self.email_to.setText(contract[20])

            # 支払タイプ（インデックス21）
            if contract[21]:
                self.payment_type.setCurrentText(contract[21])
                self.on_payment_type_changed(contract[21])  # フィールド表示を更新

            # 単価（インデックス22）
            if contract[22] is not None:
                self.unit_price.setText(str(int(contract[22])))

            # 支払タイミング（インデックス23）
            if contract[23]:
                self.payment_timing.setCurrentText(contract[23])

            # 案件選択（インデックス24）
            if contract[24]:
                for i in range(self.project_combo.count()):
                    if self.project_dict.get(self.project_combo.itemText(i)) == contract[24]:
                        self.project_combo.setCurrentIndex(i)
                        break

            # 費用項目（インデックス26）
            if contract[26]:
                self.item_name.setText(contract[26])

            # 番組選択（contract[1]: program_id）
            if contract[1]:
                for i in range(self.program_combo.count()):
                    if self.program_combo.itemData(i) == contract[1]:
                        self.program_combo.setCurrentIndex(i)
                        break

            # 案件選択（contract[27]: project_id）
            project_id = contract[27] if len(contract) > 27 else None
            if project_id:
                self.rb_project.setChecked(True)
                # 案件一覧を読み込んで選択
                self.load_projects_for_program()
                for i in range(self.project_combo.count()):
                    if self.project_combo.itemData(i) == project_id:
                        self.project_combo.setCurrentIndex(i)
                        break
            else:
                self.rb_normal.setChecked(True)

    def on_start_date_changed(self, date):
        """開始日変更時に終了日を自動設定"""
        period_type = self.period_type.currentText()
        months = {"3ヶ月": 3, "半年": 6, "1年": 12}

        if period_type in months:
            new_end_date = date.addMonths(months[period_type])
            self.end_date.setDate(new_end_date)

    def on_period_type_changed(self, period_type):
        """契約期間種別変更時に終了日を自動設定"""
        months = {"3ヶ月": 3, "半年": 6, "1年": 12}

        if period_type in months:
            start_date = self.start_date.date()
            new_end_date = start_date.addMonths(months[period_type])
            self.end_date.setDate(new_end_date)


    def save(self):
        """保存"""
        # バリデーション
        if self.program_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "番組を選択してください。")
            return

        if self.rb_project.isChecked():
            if self.project_combo.currentIndex() < 0 or self.project_combo.currentData() is None:
                QMessageBox.warning(self, "警告", "案件を選択してください。")
                return

        if not self.item_name.text().strip():
            QMessageBox.warning(self, "警告", "費用項目を入力してください。")
            return

        if self.partner_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "取引先を選択してください。")
            return

        # PDFファイルを保存
        saved_pdf_path = ""
        if self.pdf_file_path and os.path.exists(self.pdf_file_path):
            # ファイル名を生成
            program_text = self.program_combo.currentText().split(" (ID:")[0]
            partner_text = self.partner_combo.currentText().split(" (")[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"発注書_{partner_text}_{program_text}_{timestamp}.pdf"

            saved_pdf_path = os.path.join(self.pdf_dir, filename)

            try:
                # ディレクトリが存在しない場合は作成
                if not os.path.exists(self.pdf_dir):
                    os.makedirs(self.pdf_dir)

                shutil.copy2(self.pdf_file_path, saved_pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"PDFファイルの保存に失敗しました:\n{str(e)}")
                return

        # 発注書データを作成
        # currentData()でIDを取得（より安全）
        partner_id = self.partner_combo.currentData()

        # IDが取得できない場合は辞書から取得（フォールバック）
        if partner_id is None:
            partner_key = self.partner_combo.currentText()
            partner_id = self.partner_dict.get(partner_key)
            if partner_id is None:
                QMessageBox.warning(self, "警告", "取引先が正しく選択されていません。")
                return

        # 書類タイプの判定
        if self.doc_type_contract.isChecked():
            doc_type = "契約書"
        elif self.doc_type_email.isChecked():
            doc_type = "メール発注"
        else:
            doc_type = "発注書"

        # 発注種別の判定
        order_type_text = "レギュラー" if self.order_type_regular.isChecked() else "単発"

        contract_data = {
            'item_name': self.item_name.text().strip(),
            'partner_id': partner_id,
            'contract_start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'contract_end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'contract_period_type': self.period_type.currentText(),
            'order_type': doc_type,  # 書類タイプを保存
            'order_status': self.order_status_combo.currentText(),
            'pdf_status': "",  # 削除されたフィールド
            'pdf_file_path': saved_pdf_path if saved_pdf_path else (
                self.pdf_file_path if self.contract_id else ""
            ),
            'pdf_distributed_date': "",  # 削除されたフィールド
            'confirmed_by': self.confirmed_by.text(),
            'email_subject': self.email_subject.text(),
            'email_body': self.email_body.toPlainText(),
            'email_sent_date': self.email_sent_date.date().toString("yyyy-MM-dd"),
            'email_to': self.email_to.text(),
            'notes': self.notes.toPlainText(),
            # レギュラー番組契約条件
            'payment_type': self.payment_type.currentText(),
            'unit_price': float(self.unit_price.text()) if self.unit_price.text() else None,
            'payment_timing': self.payment_timing.currentText(),
            # V6フィールド
            'contract_type': 'regular_fixed' if self.payment_type.currentText() == '月額固定' else 'regular_count'
        }

        # 番組と案件の設定
        program_id = self.program_combo.currentData()
        if program_id is None:
            program_key = self.program_combo.currentText()
            program_id = self.program_dict.get(program_key)

        contract_data['program_id'] = program_id

        # 案件の設定（特定案件が選択されている場合のみ）
        if self.rb_project.isChecked():
            project_id = self.project_combo.currentData()
            contract_data['project_id'] = project_id
        else:
            contract_data['project_id'] = None

        # 後方互換性のため、古いフィールドも設定
        contract_data['project_name_type'] = 'program'
        contract_data['custom_project_name'] = None

        if self.contract_id:
            contract_data['id'] = self.contract_id

        try:
            self.db.save_order_contract(contract_data)
            QMessageBox.information(self, "成功", "発注書を保存しました。")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"発注書の保存に失敗しました:\n{str(e)}")

    def add_new_program(self):
        """新規番組を追加"""
        dialog = ProgramEditDialog(self)
        if dialog.exec_():
            # 番組一覧を再読み込み
            current_count = self.program_combo.count()
            self.program_combo.clear()
            self.load_programs()

            # 新しく追加された番組を自動選択
            if self.program_combo.count() > current_count:
                self.program_combo.setCurrentIndex(self.program_combo.count() - 1)

    def add_new_partner(self):
        """新規取引先を追加"""
        dialog = PartnerEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            partner_data = dialog.get_data()
            try:
                # 重複チェック
                if self.pm.check_duplicate_name(partner_data['name']):
                    QMessageBox.warning(self, "警告", "同じ名前の取引先が既に存在します")
                    return

                # コードが空欄の場合は自動生成
                if not partner_data['code']:
                    import time
                    partner_data['code'] = f"P{int(time.time())}"  # タイムスタンプベースのユニークコード

                if partner_data['code'] and self.pm.check_duplicate_code(partner_data['code']):
                    QMessageBox.warning(self, "警告", "同じコードの取引先が既に存在します")
                    return

                # 取引先を保存
                self.pm.save_partner(partner_data, is_new=True)

                # 取引先一覧を再読み込み
                current_count = self.partner_combo.count()
                self.partner_combo.clear()
                self.load_partners()

                # 新しく追加された取引先を自動選択
                if self.partner_combo.count() > current_count:
                    self.partner_combo.setCurrentIndex(self.partner_combo.count() - 1)

                QMessageBox.information(self, "成功", "取引先を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")
