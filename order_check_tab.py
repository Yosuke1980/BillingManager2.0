"""発注チェックタブ

費用マスターの各レコードが発注マスタに登録されているかをチェックし、
未登録のものを簡単に追加できる機能を提供します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel,
                             QRadioButton, QButtonGroup, QLineEdit, QHeaderView,
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from database import DatabaseManager
from order_management.database_manager import OrderManagementDB
from order_management.ui.unified_order_dialog import UnifiedOrderDialog


class OrderCheckTab(QWidget):
    """発注チェックタブ"""

    # シグナル定義：発注追加時に発火
    order_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.order_db = OrderManagementDB()
        self.expense_data = []  # 費用マスターデータを保持
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # === 上部: フィルタエリア ===
        filter_layout = QHBoxLayout()

        # フィルタラジオボタン
        filter_label = QLabel("表示フィルタ:")
        filter_layout.addWidget(filter_label)

        self.filter_group = QButtonGroup()
        self.rb_all = QRadioButton("全て表示")
        self.rb_no_order = QRadioButton("未登録のみ")
        self.rb_has_order = QRadioButton("登録済のみ")

        self.rb_all.setChecked(True)
        self.filter_group.addButton(self.rb_all)
        self.filter_group.addButton(self.rb_no_order)
        self.filter_group.addButton(self.rb_has_order)

        self.rb_all.toggled.connect(self.apply_filter)
        self.rb_no_order.toggled.connect(self.apply_filter)
        self.rb_has_order.toggled.connect(self.apply_filter)

        filter_layout.addWidget(self.rb_all)
        filter_layout.addWidget(self.rb_no_order)
        filter_layout.addWidget(self.rb_has_order)

        filter_layout.addSpacing(20)

        # 検索ボックス
        search_label = QLabel("検索:")
        filter_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("番組名または取引先名で検索")
        self.search_input.textChanged.connect(self.apply_filter)
        self.search_input.setMinimumWidth(250)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        # 再読み込みボタン
        reload_btn = QPushButton("🔄 再チェック")
        reload_btn.clicked.connect(self.load_data)
        reload_btn.setMinimumWidth(100)
        filter_layout.addWidget(reload_btn)

        layout.addLayout(filter_layout)

        # === 中央: テーブル ===
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "番組名", "費用項目", "取引先名", "金額",
            "契約期間", "支払タイプ", "発注状況", "アクション", "元の案件名"
        ])

        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 費用項目
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 取引先名
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 契約期間

        # IDカラムと元の案件名カラムを非表示
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(9, True)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 編集不可

        layout.addWidget(self.table)

        # === 下部: 統計情報 ===
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("全体: 0件 | 登録済: 0件 | 未登録: 0件")
        self.stats_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def load_data(self):
        """費用マスターデータを読み込み"""
        self.expense_data = self.db.get_expense_master_with_order_status()
        self.apply_filter()
        self.update_statistics()

    def apply_filter(self):
        """フィルタを適用してテーブルを更新"""
        filter_type = None
        if self.rb_no_order.isChecked():
            filter_type = "no_order"
        elif self.rb_has_order.isChecked():
            filter_type = "has_order"

        search_term = self.search_input.text().lower()

        # フィルタリング
        filtered_data = []
        for item in self.expense_data:
            # フィルタタイプチェック
            if filter_type == "no_order" and item['has_order']:
                continue
            if filter_type == "has_order" and not item['has_order']:
                continue

            # 検索キーワードチェック
            if search_term:
                if (search_term not in item['program_name'].lower() and
                    search_term not in item['payee'].lower()):
                    continue

            filtered_data.append(item)

        # テーブル更新
        self.populate_table(filtered_data)

    def populate_table(self, data):
        """テーブルにデータを表示"""
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            # ID (非表示)
            self.table.setItem(row, 0, QTableWidgetItem(str(item['master_id'])))

            # 番組名
            self.table.setItem(row, 1, QTableWidgetItem(item['program_name']))

            # 費用項目
            self.table.setItem(row, 2, QTableWidgetItem(item['item_name']))

            # 取引先名
            self.table.setItem(row, 3, QTableWidgetItem(item['payee']))

            # 金額
            amount_text = f"{int(item['amount']):,}円" if item['amount'] else "-"
            self.table.setItem(row, 4, QTableWidgetItem(amount_text))

            # 契約期間
            period_text = ""
            if item['start_date'] and item['end_date']:
                period_text = f"{item['start_date']} ~ {item['end_date']}"
            elif item['start_date']:
                period_text = f"{item['start_date']} ~"
            self.table.setItem(row, 5, QTableWidgetItem(period_text))

            # 支払タイプ
            self.table.setItem(row, 6, QTableWidgetItem(item['payment_type']))

            # 発注状況
            status_text = "✓ 登録済" if item['has_order'] else "✕ 未登録"
            status_item = QTableWidgetItem(status_text)
            if item['has_order']:
                status_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                status_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            self.table.setItem(row, 7, status_item)

            # アクションボタン
            if not item['has_order']:
                add_btn = QPushButton("発注追加")
                add_btn.clicked.connect(lambda checked, r=row: self.add_order_contract(r))
                add_btn.setMinimumWidth(80)
                self.table.setCellWidget(row, 8, add_btn)
            else:
                self.table.setItem(row, 8, QTableWidgetItem(""))

            # 元の案件名 (非表示)
            self.table.setItem(row, 9, QTableWidgetItem(item['project_name_full']))

            # 行全体の背景色
            for col in range(self.table.columnCount()):
                cell_item = self.table.item(row, col)
                if cell_item and not item['has_order']:
                    cell_item.setBackground(QColor(255, 240, 240))  # とても薄い赤

    def add_order_contract(self, row):
        """発注契約を追加"""
        # 現在表示されているデータから該当行を取得
        master_id = int(self.table.item(row, 0).text())

        # expense_dataから該当レコードを取得
        expense_item = None
        for item in self.expense_data:
            if item['master_id'] == master_id:
                expense_item = item
                break

        if not expense_item:
            QMessageBox.warning(self, "エラー", "費用マスターデータが見つかりません。")
            return

        # ダイアログを開いて費用マスターの情報を自動入力
        self.open_order_dialog_with_data(expense_item)

    def open_order_dialog_with_data(self, expense_item):
        """費用マスターのデータを使って発注ダイアログを開く"""
        # 発注種別を費用項目名から推定
        item_name = expense_item['item_name']

        # デフォルトはレギュラー制作発注書
        category = "レギュラー制作発注書"

        # 費用項目名から判定
        if "出演" in item_name:
            category = "レギュラー出演契約書"
        elif "制作" in item_name or "構成" in item_name or "演出" in item_name:
            category = "レギュラー制作発注書"

        # 発注ダイアログを開く前に、番組と取引先の存在を確認
        program_name = expense_item['program_name']
        payee_name = expense_item['payee']

        # 番組の存在確認
        programs = self.order_db.get_programs()
        program_id = None
        for prog in programs:
            if prog[1] == program_name:  # prog[1] = name
                program_id = prog[0]
                break

        # 番組が存在しない場合、確認ダイアログを表示
        use_custom_name = False
        if program_id is None:
            # カスタムダイアログで3つの選択肢を提供
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

            choice_dialog = QDialog(self)
            choice_dialog.setWindowTitle("番組未登録")
            choice_dialog.setMinimumWidth(400)

            layout = QVBoxLayout()

            message = QLabel(
                f"番組「{program_name}」が番組マスタに登録されていません。\n\n"
                f"どのように処理しますか？"
            )
            message.setWordWrap(True)
            layout.addWidget(message)

            # 選択肢1: 番組マスタに自動追加
            auto_add_btn = QPushButton("1. 番組マスタに自動追加して発注を作成")
            auto_add_btn.clicked.connect(lambda: choice_dialog.done(1))
            layout.addWidget(auto_add_btn)

            # 選択肢2: 自由入力モードで案件名として登録
            custom_name_btn = QPushButton("2. 自由入力モードで案件名として登録")
            custom_name_btn.clicked.connect(lambda: choice_dialog.done(2))
            layout.addWidget(custom_name_btn)

            # 選択肢3: キャンセル
            cancel_btn = QPushButton("3. キャンセル")
            cancel_btn.clicked.connect(lambda: choice_dialog.done(0))
            layout.addWidget(cancel_btn)

            choice_dialog.setLayout(layout)
            choice = choice_dialog.exec_()

            if choice == 0:
                # キャンセル
                return
            elif choice == 1:
                # 番組マスタに自動追加
                try:
                    # 既に同じ名前の番組が存在するか再チェック
                    # （ユーザーが選択肢を選んでいる間に別のユーザーが追加した可能性を考慮）
                    programs = self.order_db.get_programs()
                    for prog in programs:
                        if prog[1] == program_name:  # prog[1] = name
                            program_id = prog[0]
                            QMessageBox.information(
                                self, "情報",
                                f"番組「{program_name}」は既に番組マスタに存在していました。"
                            )
                            use_custom_name = False
                            break
                    else:
                        # broadcast_daysがある場合は使用、なければ空文字
                        broadcast_days = expense_item.get('broadcast_days', '')

                        # 番組マスタに追加
                        program_data = {
                            'name': program_name,
                            'broadcast_days': broadcast_days,
                            'notes': '発注チェックから自動追加'
                        }
                        program_id = self.order_db.save_program(program_data)

                        QMessageBox.information(
                            self, "成功",
                            f"番組「{program_name}」を番組マスタに追加しました。"
                        )
                        use_custom_name = False
                except Exception as e:
                    # UNIQUE constraint違反の場合
                    error_msg = str(e)
                    if 'UNIQUE constraint failed' in error_msg or 'UNIQUE' in error_msg:
                        QMessageBox.warning(
                            self, "番組名が重複",
                            f"番組「{program_name}」は既に番組マスタに登録されています。\n"
                            f"別の番組名を使用するか、自由入力モードを選択してください。"
                        )
                    else:
                        QMessageBox.critical(
                            self, "エラー",
                            f"番組マスタへの追加に失敗しました:\n{error_msg}"
                        )
                    return
            elif choice == 2:
                # 自由入力モード
                use_custom_name = True

        # 取引先の存在確認
        partners = self.order_db.get_partners()
        partner_id = None
        for partner in partners:
            if partner[1] == payee_name:  # partner[1] = name
                partner_id = partner[0]
                break

        if partner_id is None:
            QMessageBox.warning(
                self, "取引先未登録",
                f"取引先「{payee_name}」が取引先マスタに登録されていません。\n"
                f"先に取引先マスタに登録してから、再度発注追加を行ってください。"
            )
            return

        # 統合発注ダイアログを開く（推定された種別で）
        dialog = UnifiedOrderDialog(self, category=category)

        # 自動入力
        if use_custom_name:
            # 自由入力モード
            dialog.rb_custom.setChecked(True)
            dialog.custom_project_name.setText(program_name)
        else:
            # 番組選択モード
            dialog.rb_program.setChecked(True)

            # 番組が自動追加された場合、コンボボックスを再読み込み
            if program_id:
                # 番組コンボボックスを再読み込み
                dialog.program_combo.clear()
                dialog.load_programs()

                # 番組コンボボックスで該当番組を選択
                for i in range(dialog.program_combo.count()):
                    if dialog.program_combo.itemData(i) == program_id:
                        dialog.program_combo.setCurrentIndex(i)
                        break

        # 費用項目
        dialog.item_name.setText(expense_item['item_name'])

        # 取引先
        for i in range(dialog.partner_combo.count()):
            if dialog.partner_combo.itemData(i) == partner_id:
                dialog.partner_combo.setCurrentIndex(i)
                break

        # 契約開始日・終了日（レギュラーの場合のみ）
        if category.startswith("レギュラー"):
            if expense_item['start_date']:
                from PyQt5.QtCore import QDate
                start_date = QDate.fromString(expense_item['start_date'], "yyyy-MM-dd")
                dialog.contract_start_date.setDate(start_date)

            if expense_item['end_date']:
                from PyQt5.QtCore import QDate
                end_date = QDate.fromString(expense_item['end_date'], "yyyy-MM-dd")
                dialog.contract_end_date.setDate(end_date)

            # 支払タイプ（レギュラーの場合のみ）
            if expense_item['payment_type']:
                dialog.payment_type.setCurrentText(expense_item['payment_type'])

            # 支払タイミング（レギュラーの場合のみ）
            if expense_item['payment_timing']:
                dialog.payment_timing.setCurrentText(expense_item['payment_timing'])
        else:
            # 単発の場合は実施日を設定
            # 開始日がある場合は実施日として使用
            if expense_item['start_date']:
                from PyQt5.QtCore import QDate
                impl_date = QDate.fromString(expense_item['start_date'], "yyyy-MM-dd")
                dialog.implementation_date.setDate(impl_date)

            # 金額を設定
            if expense_item['amount']:
                dialog.spot_amount.setValue(float(expense_item['amount']))

        # ダイアログを表示
        if dialog.exec_():
            # 保存成功したら再読み込み
            QMessageBox.information(self, "成功", "発注契約を追加しました。")
            self.load_data()

            # シグナルを発火して、発注書マスタを更新
            self.order_added.emit()

    def update_statistics(self):
        """統計情報を更新"""
        total = len(self.expense_data)
        has_order = sum(1 for item in self.expense_data if item['has_order'])
        no_order = total - has_order

        self.stats_label.setText(
            f"全体: {total}件 | 登録済: {has_order}件 | 未登録: {no_order}件"
        )
