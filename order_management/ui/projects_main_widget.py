"""案件管理メインウィジェット

案件一覧、ツリービュー、アラートを統合したメインウィジェットです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from order_management.ui.alert_widget import AlertWidget
from order_management.ui.project_list_widget import ProjectListWidget
from order_management.ui.project_tree_widget import ProjectTreeWidget


class ProjectsMainWidget(QWidget):
    """案件管理メインウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

        # 初回アラート更新
        self.alert_widget.update_alerts()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # アラートウィジェット
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)

        # スプリッター（案件一覧とツリービュー）
        splitter = QSplitter(Qt.Vertical)

        # 案件一覧
        self.project_list = ProjectListWidget()

        # ツリービュー
        self.project_tree = ProjectTreeWidget()

        splitter.addWidget(self.project_list)
        splitter.addWidget(self.project_tree)

        # 初期サイズ比率を設定
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)

    def _connect_signals(self):
        """シグナルを接続"""
        # 案件選択時にツリービューを更新（複数ID対応）
        self.project_list.projects_selected.connect(self.on_projects_selected)

    def on_projects_selected(self, project_ids: list):
        """案件選択時の処理（複数ID対応）"""
        self.project_tree.load_projects(project_ids)
        # アラートも更新
        self.alert_widget.update_alerts()

    def refresh_all(self):
        """全体をリフレッシュ"""
        self.project_list.load_projects()
        self.alert_widget.update_alerts()
        if self.project_list.current_project_id:
            self.project_tree.load_project(self.project_list.current_project_id)
