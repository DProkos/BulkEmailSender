"""
Main Window for Bulk Email Sender Application

This module implements the main application window with a tabbed interface
for SMTP settings, recipients, template, and send operations.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import QSettings, QSize, QPoint
from PyQt6.QtGui import QAction, QCloseEvent
from typing import Optional

from storage.config_manager import ConfigManager
from storage.credential_store import CredentialStore
from storage.database import Database
from ui.smtp_tab import SMTPTab
from ui.recipients_tab import RecipientsTab
from ui.template_tab import TemplateTab
from ui.send_tab import SendTab
from ui.company_settings_tab import CompanySettingsTab


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    
    Provides:
    - Tabbed interface with 4 tabs: SMTP Settings, Recipients, Template, Send
    - Menu bar with File and Help menus
    - Window state persistence (size, position)
    
    Validates Requirements: 7.1, 7.6
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.settings = QSettings("BulkEmailSender", "BulkEmailSender")
        
        # Initialize storage managers
        self.config_manager = ConfigManager()
        self.credential_store = CredentialStore()
        
        # Initialize database with default path
        from pathlib import Path
        db_dir = Path.home() / ".bulk_email_sender"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "data.db"
        self.database = Database(str(db_path))
        
        self.init_ui()
        self.restore_window_state()
        
        # Check for incomplete jobs on startup (crash recovery)
        self.check_incomplete_jobs()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Bulk Email Sender")
        self.setMinimumSize(900, 700)
        
        # Set window icon
        import os
        from PyQt6.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Create tabs
        self.smtp_tab = SMTPTab(self.config_manager, self.credential_store)
        self.recipients_tab = RecipientsTab(self.database)
        self.company_settings_tab = CompanySettingsTab(self.config_manager)
        self.template_tab = TemplateTab(self.config_manager)
        self.send_tab = SendTab(self.database)
        
        # Connect recipients tab to template tab
        # When recipients are loaded, update template tab with available fields
        self.recipients_tab.recipients_loaded.connect(self.update_template_fields)
        
        # Connect company settings to template tab
        self.company_settings_tab.settings_saved.connect(self.update_template_company_settings)
        
        # Connect tabs to send tab
        # When configuration changes, update send tab
        self.smtp_tab.config_saved.connect(self.update_send_tab_config)
        self.recipients_tab.recipients_loaded.connect(self.update_send_tab_recipients)
        self.recipients_tab.selection_changed.connect(self.update_send_tab_recipients)
        self.template_tab.template_saved.connect(self.update_send_tab_template)
        self.template_tab.set_recipients(self.recipients_tab.get_recipients())  # Initial sync
        
        # Load initial company settings into template tab
        company_settings = self.company_settings_tab.get_settings()
        if company_settings:
            self.template_tab.set_company_settings(company_settings)
        
        # Load initial SMTP config into send tab (if already saved)
        smtp_config = self.smtp_tab.get_smtp_config()
        if smtp_config:
            self.send_tab.set_smtp_config(smtp_config)
        
        # Load initial recipients into send tab (if already loaded from database)
        if self.recipients_tab.has_recipients():
            recipients = self.recipients_tab.get_selected_recipients()
            self.send_tab.set_recipients(recipients)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.smtp_tab, "SMTP Settings")
        self.tab_widget.addTab(self.recipients_tab, "Recipients")
        self.tab_widget.addTab(self.company_settings_tab, "Company Settings")
        self.tab_widget.addTab(self.template_tab, "Template")
        self.tab_widget.addTab(self.send_tab, "Send")
        
        # Set tab widget as central widget
        self.setCentralWidget(self.tab_widget)
    
    def create_placeholder_tab(self, name: str) -> QWidget:
        """
        Create a placeholder tab widget.
        
        Args:
            name: Name of the tab
            
        Returns:
            QWidget with placeholder content
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_menu_bar(self):
        """Create the menu bar with File and Help menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Opt-out list action
        optout_action = QAction("&Opt-Out List", self)
        optout_action.setStatusTip("Manage opt-out list")
        optout_action.triggered.connect(self.show_optout_dialog)
        tools_menu.addAction(optout_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # User Guide action
        guide_action = QAction("📖 &Οδηγίες Χρήσης", self)
        guide_action.setShortcut("F1")
        guide_action.setStatusTip("Άνοιγμα οδηγιών χρήσης")
        guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(guide_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&Σχετικά...", self)
        about_action.setStatusTip("Σχετικά με το Bulk Email Sender")
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def show_about_dialog(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "Σχετικά με το Bulk Email Sender",
            "<h3>Bulk Email Sender v1.0.0</h3>"
            "<p><b>Developed by:</b> Dionisis Prokos</p>"
            "<hr>"
            "<p><b>Τι είναι:</b><br>"
            "Εφαρμογή για μαζική αποστολή εξατομικευμένων emails μέσω SMTP.</p>"
            "<p><b>Που χρησιμεύει:</b><br>"
            "• Μαζική αποστολή newsletters<br>"
            "• Ενημερωτικά emails σε πελάτες<br>"
            "• Προωθητικές καμπάνιες<br>"
            "• Εταιρική επικοινωνία</p>"
            "<p><b>Χαρακτηριστικά:</b></p>"
            "<ul>"
            "<li>Ασφαλής αποθήκευση κωδικών στο OS keyring</li>"
            "<li>Εισαγωγή παραληπτών από Excel</li>"
            "<li>Επεξεργαστής templates με μεταβλητές</li>"
            "<li>Έλεγχος ρυθμού αποστολής (throttling)</li>"
            "<li>Ανάκτηση από crash και αυτόματη επανάληψη</li>"
            "<li>Λίστα opt-out για συμμόρφωση</li>"
            "</ul>"
            "<p><b>Τεχνολογίες:</b> PyQt6, pandas, Jinja2, SQLite</p>"
            "<p>&copy; 2025 Dionisis Prokos</p>"
        )
    
    def show_user_guide(self):
        """Show the user guide in a dialog."""
        import os
        guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'ΟΔΗΓΙΕΣ_ΧΡΗΣΗΣ.md')
        
        try:
            with open(guide_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple markdown to HTML conversion
            import re
            html = content
            html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
            html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
            html = re.sub(r'^- (.+)$', r'• \1<br>', html, flags=re.MULTILINE)
            html = re.sub(r'^(\d+)\. (.+)$', r'\1. \2<br>', html, flags=re.MULTILINE)
            html = html.replace('\n\n', '<br><br>')
            html = html.replace('---', '<hr>')
            
            from ui.dialogs import UserGuideDialog
            dialog = UserGuideDialog(html, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Σφάλμα",
                f"Δεν ήταν δυνατή η φόρτωση των οδηγιών:\n{str(e)}"
            )
    
    def show_optout_dialog(self):
        """Show the Opt-Out List Management dialog."""
        from ui.dialogs import OptOutListDialog
        dialog = OptOutListDialog(self.database, self)
        dialog.exec()
    
    def update_template_fields(self):
        """Update template tab with available fields from recipients."""
        if self.recipients_tab.has_recipients():
            recipients = self.recipients_tab.get_recipients()
            self.template_tab.set_recipients(recipients)
    
    def update_template_company_settings(self):
        """Update template tab with company settings."""
        company_settings = self.company_settings_tab.get_settings()
        if company_settings:
            self.template_tab.set_company_settings(company_settings)
    
    def update_send_tab_config(self):
        """Update send tab with SMTP configuration."""
        smtp_config = self.smtp_tab.get_smtp_config()
        if smtp_config:
            self.send_tab.set_smtp_config(smtp_config)
    
    def update_send_tab_template(self):
        """Update send tab with template."""
        if self.template_tab.has_template():
            template = self.template_tab.get_template()
            if template:
                self.send_tab.set_template(template)
    
    def update_send_tab_recipients(self):
        """Update send tab with recipients and template."""
        if self.recipients_tab.has_recipients():
            # Get only selected recipients for sending
            recipients = self.recipients_tab.get_selected_recipients()
            self.send_tab.set_recipients(recipients)
        
        if self.template_tab.has_template():
            template = self.template_tab.get_template()
            if template:
                self.send_tab.set_template(template)
    
    def restore_window_state(self):
        """
        Restore window size and position from saved settings.
        
        Validates Requirement: 7.6 (window state persistence)
        """
        # Restore window size
        size = self.settings.value("window/size", QSize(1024, 768))
        if isinstance(size, QSize):
            self.resize(size)
        
        # Restore window position
        pos = self.settings.value("window/position")
        if isinstance(pos, QPoint):
            self.move(pos)
    
    def save_window_state(self):
        """
        Save window size and position to settings.
        
        Validates Requirement: 7.6 (window state persistence)
        """
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
    
    def closeEvent(self, event: QCloseEvent):
        """
        Handle window close event.
        
        Saves window state before closing.
        
        Args:
            event: Close event
        """
        self.save_window_state()
        event.accept()

    def check_incomplete_jobs(self):
        """
        Check for incomplete jobs on startup and offer to resume.
        
        This method implements crash recovery by:
        1. Detecting incomplete jobs in the database
        2. Showing a dialog offering to resume
        3. Loading queue state and resuming from last checkpoint
        
        Validates Requirement: 8.3 (crash recovery)
        """
        from PyQt6.QtCore import QTimer
        
        # Delay the check slightly to allow UI to fully initialize
        QTimer.singleShot(500, self._do_check_incomplete_jobs)
    
    def _do_check_incomplete_jobs(self):
        """Perform the actual incomplete jobs check."""
        try:
            # Get incomplete jobs from database
            incomplete_jobs = self.database.get_incomplete_jobs()
            
            if not incomplete_jobs:
                # No incomplete jobs, nothing to do
                return
            
            # Show recovery dialog
            from ui.dialogs import JobRecoveryDialog
            dialog = JobRecoveryDialog(incomplete_jobs, self.database, self)
            
            if dialog.exec() == JobRecoveryDialog.DialogCode.Accepted:
                # User chose to resume a job
                if dialog.action == 'resume' and dialog.selected_job_id:
                    self._resume_job(dialog.selected_job_id)
        
        except Exception as e:
            # Log error but don't crash the application
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error checking incomplete jobs: {e}", exc_info=True)
    
    def _resume_job(self, job_id: str):
        """
        Resume an incomplete job.
        
        Loads the job state from database and sets up the send tab
        to resume sending.
        
        Args:
            job_id: ID of the job to resume
        """
        try:
            # Load job from database
            job = self.database.load_queue_state(job_id)
            
            if not job:
                from ui.dialogs import ErrorDialog
                ErrorDialog(
                    "Job Not Found",
                    f"Could not load job {job_id} from database.",
                    parent=self
                ).exec()
                return
            
            # Set up the tabs with job data
            # Note: We need to restore SMTP config, recipients, and template
            
            # 1. Restore SMTP config to SMTP tab
            self.smtp_tab.set_smtp_config(job.smtp_config)
            
            # 2. Restore recipients to recipients tab
            # Filter to only show recipients (not their status)
            self.recipients_tab.set_recipients(job.recipients)
            
            # 3. Restore template to template tab
            self.template_tab.set_template(job.template)
            
            # 4. Set up send tab with the job
            self.send_tab.set_smtp_config(job.smtp_config)
            self.send_tab.set_recipients(job.recipients)
            self.send_tab.set_template(job.template)
            
            # 5. Load the job into send tab for resuming
            self.send_tab.load_job_for_resume(job)
            
            # 6. Switch to send tab
            self.tab_widget.setCurrentWidget(self.send_tab)
            
            # 7. Show info message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Job Loaded",
                f"Job loaded successfully!\n\n"
                f"Sent: {sum(1 for r in job.recipients if r.status == 'SENT')}\n"
                f"Pending: {sum(1 for r in job.recipients if r.status == 'PENDING')}\n"
                f"Failed: {sum(1 for r in job.recipients if r.status == 'FAILED')}\n\n"
                f"Click 'Start Send' to resume from where you left off."
            )
        
        except Exception as e:
            from ui.dialogs import ErrorDialog
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error resuming job {job_id}: {e}", exc_info=True)
            
            ErrorDialog(
                "Error Resuming Job",
                "Failed to resume the job.",
                str(e),
                parent=self
            ).exec()
