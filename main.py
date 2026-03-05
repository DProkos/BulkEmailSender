#!/usr/bin/env python3
"""
Bulk Email Sender - Main Entry Point

A desktop application for sending bulk personalized emails via SMTP.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.theme import apply_dark_theme


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Bulk Email Sender")
    app.setOrganizationName("BulkEmailSender")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Apply dark theme for better visibility with Windows dark mode
    apply_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
