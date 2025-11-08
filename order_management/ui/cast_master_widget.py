"""出演者マスターウィジェット"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QMessageBox, QLabel, QLineEdit, QFileDialog, QHeaderView, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.cast_edit_dialog import CastEditDialog
from order_management.ui.ui_helpers import create_readonly_table_item
import csv
import codecs


class CastMasterWidget(QWidget):
    """出演者マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_casts()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 上部レイアウト
        top_layout = QHBoxLayout()

        # 検索
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("出演者名、所属事務所で検索...")
        self.search_edit.textChanged.connect(self.load_casts)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_edit)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")
        self.export_csv_button = QPushButton("CSV出力")
        self.import_csv_button = QPushButton("CSV読込")

        self.add_button.clicked.connect(self.add_cast)
        self.edit_button.clicked.connect(self.edit_cast)
        self.delete_button.clicked.connect(self.delete_cast)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.import_csv_button.clicked.connect(self.import_from_csv)

        top_layout.addWidget(self.add_button)
        top_layout.addWidget(self.edit_button)
        top_layout.addWidget(self.delete_button)
        top_layout.addWidget(self.export_csv_button)
        top_layout.addWidget(self.import_csv_button)

        layout.addLayout(top_layout)

        # 統計情報
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "出演者名", "所属事務所", "所属コード", "備考"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # 複数選択を許可
        self.table.doubleClicked.connect(self.edit_cast)
        self.table.setColumnHidden(0, True)

        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 所属コード
        # 名前系はStretch
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 出演者名
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 所属事務所
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 備考

        layout.addWidget(self.table)

    def load_casts(self):
        """出演者一覧を読み込み"""
        search_term = self.search_edit.text()
        casts = self.db.get_casts(search_term)

        self.table.setRowCount(len(casts))

        for row, cast in enumerate(casts):
            # cast: (id, name, partner_name, partner_code, notes)
            self.table.setItem(row, 0, create_readonly_table_item(str(cast[0])))
            self.table.setItem(row, 1, create_readonly_table_item(cast[1] or ""))
            self.table.setItem(row, 2, create_readonly_table_item(cast[2] or ""))
            self.table.setItem(row, 3, create_readonly_table_item(cast[3] or ""))
            self.table.setItem(row, 4, create_readonly_table_item(cast[4] or ""))

        self.table.resizeColumnsToContents()
        self.stats_label.setText(f"登録出演者数: {len(casts)}件")

    def add_cast(self):
        """新規出演者追加"""
        dialog = CastEditDialog(self)
        if dialog.exec_():
            self.load_casts()

    def edit_cast(self):
        """出演者編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する出演者を選択してください")
            return

        cast_id = int(self.table.item(current_row, 0).text())
        cast = self.db.get_cast_by_id(cast_id)

        if not cast:
            QMessageBox.warning(self, "エラー", "出演者情報の取得に失敗しました")
            return

        dialog = CastEditDialog(self, cast)
        if dialog.exec_():
            self.load_casts()

    def delete_cast(self):
        """出演者削除（複数選択対応）"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "削除する出演者を選択してください")
            return

        # 選択された出演者のIDと名前を取得
        casts_to_delete = []
        for index in selected_rows:
            row = index.row()
            cast_id = int(self.table.item(row, 0).text())
            cast_name = self.table.item(row, 1).text()
            casts_to_delete.append((cast_id, cast_name))

        # 確認メッセージ
        if len(casts_to_delete) == 1:
            message = f"出演者「{casts_to_delete[0][1]}」を削除してもよろしいですか?\n\n"
        else:
            message = f"{len(casts_to_delete)}件の出演者を削除してもよろしいですか?\n\n"
            message += "削除対象:\n"
            for _, name in casts_to_delete[:5]:  # 最初の5件のみ表示
                message += f"  • {name}\n"
            if len(casts_to_delete) > 5:
                message += f"  ...他{len(casts_to_delete) - 5}件\n\n"

        message += "※関連する番組が存在する場合は削除できません。"

        reply = QMessageBox.question(
            self, "確認", message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_messages = []

            for cast_id, cast_name in casts_to_delete:
                try:
                    self.db.delete_cast(cast_id)
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"{cast_name}: {str(e)}")

            # 結果を表示
            if success_count > 0:
                self.load_casts()

            if error_messages:
                error_text = "\n".join(error_messages)
                QMessageBox.warning(
                    self, "削除結果",
                    f"{success_count}件削除しました。\n\n以下の削除に失敗しました:\n{error_text}"
                )
            elif success_count > 0:
                QMessageBox.information(
                    self, "成功",
                    f"{success_count}件の出演者を削除しました。"
                )

    def export_to_csv(self):
        """出演者データをCSVに出力"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                "出演者マスター.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # 全ての出演者データを取得
            casts = self.db.get_casts("")

            # CSV出力（UTF-8 with BOM）
            with codecs.open(file_path, 'w', 'utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow(['ID', '出演者名', '所属事務所', '所属コード', '備考'])

                # データ行
                for cast in casts:
                    writer.writerow([
                        cast[0],  # ID
                        cast[1] or '',  # 出演者名
                        cast[2] or '',  # 所属事務所
                        cast[3] or '',  # 所属コード
                        cast[4] or ''   # 備考
                    ])

            QMessageBox.information(
                self,
                "CSV出力完了",
                f"{len(casts)}件の出演者データをCSVに出力しました。\n\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{e}")

    def import_from_csv(self):
        """CSVから出演者データを読み込み"""
        try:
            # ファイル選択ダイアログ
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "CSV読み込み",
                "",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # CSV読み込み
            csv_data = []
            with codecs.open(file_path, 'r', 'utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    csv_data.append(row)

            if not csv_data:
                QMessageBox.warning(self, "警告", "CSVファイルにデータがありません")
                return

            # 上書き/追記の選択ダイアログを表示
            reply = QMessageBox.question(
                self,
                'インポート方法の選択',
                f'{len(csv_data)}件のデータを読み込みます。\n\n'
                '既存のデータをどうしますか？\n\n'
                '「はい」: 上書き（既存データを削除して新規データのみ）\n'
                '「いいえ」: 追記（既存データを保持してIDがあれば更新、なければ追加）',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )

            if reply == QMessageBox.Cancel:
                return

            overwrite = (reply == QMessageBox.Yes)

            # データベースにインポート
            result = self.db.import_casts_from_csv(csv_data, overwrite)

            # 結果を表示
            message = f"CSV読み込み完了\n\n"
            message += f"成功: {result['success']}件\n"
            message += f"  - 新規追加: {result['inserted']}件\n"
            message += f"  - 更新: {result['updated']}件\n"
            message += f"スキップ: {result['skipped']}件\n"

            if result['errors']:
                message += f"\nエラー詳細:\n"
                for error in result['errors'][:10]:  # 最初の10件のみ表示
                    message += f"  - {error['row']}行目: {error['reason']}\n"
                if len(result['errors']) > 10:
                    message += f"  ... 他{len(result['errors']) - 10}件のエラー\n"

            QMessageBox.information(self, "CSV読み込み完了", message)

            # データを再読み込み
            self.load_casts()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV読み込みに失敗しました:\n{e}")
