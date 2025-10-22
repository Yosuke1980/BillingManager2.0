"""
Generic Action Management System for PyQt5 Applications

This module provides a centralized system for managing QActions, menus, and toolbars
in a configuration-driven manner.
"""

from PyQt5.QtWidgets import QAction, QActionGroup, QMenu, QToolBar
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QKeySequence
from typing import Dict, List, Optional, Callable, Any
import json
import os


class ActionManager(QObject):
    """
    Centralized manager for QActions, menus, and toolbars.
    
    Features:
    - Configuration-driven action creation
    - Action grouping and state management
    - Automatic menu and toolbar population
    - Plugin-friendly action registration
    - Multi-language support
    """
    
    action_triggered = pyqtSignal(str)  # action_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: Dict[str, QAction] = {}
        self._action_groups: Dict[str, QActionGroup] = {}
        self._menus: Dict[str, QMenu] = {}
        self._toolbars: Dict[str, QToolBar] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._config = {}
        
    def load_config(self, config_path: str) -> None:
        """Load action configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except Exception as e:
            print(f"Failed to load action config: {e}")
            self._config = {}
    
    def register_callback(self, action_id: str, callback: Callable) -> None:
        """Register a callback function for an action."""
        self._callbacks[action_id] = callback
    
    def create_action(self, 
                     action_id: str,
                     text: str,
                     callback: Optional[Callable] = None,
                     shortcut: Optional[str] = None,
                     icon: Optional[str] = None,
                     tooltip: Optional[str] = None,
                     checkable: bool = False,
                     enabled: bool = True,
                     group: Optional[str] = None) -> QAction:
        """Create and register a QAction."""
        
        action = QAction(text, self.parent())
        action.setObjectName(action_id)
        
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        
        if icon and os.path.exists(icon):
            action.setIcon(QIcon(icon))
        
        if tooltip:
            action.setStatusTip(tooltip)
            action.setToolTip(tooltip)
        
        action.setCheckable(checkable)
        action.setEnabled(enabled)
        
        # Connect callback
        if callback:
            action.triggered.connect(callback)
            self._callbacks[action_id] = callback
        else:
            action.triggered.connect(lambda: self._on_action_triggered(action_id))
        
        # Add to group if specified
        if group:
            if group not in self._action_groups:
                self._action_groups[group] = QActionGroup(self.parent())
            self._action_groups[group].addAction(action)
        
        self._actions[action_id] = action
        return action
    
    def get_action(self, action_id: str) -> Optional[QAction]:
        """Get action by ID."""
        return self._actions.get(action_id)
    
    def set_action_enabled(self, action_id: str, enabled: bool) -> None:
        """Enable/disable an action."""
        action = self.get_action(action_id)
        if action:
            action.setEnabled(enabled)
    
    def set_action_checked(self, action_id: str, checked: bool) -> None:
        """Set action checked state."""
        action = self.get_action(action_id)
        if action and action.isCheckable():
            action.setChecked(checked)
    
    def create_actions_from_config(self) -> None:
        """Create actions based on configuration."""
        actions_config = self._config.get('actions', {})
        
        for action_id, config in actions_config.items():
            self.create_action(
                action_id=action_id,
                text=config.get('text', action_id),
                shortcut=config.get('shortcut'),
                icon=config.get('icon'),
                tooltip=config.get('tooltip'),
                checkable=config.get('checkable', False),
                enabled=config.get('enabled', True),
                group=config.get('group')
            )
    
    def populate_menu(self, menu: QMenu, menu_config: List[Dict[str, Any]]) -> None:
        """Populate menu based on configuration."""
        for item in menu_config:
            item_type = item.get('type', 'action')
            
            if item_type == 'separator':
                menu.addSeparator()
            elif item_type == 'action':
                action_id = item.get('action_id')
                action = self.get_action(action_id)
                if action:
                    menu.addAction(action)
            elif item_type == 'submenu':
                submenu = menu.addMenu(item.get('text', 'Submenu'))
                submenu_items = item.get('items', [])
                self.populate_menu(submenu, submenu_items)
    
    def populate_toolbar(self, toolbar: QToolBar, toolbar_config: List[Dict[str, Any]]) -> None:
        """Populate toolbar based on configuration."""
        for item in toolbar_config:
            item_type = item.get('type', 'action')
            
            if item_type == 'separator':
                toolbar.addSeparator()
            elif item_type == 'action':
                action_id = item.get('action_id')
                action = self.get_action(action_id)
                if action:
                    toolbar.addAction(action)
    
    def create_standard_actions(self) -> None:
        """Create standard application actions."""
        # File actions
        self.create_action('file_new', 'New', shortcut='Ctrl+N', 
                          tooltip='Create new document', group='file')
        self.create_action('file_open', 'Open', shortcut='Ctrl+O', 
                          tooltip='Open document', group='file')
        self.create_action('file_save', 'Save', shortcut='Ctrl+S', 
                          tooltip='Save document', group='file')
        self.create_action('file_save_as', 'Save As...', shortcut='Ctrl+Shift+S', 
                          tooltip='Save document as...', group='file')
        self.create_action('file_export', 'Export', shortcut='Ctrl+E', 
                          tooltip='Export data', group='file')
        self.create_action('file_import', 'Import', shortcut='Ctrl+I', 
                          tooltip='Import data', group='file')
        self.create_action('file_reload', 'Reload', shortcut='F5', 
                          tooltip='Reload data', group='file')
        self.create_action('file_exit', 'Exit', shortcut='Ctrl+Q', 
                          tooltip='Exit application', group='file')
        
        # Edit actions
        self.create_action('edit_undo', 'Undo', shortcut='Ctrl+Z', 
                          tooltip='Undo last action', group='edit')
        self.create_action('edit_redo', 'Redo', shortcut='Ctrl+Y', 
                          tooltip='Redo action', group='edit')
        self.create_action('edit_cut', 'Cut', shortcut='Ctrl+X', 
                          tooltip='Cut selection', group='edit')
        self.create_action('edit_copy', 'Copy', shortcut='Ctrl+C', 
                          tooltip='Copy selection', group='edit')
        self.create_action('edit_paste', 'Paste', shortcut='Ctrl+V', 
                          tooltip='Paste from clipboard', group='edit')
        self.create_action('edit_delete', 'Delete', shortcut='Delete', 
                          tooltip='Delete selection', group='edit')
        self.create_action('edit_select_all', 'Select All', shortcut='Ctrl+A', 
                          tooltip='Select all', group='edit')
        self.create_action('edit_find', 'Find', shortcut='Ctrl+F', 
                          tooltip='Find text', group='edit')
        
        # View actions
        self.create_action('view_refresh', 'Refresh', shortcut='F5', 
                          tooltip='Refresh view', group='view')
        self.create_action('view_zoom_in', 'Zoom In', shortcut='Ctrl++', 
                          tooltip='Zoom in', group='view')
        self.create_action('view_zoom_out', 'Zoom Out', shortcut='Ctrl+-', 
                          tooltip='Zoom out', group='view')
        self.create_action('view_reset_zoom', 'Reset Zoom', shortcut='Ctrl+0', 
                          tooltip='Reset zoom level', group='view')
        
        # Tool actions
        self.create_action('tools_options', 'Options', 
                          tooltip='Application options', group='tools')
        
        # Help actions
        self.create_action('help_about', 'About', 
                          tooltip='About this application', group='help')
        self.create_action('help_help', 'Help', shortcut='F1', 
                          tooltip='Show help', group='help')
    
    def _on_action_triggered(self, action_id: str) -> None:
        """Handle action triggers when no specific callback is set."""
        if action_id in self._callbacks:
            try:
                self._callbacks[action_id]()
            except Exception as e:
                print(f"Error executing callback for {action_id}: {e}")
        else:
            # Emit signal for external handling
            self.action_triggered.emit(action_id)
    
    def get_standard_menu_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return standard menu structure configuration."""
        return {
            'File': [
                {'type': 'action', 'action_id': 'file_new'},
                {'type': 'action', 'action_id': 'file_open'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'file_save'},
                {'type': 'action', 'action_id': 'file_save_as'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'file_import'},
                {'type': 'action', 'action_id': 'file_export'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'file_reload'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'file_exit'}
            ],
            'Edit': [
                {'type': 'action', 'action_id': 'edit_undo'},
                {'type': 'action', 'action_id': 'edit_redo'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'edit_cut'},
                {'type': 'action', 'action_id': 'edit_copy'},
                {'type': 'action', 'action_id': 'edit_paste'},
                {'type': 'action', 'action_id': 'edit_delete'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'edit_select_all'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'edit_find'}
            ],
            'View': [
                {'type': 'action', 'action_id': 'view_refresh'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'view_zoom_in'},
                {'type': 'action', 'action_id': 'view_zoom_out'},
                {'type': 'action', 'action_id': 'view_reset_zoom'}
            ],
            'Tools': [
                {'type': 'action', 'action_id': 'tools_options'}
            ],
            'Help': [
                {'type': 'action', 'action_id': 'help_help'},
                {'type': 'separator'},
                {'type': 'action', 'action_id': 'help_about'}
            ]
        }
    
    def get_standard_toolbar_structure(self) -> List[Dict[str, Any]]:
        """Return standard toolbar structure configuration."""
        return [
            {'type': 'action', 'action_id': 'file_new'},
            {'type': 'action', 'action_id': 'file_open'},
            {'type': 'action', 'action_id': 'file_save'},
            {'type': 'separator'},
            {'type': 'action', 'action_id': 'edit_cut'},
            {'type': 'action', 'action_id': 'edit_copy'},
            {'type': 'action', 'action_id': 'edit_paste'},
            {'type': 'separator'},
            {'type': 'action', 'action_id': 'edit_find'},
            {'type': 'action', 'action_id': 'view_refresh'}
        ]