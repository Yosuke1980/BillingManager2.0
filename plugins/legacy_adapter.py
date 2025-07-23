"""
Legacy Tab Adapter Plugin

This module provides adapters to integrate existing tab classes
with the new plugin system, allowing for gradual migration.
"""

from PyQt5.QtWidgets import QWidget
from core.tab_manager import BaseTabPlugin
from typing import Optional, Dict, Any


class LegacyTabAdapter(BaseTabPlugin):
    """
    Adapter to wrap existing tab classes as plugins.
    
    This allows existing tabs to work with the new plugin system
    without requiring immediate refactoring.
    """
    
    def __init__(self, legacy_tab_class, display_name: str, description: str, 
                 parent=None, app_context=None):
        super().__init__(parent, app_context)
        
        self._legacy_tab_class = legacy_tab_class
        self._display_name = display_name
        self._description = description
        self._legacy_instance = None
        
    def get_display_name(self) -> str:
        return self._display_name
    
    def get_description(self) -> str:
        return self._description
    
    def initialize(self) -> bool:
        """Initialize the legacy tab."""
        try:
            # Create instance of legacy tab
            if self.app_context and 'main_window' in self.app_context:
                # Pass the main window if the legacy tab expects it
                main_window = self.app_context['main_window']
                self._legacy_instance = self._legacy_tab_class(self, main_window)
            else:
                self._legacy_instance = self._legacy_tab_class(self)
            
            # Copy the legacy tab's UI to this widget
            if hasattr(self._legacy_instance, 'layout'):
                # If legacy tab has a layout, set it
                layout = self._legacy_instance.layout()
                if layout:
                    self.setLayout(layout)
            else:
                # If no layout, try to move all child widgets
                for child in self._legacy_instance.findChildren(QWidget):
                    if child.parent() == self._legacy_instance:
                        child.setParent(self)
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize legacy tab {self._display_name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup legacy tab resources."""
        if self._legacy_instance and hasattr(self._legacy_instance, 'cleanup'):
            self._legacy_instance.cleanup()
    
    # Delegate plugin capabilities to legacy instance
    def can_export(self) -> bool:
        if self._legacy_instance:
            return hasattr(self._legacy_instance, 'export_csv')
        return False
    
    def can_create(self) -> bool:
        if self._legacy_instance:
            return hasattr(self._legacy_instance, 'create_new_entry')
        return False
    
    def can_delete(self) -> bool:
        if self._legacy_instance:
            return hasattr(self._legacy_instance, 'delete_selected')
        return False
    
    def can_search(self) -> bool:
        if self._legacy_instance:
            return hasattr(self._legacy_instance, 'show_search')
        return False
    
    # Delegate actions to legacy instance
    def export_data(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'export_csv'):
            try:
                self._legacy_instance.export_csv()
                return True
            except Exception as e:
                print(f"Export failed: {e}")
        return False
    
    def create_new_entry(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'create_new_entry'):
            try:
                self._legacy_instance.create_new_entry()
                return True
            except Exception as e:
                print(f"Create new entry failed: {e}")
        return False
    
    def delete_selected(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'delete_selected'):
            try:
                self._legacy_instance.delete_selected()
                return True
            except Exception as e:
                print(f"Delete selected failed: {e}")
        return False
    
    def search_data(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'show_search'):
            try:
                self._legacy_instance.show_search()
                return True
            except Exception as e:
                print(f"Search failed: {e}")
        return False
    
    def refresh_data(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'refresh_data'):
            try:
                self._legacy_instance.refresh_data()
                return True
            except Exception as e:
                print(f"Refresh failed: {e}")
        return False
    
    def reset_filters(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'reset_filters'):
            try:
                self._legacy_instance.reset_filters()
                return True
            except Exception as e:
                print(f"Reset filters failed: {e}")
        return False
    
    def toggle_filter_panel(self, visible: bool) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'toggle_filter_panel'):
            try:
                self._legacy_instance.toggle_filter_panel(visible)
                return True
            except Exception as e:
                print(f"Toggle filter panel failed: {e}")
        return False
    
    def run_matching(self) -> bool:
        if self._legacy_instance and hasattr(self._legacy_instance, 'run_matching'):
            try:
                self._legacy_instance.run_matching()
                return True
            except Exception as e:
                print(f"Run matching failed: {e}")
        return False


# Specific adapter classes for existing tabs
class PaymentTabPlugin(LegacyTabAdapter):
    def __init__(self, parent=None, app_context=None):
        # Import here to avoid circular imports
        from payment_tab import PaymentTab
        super().__init__(
            PaymentTab,
            "支払い情報 (閲覧専用)",
            "支払いデータの閲覧と検索",
            parent,
            app_context
        )


class ExpenseTabPlugin(LegacyTabAdapter):
    def __init__(self, parent=None, app_context=None):
        from expense_tab import ExpenseTab
        super().__init__(
            ExpenseTab,
            "費用管理",
            "費用データの管理と照合",
            parent,
            app_context
        )


class MasterTabPlugin(LegacyTabAdapter):
    def __init__(self, parent=None, app_context=None):
        from master_tab import MasterTab
        super().__init__(
            MasterTab,
            "費用マスター",
            "費用マスターデータの管理",
            parent,
            app_context
        )
    
    def generate_master_data(self) -> bool:
        """Special method for master data generation."""
        if self._legacy_instance and hasattr(self._legacy_instance, 'generate_master_data'):
            try:
                self._legacy_instance.generate_master_data()
                return True
            except Exception as e:
                print(f"Generate master data failed: {e}")
        return False


class ProjectFilterTabPlugin(LegacyTabAdapter):
    def __init__(self, parent=None, app_context=None):
        from project_filter_tab import ProjectFilterTab
        super().__init__(
            ProjectFilterTab,
            "案件絞込み・管理",
            "案件の絞込みと管理",
            parent,
            app_context
        )