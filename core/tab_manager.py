"""
Generic Tab Plugin System for PyQt5 Applications

This module provides a plugin-based architecture for tab management,
allowing for dynamic loading and unloading of tab functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from PyQt5.QtWidgets import QWidget, QTabWidget, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QAbstractItemModel
import importlib
import importlib.util
import inspect
import os


class BaseTabPluginMeta(type(QWidget), type(ABC)):
    """Metaclass to resolve metaclass conflict between QWidget and ABC."""
    pass


class BaseTabPlugin(QWidget, ABC, metaclass=BaseTabPluginMeta):
    """
    Abstract base class for tab plugins.
    
    All tab implementations should inherit from this class and implement
    the required abstract methods.
    """
    
    # Signals for plugin communication
    data_changed = pyqtSignal(str, object)  # plugin_id, data
    status_changed = pyqtSignal(str, str)   # plugin_id, status_message
    action_requested = pyqtSignal(str, str) # plugin_id, action_name
    
    def __init__(self, parent=None, app_context=None):
        super().__init__(parent)
        self._app_context = app_context
        self._plugin_id = self.__class__.__name__
        self._is_initialized = False
        
    @property
    def plugin_id(self) -> str:
        """Get unique plugin identifier."""
        return self._plugin_id
    
    @property
    def app_context(self):
        """Get application context."""
        return self._app_context
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Return the display name for this tab."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return description of this tab's functionality."""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the tab plugin.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources when tab is being destroyed."""
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        Return list of required plugin dependencies.
        
        Returns:
            List[str]: List of plugin IDs this plugin depends on
        """
        return []
    
    def get_version(self) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    def get_author(self) -> str:
        """Return plugin author."""
        return "Unknown"
    
    # Standard action methods that plugins can override
    def export_data(self) -> bool:
        """Export data functionality. Override if supported."""
        return False
    
    def import_data(self) -> bool:
        """Import data functionality. Override if supported."""
        return False
    
    def create_new_entry(self) -> bool:
        """Create new entry functionality. Override if supported."""
        return False
    
    def delete_selected(self) -> bool:
        """Delete selected functionality. Override if supported."""
        return False
    
    def search_data(self) -> bool:
        """Search functionality. Override if supported."""
        return False
    
    def refresh_data(self) -> bool:
        """Refresh data functionality. Override if supported."""
        return False
    
    def reset_filters(self) -> bool:
        """Reset filters functionality. Override if supported."""
        return False
    
    def can_export(self) -> bool:
        """Check if plugin supports export."""
        return False
    
    def can_import(self) -> bool:
        """Check if plugin supports import."""
        return False
    
    def can_create(self) -> bool:
        """Check if plugin supports creating new entries."""
        return False
    
    def can_delete(self) -> bool:
        """Check if plugin supports deletion."""
        return False
    
    def can_search(self) -> bool:
        """Check if plugin supports search."""
        return False
    
    def get_supported_actions(self) -> List[str]:
        """Return list of supported actions."""
        actions = []
        if self.can_export():
            actions.append('export')
        if self.can_import():
            actions.append('import')
        if self.can_create():
            actions.append('create')
        if self.can_delete():
            actions.append('delete')
        if self.can_search():
            actions.append('search')
        return actions


class TabManager(QObject):
    """
    Manager for tab plugins.
    
    Features:
    - Dynamic plugin loading and unloading
    - Dependency resolution
    - Plugin lifecycle management
    - Configuration-driven tab registration
    """
    
    tab_loaded = pyqtSignal(str)    # plugin_id
    tab_unloaded = pyqtSignal(str)  # plugin_id
    tab_error = pyqtSignal(str, str) # plugin_id, error_message
    
    def __init__(self, tab_widget: QTabWidget, parent=None):
        super().__init__(parent)
        self._tab_widget = tab_widget
        self._plugins: Dict[str, BaseTabPlugin] = {}
        self._plugin_classes: Dict[str, Type[BaseTabPlugin]] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._load_order: List[str] = []
        self._app_context = None
        
    def set_app_context(self, context):
        """Set application context for plugins."""
        self._app_context = context
        
    def register_plugin_class(self, plugin_class: Type[BaseTabPlugin], config: Optional[Dict[str, Any]] = None) -> None:
        """Register a plugin class."""
        plugin_id = plugin_class.__name__
        self._plugin_classes[plugin_id] = plugin_class
        self._plugin_configs[plugin_id] = config or {}
        
    def load_plugin(self, plugin_id: str) -> bool:
        """Load and initialize a plugin."""
        if plugin_id in self._plugins:
            return True  # Already loaded
            
        if plugin_id not in self._plugin_classes:
            self.tab_error.emit(plugin_id, f"Plugin class not found: {plugin_id}")
            return False
            
        try:
            # Check dependencies
            plugin_class = self._plugin_classes[plugin_id]
            temp_instance = plugin_class()
            dependencies = temp_instance.get_dependencies()
            
            # Load dependencies first
            for dep_id in dependencies:
                if not self.load_plugin(dep_id):
                    self.tab_error.emit(plugin_id, f"Failed to load dependency: {dep_id}")
                    return False
            
            # Create plugin instance
            plugin = plugin_class(self._tab_widget, self._app_context)
            
            # Initialize plugin
            if not plugin.initialize():
                self.tab_error.emit(plugin_id, f"Plugin initialization failed: {plugin_id}")
                return False
            
            # Add to tab widget
            tab_index = self._tab_widget.addTab(plugin, plugin.get_display_name())
            self._tab_widget.setTabToolTip(tab_index, plugin.get_description())
            
            # Register plugin
            self._plugins[plugin_id] = plugin
            self._load_order.append(plugin_id)
            
            # Connect signals
            plugin.data_changed.connect(lambda pid, data: self._on_plugin_data_changed(pid, data))
            plugin.status_changed.connect(lambda pid, status: self._on_plugin_status_changed(pid, status))
            plugin.action_requested.connect(lambda pid, action: self._on_plugin_action_requested(pid, action))
            
            self.tab_loaded.emit(plugin_id)
            return True
            
        except Exception as e:
            self.tab_error.emit(plugin_id, f"Error loading plugin {plugin_id}: {str(e)}")
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        if plugin_id not in self._plugins:
            return True  # Not loaded
            
        try:
            plugin = self._plugins[plugin_id]
            
            # Remove from tab widget
            for i in range(self._tab_widget.count()):
                if self._tab_widget.widget(i) == plugin:
                    self._tab_widget.removeTab(i)
                    break
            
            # Cleanup plugin
            plugin.cleanup()
            
            # Remove from registry
            del self._plugins[plugin_id]
            if plugin_id in self._load_order:
                self._load_order.remove(plugin_id)
            
            self.tab_unloaded.emit(plugin_id)
            return True
            
        except Exception as e:
            self.tab_error.emit(plugin_id, f"Error unloading plugin {plugin_id}: {str(e)}")
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[BaseTabPlugin]:
        """Get plugin instance by ID."""
        return self._plugins.get(plugin_id)
    
    def get_current_plugin(self) -> Optional[BaseTabPlugin]:
        """Get currently active plugin."""
        current_widget = self._tab_widget.currentWidget()
        if current_widget and isinstance(current_widget, BaseTabPlugin):
            return current_widget
        return None
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin IDs."""
        return list(self._plugins.keys())
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin."""
        if self.unload_plugin(plugin_id):
            return self.load_plugin(plugin_id)
        return False
    
    def load_plugins_from_config(self, config: Dict[str, Any]) -> None:
        """Load plugins based on configuration."""
        plugins_config = config.get('plugins', [])
        
        for plugin_config in plugins_config:
            plugin_id = plugin_config.get('id')
            enabled = plugin_config.get('enabled', True)
            
            if enabled and plugin_id:
                self.load_plugin(plugin_id)
    
    def discover_plugins_in_directory(self, directory: str) -> None:
        """Discover and register plugins in a directory."""
        if not os.path.exists(directory):
            return
            
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Import module
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        os.path.join(directory, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseTabPlugin) and 
                            obj != BaseTabPlugin):
                            self.register_plugin_class(obj)
                            
                except Exception as e:
                    print(f"Error discovering plugin in {filename}: {e}")
    
    def execute_action_on_current_plugin(self, action: str) -> bool:
        """Execute action on currently active plugin."""
        plugin = self.get_current_plugin()
        if not plugin:
            return False
            
        try:
            if action == 'export' and plugin.can_export():
                return plugin.export_data()
            elif action == 'import' and plugin.can_import():
                return plugin.import_data()
            elif action == 'create' and plugin.can_create():
                return plugin.create_new_entry()
            elif action == 'delete' and plugin.can_delete():
                return plugin.delete_selected()
            elif action == 'search' and plugin.can_search():
                return plugin.search_data()
            elif action == 'refresh':
                return plugin.refresh_data()
            elif action == 'reset':
                return plugin.reset_filters()
            else:
                return False
        except Exception as e:
            print(f"Error executing action {action} on plugin {plugin.plugin_id}: {e}")
            return False
    
    def get_current_plugin_capabilities(self) -> List[str]:
        """Get capabilities of current plugin."""
        plugin = self.get_current_plugin()
        if plugin:
            return plugin.get_supported_actions()
        return []
    
    def _on_plugin_data_changed(self, plugin_id: str, data: Any) -> None:
        """Handle plugin data change event."""
        # Can be used for inter-plugin communication
        pass
    
    def _on_plugin_status_changed(self, plugin_id: str, status: str) -> None:
        """Handle plugin status change event."""
        # Can be used to update status bar
        pass
    
    def _on_plugin_action_requested(self, plugin_id: str, action: str) -> None:
        """Handle plugin action request."""
        # Can be used for cross-plugin actions
        pass