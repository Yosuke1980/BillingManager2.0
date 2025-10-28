from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QScrollArea,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QMessageBox,
    QSplitter,
    QCheckBox,
    QSpinBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QBrush
from utils import format_amount, log_message


class ProjectFilterTab(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db_manager = app.db_manager
        self.status_label = app.status_label

        # フォントサイズは統一スタイルシートから取得するため削除

        # 色分け設定（標準CSS色を使用）
        self.urgent_color = QColor("lightpink")      # ライトピンク（緊急）
        self.warning_color = QColor("lightyellow")   # ライトイエロー（警告）
        self.normal_color = QColor("whitesmoke")     # ホワイトスモーク（通常）
        self.paid_color = QColor("lightgreen")       # ライトグリーン（支払済み）
        self.processing_color = QColor("lightblue")  # ライトブルー（処理中）

        # 現在選択されている案件とフィルター
        self.current_project = None
        self.current_filters = {}

        # レイアウト設定
        self.setup_ui()

    def setup_ui(self):
        """UIセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # タイトル
        title_label = QLabel("📋 案件絞込み・管理")
        title_label.setProperty("title", True)  # 統一スタイルシートのタイトル用スタイルを適用
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 3ペインスプリッター
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左ペイン：絞込み条件
        self.create_filter_pane(splitter)

        # 中央ペイン：案件別支払い一覧
        self.create_project_list_pane(splitter)

        # 右ペイン：詳細情報・編集
        self.create_detail_pane(splitter)

        # スプリッターの初期サイズ設定
        splitter.setSizes([280, 400, 400])

        # ステータスバー
        self.create_status_bar(main_layout)

        # 初期データ読み込み
        self.refresh_filter_options()
        self.refresh_project_data()

    def create_filter_pane(self, parent):
        """左ペイン：絞込み条件の作成"""
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_frame.setMaximumWidth(300)
        parent.addWidget(filter_frame)

        layout = QVBoxLayout(filter_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ヘッダー
        header = QLabel("案件絞込み")
        header.setStyleSheet("background: darkslategray; color: white; padding: 8px; margin-bottom: 5px; font-weight: bold;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # 検索ボックス
        search_group = QGroupBox("検索")
        search_layout = QVBoxLayout(search_group)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("案件名・クライアント名で検索...")
        self.search_entry.returnPressed.connect(self.apply_filters)
        search_layout.addWidget(self.search_entry)

        # フィルター適用ボタン
        filter_button_layout = QHBoxLayout()
        
        apply_button = QPushButton("フィルター適用")
        apply_button.clicked.connect(self.apply_filters)
        filter_button_layout.addWidget(apply_button)
        
        search_layout.addLayout(filter_button_layout)

        layout.addWidget(search_group)

        # 支払い月フィルター
        month_group = QGroupBox("📅 支払い月")
        month_layout = QVBoxLayout(month_group)

        self.payment_month_filter = QComboBox()
        self.payment_month_filter.addItem("すべて")
        # 自動適用を削除し、手動適用ボタンで制御
        month_layout.addWidget(self.payment_month_filter)

        layout.addWidget(month_group)

        # 案件状況フィルター
        project_status_group = QGroupBox("案件状況")
        project_status_layout = QVBoxLayout(project_status_group)

        self.project_status_filter = QComboBox()
        self.project_status_filter.addItem("すべて")
        project_status_layout.addWidget(self.project_status_filter)

        layout.addWidget(project_status_group)

        # 支払い状態フィルター
        payment_status_group = QGroupBox("💳 支払い状態")
        payment_status_layout = QVBoxLayout(payment_status_group)

        self.payment_status_filter = QComboBox()
        self.payment_status_filter.addItem("すべて")
        payment_status_layout.addWidget(self.payment_status_filter)

        layout.addWidget(payment_status_group)

        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # リセットボタン
        reset_button = QPushButton("リセット")
        reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)

        layout.addStretch()

    def create_project_list_pane(self, parent):
        """中央ペイン：案件別支払い一覧の作成"""
        center_frame = QFrame()
        center_frame.setFrameStyle(QFrame.StyledPanel)
        parent.addWidget(center_frame)

        layout = QVBoxLayout(center_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ヘッダー
        header = QLabel("📋 案件一覧")
        header.setStyleSheet("background: darkslategray; color: white; padding: 8px; margin-bottom: 5px; font-weight: bold;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # 案件情報表示エリア
        self.project_info_frame = QFrame()
        self.project_info_frame.setStyleSheet("background: whitesmoke; border: 1px solid lightgray; padding: 10px;")
        self.project_info_frame.setMaximumHeight(100)
        layout.addWidget(self.project_info_frame)

        project_info_layout = QVBoxLayout(self.project_info_frame)
        project_info_layout.setContentsMargins(10, 8, 10, 8)
        project_info_layout.setSpacing(4)

        self.project_name_label = QLabel("案件を選択してください")
        self.project_name_label.setStyleSheet("font-weight: bold; color: darkslategray;")
        project_info_layout.addWidget(self.project_name_label)

        self.project_details_label = QLabel("")
        self.project_details_label.setProperty("small", True)
        project_info_layout.addWidget(self.project_details_label)

        # 支払い一覧
        self.payment_tree = QTreeWidget()
        self.payment_tree.setHeaderLabels([
            "支払先", "件名", "金額", "支払期限", "状態", "緊急度"
        ])
        self.payment_tree.itemSelectionChanged.connect(self.on_payment_select)
        layout.addWidget(self.payment_tree)

        # 列の設定
        self.payment_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.payment_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.payment_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.payment_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.payment_tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.payment_tree.header().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        # 案件一覧（上部）
        project_list_label = QLabel("📁 案件リスト")
        project_list_label.setStyleSheet("font-weight: bold; color: darkslategray; margin-top: 10px;")
        layout.insertWidget(1, project_list_label)

        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels([
            "案件名", "クライアント", "部門", "状況", "予算", "支払件数"
        ])
        self.project_tree.setMaximumHeight(200)
        self.project_tree.itemSelectionChanged.connect(self.on_project_select)
        layout.insertWidget(2, self.project_tree)

        # 列の設定
        self.project_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.project_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.project_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.project_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.project_tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.project_tree.header().setSectionResizeMode(5, QHeaderView.ResizeToContents)

    def create_detail_pane(self, parent):
        """右ペイン：詳細情報・編集の作成"""
        detail_frame = QFrame()
        detail_frame.setFrameStyle(QFrame.StyledPanel)
        parent.addWidget(detail_frame)

        layout = QVBoxLayout(detail_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ヘッダー
        self.detail_header = QLabel("詳細情報")
        self.detail_header.setStyleSheet("background: #495057; color: white; padding: 8px; margin-bottom: 5px; font-weight: bold;")
        self.detail_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_header)

        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 基本情報グループ
        basic_group = QGroupBox("📋 基本情報")
        basic_layout = QGridLayout(basic_group)

        # フィールド作成
        self.detail_fields = {}
        field_labels = [
            ("件名", "subject"),
            ("案件名", "project_name"),
            ("支払先", "payee"),
            ("支払先コード", "payee_code"),
            ("金額", "amount"),
            ("支払期限", "payment_date"),
            ("状態", "status"),
        ]

        for i, (label, field) in enumerate(field_labels):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(f"{label}:")
            basic_layout.addWidget(label_widget, row, col)

            if field == "status":
                field_widget = QComboBox()
                field_widget.addItems(["未処理", "処理中", "処理済", "照合済"])
            elif field == "amount":
                field_widget = QLineEdit()
                field_widget.setPlaceholderText("0")
            else:
                field_widget = QLineEdit()

            basic_layout.addWidget(field_widget, row, col + 1)
            self.detail_fields[field] = field_widget

        scroll_layout.addWidget(basic_group)

        # 案件情報グループ
        project_group = QGroupBox("🏢 案件情報")
        project_layout = QGridLayout(project_group)

        project_field_labels = [
            ("クライアント", "client_name"),
            ("担当部門", "department"),
            ("案件状況", "project_status"),
            ("開始日", "project_start_date"),
            ("完了予定日", "project_end_date"),
            ("予算", "budget"),
            ("承認者", "approver"),
            ("緊急度", "urgency_level"),
        ]

        for i, (label, field) in enumerate(project_field_labels):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(f"{label}:")
            project_layout.addWidget(label_widget, row, col)

            if field == "project_status":
                field_widget = QComboBox()
                field_widget.addItems(["進行中", "完了", "中止", "保留"])
            elif field == "urgency_level":
                field_widget = QComboBox()
                field_widget.addItems(["通常", "重要", "緊急"])
            elif field in ["project_start_date", "project_end_date"]:
                field_widget = QDateEdit()
                field_widget.setDate(QDate.currentDate())
                field_widget.setCalendarPopup(True)
            elif field == "budget":
                field_widget = QLineEdit()
                field_widget.setPlaceholderText("0")
            else:
                field_widget = QLineEdit()

            project_layout.addWidget(field_widget, row, col + 1)
            self.detail_fields[field] = field_widget

        scroll_layout.addWidget(project_group)

        # ボタングループ
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout(button_group)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_payment_details)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        scroll_layout.addWidget(button_group)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

    def create_status_bar(self, layout):
        """ステータスバーの作成"""
        status_frame = QFrame()
        status_frame.setStyleSheet("background: lightgray; border-top: 1px solid gray; padding: 5px;")
        status_layout = QHBoxLayout(status_frame)

        self.status_info_label = QLabel("準備完了")
        self.status_info_label.setProperty("small", True)
        status_layout.addWidget(self.status_info_label)

        status_layout.addStretch()

        self.summary_label = QLabel("")
        self.summary_label.setProperty("small", True)
        status_layout.addWidget(self.summary_label)

        layout.addWidget(status_frame)

    def refresh_filter_options(self):
        """フィルターオプションを更新"""
        try:
            log_message("フィルターオプションの更新を開始")
            options = self.db_manager.get_filter_options()
            
            # オプションの内容をログ出力
            log_message(f"取得したオプション: {list(options.keys())}")
            
            # 支払い月フィルターの更新
            self.payment_month_filter.clear()
            self.payment_month_filter.addItem("すべて")
            
            # 支払い月フィルターの更新
            if 'payment_month_options' in options:
                payment_months = options['payment_month_options']
                log_message(f"支払い月オプション: {len(payment_months)}件 - {payment_months[:5]}")
                
                if len(payment_months) == 0:
                    # 空データの場合の処理
                    log_message("支払い月のデータが空です。データを確認してください。")
                    self.payment_month_filter.addItem("データなし")
                    self.payment_month_filter.setEnabled(False)
                    self.status_info_label.setText("データが見つかりません。CSVファイルを読み込んでください。")
                else:
                    # 正常なデータがある場合
                    self.payment_month_filter.setEnabled(True)
                    for month in payment_months:
                        if month:  # Noneや空文字を除外
                            self.payment_month_filter.addItem(month)
                    
                    log_message(f"支払い月フィルターに{len(payment_months)}件の選択肢を追加")
                    self.status_info_label.setText("準備完了")
            else:
                log_message("警告: payment_month_optionsキーが見つかりません")
                # フォールバック処理: 直接データベースから取得を試みる
                self.load_payment_months_fallback()
                
            # 案件状況フィルターの更新
            if 'project_status_options' in options:
                project_statuses = options['project_status_options']
                log_message(f"案件状況オプション: {len(project_statuses)}件 - {project_statuses}")
                
                self.project_status_filter.clear()
                self.project_status_filter.addItem("すべて")
                
                for status in project_statuses:
                    if status:
                        self.project_status_filter.addItem(status)
                        
                log_message(f"案件状況フィルターに{len(project_statuses)}件の選択肢を追加")
            
            # 支払い状態フィルターの更新
            if 'payment_status_options' in options:
                payment_statuses = options['payment_status_options']
                log_message(f"支払い状態オプション: {len(payment_statuses)}件 - {payment_statuses}")
                
                self.payment_status_filter.clear()
                self.payment_status_filter.addItem("すべて")
                
                for status in payment_statuses:
                    if status:
                        self.payment_status_filter.addItem(status)
                        
                log_message(f"支払い状態フィルターに{len(payment_statuses)}件の選択肢を追加")

        except Exception as e:
            log_message(f"フィルターオプション更新エラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")
            # エラー時のフォールバック
            self.load_payment_months_fallback()
    
    def load_payment_months_fallback(self):
        """フォールバック: 直接データベースから支払い月を取得"""
        try:
            log_message("フォールバック: 直接データベースから支払い月を取得")
            import sqlite3
            conn = sqlite3.connect(self.db_manager.billing_db)
            cursor = conn.cursor()
            
            # 支払い月を直接取得
            cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', REPLACE(payment_date, '/', '-')) as payment_month
                FROM payments 
                WHERE payment_date IS NOT NULL AND payment_date != ''
                AND strftime('%Y-%m', REPLACE(payment_date, '/', '-')) IS NOT NULL
                ORDER BY payment_month DESC
            """)
            
            months = [row[0] for row in cursor.fetchall() if row[0]]
            log_message(f"フォールバックで取得した支払い月: {len(months)}件 - {months[:5]}")
            
            # フィルターに追加
            if not hasattr(self, 'payment_month_filter'):
                log_message("エラー: payment_month_filterが初期化されていません")
                return
                
            for month in months:
                if month:
                    self.payment_month_filter.addItem(month)
                    
            log_message(f"フォールバックで{len(months)}件の支払い月を追加しました")
            
        except Exception as e:
            log_message(f"フォールバック処理エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def apply_filters(self):
        """フィルターを適用して案件データを更新"""
        try:
            # フィルター条件を収集
            filters = {}
            filter_descriptions = []
            
            search_term = self.search_entry.text().strip()
            if search_term:
                filters['search_term'] = search_term
                filter_descriptions.append(f"検索: '{search_term}'")

            payment_month = self.payment_month_filter.currentText()
            if payment_month != "すべて":
                filters['payment_month'] = payment_month
                filter_descriptions.append(f"支払い月: {payment_month}")

            project_status = self.project_status_filter.currentText()
            if project_status != "すべて":
                filters['project_status'] = project_status
                filter_descriptions.append(f"案件状況: {project_status}")

            payment_status = self.payment_status_filter.currentText()
            if payment_status != "すべて":
                filters['payment_status'] = payment_status
                filter_descriptions.append(f"支払い状態: {payment_status}")

            # フィルター状態を保存
            self.current_filters = filters
            
            # ログ出力
            if filter_descriptions:
                log_message(f"フィルターを適用: {', '.join(filter_descriptions)}")
                self.status_info_label.setText(f"適用中のフィルター: {', '.join(filter_descriptions)}")
            else:
                log_message("全てのフィルターをクリアして表示")
                self.status_info_label.setText("フィルターなし - 全件表示")
            
            # データを更新
            self.refresh_project_data()
            
        except Exception as e:
            log_message(f"フィルター適用エラー: {e}")
            self.status_info_label.setText("フィルター適用中にエラーが発生しました")

    def reset_filters(self):
        """フィルターをリセット"""
        try:
            # 検索フィールドをクリア
            if hasattr(self, 'search_entry'):
                self.search_entry.clear()
            
            # 支払い月フィルターをリセット
            if hasattr(self, 'payment_month_filter'):
                self.payment_month_filter.setCurrentText("すべて")
                
            # 案件状況フィルターをリセット
            if hasattr(self, 'project_status_filter'):
                self.project_status_filter.setCurrentText("すべて")
                
            # 支払い状態フィルターをリセット
            if hasattr(self, 'payment_status_filter'):
                self.payment_status_filter.setCurrentText("すべて")
            
            # フィルター状態をクリア
            self.current_filters = {}
            
            # データを再読み込み
            self.refresh_project_data()
            
            # 選択状態もクリア
            self.current_project = None
            self.clear_payment_list()
            
            # ステータス更新
            self.status_info_label.setText("フィルターをリセットしました")
            
            log_message("フィルターを正常にリセットしました")
            
        except Exception as e:
            log_message(f"フィルターリセットエラー: {e}")
            self.status_info_label.setText("フィルターリセット中にエラーが発生しました")

    def refresh_project_data(self):
        """案件データを更新"""
        try:
            # 案件データを取得
            project_rows = self.db_manager.get_project_filter_data(self.current_filters)

            # 案件ツリーをクリア
            self.project_tree.clear()

            project_count = 0
            total_amount = 0

            for row in project_rows:
                project_name = row[0] if row[0] else "未設定"
                client_name = row[1] if row[1] else "未設定"
                department = row[2] if row[2] else "未設定"
                project_status = row[3] if row[3] else "進行中"
                budget = row[6] if row[6] else 0
                payment_count = row[7] if row[7] else 0
                project_amount = row[8] if row[8] else 0

                item = QTreeWidgetItem()
                item.setText(0, project_name)
                item.setText(1, client_name)
                item.setText(2, department)
                item.setText(3, project_status)
                item.setText(4, format_amount(budget))
                item.setText(5, f"{payment_count}件")

                # 状況に応じた色分け
                if project_status == "完了":
                    self.apply_row_colors(item, self.paid_color)
                elif project_status == "中止":
                    self.apply_row_colors(item, self.urgent_color)
                elif project_status == "保留":
                    self.apply_row_colors(item, self.warning_color)
                else:
                    self.apply_row_colors(item, self.normal_color)

                self.project_tree.addTopLevelItem(item)
                project_count += 1
                total_amount += project_amount

            # ステータス更新
            if project_count == 0:
                if self.current_filters:
                    self.status_info_label.setText("絞込み条件に一致する案件が見つかりません")
                else:
                    self.status_info_label.setText("案件データがありません。CSVファイルを読み込んでください。")
            else:
                filter_status = ""
                if self.current_filters:
                    filter_descriptions = []
                    if 'search_term' in self.current_filters:
                        filter_descriptions.append(f"検索: '{self.current_filters['search_term']}'")
                    if 'payment_month' in self.current_filters:
                        filter_descriptions.append(f"支払い月: {self.current_filters['payment_month']}")
                    if 'project_status' in self.current_filters:
                        filter_descriptions.append(f"案件状況: {self.current_filters['project_status']}")
                    if 'payment_status' in self.current_filters:
                        filter_descriptions.append(f"支払い状態: {self.current_filters['payment_status']}")
                    if filter_descriptions:
                        filter_status = f" | フィルター: {', '.join(filter_descriptions)}"
                
                self.status_info_label.setText(
                    f"絞込み結果: {project_count}案件 | 総額: {format_amount(total_amount)}{filter_status}"
                )

        except Exception as e:
            log_message(f"案件データ更新エラー: {e}")
            self.status_info_label.setText("エラー: 案件データの取得に失敗しました")

    def on_project_select(self):
        """案件選択時の処理"""
        selected_items = self.project_tree.selectedItems()
        if not selected_items:
            self.current_project = None
            self.clear_payment_list()
            return

        item = selected_items[0]
        project_name = item.text(0)
        client_name = item.text(1)
        department = item.text(2)
        project_status = item.text(3)
        budget = item.text(4)
        payment_count = item.text(5)

        self.current_project = project_name

        # 案件情報を表示
        self.project_name_label.setText(f"📋 {project_name}")
        self.project_details_label.setText(
            f"クライアント: {client_name} | 部門: {department} | 状況: {project_status} | 予算: {budget} | 支払件数: {payment_count}"
        )

        # 支払いデータを読み込み
        self.refresh_payment_data()

    def refresh_payment_data(self):
        """選択案件の支払いデータを更新"""
        if not self.current_project:
            return

        try:
            # 支払い月フィルターを取得
            payment_month = None
            if self.current_filters.get('payment_month'):
                payment_month = self.current_filters['payment_month']
            
            payment_rows = self.db_manager.get_payments_by_project(self.current_project, payment_month)

            # 支払いツリーをクリア
            self.payment_tree.clear()

            for row in payment_rows:
                payment_id = row[0]
                subject = row[1] if row[1] else ""
                payee = row[3] if row[3] else ""
                amount = row[5] if row[5] else 0
                payment_date = row[6] if row[6] else ""
                status = row[7] if row[7] else "未処理"
                urgency = row[8] if row[8] else "通常"

                item = QTreeWidgetItem()
                item.setText(0, payee)
                item.setText(1, subject)
                item.setText(2, format_amount(amount))
                item.setText(3, payment_date)
                item.setText(4, status)
                item.setText(5, urgency)

                # データを保存
                item.setData(0, Qt.UserRole, payment_id)

                # 状態に応じた色分け
                if status == "支払済み" or status == "照合済":
                    self.apply_row_colors(item, self.paid_color)
                elif status == "処理中":
                    self.apply_row_colors(item, self.processing_color)
                elif urgency == "緊急":
                    self.apply_row_colors(item, self.urgent_color)
                elif urgency == "重要":
                    self.apply_row_colors(item, self.warning_color)
                else:
                    self.apply_row_colors(item, self.normal_color)

                self.payment_tree.addTopLevelItem(item)

        except Exception as e:
            log_message(f"支払いデータ更新エラー: {e}")

    def clear_payment_list(self):
        """支払い一覧をクリア"""
        self.payment_tree.clear()
        self.project_name_label.setText("案件を選択してください")
        self.project_details_label.setText("")

    def on_payment_select(self):
        """支払い選択時の処理"""
        selected_items = self.payment_tree.selectedItems()
        if not selected_items:
            self.clear_detail_fields()
            return

        item = selected_items[0]
        payment_id = item.data(0, Qt.UserRole)

        if payment_id:
            self.load_payment_details(payment_id)

    def load_payment_details(self, payment_id):
        """支払い詳細を読み込み"""
        try:
            # 支払いデータを取得（データベースから直接）
            import sqlite3
            conn = sqlite3.connect(self.db_manager.billing_db)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT subject, project_name, payee, payee_code, amount, payment_date, 
                       status, client_name, department, project_status, project_start_date, 
                       project_end_date, budget, approver, urgency_level
                FROM payments WHERE id = ?
                """,
                (payment_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                # 基本情報
                self.detail_fields['subject'].setText(row[0] or "")
                self.detail_fields['project_name'].setText(row[1] or "")
                self.detail_fields['payee'].setText(row[2] or "")
                self.detail_fields['payee_code'].setText(row[3] or "")
                self.detail_fields['amount'].setText(str(row[4] or 0))
                self.detail_fields['payment_date'].setText(row[5] or "")
                self.detail_fields['status'].setCurrentText(row[6] or "未処理")

                # 案件情報
                self.detail_fields['client_name'].setText(row[7] or "")
                self.detail_fields['department'].setText(row[8] or "")
                self.detail_fields['project_status'].setCurrentText(row[9] or "進行中")
                
                if row[10]:  # project_start_date
                    try:
                        date = QDate.fromString(row[10], "yyyy-MM-dd")
                        self.detail_fields['project_start_date'].setDate(date)
                    except:
                        pass

                if row[11]:  # project_end_date
                    try:
                        date = QDate.fromString(row[11], "yyyy-MM-dd")
                        self.detail_fields['project_end_date'].setDate(date)
                    except:
                        pass

                self.detail_fields['budget'].setText(str(row[12] or 0))
                self.detail_fields['approver'].setText(row[13] or "")
                self.detail_fields['urgency_level'].setCurrentText(row[14] or "通常")

                # ヘッダー更新
                payee = row[2] or "不明な支払先"
                self.detail_header.setText(f"詳細情報 - {payee}")

                # ボタンを有効化
                self.save_button.setEnabled(True)

                # 現在の支払いIDを保存
                self.current_payment_id = payment_id

        except Exception as e:
            log_message(f"支払い詳細読み込みエラー: {e}")

    def clear_detail_fields(self):
        """詳細フィールドをクリア"""
        for field_widget in self.detail_fields.values():
            if isinstance(field_widget, QLineEdit):
                field_widget.clear()
            elif isinstance(field_widget, QComboBox):
                field_widget.setCurrentIndex(0)
            elif isinstance(field_widget, QDateEdit):
                field_widget.setDate(QDate.currentDate())

        self.detail_header.setText("詳細情報")
        self.save_button.setEnabled(False)
        self.current_payment_id = None

    def save_payment_details(self):
        """支払い詳細を保存"""
        if not hasattr(self, 'current_payment_id') or not self.current_payment_id:
            return

        try:
            # 案件情報を収集
            project_info = {
                'client_name': self.detail_fields['client_name'].text(),
                'department': self.detail_fields['department'].text(),
                'project_status': self.detail_fields['project_status'].currentText(),
                'project_start_date': self.detail_fields['project_start_date'].date().toString("yyyy-MM-dd"),
                'project_end_date': self.detail_fields['project_end_date'].date().toString("yyyy-MM-dd"),
                'budget': float(self.detail_fields['budget'].text() or 0),
                'approver': self.detail_fields['approver'].text(),
                'urgency_level': self.detail_fields['urgency_level'].currentText()
            }

            # データベースを更新
            success = self.db_manager.update_payment_project_info(self.current_payment_id, project_info)

            if success:
                QMessageBox.information(self, "保存完了", "案件情報を保存しました。")
                
                # データを再読み込み
                self.refresh_project_data()
                if self.current_project:
                    self.refresh_payment_data()
            else:
                QMessageBox.warning(self, "保存失敗", "案件情報の保存に失敗しました。")

        except Exception as e:
            log_message(f"支払い詳細保存エラー: {e}")
            QMessageBox.critical(self, "エラー", f"保存中にエラーが発生しました: {e}")

    def approve_payment(self):
        """支払いを承認"""
        if hasattr(self, 'current_payment_id') and self.current_payment_id:
            self.detail_fields['status'].setCurrentText("承認済")
            self.save_payment_details()

    def hold_payment(self):
        """支払いを保留"""
        if hasattr(self, 'current_payment_id') and self.current_payment_id:
            self.detail_fields['status'].setCurrentText("保留")
            self.save_payment_details()

    def apply_row_colors(self, item, color):
        """行に色を適用"""
        brush = QBrush(color)
        text_brush = QBrush(QColor(0, 0, 0))  # 黒色

        for i in range(item.columnCount()):
            item.setBackground(i, brush)
            item.setForeground(i, text_brush)

    # ===== メニューバー/ツールバー用の共通アクション =====
    def export_csv(self):
        """CSV出力（メニュー/ツールバー用）"""
        try:
            # 現在表示されているデータをCSVで出力
            from PyQt5.QtWidgets import QFileDialog
            import csv
            from datetime import datetime
            
            # 案件データまたは支払いデータを出力
            active_tree = None
            filename_prefix = "project_filter"
            
            if hasattr(self, 'project_tree') and self.project_tree.topLevelItemCount() > 0:
                active_tree = self.project_tree
                filename_prefix = "projects"
            elif hasattr(self, 'payment_tree') and self.payment_tree.topLevelItemCount() > 0:
                active_tree = self.payment_tree
                filename_prefix = "filtered_payments"
            
            if not active_tree:
                QMessageBox.information(self, "CSV出力", "出力するデータがありません。")
                return
            
            # ファイル保存ダイアログ
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "データをCSVで保存",
                f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # ヘッダーを書き込み
                    headers = []
                    for col in range(active_tree.columnCount()):
                        headers.append(active_tree.headerItem().text(col))
                    writer.writerow(headers)
                    
                    # データを書き込み
                    for i in range(active_tree.topLevelItemCount()):
                        item = active_tree.topLevelItem(i)
                        row_data = []
                        for col in range(active_tree.columnCount()):
                            row_data.append(item.text(col))
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "完了", f"データを保存しました:\n{filename}")
                
        except Exception as e:
            log_message(f"CSV出力エラー: {e}")
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました: {e}")
    
    def create_new_entry(self):
        """新規エントリ作成（メニュー/ツールバー用）"""
        QMessageBox.information(self, "新規作成", 
                               "案件絞込みタブでは新規作成機能は利用できません。\n"
                               "費用管理タブまたはマスタータブをご利用ください。")
    
    def delete_selected(self):
        """選択項目削除（メニュー/ツールバー用）"""
        QMessageBox.information(self, "削除", 
                               "案件絞込みタブでは削除機能は利用できません。\n"
                               "費用管理タブまたはマスタータブをご利用ください。")
    
    def show_search(self):
        """検索表示（メニュー/ツールバー用）"""
        # 検索フィールドにフォーカスを設定
        if hasattr(self, 'search_entry'):
            self.search_entry.setFocus()
        elif hasattr(self, 'project_search_entry'):
            self.project_search_entry.setFocus()
        else:
            QMessageBox.information(self, "検索", "検索フィールドが見つかりません。")
    
    def reset_filters_from_menu(self):
        """フィルターリセット（メニュー/ツールバー用）"""
        # メイン関数を呼び出す
        self.reset_filters()
        # アプリケーション全体のステータスラベルも更新
        if hasattr(self, 'app') and hasattr(self.app, 'status_label'):
            self.app.status_label.setText("フィルターをリセットしました")
    
    def toggle_filter_panel(self, visible):
        """フィルターパネル表示切り替え"""
        try:
            if hasattr(self, 'search_frame'):
                self.search_frame.setVisible(visible)
        except Exception as e:
            log_message(f"フィルターパネル切り替えエラー: {e}")
    
    def run_matching(self):
        """照合実行（メニュー/ツールバー用）"""
        QMessageBox.information(self, "照合実行", 
                               "案件絞込みタブでは照合機能は利用できません。\n"
                               "費用管理タブの支払い照合をご利用ください。")


# ファイル終了確認用のコメント - project_filter_tab.py完了