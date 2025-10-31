"""案件編集ダイアログ

案件の作成・編集を行うダイアログです。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import QDate
from order_management.models import PROJECT_TYPES


class ProjectEditDialog(QDialog):
    """案件編集ダイアログ"""

    def __init__(self, parent=None, project_data=None):
        super().__init__(parent)
        self.project_data = project_data
        self.setWindowTitle("案件編集" if project_data else "案件追加")
        self.setMinimumWidth(500)
        self._setup_ui()

        if project_data:
            self._load_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 案件名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: 夏休みイベント")

        # 実施日
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")

        # 案件タイプ
        self.type_combo = QComboBox()
        self.type_combo.addItems(PROJECT_TYPES)

        # 予算
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(0, 99999999)
        self.budget_spin.setDecimals(0)
        self.budget_spin.setSuffix(" 円")
        self.budget_spin.setGroupSeparatorShown(True)

        form_layout.addRow("案件名:", self.name_edit)
        form_layout.addRow("実施日:", self.date_edit)
        form_layout.addRow("タイプ:", self.type_combo)
        form_layout.addRow("予算:", self.budget_spin)

        layout.addLayout(form_layout)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """データを読み込み"""
        if self.project_data:
            self.name_edit.setText(self.project_data[1] or "")

            # 日付を設定
            date_str = self.project_data[2]
            if date_str:
                try:
                    year, month, day = date_str.split('-')
                    self.date_edit.setDate(QDate(int(year), int(month), int(day)))
                except:
                    pass

            # タイプを設定
            project_type = self.project_data[3]
            index = self.type_combo.findText(project_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            # 予算を設定
            self.budget_spin.setValue(self.project_data[4] or 0)

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "案件名を入力してください")
            return

        self.accept()

    def get_data(self) -> dict:
        """入力データを取得"""
        return {
            'name': self.name_edit.text().strip(),
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'type': self.type_combo.currentText(),
            'budget': self.budget_spin.value(),
        }
