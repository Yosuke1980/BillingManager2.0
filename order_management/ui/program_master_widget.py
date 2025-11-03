"""番組マスターウィジェット

番組マスターの一覧表示・編集を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.program_edit_dialog import ProgramEditDialog
import csv
import codecs


class ProgramMasterWidget(QWidget):
    """番組マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_programs()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フィルターとボタン
        top_layout = QHBoxLayout()

        # 検索
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("番組名で検索...")
        self.search_edit.textChanged.connect(self.load_programs)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_edit)

        # ステータスフィルター
        status_label = QLabel("ステータス:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("全て", "")
        self.status_filter.addItem("放送中", "放送中")
        self.status_filter.addItem("終了", "終了")
        self.status_filter.currentIndexChanged.connect(self.load_programs)
        top_layout.addWidget(status_label)
        top_layout.addWidget(self.status_filter)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")
        self.export_csv_button = QPushButton("CSV出力")
        self.import_csv_button = QPushButton("CSV読込")

        self.add_button.clicked.connect(self.add_program)
        self.edit_button.clicked.connect(self.edit_program)
        self.delete_button.clicked.connect(self.delete_program)
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "番組名", "開始日", "終了日", "放送時間", "放送曜日", "ステータス"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_program)

        # ID列を非表示
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_programs(self):
        """番組一覧を読み込み（階層表示対応）"""
        search_term = self.search_edit.text()
        status = self.status_filter.currentData()

        # 階層情報付きで番組を取得
        programs = self.db.get_programs_with_hierarchy(search_term, "", True)

        # ステータスフィルタを適用（SQL側でフィルタできないため）
        if status:
            programs = [p for p in programs if p[7] == status]

        # 階層順にソート（親番組の直後にその子番組を配置）
        programs = self._sort_programs_hierarchically(programs)

        self.table.setRowCount(len(programs))

        for row, program in enumerate(programs):
            # program: (id, name, description, start_date, end_date,
            #           broadcast_time, broadcast_days, status,
            #           program_type, parent_program_id, parent_name)
            program_id = program[0]
            name = program[1] or ""
            start_date = program[3] or ""
            end_date = program[4] or ""
            broadcast_time = program[5] or ""
            broadcast_days = program[6] or ""
            status_text = program[7] or ""
            program_type = program[8] if len(program) > 8 else ""
            parent_program_id = program[9] if len(program) > 9 else None

            # コーナー（子番組）の場合は字下げして表示
            display_name = name
            if parent_program_id:
                display_name = f"　└ {name}"

            self.table.setItem(row, 0, self._create_readonly_item(str(program_id)))
            self.table.setItem(row, 1, self._create_readonly_item(display_name))
            self.table.setItem(row, 2, self._create_readonly_item(start_date))
            self.table.setItem(row, 3, self._create_readonly_item(end_date))
            self.table.setItem(row, 4, self._create_readonly_item(broadcast_time))
            self.table.setItem(row, 5, self._create_readonly_item(broadcast_days))
            self.table.setItem(row, 6, self._create_readonly_item(status_text))

        self.table.resizeColumnsToContents()

        # 統計情報を更新
        self._update_stats()

    def _sort_programs_hierarchically(self, programs):
        """番組を階層順にソート（親番組の直後にその子番組を配置）

        Args:
            programs: 番組リスト（階層情報付き）

        Returns:
            階層順にソートされた番組リスト
        """
        # 親番組（parent_program_id が None）と子番組を分離
        parent_programs = []
        children_by_parent = {}

        for program in programs:
            parent_program_id = program[9] if len(program) > 9 else None

            if parent_program_id is None:
                # 親番組
                parent_programs.append(program)
            else:
                # 子番組（コーナー）
                if parent_program_id not in children_by_parent:
                    children_by_parent[parent_program_id] = []
                children_by_parent[parent_program_id].append(program)

        # 親番組を名前順にソート
        parent_programs.sort(key=lambda p: p[1] or "")

        # 階層順に結合
        result = []
        for parent in parent_programs:
            parent_id = parent[0]
            result.append(parent)

            # この親番組の子番組（コーナー）を追加
            if parent_id in children_by_parent:
                children = children_by_parent[parent_id]
                # 子番組も名前順にソート
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
            status_item = self.table.item(row, 6)
            if status_item:
                status = status_item.text()
                if status == "放送中":
                    broadcasting += 1
                elif status == "終了":
                    ended += 1

        stats_text = f"登録番組数: {total}件 (放送中: {broadcasting}件 / 終了: {ended}件)"
        self.stats_label.setText(stats_text)

    def add_program(self):
        """新規番組追加"""
        dialog = ProgramEditDialog(self)
        if dialog.exec_():
            self.load_programs()

    def edit_program(self):
        """番組編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する番組を選択してください")
            return

        program_id = int(self.table.item(current_row, 0).text())
        program = self.db.get_program_by_id(program_id)

        if not program:
            QMessageBox.warning(self, "エラー", "番組情報の取得に失敗しました")
            return

        dialog = ProgramEditDialog(self, program)
        if dialog.exec_():
            self.load_programs()

    def delete_program(self):
        """番組削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する番組を選択してください")
            return

        program_id = int(self.table.item(current_row, 0).text())
        program_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"番組「{program_name}」を削除してもよろしいですか?\n\n"
            f"※関連する出演者・制作会社情報も削除されます。\n"
            f"※関連する案件が存在する場合は削除できません。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_program(program_id)
                self.load_programs()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{e}")

    def export_to_csv(self):
        """番組データをCSVに出力"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                "番組マスター.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # 全ての番組データを取得（階層情報含む）
            programs = self.db.get_programs("", "")

            # 親番組名のマップを作成
            program_map = {p[0]: p[1] for p in programs}

            # CSV出力（UTF-8 with BOM）
            with codecs.open(file_path, 'w', 'utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow([
                    'ID', '番組名', '説明', '開始日', '終了日',
                    '放送時間', '放送曜日', 'ステータス', '番組種別', '親番組ID', '親番組名'
                ])

                # データ行
                for program in programs:
                    # program: (id, name, description, start_date, end_date,
                    #           broadcast_time, broadcast_days, status,
                    #           program_type, parent_program_id)
                    parent_program_name = ""
                    if len(program) > 9 and program[9]:
                        parent_program_name = program_map.get(program[9], "")

                    writer.writerow([
                        program[0],  # ID
                        program[1] or '',  # 番組名
                        program[2] or '',  # 説明
                        program[3] or '',  # 開始日
                        program[4] or '',  # 終了日
                        program[5] or '',  # 放送時間
                        program[6] or '',  # 放送曜日
                        program[7] or '',  # ステータス
                        program[8] if len(program) > 8 else 'レギュラー',  # 番組種別
                        program[9] if len(program) > 9 else '',  # 親番組ID
                        parent_program_name  # 親番組名
                    ])

            QMessageBox.information(
                self,
                "CSV出力完了",
                f"{len(programs)}件の番組データをCSVに出力しました。\n\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{e}")

    def import_from_csv(self):
        """CSVから番組データを読み込み"""
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
            result = self.db.import_programs_from_csv(csv_data, overwrite)

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
            self.load_programs()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV読み込みに失敗しました:\n{e}")
