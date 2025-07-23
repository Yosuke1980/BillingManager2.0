"""
Generic Application Framework for PyQt5

This module provides a reusable application framework that can be configured
for different business domains through configuration files.
"""

import sys
import json
import os
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QMessageBox, QMenuBar, QToolBar
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .action_manager import ActionManager
from .tab_manager import TabManager, BaseTabPlugin


class GenericApplication(QMainWindow):
    """
    Generic configurable application framework.
    
    Features:
    - Configuration-driven UI
    - Plugin-based tab system
    - Centralized action management
    - Extensible architecture
    """
    
    status_changed = pyqtSignal(str)
    
    def __init__(self, config_path: str = None):
        super().__init__()
        
        # Load configuration
        self._config = self._load_config(config_path or "config/app_config.json")
        
        # Initialize managers
        self._action_manager = ActionManager(self)
        self._tab_manager = None
        
        # Application context for plugins
        self._app_context = {
            'config': self._config,
            'action_manager': self._action_manager,
            'main_window': self
        }
        
        # UI components
        self._tab_widget = None
        self._status_bar = None
        
        # Initialize UI
        self._setup_window()
        self._setup_ui()
        self._setup_actions()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_plugins()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "application": {
                "name": "Generic Application",
                "version": "1.0.0",
                "window": {
                    "title": "Generic Application",
                    "geometry": {"x": 100, "y": 100, "width": 1200, "height": 800}
                }
            },
            "plugins": [],
            "menus": {},
            "toolbar": {"main": []},
            "actions": {}
        }
    
    def _setup_window(self) -> None:
        """Setup main window properties."""
        app_config = self._config.get('application', {})
        window_config = app_config.get('window', {})
        
        # Set window title
        title = window_config.get('title', app_config.get('name', 'Generic Application'))
        self.setWindowTitle(title)
        
        # Set window geometry
        geometry = window_config.get('geometry', {})
        x = geometry.get('x', 100)
        y = geometry.get('y', 100)
        width = geometry.get('width', 1200)
        height = geometry.get('height', 800)
        self.setGeometry(x, y, width, height)
        
        # Set minimum size
        min_size = window_config.get('minimum_size', {})
        min_width = min_size.get('width', 800)
        min_height = min_size.get('height', 600)
        self.setMinimumSize(min_width, min_height)
    
    def _setup_ui(self) -> None:
        """Setup main UI components."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabPosition(QTabWidget.North)
        self._tab_widget.setMovable(False)
        self._tab_widget.setTabsClosable(False)
        
        main_layout.addWidget(self._tab_widget)
        
        # Create status bar
        self._status_bar = self.statusBar()
        self._status_bar.showMessage("Ready")
        
        # Connect signals
        self.status_changed.connect(self._status_bar.showMessage)
    
    def _setup_actions(self) -> None:
        """Setup application actions."""
        # Load actions from config
        actions_config = self._config.get('actions', {})
        for action_id, action_config in actions_config.items():
            self._action_manager.create_action(
                action_id=action_id,
                text=action_config.get('text', action_id),
                shortcut=action_config.get('shortcut'),
                tooltip=action_config.get('tooltip'),
                checkable=action_config.get('checkable', False),
                enabled=action_config.get('enabled', True),
                callback=lambda aid=action_id: self._handle_action(aid)
            )
        
        # Connect action manager signals
        self._action_manager.action_triggered.connect(self._handle_action)
    
    def _setup_menus(self) -> None:
        """Setup application menus."""
        menubar = self.menuBar()
        menus_config = self._config.get('menus', {})
        
        for menu_name, menu_items in menus_config.items():
            menu = menubar.addMenu(menu_name)
            self._action_manager.populate_menu(menu, menu_items)
    
    def _setup_toolbars(self) -> None:
        """Setup application toolbars."""
        toolbar_config = self._config.get('toolbar', {})
        
        for toolbar_name, toolbar_items in toolbar_config.items():
            toolbar = self.addToolBar(toolbar_name.title())
            toolbar.setMovable(False)
            self._action_manager.populate_toolbar(toolbar, toolbar_items)
    
    def _setup_plugins(self) -> None:
        """Setup plugin system."""
        # Initialize tab manager
        self._tab_manager = TabManager(self._tab_widget, self)
        self._tab_manager.set_app_context(self._app_context)
        
        # Connect signals
        self._tab_manager.tab_loaded.connect(self._on_tab_loaded)
        self._tab_manager.tab_unloaded.connect(self._on_tab_unloaded)
        self._tab_manager.tab_error.connect(self._on_tab_error)
        
        # Discover plugins in plugins directory
        plugins_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins')
        if os.path.exists(plugins_dir):
            self._tab_manager.discover_plugins_in_directory(plugins_dir)
        
        # Load plugins from config
        self._tab_manager.load_plugins_from_config(self._config)
        
        # Connect tab change signal
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _handle_action(self, action_id: str) -> None:
        """Handle application actions."""
        # Try to execute action on current plugin first
        if self._tab_manager:
            current_plugin = self._tab_manager.get_current_plugin()
            if current_plugin:
                # Map generic action IDs to plugin methods
                action_mapping = {
                    'file_export': 'export_data',
                    'file_import': 'import_data', 
                    'edit_new': 'create_new_entry',
                    'edit_delete': 'delete_selected',
                    'edit_find': 'search_data',
                    'view_refresh': 'refresh_data',
                    'edit_reset': 'reset_filters'
                }
                
                if action_id in action_mapping:
                    method_name = action_mapping[action_id]
                    if hasattr(current_plugin, method_name):
                        try:
                            method = getattr(current_plugin, method_name)
                            method()
                            return
                        except Exception as e:
                            self.status_changed.emit(f"Error executing {action_id}: {str(e)}")
                            return
        
        # Handle application-level actions
        if action_id == 'file_reload':
            self._reload_data()
        elif action_id == 'file_exit':
            self.close()
        elif action_id == 'view_toggle_filter':
            self._toggle_filter_panel()
        elif action_id == 'tools_match':
            self._run_matching()
        elif action_id == 'tools_generate_master':
            self._generate_master()
        elif action_id == 'help_about':
            self._show_about()
        else:
            self.status_changed.emit(f"Action not implemented: {action_id}")
    
    def _reload_data(self) -> None:
        """Reload application data."""
        if self._tab_manager:
            current_plugin = self._tab_manager.get_current_plugin()
            if current_plugin and hasattr(current_plugin, 'refresh_data'):
                current_plugin.refresh_data()
                self.status_changed.emit("Data reloaded")
            else:
                self.status_changed.emit("Current tab does not support data reload")
    
    def _toggle_filter_panel(self) -> None:
        """Toggle filter panel visibility."""
        action = self._action_manager.get_action('view_toggle_filter')
        if action:
            visible = action.isChecked()
            if self._tab_manager:
                current_plugin = self._tab_manager.get_current_plugin()
                if current_plugin and hasattr(current_plugin, 'toggle_filter_panel'):
                    current_plugin.toggle_filter_panel(visible)
    
    def _run_matching(self) -> None:
        """Run matching operation."""
        if self._tab_manager:
            current_plugin = self._tab_manager.get_current_plugin()
            if current_plugin and hasattr(current_plugin, 'run_matching'):
                current_plugin.run_matching()
                self.status_changed.emit("Matching completed")
            else:
                QMessageBox.information(self, "Matching", "Current tab does not support matching")
    
    def _generate_master(self) -> None:
        """Generate master data."""
        if self._tab_manager:
            # Find master plugin
            master_plugin = self._tab_manager.get_plugin('MasterPlugin')
            if master_plugin and hasattr(master_plugin, 'generate_master_data'):
                master_plugin.generate_master_data()
                self.status_changed.emit("Master data generated")
            else:
                QMessageBox.information(self, "Master Generation", "Master plugin not available")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        app_config = self._config.get('application', {})
        name = app_config.get('name', 'Generic Application')
        version = app_config.get('version', '1.0.0')
        author = app_config.get('author', 'Unknown')
        
        QMessageBox.about(self, "About", 
                         f"{name}\n"
                         f"Version {version}\n"
                         f"Author: {author}\n\n"
                         f"Generic PyQt5 Application Framework")
    
    def _on_tab_loaded(self, plugin_id: str) -> None:
        """Handle tab loaded event."""
        self.status_changed.emit(f"Plugin loaded: {plugin_id}")
    
    def _on_tab_unloaded(self, plugin_id: str) -> None:
        """Handle tab unloaded event."""
        self.status_changed.emit(f"Plugin unloaded: {plugin_id}")
    
    def _on_tab_error(self, plugin_id: str, error_message: str) -> None:
        """Handle tab error event."""
        self.status_changed.emit(f"Plugin error ({plugin_id}): {error_message}")
        QMessageBox.critical(self, "Plugin Error", f"Error with plugin {plugin_id}:\n{error_message}")
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event."""
        if index >= 0 and self._tab_manager:
            current_plugin = self._tab_manager.get_current_plugin()
            if current_plugin:
                # Update action states based on current plugin capabilities
                capabilities = current_plugin.get_supported_actions()
                
                # Enable/disable actions based on plugin capabilities
                self._action_manager.set_action_enabled('file_export', 'export' in capabilities)
                self._action_manager.set_action_enabled('file_import', 'import' in capabilities)
                self._action_manager.set_action_enabled('edit_new', 'create' in capabilities)
                self._action_manager.set_action_enabled('edit_delete', 'delete' in capabilities)
                self._action_manager.set_action_enabled('edit_find', 'search' in capabilities)
                
                self.status_changed.emit(f"Switched to: {current_plugin.get_display_name()}")
    
    # Public API for extending functionality
    def get_action_manager(self) -> ActionManager:
        """Get action manager instance."""
        return self._action_manager
    
    def get_tab_manager(self) -> Optional[TabManager]:
        """Get tab manager instance.""" 
        return self._tab_manager
    
    def get_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return self._config
    
    def register_plugin(self, plugin_class, config: Optional[Dict[str, Any]] = None) -> None:
        """Register a plugin class."""
        if self._tab_manager:
            self._tab_manager.register_plugin_class(plugin_class, config)
    
    def load_plugin(self, plugin_id: str) -> bool:
        """Load a plugin."""
        if self._tab_manager:
            return self._tab_manager.load_plugin(plugin_id)
        return False


def create_application(config_path: str = None) -> GenericApplication:
    """Create and configure application instance."""
    # Ensure QApplication exists
    if not QApplication.instance():
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create main window
    main_window = GenericApplication(config_path)
    return main_window