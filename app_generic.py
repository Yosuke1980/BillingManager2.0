#!/usr/bin/env python3
"""
Generic Business Manager Application

This is the main entry point for the generic application framework,
configured for the billing management system.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from core.application import create_application
from plugins.legacy_adapter import (
    PaymentTabPlugin,
    ExpenseTabPlugin, 
    MasterTabPlugin,
    ProjectFilterTabPlugin
)


def main():
    """Main application entry point."""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Create main application window
        main_window = create_application("config/app_config.json")
        
        # Register legacy plugins
        main_window.register_plugin(PaymentTabPlugin)
        main_window.register_plugin(ExpenseTabPlugin)
        main_window.register_plugin(MasterTabPlugin) 
        main_window.register_plugin(ProjectFilterTabPlugin)
        
        # Load plugins
        main_window.load_plugin('PaymentTabPlugin')
        main_window.load_plugin('ExpenseTabPlugin')
        main_window.load_plugin('MasterTabPlugin')
        main_window.load_plugin('ProjectFilterTabPlugin')
        
        # Show main window
        main_window.show()
        
        # Run application
        return app.exec_()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())