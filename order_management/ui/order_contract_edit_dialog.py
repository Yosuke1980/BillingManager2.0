"""発注書編集ダイアログ

発注書の登録・編集を行います。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel,
                             QTextEdit, QFileDialog, QMessageBox, QWidget,
                             QRadioButton, QButtonGroup, QScrollArea, QApplication, QGroupBox,
                             QSizePolicy, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.custom_date_edit import ImprovedDateEdit
from order_management.ui.production_edit_dialog import ProductionEditDialog
from order_management.ui.partner_master_widget import PartnerEditDialog
from partner_manager import PartnerManager


class OrderContractEditDialog(QDialog):
    """発注書編集ダイアログ"""

    def __init__(self, parent=None, contract_id=None, production_id=None, partner_id=None, work_type=None):
        super().__init__(parent)
        try:
            self.db = OrderManagementDB()
            self.pm = PartnerManager()
            self.contract_id = contract_id
            self.pdf_file_path = ""
            self.pdf_dir = "order_pdfs"

            # 番組詳細からの呼び出し用パラメータ
            self.preset_production_id = production_id
            self.preset_partner_id = partner_id
            self.preset_work_type = work_type  # '出演' or '制作'

            self.setWindowTitle("発注書編集" if contract_id else "新規発注書")

            # 画面サイズを取得して適切なダイアログサイズを設定
            screen = QApplication.primaryScreen().geometry()
            dialog_height = min(800, int(screen.height() * 0.8))  # 画面の80%または800pxの小さい方
            self.setMinimumSize(650, 600)
            self.resize(700, dialog_height)

            self.init_ui()

            if contract_id:
                self.load_contract_data()
            elif production_id and partner_id:
                # 番組詳細から呼び出された場合、自動設定
                self.apply_preset_values()
        except Exception as e:
            from utils import log_message
            import traceback
            log_message(f"OrderContractEditDialog 初期化エラー: {e}")
            log_message(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"契約編集ダイアログの初期化に失敗しました:\n{str(e)}")
            raise

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
        self.order_type_regular.toggled.connect(self.on_order_configuration_changed)
        order_type_layout.addWidget(self.order_type_regular)
        order_type_layout.addWidget(self.order_type_spot)
        order_type_layout.addStretch()

        order_type_widget = QWidget()
        order_type_widget.setLayout(order_type_layout)
        order_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        order_type_widget.setMinimumHeight(40)
        basic_layout.addRow("発注種別:", order_type_widget)

        # 業務種別（制作・出演）
        work_type_layout = QHBoxLayout()
        work_type_layout.setContentsMargins(0, 0, 0, 0)
        self.work_type_group = QButtonGroup()
        self.work_type_production = QRadioButton("制作")
        self.work_type_cast = QRadioButton("出演")
        self.work_type_production.setMinimumWidth(100)
        self.work_type_cast.setMinimumWidth(80)
        self.work_type_group.addButton(self.work_type_production)
        self.work_type_group.addButton(self.work_type_cast)
        self.work_type_production.setChecked(True)
        work_type_layout.addWidget(self.work_type_production)
        work_type_layout.addWidget(self.work_type_cast)
        work_type_layout.addStretch()

        work_type_widget = QWidget()
        work_type_widget.setLayout(work_type_layout)
        work_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        work_type_widget.setMinimumHeight(40)
        basic_layout.addRow("業務種別:", work_type_widget)

        # 書類タイプ（選択式）
        doc_type_layout = QHBoxLayout()
        doc_type_layout.setContentsMargins(0, 0, 0, 0)
        self.doc_type_group = QButtonGroup()
        self.doc_type_contract = QRadioButton("契約書")
        self.doc_type_order = QRadioButton("発注書")
        self.doc_type_email = QRadioButton("発注メール")
        self.doc_type_contract.setMinimumWidth(100)
        self.doc_type_order.setMinimumWidth(100)
        self.doc_type_email.setMinimumWidth(120)
        self.doc_type_group.addButton(self.doc_type_contract)
        self.doc_type_group.addButton(self.doc_type_order)
        self.doc_type_group.addButton(self.doc_type_email)
        self.doc_type_order.setChecked(True)  # デフォルトは発注書
        self.doc_type_contract.toggled.connect(self.on_doc_type_changed)
        self.doc_type_order.toggled.connect(self.on_doc_type_changed)
        self.doc_type_email.toggled.connect(self.on_doc_type_changed)
        doc_type_layout.addWidget(self.doc_type_contract)
        doc_type_layout.addWidget(self.doc_type_order)
        doc_type_layout.addWidget(self.doc_type_email)
        doc_type_layout.addStretch()

        doc_type_widget = QWidget()
        doc_type_widget.setLayout(doc_type_layout)
        doc_type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        doc_type_widget.setMinimumHeight(40)
        basic_layout.addRow("書面:", doc_type_widget)

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
        self.program_combo.setEditable(True)  # 編集可能に設定（入力時に候補を表示）
        self.program_combo.setInsertPolicy(QComboBox.NoInsert)  # 新規項目は追加しない
        self.program_combo.setMinimumWidth(300)
        # オートコンプリート設定
        self.program_combo.completer().setCompletionMode(self.program_combo.completer().PopupCompletion)
        self.program_combo.completer().setFilterMode(Qt.MatchContains)  # 部分一致で候補を表示
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
        self.item_name.setPlaceholderText("例: 山田太郎出演料、制作費（空欄の場合は業務種別から自動設定）")
        item_name_label = QLabel("費用項目:")
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

        # ===== セクション3.5: 出演者情報（出演契約の場合のみ表示） =====
        self.cast_group = QGroupBox("出演者情報")
        self.cast_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        cast_layout_main = QVBoxLayout()

        # 出演者テーブル
        from PyQt5.QtWidgets import QHeaderView
        self.cast_table = QTableWidget()
        self.cast_table.setColumnCount(4)
        self.cast_table.setHorizontalHeaderLabels(["出演者名", "所属", "役割", ""])
        self.cast_table.setMaximumHeight(150)
        header = self.cast_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cast_layout_main.addWidget(self.cast_table)

        # 出演者追加ボタン
        cast_button_layout = QHBoxLayout()
        add_cast_btn = create_button("➕ 出演者を追加", self.add_cast_to_contract)
        cast_button_layout.addWidget(add_cast_btn)
        cast_button_layout.addStretch()
        cast_layout_main.addLayout(cast_button_layout)

        self.cast_group.setLayout(cast_layout_main)
        self.cast_group.setVisible(False)  # デフォルトは非表示（出演契約の場合のみ表示）

        # 業務種別が変更されたときに表示/非表示を切り替え
        self.work_type_cast.toggled.connect(lambda checked: self.cast_group.setVisible(checked))

        # ===== セクション4: 契約条件 =====
        contract_group = QGroupBox("契約条件")
        contract_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        contract_layout = QFormLayout()
        contract_layout.setVerticalSpacing(8)

        # 契約期間（レギュラー用）
        date_layout = QHBoxLayout()
        self.start_date = ImprovedDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.dateChanged.connect(self.on_start_date_changed)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("  〜  "))
        self.end_date = ImprovedDateEdit()
        self.end_date.setDate(QDate.currentDate().addMonths(6))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()

        self.date_range_widget = QWidget()
        self.date_range_widget.setLayout(date_layout)
        contract_layout.addRow("開始日 〜 終了日:", self.date_range_widget)

        # 実施日（単発用）
        impl_date_layout = QHBoxLayout()
        self.implementation_date = ImprovedDateEdit()
        self.implementation_date.setDate(QDate.currentDate())
        impl_date_layout.addWidget(self.implementation_date)
        impl_date_layout.addStretch()

        self.impl_date_widget = QWidget()
        self.impl_date_widget.setLayout(impl_date_layout)
        self.impl_date_widget.setVisible(False)  # デフォルト非表示
        contract_layout.addRow("実施日:", self.impl_date_widget)

        # 期間タイプ（レギュラー用）
        self.period_type = QComboBox()
        self.period_type.addItems(["3ヶ月", "半年", "1年"])
        self.period_type.setCurrentText("半年")
        self.period_type.currentTextChanged.connect(self.on_period_type_changed)
        self.period_type_row_index = contract_layout.rowCount()
        contract_layout.addRow("期間タイプ:", self.period_type)

        # 支払い方法と金額（レギュラー用）
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

        self.regular_payment_widget = QWidget()
        self.regular_payment_widget.setLayout(payment_layout)
        contract_layout.addRow("", self.regular_payment_widget)

        # ヘルプテキスト（レギュラー用）
        payment_help = QLabel("<i><font color='#666'>ヒント: 月額固定は毎月同じ金額、回数ベースは放送回数×単価で計算</font></i>")
        payment_help.setWordWrap(True)
        self.regular_payment_help = payment_help
        contract_layout.addRow("", self.regular_payment_help)

        # スポット金額（単発用）
        spot_amount_layout = QHBoxLayout()
        spot_amount_layout.addWidget(QLabel("金額:"))
        self.spot_amount = QLineEdit()
        self.spot_amount.setPlaceholderText("例: 100000")
        self.spot_amount.setMaximumWidth(150)
        spot_amount_layout.addWidget(self.spot_amount)
        spot_amount_layout.addStretch()

        self.spot_payment_widget = QWidget()
        self.spot_payment_widget.setLayout(spot_amount_layout)
        self.spot_payment_widget.setVisible(False)  # デフォルト非表示
        contract_layout.addRow("スポット金額:", self.spot_payment_widget)

        # 支払いタイミング
        self.payment_timing = QComboBox()
        self.payment_timing.addItems(["翌月末払い", "当月末払い"])
        self.payment_timing.setCurrentText("翌月末払い")
        contract_layout.addRow("支払いタイミング:", self.payment_timing)

        # === 契約自動延長設定（レギュラー出演契約書のみ） ===
        self.renewal_section_widgets = []  # 自動延長関連ウィジェットを保存

        renewal_header = QLabel("<b>契約自動延長設定</b>")
        contract_layout.addRow("", renewal_header)
        self.renewal_section_widgets.append((contract_layout.rowCount() - 1, renewal_header))

        # 自動延長有効チェックボックス
        renewal_enable_layout = QHBoxLayout()
        self.auto_renewal_checkbox = QCheckBox("自動延長を有効にする")
        self.auto_renewal_checkbox.setChecked(True)
        self.auto_renewal_checkbox.stateChanged.connect(self.on_auto_renewal_changed)
        renewal_enable_layout.addWidget(self.auto_renewal_checkbox)
        renewal_enable_layout.addStretch()
        renewal_enable_widget = QWidget()
        renewal_enable_widget.setLayout(renewal_enable_layout)
        contract_layout.addRow("", renewal_enable_widget)
        self.renewal_section_widgets.append((contract_layout.rowCount() - 1, renewal_enable_widget))

        # 延長期間
        renewal_period_layout = QHBoxLayout()
        self.renewal_period_spin = QSpinBox()
        self.renewal_period_spin.setMinimum(1)
        self.renewal_period_spin.setMaximum(12)
        self.renewal_period_spin.setValue(3)
        self.renewal_period_spin.setSuffix(" ヶ月")
        renewal_period_layout.addWidget(self.renewal_period_spin)
        renewal_period_layout.addWidget(QLabel("ずつ自動延長"))
        renewal_period_layout.addStretch()
        renewal_period_widget = QWidget()
        renewal_period_widget.setLayout(renewal_period_layout)
        contract_layout.addRow("延長期間:", renewal_period_widget)
        self.renewal_section_widgets.append((contract_layout.rowCount() - 1, renewal_period_widget))

        # 終了通知受領日
        termination_notice_layout = QHBoxLayout()
        self.termination_notice_date = ImprovedDateEdit()
        self.termination_notice_date.setSpecialValueText("未受領")
        self.termination_notice_date.setDate(QDate(2000, 1, 1))  # 最小値
        self.termination_notice_date.setMinimumDate(QDate(2000, 1, 1))
        termination_notice_layout.addWidget(self.termination_notice_date)
        clear_notice_btn = QPushButton("クリア")
        clear_notice_btn.clicked.connect(lambda: self.termination_notice_date.setDate(QDate(2000, 1, 1)))
        clear_notice_btn.setMaximumWidth(80)
        termination_notice_layout.addWidget(clear_notice_btn)
        termination_notice_layout.addStretch()
        termination_notice_widget = QWidget()
        termination_notice_widget.setLayout(termination_notice_layout)
        contract_layout.addRow("終了通知受領日:", termination_notice_widget)
        self.renewal_section_widgets.append((contract_layout.rowCount() - 1, termination_notice_widget))

        # ヘルプテキスト
        renewal_help = QLabel(
            "<i><font color='#666'>ヒント: 終了日の1ヶ月前までに終了通知がない場合、設定した期間で自動延長されます</font></i>"
        )
        renewal_help.setWordWrap(True)
        contract_layout.addRow("", renewal_help)
        self.renewal_section_widgets.append((contract_layout.rowCount() - 1, renewal_help))

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
        self.email_sent_date = ImprovedDateEdit()
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
        form_main_layout.addWidget(self.cast_group)  # 出演者情報
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

        # 初期表示：デフォルト設定に基づいて画面項目を調整
        self.on_order_configuration_changed()
        self.on_doc_type_changed()

    def on_payment_type_changed(self, payment_type):
        """支払タイプが変更されたときの処理"""
        # 既存の処理を維持
        pass

    def on_auto_renewal_changed(self, state):
        """自動延長チェックボックスが変更されたときの処理"""
        enabled = (state == Qt.Checked)
        self.renewal_period_spin.setEnabled(enabled)
        if not enabled:
            # 自動延長を無効にした場合、終了通知受領日もクリア推奨
            pass  # ユーザーの判断に任せる

    def on_order_configuration_changed(self):
        """発注種別が変更されたときの処理

        組み合わせに応じて画面項目を表示/非表示する:
        - レギュラー: 期間、月額固定/回数ベース
        - 単発: 実施日、スポット金額
        """
        is_regular = self.order_type_regular.isChecked()

        # 日付フィールドの表示切り替え
        if is_regular:
            # レギュラー: 開始日〜終了日
            self.date_range_widget.setVisible(True)
            self.impl_date_widget.setVisible(False)
            self.period_type.setVisible(True)
        else:
            # 単発: 実施日のみ
            self.date_range_widget.setVisible(False)
            self.impl_date_widget.setVisible(True)
            self.period_type.setVisible(False)

        # 支払いフィールドの表示切り替え
        if is_regular:
            # レギュラー: 月額固定 or 回数ベース
            self.regular_payment_widget.setVisible(True)
            self.regular_payment_help.setVisible(True)
            self.spot_payment_widget.setVisible(False)
        else:
            # 単発: スポット金額
            self.regular_payment_widget.setVisible(False)
            self.regular_payment_help.setVisible(False)
            self.spot_payment_widget.setVisible(True)

        # 単発の場合は案件指定を「特定案件」に固定
        if not is_regular:
            self.rb_project.setChecked(True)
            self.rb_normal.setEnabled(False)
        else:
            self.rb_normal.setEnabled(True)

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
        is_contract = self.doc_type_contract.isChecked()

        # メール発注の場合：確認情報を非表示、メールグループを表示
        # 契約書 or 発注書の場合：確認情報を表示、メールグループを非表示
        self.confirm_group.setVisible(not is_email)
        self.email_group.setVisible(is_email)

        # 自動延長設定の表示切り替え（契約書を選んだ場合のみ表示）
        show_renewal = is_contract
        for row_index, widget in self.renewal_section_widgets:
            widget.setVisible(show_renewal)

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
        # rb_projectが初期化済みの場合のみチェック（初期化中のシグナル発火を防ぐ）
        if hasattr(self, 'rb_project') and self.rb_project.isChecked():
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
            # project: (id, name, implementation_date, project_type,
            #          parent_id, program_id, program_name)
            display_text = f"{project[1]}"
            if project[3]:  # project_type
                display_text += f" ({project[3]})"
            if project[2]:  # implementation_date
                display_text += f" [{project[2]}]"
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
        programs = self.db.get_productions()
        self.program_dict = {}

        # プレースホルダーを追加
        self.program_combo.addItem("（番組を選択）", None)

        for program in programs:
            # production: (id, name, description, production_type, start_date, end_date,
            #             start_time, end_time, broadcast_time, broadcast_days, status,
            #             parent_production_id)
            display_text = f"{program[1]} (ID: {program[0]})"
            self.program_combo.addItem(display_text, program[0])  # IDをデータとして保存
            self.program_dict[display_text] = program[0]

    def load_partners(self):
        """取引先一覧を読み込み"""
        partners = self.db.get_partners()
        self.partner_dict = {}

        # プレースホルダーを追加
        self.partner_combo.addItem("（取引先を選択）", None)

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
            # contract フィールド順序（database_manager.py get_order_contract_by_id参照）:
            # 0:id, 1:program_id, 2:program_name, 3:partner_id, 4:partner_name,
            # 5:contract_start_date, 6:contract_end_date, 7:contract_period_type,
            # 8:pdf_status, 9:pdf_distributed_date, 10:pdf_file_path, 11:notes,
            # 12:created_at, 13:updated_at, 14:order_type, 15:order_status,
            # 16:email_sent_date, 17:payment_type, 18:unit_price, 19:payment_timing,
            # 20:project_id, 21:project_name, 22:item_name,
            # 23:contract_type, 24:project_name_type, 25:implementation_date,
            # 26:spot_amount, 27:order_category,
            # 28:email_subject, 29:email_body, 30:email_to,
            # 31:auto_renewal_enabled, 32:renewal_period_months, 33:termination_notice_date,
            # 34:last_renewal_date, 35:renewal_count, 36:work_type

            # 番組選択
            for i in range(self.program_combo.count()):
                if self.program_combo.itemData(i) == contract[1]:
                    self.program_combo.setCurrentIndex(i)
                    break

            # 取引先選択
            for i in range(self.partner_combo.count()):
                if self.partner_combo.itemData(i) == contract[3]:
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

            # ファイルパス（インデックス10）
            if contract[10]:
                self.pdf_file_path = contract[10]
                self.file_label.setText(os.path.basename(self.pdf_file_path))

            # 備考（インデックス11）
            if contract[11]:
                self.notes.setPlainText(contract[11])

            # 書類タイプ（インデックス14: order_type）
            if contract[14]:
                doc_type = contract[14]
                if doc_type == "契約書":
                    self.doc_type_contract.setChecked(True)
                elif doc_type == "発注メール":
                    self.doc_type_email.setChecked(True)
                else:
                    self.doc_type_order.setChecked(True)

            # 発注ステータス（インデックス15）
            if contract[15]:
                self.order_status_combo.setCurrentText(contract[15])

            # メール送信日（インデックス16）
            if contract[16]:
                self.email_sent_date.setDate(QDate.fromString(str(contract[16]), "yyyy-MM-dd"))

            # 支払タイプ（インデックス17）
            if contract[17]:
                self.payment_type.setCurrentText(contract[17])
                self.on_payment_type_changed(contract[17])  # フィールド表示を更新

            # 単価（インデックス18）
            if contract[18] is not None:
                self.unit_price.setText(str(int(contract[18])))

            # 支払タイミング（インデックス19）
            if contract[19]:
                self.payment_timing.setCurrentText(contract[19])

            # 案件ID（インデックス20: project_id）
            if contract[20]:
                # project_idが存在する場合は特定案件モード
                self.rb_project.setChecked(True)
                # 案件一覧を読み込んで選択
                self.load_projects_for_program()
                for i in range(self.project_combo.count()):
                    if self.project_combo.itemData(i) == contract[20]:
                        self.project_combo.setCurrentIndex(i)
                        break
            else:
                self.rb_normal.setChecked(True)

            # 費用項目（インデックス22）
            if contract[22]:
                self.item_name.setText(contract[22])

            # メール件名（インデックス28）
            if contract[28]:
                self.email_subject.setText(str(contract[28]))

            # メール本文（インデックス29）
            if contract[29]:
                self.email_body.setPlainText(str(contract[29]))

            # メール送信先（インデックス30）
            if contract[30]:
                self.email_to.setText(str(contract[30]))

            # 番組選択（contract[1]: program_id）
            if contract[1]:
                for i in range(self.program_combo.count()):
                    if self.program_combo.itemData(i) == contract[1]:
                        self.program_combo.setCurrentIndex(i)
                        break

            # === 自動延長設定の読み込み ===
            # 自動延長有効フラグ
            auto_renewal_enabled = contract[31] if len(contract) > 31 else 1
            self.auto_renewal_checkbox.setChecked(bool(auto_renewal_enabled))

            # 延長期間
            renewal_period = contract[32] if len(contract) > 32 else 3
            if renewal_period:
                self.renewal_period_spin.setValue(int(renewal_period))

            # 終了通知受領日
            termination_notice = contract[33] if len(contract) > 33 else None
            if termination_notice:
                self.termination_notice_date.setDate(QDate.fromString(str(termination_notice), "yyyy-MM-dd"))
            else:
                self.termination_notice_date.setDate(QDate(2000, 1, 1))

            # === 業務種別の読み込み ===
            work_type = contract[36] if len(contract) > 36 else '制作'
            if work_type == '出演':
                self.work_type_cast.setChecked(True)
            else:
                self.work_type_production.setChecked(True)

            # === 発注区分（レギュラー/単発）の読み込み ===
            # order_category (index 27) から判断: '単発' なら単発、それ以外はレギュラー
            order_category = contract[27] if len(contract) > 27 else None
            if order_category == '単発':
                self.order_type_spot.setChecked(True)
                # 単発の場合、実施日を設定
                if contract[25]:  # implementation_date
                    self.implementation_date.setDate(QDate.fromString(contract[25], "yyyy-MM-dd"))
                # 単発金額を設定
                if contract[26] is not None:  # spot_amount
                    self.spot_amount.setText(str(int(contract[26])))
            else:
                self.order_type_regular.setChecked(True)

            # 画面の表示状態を更新
            self.on_order_configuration_changed()
            self.on_doc_type_changed()

            # 出演者情報を読み込み
            self.load_contract_cast()

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

        # 費用項目が空欄の場合はデフォルト値を設定
        if not self.item_name.text().strip():
            work_type = '出演' if self.work_type_cast.isChecked() else '制作'
            default_item_name = f"{work_type}料"
            self.item_name.setText(default_item_name)

        if self.partner_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "取引先を選択してください。")
            return

        # 単発の場合の追加バリデーション
        if self.order_type_spot.isChecked():
            if not self.spot_amount.text().strip():
                QMessageBox.warning(self, "警告", "単発金額を入力してください。")
                return
            try:
                float(self.spot_amount.text())
            except ValueError:
                QMessageBox.warning(self, "警告", "単発金額は数値で入力してください。")
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

        # 書類タイプの取得
        if self.doc_type_contract.isChecked():
            doc_type = "契約書"
        elif self.doc_type_email.isChecked():
            doc_type = "発注メール"
        else:
            doc_type = "発注書"

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
            # currentData()がNoneの場合は、入力されたテキストで辞書検索
            program_key = self.program_combo.currentText()
            program_id = self.program_dict.get(program_key)

            # それでもNoneの場合は、番組がリストに存在しない
            if program_id is None:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"番組「{program_key}」がリストに存在しません。\n"
                    "リストから既存の番組を選択するか、「新規番組追加」ボタンで番組を追加してください。"
                )
                return

        contract_data['production_id'] = program_id  # データベースはproduction_idを使用

        # 案件の設定（特定案件が選択されている場合のみ）
        if self.rb_project.isChecked():
            project_id = self.project_combo.currentData()
            contract_data['project_id'] = project_id
        else:
            contract_data['project_id'] = None

        # 後方互換性のため、古いフィールドも設定
        contract_data['project_name_type'] = 'program'
        contract_data['custom_project_name'] = None

        # === 自動延長設定 ===
        contract_data['auto_renewal_enabled'] = 1 if self.auto_renewal_checkbox.isChecked() else 0
        contract_data['renewal_period_months'] = self.renewal_period_spin.value()

        # 終了通知受領日（最小値の場合はNULLとして扱う）
        termination_date = self.termination_notice_date.date()
        if termination_date == QDate(2000, 1, 1):
            contract_data['termination_notice_date'] = None
        else:
            contract_data['termination_notice_date'] = termination_date.toString("yyyy-MM-dd")

        # === 業務種別 ===
        contract_data['work_type'] = '出演' if self.work_type_cast.isChecked() else '制作'

        # === 発注区分 ===
        contract_data['order_category'] = '単発' if self.order_type_spot.isChecked() else 'レギュラー'

        # 単発の場合は実施日と単発金額を保存
        if self.order_type_spot.isChecked():
            contract_data['implementation_date'] = self.implementation_date.date().toString("yyyy-MM-dd")
            contract_data['spot_amount'] = float(self.spot_amount.text()) if self.spot_amount.text() else None
        else:
            contract_data['implementation_date'] = None
            contract_data['spot_amount'] = None

        if self.contract_id:
            contract_data['id'] = self.contract_id

        # 出演契約の場合、出演者の所属と契約先の整合性をチェック
        if self.work_type_cast.isChecked():
            mismatched_casts = []
            for row in range(self.cast_table.rowCount()):
                name_item = self.cast_table.item(row, 0)
                if name_item:
                    cast_id = name_item.data(Qt.UserRole)
                    cast_name = name_item.text()

                    # 出演者の所属事務所IDを取得
                    cast_info = self.db.get_cast_by_id(cast_id)
                    if cast_info and len(cast_info) > 2:
                        cast_partner_id = cast_info[2]  # partner_id
                        cast_partner_name = cast_info[3] if len(cast_info) > 3 else "(不明)"

                        # 契約取引先と出演者の所属が一致しない場合
                        if cast_partner_id and cast_partner_id != partner_id:
                            mismatched_casts.append((cast_name, cast_partner_name))

            # 不一致がある場合は警告
            if mismatched_casts:
                contract_partner_name = self.partner_combo.currentText()
                warning_message = "以下の出演者の所属事務所と契約取引先が一致しません。\n\n"
                warning_message += f"契約先: {contract_partner_name}\n\n"
                warning_message += "不一致の出演者:\n"
                for cast_name, cast_partner in mismatched_casts:
                    warning_message += f"  • {cast_name} (所属: {cast_partner})\n"
                warning_message += "\nこのまま保存しますか？"

                reply = QMessageBox.question(
                    self, "所属事務所の不一致",
                    warning_message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.No:
                    return  # 保存をキャンセル

        try:
            saved_id = self.db.save_order_contract(contract_data)

            # 出演者情報を保存（出演契約の場合のみ）
            if self.work_type_cast.isChecked():
                try:
                    contract_id = saved_id if saved_id else self.contract_id
                    self.save_contract_cast(contract_id)
                except Exception as e:
                    QMessageBox.warning(
                        self, "警告",
                        f"出演者情報の保存に失敗しました:\n{str(e)}\n\n"
                        f"契約は保存されています。"
                    )

            # 費用項目自動生成の確認
            reply = QMessageBox.question(
                self, "費用項目の自動生成",
                "契約から費用項目を自動生成しますか？\n\n"
                "（既存の費用項目がある場合は削除されます）",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    # 既存の費用項目を削除
                    contract_id = saved_id if saved_id else self.contract_id
                    deleted_count = self.db.delete_expense_items_by_contract(contract_id)

                    # 費用項目を生成
                    generated_count = self.db.generate_expense_items_from_contract(contract_id)

                    QMessageBox.information(
                        self, "成功",
                        f"費用項目を{generated_count}件生成しました。\n"
                        f"（既存{deleted_count}件を削除）"
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self, "警告",
                        f"費用項目の自動生成に失敗しました:\n{str(e)}\n\n"
                        f"契約は保存されています。"
                    )

            # 成功ダイアログを表示せず、直接閉じる
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"発注書の保存に失敗しました:\n{str(e)}")

    def add_new_program(self):
        """新規番組を追加"""
        dialog = ProductionEditDialog(self)
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

    def apply_preset_values(self):
        """番組詳細から呼び出された場合の自動設定"""
        # 番組を自動選択
        if self.preset_production_id:
            found = False
            for i in range(self.program_combo.count()):
                if self.program_combo.itemData(i) == self.preset_production_id:
                    self.program_combo.setCurrentIndex(i)
                    self.program_combo.setEnabled(False)  # 編集不可
                    found = True
                    break

            if not found:
                # デバッグ用: 番組が見つからない場合は警告
                from utils import log_message
                log_message(f"警告: 番組ID {self.preset_production_id} が番組コンボボックスに見つかりません")

        # 取引先を自動選択
        if self.preset_partner_id:
            for i in range(self.partner_combo.count()):
                if self.partner_combo.itemData(i) == self.preset_partner_id:
                    self.partner_combo.setCurrentIndex(i)
                    self.partner_combo.setEnabled(False)  # 編集不可
                    break

        # 業務種別を自動選択
        if self.preset_work_type:
            if self.preset_work_type == '出演':
                self.work_type_cast.setChecked(True)
            elif self.preset_work_type == '制作':
                self.work_type_production.setChecked(True)
            # 業務種別を固定（編集不可）
            self.work_type_cast.setEnabled(False)
            self.work_type_production.setEnabled(False)

    def add_cast_to_contract(self):
        """出演者を契約に追加"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QListWidgetItem

        # 出演者選択ダイアログを作成
        dialog = QDialog(self)
        dialog.setWindowTitle("出演者を選択")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # 出演者リストを作成
        cast_list = QListWidget()
        all_cast = self.db.get_all_cast()

        for cast in all_cast:
            cast_id, cast_name, partner_name = cast[0], cast[1], cast[2] if len(cast) > 2 else None

            # 既にテーブルに追加されている出演者をスキップ
            already_added = False
            for row in range(self.cast_table.rowCount()):
                if self.cast_table.item(row, 0) and self.cast_table.item(row, 0).data(Qt.UserRole) == cast_id:
                    already_added = True
                    break

            if not already_added:
                display_text = f"{cast_name}"
                if partner_name:
                    display_text += f" ({partner_name})"

                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, cast_id)
                item.setData(Qt.UserRole + 1, cast_name)
                item.setData(Qt.UserRole + 2, partner_name or "")
                cast_list.addItem(item)

        layout.addWidget(cast_list)

        # ボタン
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        # ダイアログを表示
        if dialog.exec_() == QDialog.Accepted:
            selected_items = cast_list.selectedItems()

            # 契約取引先を取得
            contract_partner_id = self.partner_combo.currentData()
            contract_partner_name = self.partner_combo.currentText()

            # 整合性チェック用のリスト
            mismatched_casts = []

            for item in selected_items:
                cast_id = item.data(Qt.UserRole)
                cast_name = item.data(Qt.UserRole + 1)
                partner_name = item.data(Qt.UserRole + 2)

                # 出演者の所属事務所IDを取得
                cast_info = self.db.get_cast_by_id(cast_id)
                if cast_info and len(cast_info) > 2:
                    cast_partner_id = cast_info[2]  # partner_id

                    # 契約取引先と出演者の所属が一致しない場合
                    if contract_partner_id and cast_partner_id != contract_partner_id:
                        mismatched_casts.append((cast_name, partner_name, contract_partner_name))

            # 不一致がある場合は警告
            if mismatched_casts:
                warning_message = "以下の出演者の所属事務所と契約取引先が一致しません。\n\n"
                for cast_name, cast_partner, contract_partner in mismatched_casts:
                    warning_message += f"• {cast_name}\n  所属: {cast_partner}\n  契約先: {contract_partner}\n\n"
                warning_message += "このまま追加しますか？"

                reply = QMessageBox.question(
                    self, "所属事務所の不一致",
                    warning_message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.No:
                    return  # 追加をキャンセル

            # テーブルに追加
            for item in selected_items:
                cast_id = item.data(Qt.UserRole)
                cast_name = item.data(Qt.UserRole + 1)
                partner_name = item.data(Qt.UserRole + 2)

                row = self.cast_table.rowCount()
                self.cast_table.insertRow(row)

                # 出演者名
                name_item = QTableWidgetItem(cast_name)
                name_item.setData(Qt.UserRole, cast_id)
                self.cast_table.setItem(row, 0, name_item)

                # 所属
                self.cast_table.setItem(row, 1, QTableWidgetItem(partner_name))

                # 役割（編集可能）
                role_item = QTableWidgetItem("")
                self.cast_table.setItem(row, 2, role_item)

                # 削除ボタン
                delete_btn = QPushButton("🗑️")
                delete_btn.setMaximumWidth(40)
                delete_btn.clicked.connect(lambda checked, r=row: self.remove_cast_from_table(r))
                self.cast_table.setCellWidget(row, 3, delete_btn)

    def remove_cast_from_table(self, row):
        """テーブルから出演者を削除"""
        from PyQt5.QtWidgets import QMessageBox

        cast_name = self.cast_table.item(row, 0).text() if self.cast_table.item(row, 0) else ""

        reply = QMessageBox.question(
            self, "確認",
            f"出演者「{cast_name}」を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cast_table.removeRow(row)

            # 削除後、残りの行の削除ボタンのコールバックを再設定
            for r in range(self.cast_table.rowCount()):
                delete_btn = self.cast_table.cellWidget(r, 3)
                if delete_btn:
                    delete_btn.clicked.disconnect()
                    delete_btn.clicked.connect(lambda checked, row_idx=r: self.remove_cast_from_table(row_idx))

    def load_contract_cast(self):
        """契約に紐付いた出演者を読み込み"""
        if not self.contract_id:
            return

        cast_list = self.db.get_contract_cast(self.contract_id)

        self.cast_table.setRowCount(0)  # テーブルをクリア

        for cast in cast_list:
            # データ構造: (contract_cast_id, cast_id, cast_name, partner_name, role)
            contract_cast_id = cast[0]
            cast_id = cast[1]
            cast_name = cast[2]
            partner_name = cast[3] or ""
            role = cast[4] or ""

            row = self.cast_table.rowCount()
            self.cast_table.insertRow(row)

            # 出演者名
            name_item = QTableWidgetItem(cast_name)
            name_item.setData(Qt.UserRole, cast_id)
            name_item.setData(Qt.UserRole + 1, contract_cast_id)  # 既存レコードのID
            self.cast_table.setItem(row, 0, name_item)

            # 所属
            self.cast_table.setItem(row, 1, QTableWidgetItem(partner_name))

            # 役割
            role_item = QTableWidgetItem(role)
            self.cast_table.setItem(row, 2, role_item)

            # 削除ボタン
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(40)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_cast_from_table(r))
            self.cast_table.setCellWidget(row, 3, delete_btn)

    def save_contract_cast(self, contract_id):
        """契約に紐付いた出演者を保存"""
        # テーブルから出演者リストを取得
        cast_list = []
        for row in range(self.cast_table.rowCount()):
            name_item = self.cast_table.item(row, 0)
            role_item = self.cast_table.item(row, 2)

            if name_item:
                cast_id = name_item.data(Qt.UserRole)
                role = role_item.text() if role_item else None
                cast_list.append((cast_id, role))

        # データベースマネージャーの一括保存メソッドを使用
        self.db.save_contract_cast_list(contract_id, cast_list)
