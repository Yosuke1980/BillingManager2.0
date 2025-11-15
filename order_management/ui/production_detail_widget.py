"""番組詳細表示ウィジェット

月別番組一覧と選択された番組の詳細情報を表示します。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QSplitter, QTextBrowser, QFrame,
    QRadioButton, QButtonGroup, QPushButton, QMessageBox,
    QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QScrollArea, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate, QTime
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
        self.is_edit_mode = False  # 編集モードフラグ
        self.current_production_data = None  # 現在の番組データ
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

        # タイトル・モード切替・編集ボタンのレイアウト
        title_layout = QHBoxLayout()

        self.detail_title_label = QLabel("番組を選択してください")
        self.detail_title_label.setFont(QFont("", 16, QFont.Bold))
        self.detail_title_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        title_layout.addWidget(self.detail_title_label)

        # モード切替コンボボックス
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("表示モード")
        self.mode_combo.addItem("編集モード")
        self.mode_combo.setFixedWidth(120)
        self.mode_combo.setEnabled(False)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        title_layout.addWidget(self.mode_combo)

        # 編集ボタン（別ダイアログで開く用 - 将来削除予定）
        self.edit_button = QPushButton("別ウィンドウで編集")
        self.edit_button.setFixedWidth(140)
        self.edit_button.setFixedHeight(35)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        title_layout.addWidget(self.edit_button)

        layout.addLayout(title_layout)

        # 表示モードエリア（HTML表示）
        self.display_area = QWidget()
        display_layout = QVBoxLayout(self.display_area)
        display_layout.setContentsMargins(0, 0, 0, 0)

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
        display_layout.addWidget(self.detail_browser)

        # 編集モードエリア（フォーム）
        self.edit_area = QWidget()
        self.edit_area.setVisible(False)  # 初期は非表示
        self._create_edit_form()

        # 両エリアを追加
        layout.addWidget(self.display_area)
        layout.addWidget(self.edit_area)

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

            # 番組基本情報を取得
            production = self.db.get_production_by_id(production_id)
            if not production:
                self.detail_browser.setHtml("<p>番組情報が見つかりません</p>")
                self.edit_button.setEnabled(False)
                self.mode_combo.setEnabled(False)
                return

            # 現在の番組データを保存
            self.current_production_data = production

            # 編集ボタンとモード切替を有効化
            self.edit_button.setEnabled(True)
            self.mode_combo.setEnabled(True)

            # 表示モードに戻す
            self.mode_combo.setCurrentIndex(0)

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

        # 曜日別放送時間のマッピング
        day_mapping = {
            '月': 'broadcast_time_mon',
            '火': 'broadcast_time_tue',
            '水': 'broadcast_time_wed',
            '木': 'broadcast_time_thu',
            '金': 'broadcast_time_fri',
            '土': 'broadcast_time_sat',
            '日': 'broadcast_time_sun'
        }

        if broadcast_days:
            html += f'<div class="info-row"><span class="label">放送時間</span></div>'

            # 曜日ごとに分けて表示
            days_list = broadcast_days.split(',') if ',' in broadcast_days else [broadcast_days]

            for day in days_list:
                day = day.strip()

                # 曜日別の放送時間を取得
                col_name = day_mapping.get(day)
                day_time = production.get(col_name, '') if col_name else ''

                if day_time:
                    # 曜日別時間が設定されている場合
                    time_str = day_time
                else:
                    # 従来の方法（全曜日共通）
                    start_time = production.get('start_time', '')
                    end_time = production.get('end_time', '')
                    broadcast_time = production.get('broadcast_time', '')

                    if start_time and start_time != "00:00:00" and end_time and end_time != "00:00:00":
                        time_str = f"{start_time}~{end_time}"
                    elif broadcast_time and broadcast_time != "00:00:00":
                        time_str = broadcast_time
                    else:
                        time_str = ""

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

    def _create_edit_form(self):
        """編集フォームを作成"""
        layout = QVBoxLayout(self.edit_area)
        layout.setContentsMargins(0, 0, 0, 0)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ccc; background-color: white; }")

        # フォームコンテナ
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)

        # 基本情報グループ
        self.basic_group = QGroupBox("基本情報")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(8)

        # 番組名
        self.name_edit = QLineEdit()
        basic_layout.addRow("番組名:", self.name_edit)

        # 日付（単発用）
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        basic_layout.addRow("日付:", self.date_edit)

        # 開始日（レギュラー用）
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        basic_layout.addRow("放送開始日:", self.start_date_edit)

        # 終了日（レギュラー用）
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setSpecialValueText("未設定")
        basic_layout.addRow("放送終了日:", self.end_date_edit)

        # 開始時間
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        basic_layout.addRow("開始時間:", self.start_time_edit)

        # 終了時間
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        basic_layout.addRow("終了時間:", self.end_time_edit)

        # 放送曜日（レギュラー用）
        days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        for day in ['月', '火', '水', '木', '金', '土', '日']:
            cb = QCheckBox(day)
            self.day_checkboxes[day] = cb
            days_layout.addWidget(cb)
        days_layout.addStretch()
        basic_layout.addRow("放送曜日:", days_layout)

        # 曜日別放送時間（レギュラー用）
        self.broadcast_times_group = QGroupBox("曜日別放送時間")
        broadcast_times_layout = QVBoxLayout()

        self.day_time_widgets = {}
        day_names = {
            '月': 'mon', '火': 'tue', '水': 'wed', '木': 'thu',
            '金': 'fri', '土': 'sat', '日': 'sun'
        }

        for day_jp, day_en in day_names.items():
            day_row = QHBoxLayout()

            # チェックボックス
            day_check = QCheckBox(f"{day_jp}曜日")
            day_check.setFixedWidth(80)
            day_row.addWidget(day_check)

            # 開始時刻
            start_time = QTimeEdit()
            start_time.setDisplayFormat("HH:mm")
            start_time.setTime(QTime(0, 0))
            day_row.addWidget(QLabel("開始:"))
            day_row.addWidget(start_time)

            # 終了時刻
            end_time = QTimeEdit()
            end_time.setDisplayFormat("HH:mm")
            end_time.setTime(QTime(0, 0))
            day_row.addWidget(QLabel("終了:"))
            day_row.addWidget(end_time)

            day_row.addStretch()

            # ウィジェットを保存
            self.day_time_widgets[day_en] = {
                'check': day_check,
                'start': start_time,
                'end': end_time
            }

            broadcast_times_layout.addLayout(day_row)

        self.broadcast_times_group.setLayout(broadcast_times_layout)
        self.broadcast_times_group.setVisible(False)  # デフォルトで非表示
        basic_layout.addRow("", self.broadcast_times_group)

        # 説明
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        basic_layout.addRow("説明:", self.description_edit)

        # ステータス
        self.status_combo = QComboBox()
        self.status_combo.addItems(['active', '終了', '休止'])
        basic_layout.addRow("ステータス:", self.status_combo)

        self.basic_group.setLayout(basic_layout)
        form_layout.addWidget(self.basic_group)

        # 出演者グループ
        self.cast_group = QGroupBox("出演者")
        cast_layout = QVBoxLayout()

        self.cast_table = QTableWidget()
        self.cast_table.setColumnCount(7)
        self.cast_table.setHorizontalHeaderLabels(['役割', '出演者名', '金額', '開始日', '終了日', '支払予定日', '削除'])
        self.cast_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cast_table.setMaximumHeight(200)
        cast_layout.addWidget(self.cast_table)

        add_cast_btn = QPushButton("+ 出演者を追加")
        add_cast_btn.clicked.connect(self._add_cast_row)
        cast_layout.addWidget(add_cast_btn)

        self.cast_group.setLayout(cast_layout)
        form_layout.addWidget(self.cast_group)

        # 制作グループ
        self.production_group = QGroupBox("制作")
        production_layout = QVBoxLayout()

        self.production_table = QTableWidget()
        self.production_table.setColumnCount(7)
        self.production_table.setHorizontalHeaderLabels(['項目名', '制作会社', '金額', '開始日', '終了日', '支払予定日', '削除'])
        self.production_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.production_table.setMaximumHeight(200)
        production_layout.addWidget(self.production_table)

        add_production_btn = QPushButton("+ 制作項目を追加")
        add_production_btn.clicked.connect(self._add_production_row)
        production_layout.addWidget(add_production_btn)

        self.production_group.setLayout(production_layout)
        form_layout.addWidget(self.production_group)

        # 保存・キャンセルボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self._cancel_edit)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)

        form_layout.addLayout(button_layout)
        form_layout.addStretch()

        scroll.setWidget(form_container)
        layout.addWidget(scroll)

    def _on_mode_changed(self, index):
        """モード切替時の処理"""
        if index == 0:  # 表示モード
            self.is_edit_mode = False
            self.display_area.setVisible(True)
            self.edit_area.setVisible(False)
        else:  # 編集モード
            if not self.current_production_id:
                self.mode_combo.setCurrentIndex(0)
                return

            self.is_edit_mode = True
            self._load_edit_form()
            self.display_area.setVisible(False)
            self.edit_area.setVisible(True)


    def _load_edit_form(self):
        """編集フォームにデータを読み込む"""
        if not self.current_production_data:
            return

        production = self.current_production_data
        is_regular = self.regular_radio.isChecked()

        # 基本情報
        self.name_edit.setText(production.get('name', ''))
        self.description_edit.setPlainText(production.get('description', ''))
        self.status_combo.setCurrentText(production.get('status', 'active'))

        # 日付・時間の処理
        if production.get('start_date'):
            try:
                date = QDate.fromString(production['start_date'], 'yyyy-MM-dd')
                if is_regular:
                    self.start_date_edit.setDate(date)
                    self.start_date_edit.setVisible(True)
                    self.date_edit.setVisible(False)
                else:
                    self.date_edit.setDate(date)
                    self.date_edit.setVisible(True)
                    self.start_date_edit.setVisible(False)
            except:
                pass

        if production.get('end_date') and is_regular:
            try:
                date = QDate.fromString(production['end_date'], 'yyyy-MM-dd')
                self.end_date_edit.setDate(date)
                self.end_date_edit.setVisible(True)
            except:
                self.end_date_edit.setVisible(False)
        else:
            self.end_date_edit.setVisible(is_regular)

        # 時間
        if production.get('start_time'):
            try:
                time = QTime.fromString(production['start_time'], 'HH:mm:ss')
                self.start_time_edit.setTime(time)
            except:
                pass

        if production.get('end_time'):
            try:
                time = QTime.fromString(production['end_time'], 'HH:mm:ss')
                self.end_time_edit.setTime(time)
            except:
                pass

        # 放送曜日（レギュラーのみ）
        if is_regular and production.get('broadcast_days'):
            days_str = production['broadcast_days']
            for day, cb in self.day_checkboxes.items():
                cb.setChecked(day in days_str)
                cb.setVisible(True)
        else:
            for cb in self.day_checkboxes.values():
                cb.setVisible(is_regular)

        # 曜日別放送時間（レギュラーのみ）
        if is_regular:
            self.broadcast_times_group.setVisible(True)
            day_mapping = {
                'mon': '月', 'tue': '火', 'wed': '水', 'thu': '木',
                'fri': '金', 'sat': '土', 'sun': '日'
            }

            for day_en, day_jp in day_mapping.items():
                col_name = f'broadcast_time_{day_en}'
                time_str = production.get(col_name, '')
                widgets = self.day_time_widgets.get(day_en)

                if widgets and time_str:
                    # 時間が設定されている場合
                    widgets['check'].setChecked(True)
                    # HH:MM または HH:MM:SS 形式をパース
                    if '-' in time_str:  # 範囲形式（開始-終了）
                        parts = time_str.split('-')
                        if len(parts) == 2:
                            try:
                                start_time = QTime.fromString(parts[0].strip(), 'HH:mm')
                                end_time = QTime.fromString(parts[1].strip(), 'HH:mm')
                                widgets['start'].setTime(start_time)
                                widgets['end'].setTime(end_time)
                            except:
                                pass
                    else:
                        # 単一時間の場合は開始時間として設定
                        try:
                            time = QTime.fromString(time_str, 'HH:mm:ss')
                            widgets['start'].setTime(time)
                        except:
                            pass
                else:
                    if widgets:
                        widgets['check'].setChecked(False)
        else:
            self.broadcast_times_group.setVisible(False)

        # 費用項目を取得
        expenses = self.db.get_expenses_by_production(self.current_production_id)

        # 出演者テーブルをクリアして読み込み
        self.cast_table.setRowCount(0)
        cast_expenses = [e for e in expenses if '出演' in (e.get('work_type', '') or '')] if expenses else []

        for expense in cast_expenses:
            self._add_cast_row(expense)

        # 制作テーブルをクリアして読み込み
        self.production_table.setRowCount(0)
        production_expenses = [e for e in expenses if '出演' not in (e.get('work_type', '') or '')] if expenses else []

        for expense in production_expenses:
            self._add_production_row(expense)

    def _add_cast_row(self, data=None):
        """出演者行を追加"""
        row = self.cast_table.rowCount()
        self.cast_table.insertRow(row)

        # 役割
        role_edit = QLineEdit(data.get('role', 'MC') if data else 'MC')
        self.cast_table.setCellWidget(row, 0, role_edit)

        # 出演者名
        name_edit = QComboBox()
        name_edit.setEditable(True)
        # 既存の出演者を取得して追加
        try:
            cast_list = self.db.get_all_cast()
            for cast in cast_list:
                name_edit.addItem(cast[1])  # cast[1] is name
        except:
            pass
        if data:
            name_edit.setCurrentText(data.get('cast_name', '') or data.get('partner_name', ''))
        self.cast_table.setCellWidget(row, 1, name_edit)

        # 金額
        amount_spin = QSpinBox()
        amount_spin.setMaximum(10000000)
        amount_spin.setSingleStep(1000)
        amount_spin.setValue(int(data.get('amount', 0)) if data else 0)
        self.cast_table.setCellWidget(row, 2, amount_spin)

        # 開始日
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("yyyy-MM-dd")
        if data and data.get('start_date'):
            try:
                date = QDate.fromString(data['start_date'], 'yyyy-MM-dd')
                start_date.setDate(date)
            except:
                start_date.setDate(QDate.currentDate())
        else:
            start_date.setDate(QDate.currentDate())
        self.cast_table.setCellWidget(row, 3, start_date)

        # 終了日
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("yyyy-MM-dd")
        end_date.setSpecialValueText("未設定")
        end_date.setMinimumDate(QDate(2000, 1, 1))
        end_date.setDate(QDate(2000, 1, 1))  # デフォルトで「未設定」
        if data and data.get('end_date'):
            try:
                date = QDate.fromString(data['end_date'], 'yyyy-MM-dd')
                end_date.setDate(date)
            except:
                pass
        self.cast_table.setCellWidget(row, 4, end_date)

        # 支払予定日
        payment_date = QDateEdit()
        payment_date.setCalendarPopup(True)
        payment_date.setDisplayFormat("yyyy-MM-dd")
        if data and data.get('expected_payment_date'):
            try:
                date = QDate.fromString(data['expected_payment_date'], 'yyyy-MM-dd')
                payment_date.setDate(date)
            except:
                payment_date.setDate(QDate.currentDate())
        else:
            payment_date.setDate(QDate.currentDate())
        self.cast_table.setCellWidget(row, 5, payment_date)

        # 削除ボタン
        delete_btn = QPushButton("×")
        delete_btn.setFixedWidth(30)
        delete_btn.clicked.connect(lambda: self.cast_table.removeRow(row))
        self.cast_table.setCellWidget(row, 6, delete_btn)

        # expense_id を保存（更新用）
        if data and data.get('id'):
            self.cast_table.setItem(row, 0, QTableWidgetItem(str(data['id'])))

    def _add_production_row(self, data=None):
        """制作項目行を追加"""
        row = self.production_table.rowCount()
        self.production_table.insertRow(row)

        # 項目名
        item_edit = QLineEdit(data.get('item_name', '') if data else '')
        self.production_table.setCellWidget(row, 0, item_edit)

        # 制作会社名
        company_edit = QComboBox()
        company_edit.setEditable(True)
        # 既存の取引先を取得して追加
        try:
            partners = self.db.get_all_partners()
            for partner in partners:
                company_edit.addItem(partner[1])  # partner[1] is name
        except:
            pass
        if data:
            company_edit.setCurrentText(data.get('partner_name', ''))
        self.production_table.setCellWidget(row, 1, company_edit)

        # 金額
        amount_spin = QSpinBox()
        amount_spin.setMaximum(10000000)
        amount_spin.setSingleStep(1000)
        amount_spin.setValue(int(data.get('amount', 0)) if data else 0)
        self.production_table.setCellWidget(row, 2, amount_spin)

        # 開始日
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("yyyy-MM-dd")
        if data and data.get('start_date'):
            try:
                date = QDate.fromString(data['start_date'], 'yyyy-MM-dd')
                start_date.setDate(date)
            except:
                start_date.setDate(QDate.currentDate())
        else:
            start_date.setDate(QDate.currentDate())
        self.production_table.setCellWidget(row, 3, start_date)

        # 終了日
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("yyyy-MM-dd")
        end_date.setSpecialValueText("未設定")
        end_date.setMinimumDate(QDate(2000, 1, 1))
        end_date.setDate(QDate(2000, 1, 1))  # デフォルトで「未設定」
        if data and data.get('end_date'):
            try:
                date = QDate.fromString(data['end_date'], 'yyyy-MM-dd')
                end_date.setDate(date)
            except:
                pass
        self.production_table.setCellWidget(row, 4, end_date)

        # 支払予定日
        payment_date = QDateEdit()
        payment_date.setCalendarPopup(True)
        payment_date.setDisplayFormat("yyyy-MM-dd")
        if data and data.get('expected_payment_date'):
            try:
                date = QDate.fromString(data['expected_payment_date'], 'yyyy-MM-dd')
                payment_date.setDate(date)
            except:
                payment_date.setDate(QDate.currentDate())
        else:
            payment_date.setDate(QDate.currentDate())
        self.production_table.setCellWidget(row, 5, payment_date)

        # 削除ボタン
        delete_btn = QPushButton("×")
        delete_btn.setFixedWidth(30)
        delete_btn.clicked.connect(lambda: self.production_table.removeRow(row))
        self.production_table.setCellWidget(row, 6, delete_btn)

        # expense_id を保存（更新用）
        if data and data.get('id'):
            self.production_table.setItem(row, 0, QTableWidgetItem(str(data['id'])))

    def _cancel_edit(self):
        """編集をキャンセル"""
        self.mode_combo.setCurrentIndex(0)  # 表示モードに戻る

    def _save_changes(self):
        """変更を保存"""
        try:
            # バリデーション
            if not self.name_edit.text().strip():
                QMessageBox.warning(self, "入力エラー", "番組名を入力してください")
                return

            # 番組情報を更新
            is_regular = self.regular_radio.isChecked()
            
            production_data = {
                'name': self.name_edit.text().strip(),
                'description': self.description_edit.toPlainText().strip(),
                'status': self.status_combo.currentText(),
            }

            if is_regular:
                production_data['start_date'] = self.start_date_edit.date().toString('yyyy-MM-dd')
                # 終了日が「未設定」（最小値）の場合はNULLとして保存
                if self.end_date_edit.date() > QDate(2000, 1, 1):
                    production_data['end_date'] = self.end_date_edit.date().toString('yyyy-MM-dd')
                else:
                    production_data['end_date'] = None

                # 放送曜日
                checked_days = [day for day, cb in self.day_checkboxes.items() if cb.isChecked()]
                production_data['broadcast_days'] = ','.join(checked_days)

                # 曜日別放送時間を保存
                day_mapping = {
                    'mon': '月', 'tue': '火', 'wed': '水', 'thu': '木',
                    'fri': '金', 'sat': '土', 'sun': '日'
                }
                for day_en in day_mapping.keys():
                    widgets = self.day_time_widgets.get(day_en)
                    if widgets and widgets['check'].isChecked():
                        start = widgets['start'].time().toString('HH:mm')
                        end = widgets['end'].time().toString('HH:mm')
                        # 開始-終了 形式で保存
                        production_data[f'broadcast_time_{day_en}'] = f"{start}-{end}"
                    else:
                        production_data[f'broadcast_time_{day_en}'] = None
            else:
                production_data['start_date'] = self.date_edit.date().toString('yyyy-MM-dd')

            # 時間
            production_data['start_time'] = self.start_time_edit.time().toString('HH:mm:ss')
            production_data['end_time'] = self.end_time_edit.time().toString('HH:mm:ss')

            # 番組情報を更新
            self.db.update_production(self.current_production_id, production_data)

            # 既存の費用項目を取得
            existing_expenses = self.db.get_expenses_by_production(self.current_production_id)
            existing_expense_ids = set(e.get('id') for e in existing_expenses if e.get('id'))

            # 保存された費用項目のIDを追跡
            saved_expense_ids = set()

            # 出演者の保存
            for row in range(self.cast_table.rowCount()):
                expense_data = self._get_cast_row_data(row)
                if expense_data:
                    expense_id = self._save_expense_item(expense_data, '出演')
                    if expense_id:
                        saved_expense_ids.add(expense_id)

            # 制作項目の保存
            for row in range(self.production_table.rowCount()):
                expense_data = self._get_production_row_data(row)
                if expense_data:
                    expense_id = self._save_expense_item(expense_data, '制作')
                    if expense_id:
                        saved_expense_ids.add(expense_id)

            # 削除された費用項目を削除
            deleted_ids = existing_expense_ids - saved_expense_ids
            for expense_id in deleted_ids:
                try:
                    self.db.delete_expense_item(expense_id)
                except Exception as e:
                    print(f"費用項目削除エラー (ID: {expense_id}): {e}")

            QMessageBox.information(self, "保存完了", "変更を保存しました")

            # 表示モードに戻る
            self.mode_combo.setCurrentIndex(0)

            # 詳細を再表示
            self.display_production_detail(self.current_production_id)

            # 一覧を再読み込み
            self.load_productions_for_month()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存中にエラーが発生しました: {e}")
            print(f"保存エラー: {e}")
            import traceback
            traceback.print_exc()

    def _get_cast_row_data(self, row):
        """出演者テーブルから行データを取得"""
        try:
            # 各セルのウィジェットを取得
            role_widget = self.cast_table.cellWidget(row, 0)
            name_widget = self.cast_table.cellWidget(row, 1)
            amount_widget = self.cast_table.cellWidget(row, 2)
            start_date_widget = self.cast_table.cellWidget(row, 3)
            end_date_widget = self.cast_table.cellWidget(row, 4)
            payment_date_widget = self.cast_table.cellWidget(row, 5)

            if not name_widget or not amount_widget:
                return None

            # 既存のexpense_idを取得（更新の場合）
            expense_id = None
            id_item = self.cast_table.item(row, 0)
            if id_item and id_item.text():
                try:
                    expense_id = int(id_item.text())
                except:
                    pass

            # 終了日が「未設定」の場合はNone
            end_date = None
            if end_date_widget and end_date_widget.date() > QDate(2000, 1, 1):
                end_date = end_date_widget.date().toString('yyyy-MM-dd')

            data = {
                'id': expense_id,
                'role': role_widget.text() if role_widget else '',
                'cast_name': name_widget.currentText() if hasattr(name_widget, 'currentText') else '',
                'amount': amount_widget.value() if amount_widget else 0,
                'start_date': start_date_widget.date().toString('yyyy-MM-dd') if start_date_widget else None,
                'end_date': end_date,
                'expected_payment_date': payment_date_widget.date().toString('yyyy-MM-dd') if payment_date_widget else None,
            }

            return data

        except Exception as e:
            print(f"出演者行データ取得エラー (row {row}): {e}")
            return None

    def _get_production_row_data(self, row):
        """制作テーブルから行データを取得"""
        try:
            # 各セルのウィジェットを取得
            item_widget = self.production_table.cellWidget(row, 0)
            company_widget = self.production_table.cellWidget(row, 1)
            amount_widget = self.production_table.cellWidget(row, 2)
            start_date_widget = self.production_table.cellWidget(row, 3)
            end_date_widget = self.production_table.cellWidget(row, 4)
            payment_date_widget = self.production_table.cellWidget(row, 5)

            if not item_widget or not company_widget or not amount_widget:
                return None

            # 既存のexpense_idを取得（更新の場合）
            expense_id = None
            id_item = self.production_table.item(row, 0)
            if id_item and id_item.text():
                try:
                    expense_id = int(id_item.text())
                except:
                    pass

            # 終了日が「未設定」の場合はNone
            end_date = None
            if end_date_widget and end_date_widget.date() > QDate(2000, 1, 1):
                end_date = end_date_widget.date().toString('yyyy-MM-dd')

            data = {
                'id': expense_id,
                'item_name': item_widget.text() if item_widget else '',
                'partner_name': company_widget.currentText() if hasattr(company_widget, 'currentText') else '',
                'amount': amount_widget.value() if amount_widget else 0,
                'start_date': start_date_widget.date().toString('yyyy-MM-dd') if start_date_widget else None,
                'end_date': end_date,
                'expected_payment_date': payment_date_widget.date().toString('yyyy-MM-dd') if payment_date_widget else None,
            }

            return data

        except Exception as e:
            print(f"制作行データ取得エラー (row {row}): {e}")
            return None

    def _save_expense_item(self, data, work_type):
        """費用項目を保存（新規または更新）"""
        try:
            is_regular = self.regular_radio.isChecked()

            if is_regular:
                # レギュラー番組の場合はexpense_templatesに保存
                template_data = {
                    'production_id': self.current_production_id,
                    'work_type': work_type,
                    'amount': data.get('amount', 0),
                    'start_date': data.get('start_date'),
                    'end_date': data.get('end_date'),
                    'generation_type': '月次',
                    'auto_generate_enabled': 1,
                }
            else:
                # 単発番組の場合はexpense_itemsに保存
                expense_data = {
                    'production_id': self.current_production_id,
                    'work_type': work_type,
                    'amount': data.get('amount', 0),
                    'implementation_date': data.get('start_date') or data.get('implementation_date'),
                    'expected_payment_date': data.get('expected_payment_date'),
                    'status': '発注予定',
                    'payment_status': '未払い',
                }

            # 出演者の場合
            if work_type == '出演':
                cast_name = data.get('cast_name', '').strip()
                if not cast_name:
                    return None

                # 出演者を検索または作成
                cast_id = self._get_or_create_cast(cast_name)
                if not cast_id:
                    print(f"出演者の取得/作成に失敗: {cast_name}")
                    return None

                # パートナー（事務所）を取得
                partner_id = None
                try:
                    cast_info = self.db.get_cast_by_id(cast_id)
                    if cast_info and cast_info[2]:  # partner_id
                        partner_id = cast_info[2]
                except:
                    pass

                if is_regular:
                    template_data['cast_id'] = cast_id
                    template_data['partner_id'] = partner_id
                    template_data['item_name'] = f"{data.get('role', '')} {cast_name}".strip()
                else:
                    expense_data['cast_id'] = cast_id
                    expense_data['partner_id'] = partner_id
                    expense_data['item_name'] = f"{data.get('role', '')} {cast_name}".strip()

            # 制作の場合
            else:
                partner_name = data.get('partner_name', '').strip()
                item_name = data.get('item_name', '').strip()

                if not partner_name or not item_name:
                    return None

                # 取引先を検索または作成
                partner_id = self._get_or_create_partner(partner_name)
                if not partner_id:
                    print(f"取引先の取得/作成に失敗: {partner_name}")
                    return None

                if is_regular:
                    template_data['partner_id'] = partner_id
                    template_data['item_name'] = item_name
                else:
                    expense_data['partner_id'] = partner_id
                    expense_data['item_name'] = item_name

            # 保存
            if is_regular:
                # レギュラー番組：expense_templatesに保存
                # 既存のIDがある場合は更新、なければ新規作成
                if data.get('id'):
                    template_data['id'] = data['id']
                template_id = self.db.save_expense_template(template_data)
                return template_id
            else:
                # 単発番組：expense_itemsに保存
                if data.get('id'):
                    expense_data['id'] = data['id']
                expense_id = self.db.save_expense_item(expense_data)
                return expense_id

        except Exception as e:
            print(f"費用項目保存エラー: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_or_create_cast(self, cast_name):
        """出演者を検索、なければ作成"""
        try:
            # 既存の出演者を検索
            all_cast = self.db.get_all_cast()
            for cast in all_cast:
                if cast[1] == cast_name:  # cast[1] is name
                    return cast[0]  # cast[0] is id

            # 見つからない場合は新規作成
            cast_data = {
                'name': cast_name,
                'notes': '番組詳細画面から自動作成'
            }
            cast_id = self.db.add_cast(cast_data)
            return cast_id

        except Exception as e:
            print(f"出演者取得/作成エラー: {e}")
            return None

    def _get_or_create_partner(self, partner_name):
        """取引先を検索、なければ作成"""
        try:
            # 既存の取引先を検索
            all_partners = self.db.get_all_partners()
            for partner in all_partners:
                if partner[1] == partner_name:  # partner[1] is name
                    return partner[0]  # partner[0] is id

            # 見つからない場合は新規作成
            partner_data = {
                'name': partner_name,
                'notes': '番組詳細画面から自動作成'
            }
            partner_id = self.db.add_partner(partner_data)
            return partner_id

        except Exception as e:
            print(f"取引先取得/作成エラー: {e}")
            return None
