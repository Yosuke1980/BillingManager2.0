"""出演者編集ダイアログ"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QMessageBox, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.producer_select_dialog import ProducerSelectDialog


class CastEditDialog(QDialog):
    """出演者編集ダイアログ"""

    def __init__(self, parent=None, cast=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.cast = cast
        self.is_edit = cast is not None
        self.selected_partner_id = None
        self.selected_partner_name = ""

        self.setWindowTitle("出演者編集" if self.is_edit else "新規出演者登録")
        self.setMinimumWidth(500)

        self._setup_ui()

        if self.is_edit:
            self._load_cast_data()

    def _setup_ui(self):
        """UIセットアップ"""
        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)

        # フォーム
        form_layout = QFormLayout()

        # 出演者名
        self.name_edit = QLineEdit()
        form_layout.addRow("出演者名 *:", self.name_edit)

        # 所属事務所/個人
        partner_layout = QHBoxLayout()
        self.partner_label = QLabel("(未選択)")
        self.select_partner_button = QPushButton("選択...")
        self.select_partner_button.clicked.connect(self.select_partner)
        partner_layout.addWidget(self.partner_label)
        partner_layout.addWidget(self.select_partner_button)
        partner_layout.addStretch()

        partner_widget = QLabel()
        partner_widget.setLayout(partner_layout)
        form_layout.addRow("所属事務所/個人 *:", partner_widget)

        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

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

    def _load_cast_data(self):
        """出演者データを読み込み"""
        if not self.cast:
            return

        self.name_edit.setText(self.cast[1] or "")
        self.notes_edit.setPlainText(self.cast[3] or "")

        # 所属事務所を取得
        partner_id = self.cast[2]
        self.selected_partner_id = partner_id

        partner = self.db.get_partner_by_id(partner_id)
        if partner:
            self.selected_partner_name = partner[1]
            self.partner_label.setText(self.selected_partner_name)

    def select_partner(self):
        """所属事務所/個人を選択"""
        dialog = ProducerSelectDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_partners()
            if selected:
                partner = selected[0]  # 1件のみ選択
                self.selected_partner_id = partner['id']
                self.selected_partner_name = partner['name']
                self.partner_label.setText(self.selected_partner_name)

    def save(self):
        """保存"""
        # バリデーション
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "出演者名は必須です")
            return

        if not self.selected_partner_id:
            QMessageBox.warning(self, "入力エラー", "所属事務所/個人を選択してください")
            return

        # データ構築
        cast_data = {
            'name': self.name_edit.text().strip(),
            'partner_id': self.selected_partner_id,
            'notes': self.notes_edit.toPlainText().strip()
        }

        if self.is_edit:
            cast_data['id'] = self.cast[0]

        try:
            self.db.save_cast(cast_data, is_new=not self.is_edit)
            self.accept()
        except Exception as e:
            error_msg = str(e)
            # UNIQUE constraint違反の場合
            if 'UNIQUE constraint failed' in error_msg or 'UNIQUE' in error_msg:
                QMessageBox.warning(
                    self, "出演者名が重複",
                    f"出演者名「{cast_data['name']}」は既に登録されています。\n"
                    f"別の名前を使用してください。"
                )
            else:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {error_msg}")

    def get_data(self):
        """データ取得（互換性のため）"""
        return {}
