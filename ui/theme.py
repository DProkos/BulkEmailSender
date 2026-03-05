"""
Dark theme support for Bulk Email Sender Application.

This module provides dark theme styling that respects Windows dark mode
and ensures all UI elements are readable.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


class DarkTheme:
    """Dark theme color palette and stylesheet."""
    
    # Color definitions
    BACKGROUND = "#2b2b2b"
    BACKGROUND_LIGHT = "#3c3f41"
    BACKGROUND_LIGHTER = "#4e5254"
    FOREGROUND = "#bbbbbb"
    FOREGROUND_BRIGHT = "#ffffff"
    BORDER = "#555555"
    BORDER_LIGHT = "#6b6b6b"
    
    # Input fields
    INPUT_BACKGROUND = "#45494a"
    INPUT_FOREGROUND = "#ffffff"
    INPUT_BORDER = "#6b6b6b"
    INPUT_FOCUS_BORDER = "#4a9eff"
    
    # Buttons
    BUTTON_BACKGROUND = "#4e5254"
    BUTTON_HOVER = "#5a5d5f"
    BUTTON_PRESSED = "#3c3f41"
    BUTTON_DISABLED = "#3c3f41"
    
    # Special buttons
    BUTTON_PRIMARY = "#0d7377"
    BUTTON_PRIMARY_HOVER = "#14a085"
    BUTTON_SUCCESS = "#28a745"
    BUTTON_SUCCESS_HOVER = "#34ce57"
    BUTTON_DANGER = "#dc3545"
    BUTTON_DANGER_HOVER = "#e74c3c"
    
    # Selection
    SELECTION_BACKGROUND = "#214283"
    SELECTION_FOREGROUND = "#ffffff"
    
    # Warnings and info
    WARNING_BACKGROUND = "#5c4d2c"
    WARNING_BORDER = "#8b7355"
    WARNING_TEXT = "#ffcc00"
    
    INFO_BACKGROUND = "#2d4f5c"
    INFO_BORDER = "#4a7c8c"
    INFO_TEXT = "#87ceeb"
    
    ERROR_BACKGROUND = "#5c2d2d"
    ERROR_BORDER = "#8c4a4a"
    ERROR_TEXT = "#ff6b6b"
    
    SUCCESS_BACKGROUND = "#2d5c2d"
    SUCCESS_BORDER = "#4a8c4a"
    SUCCESS_TEXT = "#90ee90"
    
    @staticmethod
    def get_stylesheet() -> str:
        """Get the complete dark theme stylesheet with responsive font sizes."""
        return f"""
        /* Main Window and Widgets - Base font size for responsive scaling */
        QMainWindow, QWidget {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.FOREGROUND};
            font-size: 10pt;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {DarkTheme.BORDER};
            background-color: {DarkTheme.BACKGROUND};
        }}
        
        QTabBar::tab {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
            padding: 8px 16px;
            border: 1px solid {DarkTheme.BORDER};
            border-bottom: none;
            margin-right: 2px;
            font-size: 10pt;
        }}
        
        QTabBar::tab:selected {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            border-bottom: 2px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QTabBar::tab:hover {{
            background-color: {DarkTheme.BACKGROUND_LIGHTER};
        }}
        
        /* Line Edit (Text Input) */
        QLineEdit {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 8px;
            min-height: 24px;
            font-size: 10pt;
            selection-background-color: {DarkTheme.SELECTION_BACKGROUND};
            selection-color: {DarkTheme.SELECTION_FOREGROUND};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QLineEdit:disabled {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.BORDER};
        }}
        
        QLineEdit[readOnly="true"] {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
        }}
        
        /* Text Edit (Multi-line) */
        QTextEdit, QPlainTextEdit {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 8px;
            font-size: 10pt;
            selection-background-color: {DarkTheme.SELECTION_BACKGROUND};
            selection-color: {DarkTheme.SELECTION_FOREGROUND};
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.BORDER};
        }}
        
        QTextEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
        }}
        
        /* Text Browser (Read-only HTML) */
        QTextBrowser {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 8px;
        }}
        
        /* Combo Box (Dropdown) */
        QComboBox {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            min-height: 28px;
            font-size: 10pt;
        }}
        
        QComboBox:focus {{
            border: 2px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {DarkTheme.FOREGROUND};
            margin-right: 6px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            selection-background-color: {DarkTheme.SELECTION_BACKGROUND};
            selection-color: {DarkTheme.SELECTION_FOREGROUND};
        }}
        
        /* List Widget */
        QListWidget {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-radius: 3px;
        }}
        
        QListWidget::item:selected {{
            background-color: {DarkTheme.SELECTION_BACKGROUND};
            color: {DarkTheme.SELECTION_FOREGROUND};
        }}
        
        QListWidget::item:hover {{
            background-color: {DarkTheme.BACKGROUND_LIGHTER};
        }}
        
        /* Table Widget */
        QTableWidget {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            gridline-color: {DarkTheme.BORDER};
            selection-background-color: {DarkTheme.SELECTION_BACKGROUND};
            selection-color: {DarkTheme.SELECTION_FOREGROUND};
            font-size: 10pt;
        }}
        
        QTableWidget::item {{
            padding: 4px;
        }}
        
        QHeaderView::section {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            padding: 6px;
            border: 1px solid {DarkTheme.BORDER};
            font-weight: bold;
            font-size: 10pt;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {DarkTheme.BUTTON_BACKGROUND};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            border: 1px solid {DarkTheme.BORDER_LIGHT};
            border-radius: 4px;
            padding: 8px 16px;
            margin: 4px 2px;
            min-height: 28px;
            font-size: 10pt;
        }}
        
        QPushButton:hover {{
            background-color: {DarkTheme.BUTTON_HOVER};
            border: 1px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkTheme.BUTTON_PRESSED};
        }}
        
        QPushButton:disabled {{
            background-color: {DarkTheme.BUTTON_DISABLED};
            color: {DarkTheme.BORDER};
            border: 1px solid {DarkTheme.BORDER};
        }}
        
        /* Primary Button (e.g., Send) */
        QPushButton[primary="true"] {{
            background-color: {DarkTheme.BUTTON_PRIMARY};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            font-weight: bold;
        }}
        
        QPushButton[primary="true"]:hover {{
            background-color: {DarkTheme.BUTTON_PRIMARY_HOVER};
        }}
        
        /* Success Button (e.g., Start Send) */
        QPushButton[success="true"] {{
            background-color: {DarkTheme.BUTTON_SUCCESS};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            font-weight: bold;
        }}
        
        QPushButton[success="true"]:hover {{
            background-color: {DarkTheme.BUTTON_SUCCESS_HOVER};
        }}
        
        /* Danger Button (e.g., Stop, Delete) */
        QPushButton[danger="true"] {{
            background-color: {DarkTheme.BUTTON_DANGER};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            font-weight: bold;
        }}
        
        QPushButton[danger="true"]:hover {{
            background-color: {DarkTheme.BUTTON_DANGER_HOVER};
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 6px;
            margin-top: 16px;
            margin-bottom: 8px;
            padding: 16px 12px 12px 12px;
            font-weight: bold;
            font-size: 10pt;
            color: {DarkTheme.FOREGROUND_BRIGHT};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 8px;
            margin-top: 4px;
            background-color: {DarkTheme.BACKGROUND};
            border-radius: 3px;
        }}
        
        /* Labels */
        QLabel {{
            color: {DarkTheme.FOREGROUND};
            background-color: transparent;
            padding: 2px 0px;
            font-size: 10pt;
        }}
        
        /* Scroll Bar */
        QScrollBar:vertical {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            width: 14px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {DarkTheme.BORDER_LIGHT};
            border-radius: 7px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            height: 14px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {DarkTheme.BORDER_LIGHT};
            border-radius: 7px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
            text-align: center;
            color: {DarkTheme.FOREGROUND_BRIGHT};
        }}
        
        QProgressBar::chunk {{
            background-color: {DarkTheme.INPUT_FOCUS_BORDER};
            border-radius: 3px;
        }}
        
        /* Check Box */
        QCheckBox {{
            color: {DarkTheme.FOREGROUND};
            spacing: 6px;
            font-size: 10pt;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 3px;
            background-color: {DarkTheme.INPUT_BACKGROUND};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {DarkTheme.INPUT_FOCUS_BORDER};
            border: 1px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        QCheckBox::indicator:hover {{
            border: 1px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        /* Radio Button */
        QRadioButton {{
            color: {DarkTheme.FOREGROUND};
            spacing: 6px;
            font-size: 10pt;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 9px;
            background-color: {DarkTheme.INPUT_BACKGROUND};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {DarkTheme.INPUT_FOCUS_BORDER};
            border: 1px solid {DarkTheme.INPUT_FOCUS_BORDER};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
            border-bottom: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {DarkTheme.BACKGROUND_LIGHTER};
        }}
        
        QMenu {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
            border: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenu::item {{
            padding: 6px 24px;
        }}
        
        QMenu::item:selected {{
            background-color: {DarkTheme.SELECTION_BACKGROUND};
            color: {DarkTheme.SELECTION_FOREGROUND};
        }}
        
        /* Dialog */
        QDialog {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.FOREGROUND};
        }}
        
        /* Scroll Area */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        
        /* Spin Box */
        QSpinBox, QDoubleSpinBox {{
            background-color: {DarkTheme.INPUT_BACKGROUND};
            color: {DarkTheme.INPUT_FOREGROUND};
            border: 1px solid {DarkTheme.INPUT_BORDER};
            border-radius: 4px;
            padding: 4px;
            font-size: 10pt;
            min-height: 24px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {DarkTheme.BACKGROUND_LIGHT};
            color: {DarkTheme.FOREGROUND};
            border-top: 1px solid {DarkTheme.BORDER};
        }}
        
        /* Tool Tip */
        QToolTip {{
            background-color: {DarkTheme.BACKGROUND_LIGHTER};
            color: {DarkTheme.FOREGROUND_BRIGHT};
            border: 1px solid {DarkTheme.BORDER_LIGHT};
            padding: 4px;
            border-radius: 3px;
        }}
        """
    
    @staticmethod
    def apply_theme(app: QApplication):
        """
        Apply dark theme to the application.
        
        Args:
            app: QApplication instance
        """
        # Set stylesheet
        app.setStyle("Fusion")
        app.setStyleSheet(DarkTheme.get_stylesheet())
        
        # Set palette for native widgets
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(DarkTheme.BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DarkTheme.FOREGROUND))
        
        # Base colors (for input fields)
        palette.setColor(QPalette.ColorRole.Base, QColor(DarkTheme.INPUT_BACKGROUND))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DarkTheme.BACKGROUND_LIGHT))
        palette.setColor(QPalette.ColorRole.Text, QColor(DarkTheme.INPUT_FOREGROUND))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(DarkTheme.BUTTON_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DarkTheme.FOREGROUND_BRIGHT))
        
        # Highlight colors (selection)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(DarkTheme.SELECTION_BACKGROUND))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(DarkTheme.SELECTION_FOREGROUND))
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(DarkTheme.BORDER))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(DarkTheme.BORDER))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(DarkTheme.BORDER))
        
        app.setPalette(palette)


def apply_dark_theme(app: QApplication):
    """
    Convenience function to apply dark theme.
    
    Args:
        app: QApplication instance
    """
    DarkTheme.apply_theme(app)
