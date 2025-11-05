"""番組・イベント管理ウィジェット

番組・イベントの一覧表示・編集を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.production_edit_dialog import ProductionEditDialog
import csv
import codecs


class ProductionMasterWidget(QWidget):
    """番組・イベント管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_productions()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フィルターとボタン
        top_layout = QHBoxLayout()

        # 検索
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("番組・イベント名で検索...")
        self.search_edit.textChanged.connect(self.load_productions)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_edit)

        # 種別フィルター
        type_label = QLabel("種別:")
        self.type_filter = QComboBox()
        self.type_filter.addItem("全て", "")
        self.type_filter.addItem("レギュラー番組", "レギュラー番組")
        self.type_filter.addItem("特別番組", "特別番組")
        self.type_filter.addItem("イベント", "イベント")
        self.type_filter.addItem("公開放送", "公開放送")
        self.type_filter.addItem("公開収録", "公開収録")
        self.type_filter.addItem("特別企画", "特別企画")
        self.type_filter.currentIndexChanged.connect(self.load_productions)
        top_layout.addWidget(type_label)
        top_layout.addWidget(self.type_filter)

        # ステータスフィルター
        status_label = QLabel("ステータス:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("全て", "")
        self.status_filter.addItem("放送中", "放送中")
        self.status_filter.addItem("終了", "終了")
        self.status_filter.currentIndexChanged.connect(self.load_productions)
        top_layout.addWidget(status_label)
        top_layout.addWidget(self.status_filter)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")
        self.export_csv_button = QPushButton("CSV出力")
        self.import_csv_button = QPushButton("CSV読込")

        self.add_button.clicked.connect(self.add_production)
        self.edit_button.clicked.connect(self.edit_production)
        self.delete_button.clicked.connect(self.delete_production)
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "番組・イベント名", "種別", "開始日", "終了日", "放送時間", "放送曜日", "ステータス"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_production)

        # ID列を非表示
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_productions(self):
        """番組・イベント一覧を読み込み（階層表示対応）"""
        search_term = self.search_edit.text()
        production_type = self.type_filter.currentData()
        status = self.status_filter.currentData()

        # 階層情報付きで制作物を取得
        productions = self.db.get_productions_with_hierarchy(search_term, production_type, True)

        # ステータスフィルタを適用（SQL側でフィルタできないため）
        if status:
            productions = [p for p in productions if p[10] == status]

        # 階層順にソート（親制作物の直後にその子制作物を配置）
        productions = self._sort_productions_hierarchically(productions)

        self.table.setRowCount(len(productions))

        for row, production in enumerate(productions):
            # production: (id, name, description, production_type, start_date, end_date,
            #              start_time, end_time, broadcast_time, broadcast_days, status, parent_production_id)
            production_id = production[0]
            name = production[1] or ""
            production_type_text = production[3] or ""
            start_date = production[4] or ""
            end_date = production[5] or ""
            broadcast_time = production[8] or ""
            broadcast_days = production[9] or ""
            status_text = production[10] or ""
            parent_production_id = production[11] if len(production) > 11 else None

            # 子制作物の場合は字下げして表示
            display_name = name
            if parent_production_id:
                display_name = f"　└ {name}"

            self.table.setItem(row, 0, self._create_readonly_item(str(production_id)))
            self.table.setItem(row, 1, self._create_readonly_item(display_name))
            self.table.setItem(row, 2, self._create_readonly_item(production_type_text))
            self.table.setItem(row, 3, self._create_readonly_item(start_date))
            self.table.setItem(row, 4, self._create_readonly_item(end_date))
            self.table.setItem(row, 5, self._create_readonly_item(broadcast_time))
            self.table.setItem(row, 6, self._create_readonly_item(broadcast_days))
            self.table.setItem(row, 7, self._create_readonly_item(status_text))

        self.table.resizeColumnsToContents()

        # 統計情報を更新
        self._update_stats()

    def _sort_productions_hierarchically(self, productions):
        """制作物を階層順にソート（親制作物の直後にその子制作物を配置）

        Args:
            productions: 制作物リスト（階層情報付き）

        Returns:
            階層順にソートされた制作物リスト
        """
        # 親制作物（parent_production_id が None）と子制作物を分離
        parent_productions = []
        children_by_parent = {}

        for production in productions:
            parent_production_id = production[11] if len(production) > 11 else None

            if parent_production_id is None:
                # 親制作物
                parent_productions.append(production)
            else:
                # 子制作物
                if parent_production_id not in children_by_parent:
                    children_by_parent[parent_production_id] = []
                children_by_parent[parent_production_id].append(production)

        # 親制作物を名前順にソート
        parent_productions.sort(key=lambda p: p[1] or "")

        # 階層順に結合
        result = []
        for parent in parent_productions:
            parent_id = parent[0]
            result.append(parent)

            # この親制作物の子制作物を追加
            if parent_id in children_by_parent:
                children = children_by_parent[parent_id]
                # 子制作物も名前順にソート
                children.sort(key=lambda p: p[1] or "")
                result.extend(children)

        return result

    def _create_readonly_item(self, text):
        """読み取り専用のテーブルアイテムを作成"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _update_stats(self):
        """統計情報を更新"""
        total = self.table.rowCount()

        # ステータス別集計
        broadcasting = 0
        ended = 0
        for row in range(total):
            status_item = self.table.item(row, 7)
            if status_item:
                status = status_item.text()
                if status == "放送中":
                    broadcasting += 1
                elif status == "終了":
                    ended += 1

        stats_text = f"登録数: {total}件 (放送中: {broadcasting}件 / 終了: {ended}件)"
        self.stats_label.setText(stats_text)

    def add_production(self):
        """新規追加"""
        dialog = ProductionEditDialog(self)
        if dialog.exec_():
            self.load_productions()

    def edit_production(self):
        """編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する番組・イベントを選択してください")
            return

        production_id = int(self.table.item(current_row, 0).text())
        production = self.db.get_production_by_id(production_id)

        if not production:
            QMessageBox.warning(self, "エラー", "番組・イベント情報の取得に失敗しました")
            return

        dialog = ProductionEditDialog(self, production)
        if dialog.exec_():
            self.load_productions()

    def delete_production(self):
        """削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する番組・イベントを選択してください")
            return

        production_id = int(self.table.item(current_row, 0).text())
        production_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"番組・イベント「{production_name}」を削除してもよろしいですか?\n\n"
            f"※関連する出演者・制作会社情報も削除されます。\n"
            f"※関連する案件が存在する場合は削除できません。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_production(production_id)
                self.load_productions()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{e}")

    def export_to_csv(self):
        """制作物データをCSVに出力"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                "番組・イベントマスター.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # 全ての制作物データを取得
            productions = self.db.get_productions("", "")

            # 親制作物名のマップを作成
            production_map = {p[0]: p[1] for p in productions}

            # CSV出力（UTF-8 with BOM）
            with codecs.open(file_path, 'w', 'utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow([
                    'ID', '制作物名', '説明', '制作物種別', '開始日', '終了日',
                    '実施開始時間', '実施終了時間', '放送時間', '放送曜日', 'ステータス', '親制作物ID', '親制作物名'
                ])

                # データ行
                for production in productions:
                    # production: (id, name, description, production_type, start_date, end_date,
                    #              start_time, end_time, broadcast_time, broadcast_days, status, parent_production_id)
                    parent_production_name = ""
                    if len(production) > 11 and production[11]:
                        parent_production_name = production_map.get(production[11], "")

                    writer.writerow([
                        production[0],  # ID
                        production[1] or '',  # 制作物名
                        production[2] or '',  # 説明
                        production[3] or 'レギュラー番組',  # 制作物種別
                        production[4] or '',  # 開始日
                        production[5] or '',  # 終了日
                        production[6] or '',  # 実施開始時間
                        production[7] or '',  # 実施終了時間
                        production[8] or '',  # 放送時間
                        production[9] or '',  # 放送曜日
                        production[10] or '',  # ステータス
                        production[11] if len(production) > 11 else '',  # 親制作物ID
                        parent_production_name  # 親制作物名
                    ])

            QMessageBox.information(
                self,
                "CSV出力完了",
                f"{len(productions)}件の番組・イベントデータをCSVに出力しました。\n\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{e}")

    def import_from_csv(self):
        """CSVから制作物データを読み込み"""
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
            result = self.db.import_productions_from_csv(csv_data, overwrite)

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
            self.load_productions()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV読み込みに失敗しました:\n{e}")
