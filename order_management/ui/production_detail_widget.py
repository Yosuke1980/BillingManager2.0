"""番組詳細表示ウィジェット

月別番組一覧と選択された番組の詳細情報を表示します。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QSplitter, QTextBrowser, QFrame,
    QRadioButton, QButtonGroup, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta
from order_management.database_manager import OrderManagementDB


class ProductionDetailWidget(QWidget):
    """番組詳細表示ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        # デフォルトを前月に設定
        previous_month = datetime.now() - timedelta(days=30)
        self.current_month = previous_month.strftime('%Y-%m')
        self.current_production_id = None  # 現在選択されている番組ID
        self._setup_ui()
        self.load_productions_for_month()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 月選択・番組タイプ選択エリア
        month_layout = QHBoxLayout()

        # 表示月
        month_label = QLabel("表示月:")
        month_label.setFont(QFont("", 12, QFont.Bold))

        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(150)
        self._populate_months()
        self.month_combo.currentTextChanged.connect(self.on_month_changed)

        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_combo)
        month_layout.addSpacing(30)

        # 番組タイプ選択
        type_label = QLabel("番組タイプ:")
        type_label.setFont(QFont("", 12, QFont.Bold))
        month_layout.addWidget(type_label)

        self.one_time_radio = QRadioButton("単発番組")
        self.regular_radio = QRadioButton("レギュラー番組")
        self.one_time_radio.setChecked(True)  # デフォルトは単発

        self.type_button_group = QButtonGroup()
        self.type_button_group.addButton(self.one_time_radio)
        self.type_button_group.addButton(self.regular_radio)

        # ボタングループのクリックイベントに接続（どちらのボタンを押しても発火）
        self.type_button_group.buttonClicked.connect(self.on_type_changed)

        month_layout.addWidget(self.one_time_radio)
        month_layout.addWidget(self.regular_radio)
        month_layout.addStretch()

        layout.addLayout(month_layout)

        # 左右分割レイアウト
        splitter = QSplitter(Qt.Horizontal)

        # 左側: 番組一覧
        left_widget = self._create_production_list()
        splitter.addWidget(left_widget)

        # 右側: 詳細表示
        right_widget = self._create_detail_view()
        splitter.addWidget(right_widget)

        # 分割比率を設定 (左:右 = 1:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def _populate_months(self):
        """月選択コンボボックスにデータを設定"""
        # 過去6ヶ月から未来6ヶ月まで
        current_date = datetime.now()

        for i in range(-6, 7):
            target_date = current_date + timedelta(days=30*i)
            month_str = target_date.strftime('%Y-%m')
            display_str = target_date.strftime('%Y年%m月')
            self.month_combo.addItem(display_str, month_str)

            # 当月をデフォルトに設定
            if month_str == self.current_month:
                self.month_combo.setCurrentIndex(i + 6)

    def _create_production_list(self):
        """番組一覧ウィジェットを作成"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(widget)

        # タイトル
        title_label = QLabel("番組一覧")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(title_label)

        # リストウィジェット
        self.production_list = QListWidget()
        self.production_list.setStyleSheet("""
            QListWidget {
                font-size: 13px;
                border: 1px solid #ccc;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.production_list.currentItemChanged.connect(self.on_production_selected)
        layout.addWidget(self.production_list)

        return widget

    def _create_detail_view(self):
        """詳細表示ウィジェットを作成"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(widget)

        # タイトルと編集ボタンのレイアウト
        title_layout = QHBoxLayout()

        self.detail_title_label = QLabel("番組を選択してください")
        self.detail_title_label.setFont(QFont("", 16, QFont.Bold))
        self.detail_title_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        title_layout.addWidget(self.detail_title_label)

        # 編集ボタン
        self.edit_button = QPushButton("編集")
        self.edit_button.setFixedWidth(80)
        self.edit_button.setFixedHeight(35)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        title_layout.addWidget(self.edit_button)

        layout.addLayout(title_layout)

        # 詳細内容（HTML表示）
        self.detail_browser = QTextBrowser()
        self.detail_browser.setStyleSheet("""
            QTextBrowser {
                font-size: 13px;
                padding: 15px;
                border: 1px solid #ccc;
                background-color: white;
            }
        """)
        self.detail_browser.setOpenExternalLinks(False)
        layout.addWidget(self.detail_browser)

        return widget

    def on_month_changed(self, text):
        """月選択が変更された時の処理"""
        month_data = self.month_combo.currentData()
        if month_data:
            self.current_month = month_data
            self.load_productions_for_month()

    def on_type_changed(self, button=None):
        """番組タイプが変更された時の処理"""
        # ラジオボタンが変更されたら常に再読み込み
        self.load_productions_for_month()

    def load_productions_for_month(self):
        """指定月の番組を読み込み"""
        self.production_list.clear()
        self.detail_browser.clear()
        self.detail_title_label.setText("")

        try:
            # 番組タイプに応じて取得方法を変更
            is_regular = self.regular_radio.isChecked()

            if is_regular:
                # レギュラー番組の一覧を取得
                productions = self.db.get_regular_productions()
            else:
                # 単発番組（指定月の番組）を取得
                productions = self.db.get_productions_for_month(self.current_month)

            if not productions:
                msg = "レギュラー番組はありません" if is_regular else "この月の番組はありません"
                item = QListWidgetItem(msg)
                item.setFlags(Qt.NoItemFlags)
                self.production_list.addItem(item)
                return

            # 番組ごとにリストに追加
            for production in productions:
                production_id, name, production_type, start_date = production[:4]

                # レギュラー番組の場合は日付を表示しない
                if is_regular:
                    display_text = name
                else:
                    # 単発番組の場合は日付を整形して表示
                    if start_date:
                        try:
                            date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                            date_str = date_obj.strftime('%m月%d日')
                            display_text = f"{date_str} {name}"
                        except:
                            display_text = f"{start_date} {name}"
                    else:
                        display_text = name

                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, production_id)
                self.production_list.addItem(item)

        except Exception as e:
            print(f"番組読み込みエラー: {e}")
            import traceback
            traceback.print_exc()

    def on_production_selected(self, current, previous):
        """番組が選択された時の処理"""
        if not current:
            return

        production_id = current.data(Qt.UserRole)
        if not production_id:
            return

        try:
            # 番組詳細を取得して表示
            self.display_production_detail(production_id)
        except Exception as e:
            print(f"番組詳細表示エラー: {e}")
            import traceback
            traceback.print_exc()

    def display_production_detail(self, production_id):
        """番組詳細を表示"""
        try:
            # 現在選択されている番組IDを保存
            self.current_production_id = production_id

            # 編集ボタンを有効化
            self.edit_button.setEnabled(True)

            # 番組基本情報を取得
            production = self.db.get_production_by_id(production_id)
            if not production:
                self.detail_browser.setHtml("<p>番組情報が見つかりません</p>")
                self.edit_button.setEnabled(False)
                return

            # タイトルを更新
            self.detail_title_label.setText(production['name'])

            # レギュラー番組かどうかで表示を変える
            is_regular = self.regular_radio.isChecked()

            # HTML形式で詳細を生成
            if is_regular:
                html = self._generate_regular_detail_html(production, production_id)
            else:
                html = self._generate_detail_html(production, production_id)

            self.detail_browser.setHtml(html)

        except Exception as e:
            print(f"詳細表示エラー: {e}")
            import traceback
            traceback.print_exc()
            self.detail_browser.setHtml(f"<p>エラーが発生しました: {e}</p>")

    def _generate_detail_html(self, production, production_id):
        """単発番組詳細のHTMLを生成（新デザイン対応）"""
        html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "メイリオ", "Meiryo", sans-serif;
                    font-size: 13px;
                    line-height: 1.3;
                }
                .info-row {
                    margin: 3px 0;
                }
                .label {
                    font-weight: bold;
                    margin-right: 8px;
                }
                .section-title {
                    font-weight: bold;
                    margin-top: 12px;
                    margin-bottom: 4px;
                    font-size: 14px;
                }
                .item {
                    margin-left: 20px;
                    margin-top: 1px;
                }
            </style>
        </head>
        <body>
        """

        # 日時
        if production.get('start_date'):
            try:
                date_obj = datetime.strptime(production['start_date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%m月%d日')
                weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]

                time_str = ""
                start_time = production.get('start_time', '')
                end_time = production.get('end_time', '')
                broadcast_time = production.get('broadcast_time', '')

                if start_time and start_time != "00:00:00" and end_time and end_time != "00:00:00":
                    time_str = f"{start_time}～{end_time}"
                elif broadcast_time and broadcast_time != "00:00:00":
                    time_str = f"{broadcast_time}"

                html += f'<div class="info-row"><span class="label">日時</span>{date_str}（{weekday}）{time_str}</div>'
            except:
                pass

        # 説明
        if production.get('description'):
            html += f'<div class="info-row"><span class="label">説明</span>{production["description"]}</div>'

        # 出演者セクション（役割 名前 金額の形式）
        expenses = self.db.get_expenses_by_production(production_id)
        cast_expenses = [e for e in expenses if '出演' in (e.get('work_type', '') or '')] if expenses else []

        if cast_expenses:
            html += '<div class="section-title">出演者</div>'
            for expense in cast_expenses:
                # cast_nameがあればそれを使用、なければpartner_nameまたはitem_nameから抽出
                cast_name = expense.get('cast_name', '') or expense.get('partner_name', '')
                role = expense.get('role', '') or 'MC'  # デフォルトはMC
                amount = expense.get('amount', 0)
                amount_str = f"{int(amount):,}円" if amount else "未定"
                html += f'<div class="item">{role}　{cast_name}　{amount_str}</div>'

        # 制作セクション（項目名 会社名 金額の形式）
        production_expenses = [e for e in expenses if '出演' not in (e.get('work_type', '') or '')] if expenses else []

        if production_expenses:
            html += '<div class="section-title">制作</div>'
            for expense in production_expenses:
                item_name = expense.get('item_name', '')
                partner_name = expense.get('partner_name', '')
                amount = expense.get('amount', 0)
                amount_str = f"{int(amount):,}円" if amount else "未定"
                html += f'<div class="item">{item_name}　{partner_name}　{amount_str}</div>'

        html += """
        </body>
        </html>
        """

        return html

    def _generate_regular_detail_html(self, production, production_id):
        """レギュラー番組詳細のHTMLを生成（新デザイン対応）"""
        html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "メイリオ", "Meiryo", sans-serif;
                    font-size: 13px;
                    line-height: 1.3;
                }
                .info-row {
                    margin: 3px 0;
                }
                .label {
                    font-weight: bold;
                    margin-right: 8px;
                    display: inline-block;
                    min-width: 70px;
                }
                .section-title {
                    font-weight: bold;
                    margin-top: 12px;
                    margin-bottom: 4px;
                    font-size: 14px;
                }
                .item {
                    margin-left: 20px;
                    margin-top: 1px;
                }
                .corner-section {
                    border: 1px solid #ccc;
                    padding: 10px;
                    margin-top: 15px;
                    background-color: #f9f9f9;
                }
                .corner-title {
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 6px;
                }
            </style>
        </head>
        <body>
        """

        # 放送期間
        period_str = ""
        if production.get('start_date'):
            try:
                date_obj = datetime.strptime(production['start_date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%m月%d日')
                weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
                period_str = f"{date_str}（{weekday}）〜"
            except:
                period_str = f"{production['start_date']}〜"

        # 放送中かどうか
        status = production.get('status', '')
        if status == 'active' or not production.get('end_date'):
            period_str += "　放送中"
        elif production.get('end_date'):
            period_str += f"　{production['end_date']}"

        if period_str:
            html += f'<div class="info-row"><span class="label">放送期間</span>{period_str}</div>'

        # 放送時間（曜日別に表示）
        broadcast_days = production.get('broadcast_days', '') or production.get('broadcast_day', '')
        start_time = production.get('start_time', '')
        end_time = production.get('end_time', '')
        broadcast_time = production.get('broadcast_time', '')

        if broadcast_days:
            html += f'<div class="info-row"><span class="label">放送時間</span></div>'

            # 曜日ごとに分けて表示
            days_list = broadcast_days.split(',') if ',' in broadcast_days else [broadcast_days]

            for day in days_list:
                day = day.strip()
                time_str = ""
                if start_time and start_time != "00:00:00" and end_time and end_time != "00:00:00":
                    time_str = f"{start_time}~{end_time}"
                elif broadcast_time and broadcast_time != "00:00:00":
                    time_str = broadcast_time

                html += f'<div class="item">{day}　{time_str}</div>'

        # 説明
        if production.get('description'):
            html += f'<div class="info-row"><span class="label">説明</span>{production["description"]}</div>'

        # 出演者セクション（名前 金額の形式）
        all_expenses = self.db.get_expenses_by_production(production_id)
        cast_expenses = [e for e in all_expenses if '出演' in (e.get('work_type', '') or '')] if all_expenses else []

        if cast_expenses:
            html += '<div class="section-title">出演者</div>'
            # 重複を除外して出演者と金額を表示
            cast_dict = {}
            for expense in cast_expenses:
                cast_name = expense.get('cast_name', '') or expense.get('partner_name', '')
                amount = expense.get('amount', 0)
                if cast_name and cast_name not in cast_dict:
                    cast_dict[cast_name] = amount

            for cast_name, amount in cast_dict.items():
                amount_str = f"{int(amount):,}円" if amount else "未定"
                html += f'<div class="item">{cast_name}　{amount_str}</div>'

        # 制作セクション（会社名 金額の形式）
        production_expenses = [e for e in all_expenses if '出演' not in (e.get('work_type', '') or '')] if all_expenses else []

        if production_expenses:
            html += '<div class="section-title">制作</div>'
            # 重複を除外して制作会社と金額を表示
            company_dict = {}
            for expense in production_expenses:
                partner_name = expense.get('partner_name', '')
                amount = expense.get('amount', 0)
                if partner_name and partner_name not in company_dict:
                    company_dict[partner_name] = amount

            for partner_name, amount in company_dict.items():
                amount_str = f"{int(amount):,}円" if amount else "未定"
                html += f'<div class="item">{partner_name}　{amount_str}</div>'

        # コーナーセクション
        corners = self.db.get_corners_by_parent_production(production_id)
        if corners:
            for corner in corners:
                corner_id, corner_name, corner_start_date, corner_end_date = corner

                html += '<div class="corner-section">'
                html += f'<div class="corner-title">［コーナー］<br>{corner_name}</div>'

                # コーナーの放送時間
                corner_broadcast_days = None
                corner_data = self.db.get_production_by_id(corner_id)
                if corner_data:
                    corner_broadcast_days = corner_data.get('broadcast_days', '') or corner_data.get('broadcast_day', '')
                    corner_start_time = corner_data.get('start_time', '')
                    corner_end_time = corner_data.get('end_time', '')
                    corner_broadcast_time = corner_data.get('broadcast_time', '')

                    if corner_broadcast_days:
                        html += f'<div class="info-row"><span class="label">放送時間</span></div>'
                        days_list = corner_broadcast_days.split(',') if ',' in corner_broadcast_days else [corner_broadcast_days]

                        for day in days_list:
                            day = day.strip()
                            time_str = ""
                            if corner_start_time and corner_start_time != "00:00:00" and corner_end_time and corner_end_time != "00:00:00":
                                time_str = f"{corner_start_time}~{corner_end_time}"
                            elif corner_broadcast_time and corner_broadcast_time != "00:00:00":
                                time_str = corner_broadcast_time

                            html += f'<div class="item">{day}　{time_str}</div>'

                    # コーナーの説明
                    if corner_data.get('description'):
                        html += f'<div class="info-row"><span class="label">説明</span>{corner_data["description"]}</div>'

                # コーナー出演者
                corner_expenses = self.db.get_expenses_by_production(corner_id)
                corner_cast_expenses = [e for e in corner_expenses if '出演' in (e.get('work_type', '') or '')] if corner_expenses else []

                if corner_cast_expenses:
                    html += '<div style="margin-top:10px;"></div>'
                    # 重複を除外
                    corner_cast_dict = {}
                    for expense in corner_cast_expenses:
                        cast_name = expense.get('cast_name', '') or expense.get('partner_name', '')
                        amount = expense.get('amount', 0)
                        if cast_name and cast_name not in corner_cast_dict:
                            corner_cast_dict[cast_name] = amount

                    for cast_name, amount in corner_cast_dict.items():
                        amount_str = f"{int(amount):,}円" if amount else "未定"
                        html += f'<div class="item">コーナー出演者　{cast_name}　{amount_str}</div>'

                # コーナー制作会社
                corner_production_expenses = [e for e in corner_expenses if '出演' not in (e.get('work_type', '') or '')] if corner_expenses else []

                if corner_production_expenses:
                    # 重複を除外
                    corner_company_dict = {}
                    for expense in corner_production_expenses:
                        partner_name = expense.get('partner_name', '')
                        amount = expense.get('amount', 0)
                        if partner_name and partner_name not in corner_company_dict:
                            corner_company_dict[partner_name] = amount

                    for partner_name, amount in corner_company_dict.items():
                        amount_str = f"{int(amount):,}円" if amount else "未定"
                        html += f'<div class="item">コーナー制作会社　{partner_name}　{amount_str}</div>'

                html += '</div>'  # corner-section終了

        html += """
        </body>
        </html>
        """

        return html
    def _on_edit_clicked(self):
        """編集ボタンがクリックされたときの処理"""
        if not self.current_production_id:
            return

        try:
            # 番組情報を取得
            production = self.db.get_production_by_id(self.current_production_id)
            if not production:
                QMessageBox.warning(self, "エラー", "番組情報が見つかりません")
                return

            # 番組編集ダイアログを開く
            from order_management.ui.production_edit_dialog import ProductionEditDialog

            dialog = ProductionEditDialog(self, production=production)
            if dialog.exec_():
                # 編集が完了したら詳細を再表示
                self.display_production_detail(self.current_production_id)
                # 一覧も再読み込み
                self.load_productions_for_month()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"編集ダイアログを開けませんでした: {e}")
            print(f"編集ダイアログエラー: {e}")
            import traceback
            traceback.print_exc()
