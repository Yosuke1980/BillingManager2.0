"""案件編集ダイアログ

番組に紐づく案件（イベント、特別企画など）の登録・編集を行います。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QMessageBox, QLabel,
    QComboBox, QRadioButton, QButtonGroup, QWidget
)
from PyQt5.QtCore import Qt, QDate
from order_management.database_manager import OrderManagementDB


class ProjectEditDialog(QDialog):
    """案件編集ダイアログ"""

    def __init__(self, parent=None, project=None, program_id=None):
        """
        Args:
            parent: 親ウィジェット
            project: 編集対象の案件データ（新規の場合はNone）
            program_id: 紐づける番組ID（新規作成時に指定）
        """
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.project = project
        self.is_edit = project is not None
        self.initial_program_id = program_id

        self.setWindowTitle("案件編集" if self.is_edit else "新規案件登録")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._setup_ui()

        if self.is_edit:
            self._load_project_data()
        elif self.initial_program_id:
            # 新規作成時に番組が指定されている場合
            for i in range(self.program_combo.count()):
                if self.program_combo.itemData(i) == self.initial_program_id:
                    self.program_combo.setCurrentIndex(i)
                    break

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        # フォーム
        form_layout = QFormLayout()

        # 番組選択（必須）
        program_layout = QHBoxLayout()
        self.program_combo = QComboBox()
        self.program_combo.setMinimumWidth(300)
        self._load_programs()
        program_layout.addWidget(self.program_combo)
        program_layout.addStretch()

        form_layout.addRow("番組名 *:", self.program_combo)

        # 案件名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: 2025年春 公開収録イベント")
        form_layout.addRow("案件名 *:", self.name_edit)

        # 案件種別
        project_type_layout = QHBoxLayout()
        self.project_type_group = QButtonGroup()
        self.type_event = QRadioButton("イベント")
        self.type_special = QRadioButton("特別企画")
        self.type_normal = QRadioButton("通常")
        self.type_event.setMinimumWidth(100)
        self.type_special.setMinimumWidth(100)
        self.type_normal.setMinimumWidth(80)
        self.project_type_group.addButton(self.type_event)
        self.project_type_group.addButton(self.type_special)
        self.project_type_group.addButton(self.type_normal)
        self.type_event.setChecked(True)
        project_type_layout.addWidget(self.type_event)
        project_type_layout.addWidget(self.type_special)
        project_type_layout.addWidget(self.type_normal)
        project_type_layout.addStretch()

        project_type_widget = QWidget()
        project_type_widget.setLayout(project_type_layout)
        form_layout.addRow("案件種別:", project_type_widget)

        # 実施期間
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("開始日:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel("  終了日:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.end_date_edit)
        date_layout.addStretch()

        date_widget = QWidget()
        date_widget.setLayout(date_layout)
        form_layout.addRow("実施期間:", date_widget)

        # 予算（オプション）
        self.budget_edit = QLineEdit()
        self.budget_edit.setPlaceholderText("例: 500000")
        self.budget_edit.setMaximumWidth(200)
        form_layout.addRow("予算（円）:", self.budget_edit)

        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("案件に関する追加情報を入力...")
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

        # 説明ラベル
        info_label = QLabel(
            "💡 ヒント: 案件は番組に紐づく特定のイベントや企画を管理します。\n"
            "   例: 「ちょうどいいラジオ」の「2025年春公開収録」など"
        )
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()

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

    def _load_programs(self):
        """番組一覧を読み込み"""
        programs = self.db.get_programs_with_hierarchy(include_children=False)
        self.program_combo.clear()

        for program in programs:
            # program: (id, name, description, start_date, end_date,
            #          broadcast_time, broadcast_days, status,
            #          program_type, parent_program_id, parent_name)
            display_text = f"{program[1]}"
            if program[8]:  # program_type
                display_text += f" ({program[8]})"
            self.program_combo.addItem(display_text, program[0])

    def _load_project_data(self):
        """案件データを読み込み"""
        if not self.project:
            return

        # project: (id, name, date, type, budget, parent_id,
        #          start_date, end_date, project_type, program_id, program_name)

        self.name_edit.setText(self.project[1] or "")

        # 番組選択
        if self.project[9]:  # program_id
            for i in range(self.program_combo.count()):
                if self.program_combo.itemData(i) == self.project[9]:
                    self.program_combo.setCurrentIndex(i)
                    break

        # 案件種別
        if len(self.project) > 8 and self.project[8]:
            project_type = self.project[8]
            if project_type == "特別企画":
                self.type_special.setChecked(True)
            elif project_type == "通常":
                self.type_normal.setChecked(True)
            else:
                self.type_event.setChecked(True)

        # 実施期間
        if self.project[6]:  # start_date
            self.start_date_edit.setDate(QDate.fromString(self.project[6], "yyyy-MM-dd"))
        if self.project[7]:  # end_date
            self.end_date_edit.setDate(QDate.fromString(self.project[7], "yyyy-MM-dd"))

        # 予算
        if self.project[4] and self.project[4] > 0:  # budget
            self.budget_edit.setText(str(int(self.project[4])))

        # 備考（旧typeフィールドを備考として表示）
        if self.project[3]:  # type (旧フィールド)
            self.notes_edit.setPlainText(self.project[3])

    def save(self):
        """保存"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "案件名は必須です")
            return

        if self.program_combo.currentIndex() < 0:
            QMessageBox.warning(self, "入力エラー", "番組を選択してください")
            return

        # 案件種別を決定
        if self.type_special.isChecked():
            project_type = "特別企画"
        elif self.type_normal.isChecked():
            project_type = "通常"
        else:
            project_type = "イベント"

        # 予算の取得
        budget = 0.0
        if self.budget_edit.text().strip():
            try:
                budget = float(self.budget_edit.text().strip())
            except ValueError:
                QMessageBox.warning(self, "入力エラー", "予算は数値で入力してください")
                return

        project_data = {
            'name': self.name_edit.text().strip(),
            'program_id': self.program_combo.currentData(),
            'project_type': project_type,
            'start_date': self.start_date_edit.date().toString("yyyy-MM-dd") if self.start_date_edit.date().isValid() else None,
            'end_date': self.end_date_edit.date().toString("yyyy-MM-dd") if self.end_date_edit.date().isValid() else None,
            'budget': budget,
            'type': self.notes_edit.toPlainText().strip(),  # 旧フィールドを備考として使用
            'date': self.start_date_edit.date().toString("yyyy-MM-dd") if self.start_date_edit.date().isValid() else QDate.currentDate().toString("yyyy-MM-dd"),
            'parent_id': None
        }

        if self.is_edit:
            project_data['id'] = self.project[0]

        try:
            project_id = self.db.save_project(project_data, is_new=not self.is_edit)
            QMessageBox.information(self, "成功", "案件を保存しました")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました: {str(e)}")

    def get_project_id(self):
        """保存された案件IDを取得（保存後に使用）"""
        return getattr(self, 'saved_project_id', None)
