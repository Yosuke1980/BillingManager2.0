"""番組詳細表示ウィジェット

月別番組一覧と選択された番組の詳細情報を表示します。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QSplitter, QTextBrowser, QFrame,
    QRadioButton, QButtonGroup
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

        # タイトル
        self.detail_title_label = QLabel("番組を選択してください")
        self.detail_title_label.setFont(QFont("", 16, QFont.Bold))
        self.detail_title_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.detail_title_label)

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

                # 日付を整形
                if start_date:
                    try:
                        date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                        date_str = date_obj.strftime('%m月%d日')
                    except:
                        date_str = start_date
                else:
                    date_str = ""

                # リストアイテムを作成
                if date_str:
                    display_text = f"{date_str} {name}"
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
            # 番組基本情報を取得
            production = self.db.get_production_by_id(production_id)
            if not production:
                self.detail_browser.setHtml("<p>番組情報が見つかりません</p>")
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
        """番組詳細のHTMLを生成"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: "メイリオ", "Meiryo", sans-serif; }
                .section {
                    border: 2px solid #333;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: #fafafa;
                }
                .section-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                }
                .info-row {
                    margin: 5px 0;
                    padding-left: 10px;
                }
                .label {
                    font-weight: bold;
                    margin-right: 10px;
                }
                .category {
                    font-weight: bold;
                    color: #555;
                    margin-top: 8px;
                }
                .item {
                    margin-left: 20px;
                    margin-top: 3px;
                }
            </style>
        </head>
        <body>
        """

        # 【情報】セクション
        html += '<div class="section">'
        html += '<div class="section-title">情報</div>'

        # 日時
        if production.get('start_date'):
            try:
                date_obj = datetime.strptime(production['start_date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%m月%d日')
                weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]

                time_str = ""
                # 有効な時間データがあるかチェック（"00:00:00"や空文字列は除外）
                start_time = production.get('start_time', '')
                end_time = production.get('end_time', '')
                broadcast_time = production.get('broadcast_time', '')

                # "00:00:00"は無効な時間として扱う
                if start_time and start_time != "00:00:00" and end_time and end_time != "00:00:00":
                    time_str = f" {start_time}～{end_time}"
                elif broadcast_time and broadcast_time != "00:00:00":
                    time_str = f" {broadcast_time}"

                html += f'<div class="info-row"><span class="label">日時</span>{date_str}（{weekday}）{time_str}</div>'
            except:
                pass

        # 場所
        if production.get('location'):
            html += f'<div class="info-row"><span class="label">場所</span>{production["location"]}</div>'

        # 出演者
        casts = self.db.get_production_casts(production_id)
        if casts:
            html += '<div class="info-row"><span class="label">出演者</span></div>'
            for cast in casts:
                cast_name, role = cast[0], cast[1]
                role_str = f"{role} " if role else ""
                html += f'<div class="item">{role_str}{cast_name}</div>'

        # 制作関連（費用項目から取得）- 名前のみ表示（金額は費用セクションで表示）
        expenses = self.db.get_expenses_by_production(production_id)
        if expenses:
            # 制作関連をグループ化（出演料以外）
            production_expenses = [e for e in expenses if '出演' not in (e.get('work_type', '') or '')]

            if production_expenses:
                # 制作会社を重複なく取得（同じ取引先が複数の費用項目を持つ場合があるため）
                production_companies = {}
                for expense in production_expenses:
                    partner_name = expense.get('partner_name', '')
                    work_type = expense.get('work_type', '')
                    if partner_name and partner_name not in production_companies:
                        production_companies[partner_name] = work_type

                if production_companies:
                    html += '<div class="info-row"><span class="label">制作</span></div>'
                    for partner_name, work_type in production_companies.items():
                        html += f'<div class="item">{work_type}　{partner_name}</div>'

        html += '</div>'

        # 【費用】セクション
        if expenses:
            html += '<div class="section">'
            html += '<div class="section-title">費用</div>'

            # 出演料
            cast_expenses = [e for e in expenses if '出演' in (e.get('work_type', '') or '')]
            if cast_expenses:
                html += '<div class="category">出演料</div>'
                for expense in cast_expenses:
                    item_name = expense.get('item_name', '')
                    work_type = expense.get('work_type', '')
                    amount = expense.get('amount', 0)
                    amount_str = f"{int(amount):,}円" if amount else "未定"
                    html += f'<div class="item">{item_name}　{work_type}　{amount_str}</div>'

            # 制作費
            if production_expenses:
                html += '<div class="category">制作費</div>'
                for expense in production_expenses:
                    partner_name = expense.get('partner_name', '')
                    work_type = expense.get('work_type', '')
                    amount = expense.get('amount', 0)
                    amount_str = f"{int(amount):,}円" if amount else "未定"
                    html += f'<div class="item">{partner_name}　{work_type}　{amount_str}</div>'

            html += '</div>'

        html += """
        </body>
        </html>
        """

        return html

    def _generate_regular_detail_html(self, production, production_id):
        """レギュラー番組詳細のHTMLを生成"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: "メイリオ", "Meiryo", sans-serif; }
                .section {
                    border: 2px solid #333;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: #fafafa;
                }
                .section-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                }
                .info-row {
                    margin: 5px 0;
                    padding-left: 10px;
                }
                .label {
                    font-weight: bold;
                    margin-right: 10px;
                }
                .category {
                    font-weight: bold;
                    color: #555;
                    margin-top: 8px;
                }
                .item {
                    margin-left: 20px;
                    margin-top: 3px;
                }
                .total {
                    font-weight: bold;
                    font-size: 14px;
                    margin-top: 10px;
                    padding: 8px;
                    background-color: #e8f5e9;
                }
            </style>
        </head>
        <body>
        """

        # 【情報】セクション
        html += '<div class="section">'
        html += '<div class="section-title">基本情報</div>'

        # 放送開始日
        if production.get('start_date'):
            try:
                date_obj = datetime.strptime(production['start_date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%Y年%m月%d日')
                html += f'<div class="info-row"><span class="label">放送開始日</span>{date_str}</div>'
            except:
                html += f'<div class="info-row"><span class="label">放送開始日</span>{production["start_date"]}</div>'

        # 放送終了日
        if production.get('end_date'):
            try:
                date_obj = datetime.strptime(production['end_date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%Y年%m月%d日')
                html += f'<div class="info-row"><span class="label">放送終了日</span>{date_str}</div>'
            except:
                html += f'<div class="info-row"><span class="label">放送終了日</span>{production["end_date"]}</div>'

        # 放送時間
        start_time = production.get('start_time', '')
        end_time = production.get('end_time', '')
        broadcast_time = production.get('broadcast_time', '')

        if start_time and start_time != "00:00:00" and end_time and end_time != "00:00:00":
            time_str = f"{start_time}～{end_time}"
            html += f'<div class="info-row"><span class="label">放送時間</span>{time_str}</div>'
        elif broadcast_time and broadcast_time != "00:00:00":
            html += f'<div class="info-row"><span class="label">放送時間</span>{broadcast_time}</div>'

        # 放送曜日
        if production.get('broadcast_day'):
            html += f'<div class="info-row"><span class="label">放送曜日</span>{production["broadcast_day"]}</div>'

        # ステータス
        if production.get('status'):
            html += f'<div class="info-row"><span class="label">ステータス</span>{production["status"]}</div>'

        html += '</div>'

        # 【レギュラー出演者・制作会社】セクション
        # 全期間の費用項目から取得（月に関係なく）
        all_expenses = self.db.get_expenses_by_production(production_id)
        if all_expenses:
            html += '<div class="section">'
            html += '<div class="section-title">レギュラー出演者・制作会社</div>'

            # 出演者
            cast_expenses = [e for e in all_expenses if '出演' in (e.get('work_type', '') or '')]
            if cast_expenses:
                html += '<div class="category">レギュラー出演者</div>'
                # 重複を除外
                cast_names = {}
                for expense in cast_expenses:
                    item_name = expense.get('item_name', '')
                    work_type = expense.get('work_type', '')
                    if item_name and item_name not in cast_names:
                        cast_names[item_name] = work_type

                for item_name, work_type in cast_names.items():
                    html += f'<div class="item">{work_type}　{item_name}</div>'

            # 制作会社
            production_expenses = [e for e in all_expenses if '出演' not in (e.get('work_type', '') or '')]
            if production_expenses:
                html += '<div class="category">制作会社</div>'
                # 重複を除外
                production_companies = {}
                for expense in production_expenses:
                    partner_name = expense.get('partner_name', '')
                    work_type = expense.get('work_type', '')
                    if partner_name and partner_name not in production_companies:
                        production_companies[partner_name] = work_type

                for partner_name, work_type in production_companies.items():
                    html += f'<div class="item">{work_type}　{partner_name}</div>'

            html += '</div>'

        # 【コーナー】セクション
        corners = self.db.get_corners_by_parent_production(production_id)
        if corners:
            html += '<div class="section">'
            html += '<div class="section-title">コーナー</div>'

            for corner in corners:
                corner_id, corner_name, corner_start_date, corner_end_date = corner

                html += f'<div class="category">{corner_name}</div>'

                # コーナーの期間
                period_parts = []
                if corner_start_date:
                    try:
                        date_obj = datetime.strptime(corner_start_date, '%Y-%m-%d')
                        period_parts.append(date_obj.strftime('%Y/%m/%d'))
                    except:
                        period_parts.append(corner_start_date)

                if corner_end_date:
                    try:
                        date_obj = datetime.strptime(corner_end_date, '%Y-%m-%d')
                        period_parts.append(date_obj.strftime('%Y/%m/%d'))
                    except:
                        period_parts.append(corner_end_date)

                if period_parts:
                    html += f'<div class="item">期間: {" ～ ".join(period_parts)}</div>'

                # コーナーの月別費用を取得
                corner_monthly_expenses = self.db.get_monthly_expenses_by_production(corner_id, self.current_month)
                if corner_monthly_expenses:
                    corner_total = sum(e.get('amount', 0) for e in corner_monthly_expenses if e.get('amount'))

                    for expense in corner_monthly_expenses:
                        item_name = expense.get('item_name', '')
                        partner_name = expense.get('partner_name', '')
                        work_type = expense.get('work_type', '')
                        amount = expense.get('amount', 0)
                        impl_date = expense.get('implementation_date', '')
                        amount_str = f"{int(amount):,}円" if amount else "未定"

                        # 日付表示
                        date_str = ""
                        if impl_date:
                            try:
                                date_obj = datetime.strptime(impl_date, '%Y-%m-%d')
                                date_str = date_obj.strftime('%m/%d') + " "
                            except:
                                pass

                        # 出演かそれ以外か
                        if '出演' in (work_type or ''):
                            display_name = item_name
                        else:
                            display_name = partner_name

                        html += f'<div class="item">{date_str}{display_name}　{work_type}　{amount_str}</div>'

                    if corner_total > 0:
                        html += f'<div class="item" style="font-weight:bold; margin-top:5px;">コーナー月別合計: {int(corner_total):,}円</div>'

            html += '</div>'

        # 【月別費用】セクション
        monthly_expenses = self.db.get_monthly_expenses_by_production(production_id, self.current_month)
        if monthly_expenses:
            html += '<div class="section">'

            # 月表示
            try:
                date_obj = datetime.strptime(self.current_month, '%Y-%m')
                month_display = date_obj.strftime('%Y年%m月')
            except:
                month_display = self.current_month

            html += f'<div class="section-title">{month_display}の費用</div>'

            # 出演料
            cast_expenses = [e for e in monthly_expenses if '出演' in (e.get('work_type', '') or '')]
            if cast_expenses:
                html += '<div class="category">出演料</div>'
                cast_total = 0
                for expense in cast_expenses:
                    item_name = expense.get('item_name', '')
                    work_type = expense.get('work_type', '')
                    amount = expense.get('amount', 0)
                    impl_date = expense.get('implementation_date', '')
                    amount_str = f"{int(amount):,}円" if amount else "未定"

                    # 日付表示
                    date_str = ""
                    if impl_date:
                        try:
                            date_obj = datetime.strptime(impl_date, '%Y-%m-%d')
                            date_str = date_obj.strftime('%m/%d') + " "
                        except:
                            pass

                    html += f'<div class="item">{date_str}{item_name}　{work_type}　{amount_str}</div>'
                    if amount:
                        cast_total += amount

            # 制作費
            production_expenses = [e for e in monthly_expenses if '出演' not in (e.get('work_type', '') or '')]
            if production_expenses:
                html += '<div class="category">制作費</div>'
                production_total = 0
                for expense in production_expenses:
                    partner_name = expense.get('partner_name', '')
                    work_type = expense.get('work_type', '')
                    amount = expense.get('amount', 0)
                    impl_date = expense.get('implementation_date', '')
                    amount_str = f"{int(amount):,}円" if amount else "未定"

                    # 日付表示
                    date_str = ""
                    if impl_date:
                        try:
                            date_obj = datetime.strptime(impl_date, '%Y-%m-%d')
                            date_str = date_obj.strftime('%m/%d') + " "
                        except:
                            pass

                    html += f'<div class="item">{date_str}{partner_name}　{work_type}　{amount_str}</div>'
                    if amount:
                        production_total += amount

            # 月別合計
            total_amount = sum(e.get('amount', 0) for e in monthly_expenses if e.get('amount'))
            if total_amount > 0:
                html += f'<div class="total">月別合計: {int(total_amount):,}円</div>'

            html += '</div>'
        else:
            # 費用がない場合
            try:
                date_obj = datetime.strptime(self.current_month, '%Y-%m')
                month_display = date_obj.strftime('%Y年%m月')
            except:
                month_display = self.current_month

            html += '<div class="section">'
            html += f'<div class="section-title">{month_display}の費用</div>'
            html += '<div class="info-row">この月の費用データはありません</div>'
            html += '</div>'

        html += """
        </body>
        </html>
        """

        return html
