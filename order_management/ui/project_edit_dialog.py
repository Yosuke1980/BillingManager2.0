"""案件編集ダイアログ

案件の作成・編集を行うダイアログです。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QDialogButtonBox, QMessageBox, QLabel
)
from PyQt5.QtCore import QDate
from order_management.models import PROJECT_TYPES, PROJECT_TYPE_REGULAR


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

        # 初期状態のフィールド表示を更新
        self._update_date_fields()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # 案件名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: 夏休みイベント")

        # 実施日（単発用）/ 開始日（レギュラー用）
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")

        # 終了日（レギュラー用のみ）
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addMonths(6))
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")

        # 案件タイプ
        self.type_combo = QComboBox()
        self.type_combo.addItems(PROJECT_TYPES)
        self.type_combo.currentTextChanged.connect(self._update_date_fields)

        # 予算
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(0, 99999999)
        self.budget_spin.setDecimals(0)
        self.budget_spin.setSuffix(" 円")
        self.budget_spin.setGroupSeparatorShown(True)

        self.form_layout.addRow("案件名:", self.name_edit)
        self.form_layout.addRow("タイプ:", self.type_combo)

        # 日付フィールドは動的に追加される
        self.date_label = None
        self.end_date_label = None

        self.form_layout.addRow("予算:", self.budget_spin)

        layout.addLayout(self.form_layout)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_date_fields(self):
        """プロジェクトタイプに応じて日付フィールドを更新"""
        is_regular = self.type_combo.currentText() == PROJECT_TYPE_REGULAR

        # 既存の日付フィールドを削除
        if self.date_label:
            self.form_layout.removeRow(self.date_label)
            self.date_label = None
        if self.end_date_label:
            self.form_layout.removeRow(self.end_date_label)
            self.end_date_label = None

        # 日付ウィジェットの値を保存
        date_value = self.date_edit.date()
        end_date_value = self.end_date_edit.date()

        # タイプに応じたフィールドを挿入（予算の前に配置）
        budget_row = self.form_layout.rowCount() - 1

        if is_regular:
            # レギュラー案件: 開始日と終了日
            # 新しいウィジェットを作成（removeRowで削除されるため）
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDate(date_value)
            self.date_edit.setDisplayFormat("yyyy-MM-dd")

            self.end_date_edit = QDateEdit()
            self.end_date_edit.setCalendarPopup(True)
            self.end_date_edit.setDate(end_date_value)
            self.end_date_edit.setDisplayFormat("yyyy-MM-dd")

            self.date_label = QLabel("開始日:")
            self.form_layout.insertRow(budget_row, self.date_label, self.date_edit)

            self.end_date_label = QLabel("終了日:")
            self.form_layout.insertRow(budget_row + 1, self.end_date_label, self.end_date_edit)
        else:
            # 単発案件: 実施日のみ
            # 新しいウィジェットを作成
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDate(date_value)
            self.date_edit.setDisplayFormat("yyyy-MM-dd")

            self.date_label = QLabel("実施日:")
            self.form_layout.insertRow(budget_row, self.date_label, self.date_edit)
            self.end_date_label = None

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

            # レギュラー案件の場合、開始日と終了日を設定
            if project_type == PROJECT_TYPE_REGULAR:
                start_date_str = self.project_data[6] if len(self.project_data) > 6 else ""
                if start_date_str:
                    try:
                        year, month, day = start_date_str.split('-')
                        self.date_edit.setDate(QDate(int(year), int(month), int(day)))
                    except:
                        pass

                end_date_str = self.project_data[7] if len(self.project_data) > 7 else ""
                if end_date_str:
                    try:
                        year, month, day = end_date_str.split('-')
                        self.end_date_edit.setDate(QDate(int(year), int(month), int(day)))
                    except:
                        pass

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "案件名を入力してください")
            return

        self.accept()

    def get_data(self) -> dict:
        """入力データを取得"""
        is_regular = self.type_combo.currentText() == PROJECT_TYPE_REGULAR

        data = {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'budget': self.budget_spin.value(),
        }

        if is_regular:
            # レギュラー案件: 開始日と終了日を設定
            data['date'] = self.date_edit.date().toString("yyyy-MM-dd")  # start_dateとして使用
            data['start_date'] = self.date_edit.date().toString("yyyy-MM-dd")
            data['end_date'] = self.end_date_edit.date().toString("yyyy-MM-dd")
        else:
            # 単発案件: 実施日のみ設定
            data['date'] = self.date_edit.date().toString("yyyy-MM-dd")
            data['start_date'] = ''
            data['end_date'] = ''

        return data
