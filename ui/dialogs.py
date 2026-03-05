"""
Reusable dialog components for the Bulk Email Sender application.

This module provides standardized dialogs for:
- Email preview
- Error messages
- Confirmation prompts
- Progress tracking for long-running operations

Requirements: 7.3, 7.5
"""

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QLabel, QTextBrowser, QProgressBar, QPushButton,
    QWidget, QLineEdit, QFormLayout, QScrollArea, QComboBox,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from typing import List, Optional, Dict


class PreviewDialog(QDialog):
    """
    Dialog for previewing rendered email content.
    
    Displays HTML-rendered email with proper formatting.
    Used for template preview before sending.
    
    Requirements: 7.3 - Clear error messages and feedback
    """
    
    def __init__(self, preview_html: str, parent=None):
        """
        Initialize the preview dialog.
        
        Args:
            preview_html: HTML content to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Email Preview")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # HTML preview browser
        browser = QTextBrowser()
        browser.setHtml(preview_html)
        browser.setOpenExternalLinks(False)
        layout.addWidget(browser)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)


class ErrorDialog(QDialog):
    """
    Standardized error dialog with detailed error information.
    
    Provides consistent error presentation with:
    - Clear error title
    - Detailed error message
    - Optional technical details (expandable)
    
    Requirements: 7.3 - Clear error messages near relevant fields
    """
    
    def __init__(self, title: str, message: str, details: str = None, parent=None):
        """
        Initialize the error dialog.
        
        Args:
            title: Error dialog title
            message: Main error message (user-friendly)
            details: Optional technical details (for debugging)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Error icon and message
        message_layout = QHBoxLayout()
        
        # Error icon (using standard icon)
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(
                self.style().StandardPixmap.SP_MessageBoxCritical
            ).pixmap(48, 48)
        )
        message_layout.addWidget(icon_label)
        
        # Error message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_layout.addWidget(message_label, 1)
        
        layout.addLayout(message_layout)
        
        # Technical details (if provided)
        if details:
            details_label = QLabel("<b>Technical Details:</b>")
            layout.addWidget(details_label)
            
            details_browser = QTextBrowser()
            details_browser.setPlainText(details)
            details_browser.setMaximumHeight(150)
            layout.addWidget(details_browser)
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class ConfirmationDialog(QDialog):
    """
    Confirmation dialog for dangerous or irreversible operations.
    
    Provides clear warning and requires explicit user confirmation.
    Used for operations like:
    - Starting bulk send
    - Stopping send (cancelling remaining emails)
    - Deleting data
    
    Requirements: 7.3 - Clear feedback for user actions
    """
    
    def __init__(self, title: str, message: str, warning: str = None, 
                 confirm_text: str = "Confirm", cancel_text: str = "Cancel",
                 parent=None):
        """
        Initialize the confirmation dialog.
        
        Args:
            title: Dialog title
            message: Main confirmation message
            warning: Optional warning text (displayed prominently)
            confirm_text: Text for confirm button (default: "Confirm")
            cancel_text: Text for cancel button (default: "Cancel")
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Warning icon and message
        message_layout = QHBoxLayout()
        
        # Warning icon
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(
                self.style().StandardPixmap.SP_MessageBoxWarning
            ).pixmap(48, 48)
        )
        message_layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_layout.addWidget(message_label, 1)
        
        layout.addLayout(message_layout)
        
        # Warning text (if provided)
        if warning:
            warning_label = QLabel(f"<b>⚠ Warning:</b> {warning}")
            warning_label.setWordWrap(True)
            warning_label.setStyleSheet("color: #d32f2f; padding: 10px;")
            layout.addWidget(warning_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        confirm_button = button_box.addButton(
            confirm_text, 
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        cancel_button = button_box.addButton(
            cancel_text,
            QDialogButtonBox.ButtonRole.RejectRole
        )
        
        # Make confirm button prominent
        confirm_button.setDefault(False)
        cancel_button.setDefault(True)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)


class ProgressDialog(QDialog):
    """
    Progress dialog for long-running operations.
    
    Displays:
    - Operation description
    - Progress bar (determinate or indeterminate)
    - Status message
    - Optional cancel button
    
    Requirements: 7.5 - Progress indicator for long-running operations
    """
    
    # Signal emitted when user cancels the operation
    cancelled = pyqtSignal()
    
    def __init__(self, title: str, message: str, cancellable: bool = True,
                 parent=None):
        """
        Initialize the progress dialog.
        
        Args:
            title: Dialog title
            message: Operation description
            cancellable: Whether user can cancel the operation
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Prevent closing with X button if not cancellable
        if not cancellable:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
            )
        
        layout = QVBoxLayout(self)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate by default
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.status_label)
        
        # Cancel button (if cancellable)
        if cancellable:
            button_box = QDialogButtonBox()
            cancel_button = button_box.addButton(
                "Cancel",
                QDialogButtonBox.ButtonRole.RejectRole
            )
            button_box.rejected.connect(self._on_cancel)
            layout.addWidget(button_box)
            
            self.cancel_button = cancel_button
        else:
            self.cancel_button = None
    
    def set_progress(self, value: int, maximum: int = 100):
        """
        Set progress value (makes progress bar determinate).
        
        Args:
            value: Current progress value
            maximum: Maximum progress value
        """
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def set_indeterminate(self):
        """Set progress bar to indeterminate mode."""
        self.progress_bar.setMaximum(0)
    
    def set_status(self, status: str):
        """
        Update status message.
        
        Args:
            status: Status text to display
        """
        self.status_label.setText(status)
    
    def set_message(self, message: str):
        """
        Update main message.
        
        Args:
            message: Message text to display
        """
        self.message_label.setText(message)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        if self.cancel_button:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
        
        self.cancelled.emit()
    
    def closeEvent(self, event):
        """
        Handle dialog close event.
        
        Only allow closing if cancellable.
        """
        if self.cancel_button and self.cancel_button.isEnabled():
            self._on_cancel()
            event.ignore()
        elif not self.cancel_button:
            event.ignore()
        else:
            event.accept()



class JobRecoveryDialog(QDialog):
    """
    Dialog for recovering incomplete send jobs after crash.
    
    Displays incomplete jobs and allows user to:
    - Resume a job from where it left off
    - Cancel/discard incomplete jobs
    - View job details (sent, failed, pending counts)
    
    Requirements: 8.3 - Crash recovery
    """
    
    def __init__(self, incomplete_jobs: list, database, parent=None):
        """
        Initialize the job recovery dialog.
        
        Args:
            incomplete_jobs: List of incomplete job dictionaries
            database: Database instance for loading job state
            parent: Parent widget
        """
        super().__init__(parent)
        self.incomplete_jobs = incomplete_jobs
        self.database = database
        self.selected_job_id = None
        self.action = None  # 'resume' or 'cancel'
        
        self.setWindowTitle("Recover Incomplete Jobs")
        self.setModal(True)
        self.resize(700, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        from PyQt6.QtWidgets import (
            QTableWidget, QTableWidgetItem, QHeaderView
        )
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "<b>Incomplete send jobs detected!</b><br><br>"
            "The application found send jobs that were not completed. "
            "This may have happened due to an application crash or unexpected shutdown.<br><br>"
            "You can resume these jobs from where they left off, or cancel them."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Jobs table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Created At", "Status", "Sent", "Failed", "Pending", "Total"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Populate table
        self.table.setRowCount(len(self.incomplete_jobs))
        for row, job in enumerate(self.incomplete_jobs):
            # Store job_id in row data
            self.table.setItem(row, 0, QTableWidgetItem(job['id']))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, job['id'])
            
            # Format created_at
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(job['created_at'])
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = job['created_at']
            
            self.table.item(row, 0).setText(formatted_date)
            self.table.setItem(row, 1, QTableWidgetItem(job['status']))
            self.table.setItem(row, 2, QTableWidgetItem(str(job['sent'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(job['failed'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(job['pending'])))
            self.table.setItem(row, 5, QTableWidgetItem(str(job['total'])))
        
        # Select first row by default
        if self.incomplete_jobs:
            self.table.selectRow(0)
        
        layout.addWidget(self.table)
        
        # Info label
        info_label = QLabel(
            "<i>Select a job and choose an action below.</i>"
        )
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.resume_button = QPushButton("Resume Selected Job")
        self.resume_button.clicked.connect(self.resume_job)
        self.resume_button.setEnabled(len(self.incomplete_jobs) > 0)
        
        self.cancel_button = QPushButton("Cancel Selected Job")
        self.cancel_button.clicked.connect(self.cancel_job)
        self.cancel_button.setEnabled(len(self.incomplete_jobs) > 0)
        
        self.skip_button = QPushButton("Skip (Decide Later)")
        self.skip_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.skip_button)
        
        layout.addLayout(button_layout)
    
    def resume_job(self):
        """Resume the selected job."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            ErrorDialog(
                "No Job Selected",
                "Please select a job to resume.",
                parent=self
            ).exec()
            return
        
        row = selected_rows[0].row()
        self.selected_job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.action = 'resume'
        self.accept()
    
    def cancel_job(self):
        """Cancel the selected job."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            ErrorDialog(
                "No Job Selected",
                "Please select a job to cancel.",
                parent=self
            ).exec()
            return
        
        row = selected_rows[0].row()
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Confirm cancellation
        job = self.incomplete_jobs[row]
        confirm = ConfirmationDialog(
            "Cancel Job",
            f"Are you sure you want to cancel this job?<br><br>"
            f"<b>Pending emails:</b> {job['pending']}<br>"
            f"<b>Already sent:</b> {job['sent']}<br><br>"
            f"Cancelling will mark all pending emails as cancelled.",
            "This action cannot be undone.",
            confirm_text="Cancel Job",
            parent=self
        )
        
        if confirm.exec() == QDialog.DialogCode.Accepted:
            # Cancel the job in database
            from core.queue_manager import QueueManager
            queue_manager = QueueManager(self.database)
            try:
                queue_manager.cancel_job(job_id)
                
                # Remove from table
                self.table.removeRow(row)
                self.incomplete_jobs.pop(row)
                
                # If no more jobs, close dialog
                if not self.incomplete_jobs:
                    self.reject()
                
            except Exception as e:
                ErrorDialog(
                    "Error Cancelling Job",
                    "Failed to cancel the job.",
                    str(e),
                    parent=self
                ).exec()


class AddEmailManuallyDialog(QDialog):
    """
    Dialog for manually adding a single email recipient.
    
    Allows users to enter:
    - Email address (required)
    - Name (optional)
    - Company (optional)
    - Custom fields (optional)
    
    Validates email format before accepting.
    
    Requirements: 2.3, 7.1 - Manual email entry with validation
    """
    
    def __init__(self, existing_custom_fields: list = None, parent=None):
        """
        Initialize the manual email entry dialog.
        
        Args:
            existing_custom_fields: List of custom field names from existing recipients
            parent: Parent widget
        """
        super().__init__(parent)
        self.existing_custom_fields = existing_custom_fields or []
        self.recipient_data = None
        
        self.setWindowTitle("Add Email Manually")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        from PyQt6.QtWidgets import QLineEdit, QFormLayout, QScrollArea
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Enter recipient information manually. Only the email address is required."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Form layout for input fields
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Configure form layout for proper alignment
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Email field (required)
        email_label = QLabel("Email:*")
        email_label.setMinimumWidth(130)
        self.email_input = QLineEdit()
        self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.email_input.setPlaceholderText("recipient@example.com")
        self.email_input.textChanged.connect(self.validate_input)
        form_layout.addRow(email_label, self.email_input)
        
        # Name field (optional)
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(130)
        self.name_input = QLineEdit()
        self.name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_input.setPlaceholderText("John Doe")
        form_layout.addRow(name_label, self.name_input)
        
        # Company field (optional)
        company_label = QLabel("Company:")
        company_label.setMinimumWidth(130)
        self.company_input = QLineEdit()
        self.company_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.company_input.setPlaceholderText("Acme Corp")
        form_layout.addRow(company_label, self.company_input)
        
        # Custom fields section
        if self.existing_custom_fields:
            # Add separator
            separator = QLabel("<hr>")
            form_layout.addRow(separator)
            
            # Custom fields label
            custom_label = QLabel("<b>Custom Fields (Optional):</b>")
            form_layout.addRow(custom_label)
            
            # Create input for each existing custom field
            self.custom_field_inputs = {}
            for field_name in self.existing_custom_fields:
                if field_name not in ['email', 'name', 'company']:
                    field_label = QLabel(f"{field_name}:")
                    field_label.setMinimumWidth(130)
                    field_input = QLineEdit()
                    field_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    field_input.setPlaceholderText(f"Enter {field_name}")
                    form_layout.addRow(field_label, field_input)
                    self.custom_field_inputs[field_name] = field_input
        else:
            self.custom_field_inputs = {}
        
        # Scroll area for form (in case there are many custom fields)
        scroll_area = QScrollArea()
        scroll_area.setWidget(form_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        layout.addWidget(scroll_area)
        
        # Validation message label
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("QLabel { color: #d32f2f; }")
        self.validation_label.setVisible(False)
        layout.addWidget(self.validation_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton(
            "Add Recipient",
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        cancel_button = button_box.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole
        )
        
        self.add_button.setEnabled(False)  # Disabled until valid email entered
        
        button_box.accepted.connect(self.accept_recipient)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def validate_input(self):
        """Validate email input and update button state."""
        from core.validator import Validator
        
        email = self.email_input.text().strip()
        
        if not email:
            self.add_button.setEnabled(False)
            self.validation_label.setVisible(False)
            return
        
        # Validate email format
        if Validator.validate_email(email):
            self.add_button.setEnabled(True)
            self.validation_label.setVisible(False)
        else:
            self.add_button.setEnabled(False)
            self.validation_label.setText("⚠ Invalid email format")
            self.validation_label.setVisible(True)
    
    def accept_recipient(self):
        """Accept the dialog and store recipient data."""
        from core.validator import Validator
        
        email = self.email_input.text().strip()
        
        # Final validation
        if not Validator.validate_email(email):
            ErrorDialog(
                "Invalid Email",
                f"The email address '{email}' is not valid.",
                parent=self
            ).exec()
            return
        
        # Build recipient data
        self.recipient_data = {
            'email': email,
            'fields': {}
        }
        
        # Add name if provided
        name = self.name_input.text().strip()
        if name:
            self.recipient_data['fields']['name'] = name
        
        # Add company if provided
        company = self.company_input.text().strip()
        if company:
            self.recipient_data['fields']['company'] = company
        
        # Add custom fields if provided
        for field_name, field_input in self.custom_field_inputs.items():
            value = field_input.text().strip()
            if value:
                self.recipient_data['fields'][field_name] = value
        
        self.accept()
    
    def get_recipient_data(self):
        """
        Get the entered recipient data.
        
        Returns:
            Dictionary with 'email' and 'fields' keys, or None if cancelled
        """
        return self.recipient_data


class AddMultipleEmailsDialog(QDialog):
    """
    Dialog for bulk manual entry of multiple email recipients.
    
    Allows users to:
    - Paste multiple email addresses (one per line)
    - Paste CSV format data (email, name, company)
    - Parse and validate all emails before adding
    - View summary of valid/invalid emails
    
    Supports formats:
    - Plain email list (one per line)
    - CSV format: email,name,company
    - Tab-separated values
    
    Requirements: 2.3, 7.1 - Bulk manual email entry with validation
    """
    
    def __init__(self, existing_custom_fields: list = None, parent=None):
        """
        Initialize the bulk email entry dialog.
        
        Args:
            existing_custom_fields: List of custom field names from existing recipients
            parent: Parent widget
        """
        super().__init__(parent)
        self.existing_custom_fields = existing_custom_fields or []
        self.parsed_recipients = []
        self.validation_errors = []
        
        self.setWindowTitle("Add Multiple Emails")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        from PyQt6.QtWidgets import QTextEdit, QGroupBox
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "<b>Paste multiple email addresses or CSV data</b><br><br>"
            "Supported formats:<br>"
            "• One email per line: <code>user@example.com</code><br>"
            "• CSV format: <code>email,name,company</code><br>"
            "• Tab-separated values<br><br>"
            "The first line can optionally be a header row."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Input text area
        input_group = QGroupBox("Paste Email Data")
        input_layout = QVBoxLayout()
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Paste email addresses here...\n\n"
            "Examples:\n"
            "user1@example.com\n"
            "user2@example.com\n\n"
            "Or CSV format:\n"
            "email,name,company\n"
            "user1@example.com,John Doe,Acme Corp\n"
            "user2@example.com,Jane Smith,Tech Inc"
        )
        self.text_input.setMinimumHeight(200)
        self.text_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.text_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Format detection info
        self.format_label = QLabel()
        self.format_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.format_label.setVisible(False)
        layout.addWidget(self.format_label)
        
        # Parse button
        self.parse_button = QPushButton("Parse and Validate")
        self.parse_button.setToolTip("Parse the pasted data and validate email addresses")
        self.parse_button.clicked.connect(self.parse_and_validate)
        self.parse_button.setEnabled(False)
        layout.addWidget(self.parse_button)
        
        # Validation results
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout()
        
        # Status labels
        status_layout = QHBoxLayout()
        
        self.valid_count_label = QLabel("Valid: 0")
        self.valid_count_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        status_layout.addWidget(self.valid_count_label)
        
        self.invalid_count_label = QLabel("Invalid: 0")
        self.invalid_count_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        status_layout.addWidget(self.invalid_count_label)
        
        status_layout.addStretch()
        results_layout.addLayout(status_layout)
        
        # Error messages
        self.error_messages_label = QLabel()
        self.error_messages_label.setWordWrap(True)
        self.error_messages_label.setStyleSheet(
            "QLabel { color: #ff6b6b; "
            "border: 1px solid #8c4a4a; padding: 10px; border-radius: 4px; }"
        )
        self.error_messages_label.setVisible(False)
        results_layout.addWidget(self.error_messages_label)
        
        results_group.setLayout(results_layout)
        results_group.setVisible(False)
        layout.addWidget(results_group)
        
        self.results_group = results_group
        
        # Buttons
        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton(
            "Add Recipients",
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        cancel_button = button_box.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole
        )
        
        self.add_button.setEnabled(False)
        
        button_box.accepted.connect(self.accept_recipients)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def on_text_changed(self):
        """Handle text input changes."""
        text = self.text_input.toPlainText().strip()
        self.parse_button.setEnabled(len(text) > 0)
        
        # Hide results when text changes
        self.results_group.setVisible(False)
        self.add_button.setEnabled(False)
    
    def parse_and_validate(self):
        """
        Parse the pasted text and validate email addresses.
        
        Supports:
        - Plain email list (one per line)
        - CSV format (email, name, company)
        - Tab-separated values
        
        Validates Requirements:
        - 2.3: Validate email addresses
        - 7.1: Bulk manual entry
        """
        from core.validator import Validator
        import csv
        from io import StringIO
        
        text = self.text_input.toPlainText().strip()
        
        if not text:
            return
        
        self.parsed_recipients = []
        self.validation_errors = []
        
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            return
        
        # Try to detect format
        first_line = lines[0]
        
        # Check if it's CSV format (contains commas or tabs)
        is_csv = ',' in first_line or '\t' in first_line
        
        if is_csv:
            # Parse as CSV
            self.parse_csv_format(text, lines)
        else:
            # Parse as plain email list
            self.parse_plain_format(lines)
        
        # Update validation results
        self.update_validation_results()
    
    def parse_plain_format(self, lines: list):
        """
        Parse plain email list format (one email per line).
        
        Args:
            lines: List of text lines
        """
        from core.validator import Validator
        
        self.format_label.setText("Format detected: Plain email list")
        self.format_label.setVisible(True)
        
        for line_num, line in enumerate(lines, start=1):
            email = line.strip()
            
            if not email:
                continue
            
            # Validate email
            if Validator.validate_email(email):
                self.parsed_recipients.append({
                    'email': email,
                    'fields': {}
                })
            else:
                self.validation_errors.append(
                    f"Line {line_num}: Invalid email format: {email}"
                )
    
    def parse_csv_format(self, text: str, lines: list):
        """
        Parse CSV format (email, name, company).
        
        Args:
            text: Full text input
            lines: List of text lines
        """
        from core.validator import Validator
        import csv
        from io import StringIO
        
        # Detect delimiter (comma or tab)
        delimiter = ',' if ',' in lines[0] else '\t'
        
        self.format_label.setText(
            f"Format detected: CSV ({'comma' if delimiter == ',' else 'tab'}-separated)"
        )
        self.format_label.setVisible(True)
        
        # Parse CSV
        try:
            reader = csv.reader(StringIO(text), delimiter=delimiter)
            rows = list(reader)
            
            if not rows:
                return
            
            # Check if first row is a header
            first_row = rows[0]
            has_header = False
            
            # Simple heuristic: if first row contains "email" or "name", it's likely a header
            if len(first_row) > 0:
                first_cell = first_row[0].lower().strip()
                if first_cell in ['email', 'e-mail', 'mail', 'email address']:
                    has_header = True
            
            # Determine column mapping
            if has_header:
                headers = [h.strip().lower() for h in first_row]
                data_rows = rows[1:]
                
                # Find email column
                email_col = None
                for i, header in enumerate(headers):
                    if header in ['email', 'e-mail', 'mail', 'email address']:
                        email_col = i
                        break
                
                if email_col is None:
                    # No email column found, assume first column
                    email_col = 0
                
                # Find name and company columns
                name_col = None
                company_col = None
                
                for i, header in enumerate(headers):
                    if header in ['name', 'full name', 'fullname', 'recipient']:
                        name_col = i
                    elif header in ['company', 'organization', 'organisation']:
                        company_col = i
                
                # Parse data rows
                for row_num, row in enumerate(data_rows, start=2):  # Start at 2 (after header)
                    if not row or len(row) == 0:
                        continue
                    
                    # Get email
                    if email_col < len(row):
                        email = row[email_col].strip()
                    else:
                        self.validation_errors.append(
                            f"Line {row_num}: Missing email column"
                        )
                        continue
                    
                    if not email:
                        continue
                    
                    # Validate email
                    if not Validator.validate_email(email):
                        self.validation_errors.append(
                            f"Line {row_num}: Invalid email format: {email}"
                        )
                        continue
                    
                    # Build recipient data
                    fields = {}
                    
                    # Get name
                    if name_col is not None and name_col < len(row):
                        name = row[name_col].strip()
                        if name:
                            fields['name'] = name
                    
                    # Get company
                    if company_col is not None and company_col < len(row):
                        company = row[company_col].strip()
                        if company:
                            fields['company'] = company
                    
                    # Add other columns as custom fields
                    for i, value in enumerate(row):
                        if i not in [email_col, name_col, company_col]:
                            if i < len(headers):
                                field_name = headers[i]
                                if field_name and value.strip():
                                    fields[field_name] = value.strip()
                    
                    self.parsed_recipients.append({
                        'email': email,
                        'fields': fields
                    })
            else:
                # No header, assume: email, name, company
                for row_num, row in enumerate(rows, start=1):
                    if not row or len(row) == 0:
                        continue
                    
                    # Get email (first column)
                    email = row[0].strip()
                    
                    if not email:
                        continue
                    
                    # Validate email
                    if not Validator.validate_email(email):
                        self.validation_errors.append(
                            f"Line {row_num}: Invalid email format: {email}"
                        )
                        continue
                    
                    # Build recipient data
                    fields = {}
                    
                    # Get name (second column if exists)
                    if len(row) > 1:
                        name = row[1].strip()
                        if name:
                            fields['name'] = name
                    
                    # Get company (third column if exists)
                    if len(row) > 2:
                        company = row[2].strip()
                        if company:
                            fields['company'] = company
                    
                    self.parsed_recipients.append({
                        'email': email,
                        'fields': fields
                    })
        
        except Exception as e:
            self.validation_errors.append(f"CSV parsing error: {str(e)}")
    
    def update_validation_results(self):
        """Update the validation results display."""
        valid_count = len(self.parsed_recipients)
        invalid_count = len(self.validation_errors)
        
        # Update count labels
        self.valid_count_label.setText(f"Valid: {valid_count}")
        self.invalid_count_label.setText(f"Invalid: {invalid_count}")
        
        # Show/hide error messages
        if self.validation_errors:
            # Show first 10 errors
            error_text = "<b>Validation Errors:</b><br>"
            for error in self.validation_errors[:10]:
                error_text += f"• {error}<br>"
            
            if len(self.validation_errors) > 10:
                error_text += f"<br><i>... and {len(self.validation_errors) - 10} more errors</i>"
            
            self.error_messages_label.setText(error_text)
            self.error_messages_label.setVisible(True)
        else:
            self.error_messages_label.setVisible(False)
        
        # Show results group
        self.results_group.setVisible(True)
        
        # Enable add button if there are valid recipients
        self.add_button.setEnabled(valid_count > 0)
    
    def accept_recipients(self):
        """Accept the dialog and return parsed recipients."""
        if not self.parsed_recipients:
            ErrorDialog(
                "No Valid Recipients",
                "No valid email addresses were found in the pasted data.",
                parent=self
            ).exec()
            return
        
        self.accept()
    
    def get_parsed_recipients(self):
        """
        Get the parsed and validated recipients.
        
        Returns:
            List of dictionaries with 'email' and 'fields' keys
        """
        return self.parsed_recipients


class OptOutListDialog(QDialog):
    """
    Dialog for managing the opt-out list.
    
    Allows users to:
    - View all opted-out email addresses
    - Add new email addresses to opt-out list
    - Remove email addresses from opt-out list
    
    Requirements: 6.5, 6.6 - Opt-out list management
    """
    
    def __init__(self, database, parent=None):
        """
        Initialize the opt-out list dialog.
        
        Args:
            database: Database instance for opt-out list operations
            parent: Parent widget
        """
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("Opt-Out List Management")
        self.setModal(True)
        self.resize(600, 400)
        
        self.init_ui()
        self.load_optout_list()
    
    def init_ui(self):
        """Initialize the user interface."""
        from PyQt6.QtWidgets import (
            QTableWidget, QTableWidgetItem, QLineEdit,
            QHeaderView
        )
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Manage email addresses that have opted out of receiving emails. "
            "These addresses will be automatically excluded from future sends."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add email section
        add_layout = QHBoxLayout()
        add_label = QLabel("Add email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address to add to opt-out list")
        self.email_input.returnPressed.connect(self.add_email)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_email)
        
        add_layout.addWidget(add_label)
        add_layout.addWidget(self.email_input, 1)
        add_layout.addWidget(self.add_button)
        
        layout.addLayout(add_layout)
        
        # Opt-out list table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Email", "Added At", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)
    
    def load_optout_list(self):
        """Load and display the opt-out list from database."""
        from PyQt6.QtWidgets import QTableWidgetItem
        
        # Get opt-out list from database
        optout_list = self.database.get_optout_list()
        
        # Clear table
        self.table.setRowCount(0)
        
        # Populate table
        for email, added_at in optout_list:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Email column
            email_item = QTableWidgetItem(email)
            self.table.setItem(row, 0, email_item)
            
            # Added at column (format datetime)
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(added_at)
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = added_at
            
            date_item = QTableWidgetItem(formatted_date)
            self.table.setItem(row, 1, date_item)
            
            # Remove button
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda checked, e=email: self.remove_email(e))
            self.table.setCellWidget(row, 2, remove_button)
        
        # Update status
        count = len(optout_list)
        self.status_label.setText(f"Total opted-out emails: {count}")
    
    def add_email(self):
        """Add email to opt-out list."""
        from core.validator import Validator
        
        email = self.email_input.text().strip()
        
        if not email:
            ErrorDialog(
                "Invalid Input",
                "Please enter an email address.",
                parent=self
            ).exec()
            return
        
        # Validate email format
        if not Validator.validate_email(email):
            ErrorDialog(
                "Invalid Email",
                f"The email address '{email}' is not valid.",
                parent=self
            ).exec()
            return
        
        # Check if already in opt-out list
        if self.database.is_opted_out(email):
            ErrorDialog(
                "Already Opted Out",
                f"The email address '{email}' is already in the opt-out list.",
                parent=self
            ).exec()
            return
        
        # Add to database
        try:
            self.database.add_to_optout(email)
            self.email_input.clear()
            self.load_optout_list()
        except Exception as e:
            ErrorDialog(
                "Error Adding Email",
                "Failed to add email to opt-out list.",
                str(e),
                parent=self
            ).exec()
    
    def remove_email(self, email: str):
        """Remove email from opt-out list.
        
        Args:
            email: Email address to remove
        """
        # Confirm removal
        confirm = ConfirmationDialog(
            "Remove from Opt-Out List",
            f"Are you sure you want to remove '{email}' from the opt-out list?",
            "This email address will be able to receive emails again.",
            confirm_text="Remove",
            parent=self
        )
        
        if confirm.exec() == QDialog.DialogCode.Accepted:
            try:
                self.database.remove_from_optout(email)
                self.load_optout_list()
            except Exception as e:
                ErrorDialog(
                    "Error Removing Email",
                    "Failed to remove email from opt-out list.",
                    str(e),
                    parent=self
                ).exec()



class SelectByCriteriaDialog(QDialog):
    """
    Dialog for selecting recipients based on field criteria.
    
    Allows users to select all recipients where a specific field matches a value.
    Supports different match modes: exact, contains, starts with, ends with.
    """
    
    def __init__(self, available_fields: List[str], recipients: List, parent=None):
        """
        Initialize the select by criteria dialog.
        
        Args:
            available_fields: List of field names available for filtering
            recipients: List of Recipient objects (used to populate value suggestions)
            parent: Parent widget
        """
        super().__init__(parent)
        self.available_fields = available_fields
        self.recipients = recipients
        self.criteria = None
        
        self.setWindowTitle("Select by Criteria")
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Select recipients where a specific field matches a value.\n"
            "For example: select all recipients from 'Acme Corp' company."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(instructions)
        
        # Form layout for criteria
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Field selection
        field_label = QLabel("Field:")
        field_label.setMinimumWidth(130)
        self.field_combo = QComboBox()
        self.field_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.field_combo.addItems(self.available_fields)
        self.field_combo.setToolTip("Select the field to filter by")
        self.field_combo.currentIndexChanged.connect(self.on_field_changed)
        form_layout.addRow(field_label, self.field_combo)
        
        # Match mode selection
        match_mode_label = QLabel("Match mode:")
        match_mode_label.setMinimumWidth(130)
        self.match_mode_combo = QComboBox()
        self.match_mode_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.match_mode_combo.addItem("Exact match", "exact")
        self.match_mode_combo.addItem("Contains", "contains")
        self.match_mode_combo.addItem("Starts with", "starts_with")
        self.match_mode_combo.addItem("Ends with", "ends_with")
        self.match_mode_combo.setToolTip("Select how to match the value")
        form_layout.addRow(match_mode_label, self.match_mode_combo)
        
        # Value input with suggestions
        value_label = QLabel("Value:")
        value_label.setMinimumWidth(130)
        self.value_combo = QComboBox()
        self.value_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.value_combo.setEditable(True)
        self.value_combo.setToolTip("Enter or select the value to match")
        form_layout.addRow(value_label, self.value_combo)
        
        layout.addLayout(form_layout)
        
        # Preview label showing how many recipients will be selected
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(
            "QLabel { border: 1px solid #4a7c8c; "
            "padding: 10px; border-radius: 4px; margin-top: 10px; }"
        )
        layout.addWidget(self.preview_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.preview_button = QPushButton("Preview")
        self.preview_button.setToolTip("Preview how many recipients match the criteria")
        self.preview_button.clicked.connect(self.preview_selection)
        button_layout.addWidget(self.preview_button)
        
        self.select_button = QPushButton("Select")
        self.select_button.setToolTip("Apply the selection criteria")
        self.select_button.clicked.connect(self.accept)
        self.select_button.setDefault(True)
        button_layout.addWidget(self.select_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Populate initial field values
        self.on_field_changed()
    
    def on_field_changed(self):
        """Handle field selection change - populate value suggestions."""
        field_name = self.field_combo.currentText()
        
        # Clear existing values
        self.value_combo.clear()
        
        # Get unique values for this field from recipients
        unique_values = set()
        for recipient in self.recipients:
            if field_name == 'email':
                value = recipient.email
            else:
                value = recipient.fields.get(field_name, '')
            
            if value:
                unique_values.add(str(value))
        
        # Add unique values to combo box (sorted)
        if unique_values:
            self.value_combo.addItems(sorted(unique_values))
        
        # Clear preview
        self.preview_label.clear()
    
    def preview_selection(self):
        """Preview how many recipients match the criteria."""
        field_name = self.field_combo.currentText()
        field_value = self.value_combo.currentText().strip()
        match_mode = self.match_mode_combo.currentData()
        
        if not field_value:
            self.preview_label.setText("⚠️ Please enter a value to match.")
            self.preview_label.setStyleSheet(
                "QLabel { color: #ffcc00; border: 1px solid #8b7355; "
                "padding: 10px; border-radius: 4px; margin-top: 10px; }"
            )
            return
        
        # Count matching recipients
        match_count = 0
        for recipient in self.recipients:
            # Get field value
            if field_name == 'email':
                recipient_value = recipient.email
            else:
                recipient_value = recipient.fields.get(field_name, '')
            
            # Convert to string for comparison
            recipient_value = str(recipient_value).lower()
            field_value_lower = field_value.lower()
            
            # Check match based on mode
            matches = False
            if match_mode == 'exact':
                matches = recipient_value == field_value_lower
            elif match_mode == 'contains':
                matches = field_value_lower in recipient_value
            elif match_mode == 'starts_with':
                matches = recipient_value.startswith(field_value_lower)
            elif match_mode == 'ends_with':
                matches = recipient_value.endswith(field_value_lower)
            
            if matches:
                match_count += 1
        
        # Display preview
        if match_count > 0:
            self.preview_label.setText(
                f"✓ {match_count} recipient(s) will be selected "
                f"(out of {len(self.recipients)} total)"
            )
            self.preview_label.setStyleSheet(
                "QLabel { background-color: #d4edda; border: 1px solid #c3e6cb; "
                "padding: 10px; border-radius: 4px; margin-top: 10px; }"
            )
        else:
            self.preview_label.setText(
                f"⚠️ No recipients match the criteria. "
                f"Try a different value or match mode."
            )
            self.preview_label.setStyleSheet(
                "QLabel { color: #ffcc00; border: 1px solid #8b7355; "
                "padding: 10px; border-radius: 4px; margin-top: 10px; }"
            )
    
    def get_criteria(self) -> Optional[Dict[str, str]]:
        """
        Get the selected criteria.
        
        Returns:
            Dictionary with 'field', 'value', and 'match_mode' keys, or None if cancelled
        """
        if self.result() == QDialog.DialogCode.Accepted:
            field_value = self.value_combo.currentText().strip()
            
            if not field_value:
                return None
            
            return {
                'field': self.field_combo.currentText(),
                'value': field_value,
                'match_mode': self.match_mode_combo.currentData()
            }
        
        return None



class TemplateSelectionDialog(QDialog):
    """
    Dialog for selecting predefined email templates.
    
    Allows users to:
    - Browse templates by category
    - Preview template content
    - Select a template to load into the editor
    """
    
    def __init__(self, parent=None):
        """
        Initialize the template selection dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Επιλογή Έτοιμου Template")
        self.setModal(True)
        self.resize(800, 600)
        
        self.selected_template = None
        
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Επιλέξτε ένα έτοιμο template για να ξεκινήσετε. "
            "Μπορείτε να το προσαρμόσετε μετά την επιλογή."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { padding: 10px; border: 1px solid #4a7c8c; border-radius: 5px; }"
        )
        layout.addWidget(info_label)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left side - Category and template list
        left_layout = QVBoxLayout()
        
        category_label = QLabel("Κατηγορία:")
        left_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        left_layout.addWidget(self.category_combo)
        
        template_label = QLabel("Templates:")
        left_layout.addWidget(template_label)
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)
        
        content_layout.addLayout(left_layout, 1)
        
        # Right side - Preview
        right_layout = QVBoxLayout()
        
        preview_label = QLabel("Προεπισκόπηση:")
        preview_label.setStyleSheet("QLabel { font-weight: bold; }")
        right_layout.addWidget(preview_label)
        
        # Subject preview
        subject_label = QLabel("Θέμα:")
        right_layout.addWidget(subject_label)
        
        self.subject_preview = QLineEdit()
        self.subject_preview.setReadOnly(True)
        right_layout.addWidget(self.subject_preview)
        
        # HTML body preview
        html_label = QLabel("HTML Body:")
        right_layout.addWidget(html_label)
        
        self.html_preview = QTextEdit()
        self.html_preview.setReadOnly(True)
        self.html_preview.setStyleSheet("QTextEdit { font-family: monospace; }")
        right_layout.addWidget(self.html_preview)
        
        # Text body preview
        text_label = QLabel("Text Body:")
        right_layout.addWidget(text_label)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setStyleSheet("QTextEdit { font-family: monospace; }")
        right_layout.addWidget(self.text_preview)
        
        content_layout.addLayout(right_layout, 2)
        
        layout.addLayout(content_layout)
        
        # Variables info
        variables_label = QLabel(
            "💡 Διαθέσιμες μεταβλητές: {{name}}, {{email}}, {{company}}, {{subject_prefix}}, "
            "{{sender_name}}, {{tracking_id}}, {{unsubscribe_link}}"
        )
        variables_label.setWordWrap(True)
        variables_label.setStyleSheet(
            "QLabel { padding: 8px; color: #ffcc00; border: 1px solid #8b7355; border-radius: 5px; font-size: 10pt; }"
        )
        layout.addWidget(variables_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_templates(self):
        """Load predefined templates into the dialog."""
        from templates.predefined_templates import PredefinedTemplates
        
        # Get all templates organized by category
        all_templates = PredefinedTemplates.get_all_templates()
        
        # Store templates
        self.templates_by_category = all_templates
        
        # Populate category combo
        self.category_combo.addItems(all_templates.keys())
    
    def on_category_changed(self, category: str):
        """Handle category selection change."""
        if not category:
            return
        
        # Clear template list
        self.template_list.clear()
        
        # Get templates for this category
        templates = self.templates_by_category.get(category, {})
        
        # Add templates to list
        for template_name in templates.keys():
            self.template_list.addItem(template_name)
    
    def on_template_selected(self, current, previous):
        """Handle template selection change."""
        if not current:
            return
        
        template_name = current.text()
        category = self.category_combo.currentText()
        
        # Get template data
        template = self.templates_by_category[category][template_name]
        
        # Update preview
        self.subject_preview.setText(template['subject'])
        self.html_preview.setPlainText(template['html_body'])
        self.text_preview.setPlainText(template['text_body'])
        
        # Store selected template
        self.selected_template = {
            'category': category,
            'name': template_name,
            'subject': template['subject'],
            'html_body': template['html_body'],
            'text_body': template['text_body']
        }
    
    def get_selected_template(self):
        """
        Get the selected template.
        
        Returns:
            Dictionary with template data or None if no selection
        """
        return self.selected_template


class EmailBodyEditorDialog(QDialog):
    """
    Dialog for editing HTML and Plain Text email body.
    
    Provides a larger editing area with variable insertion support.
    """
    
    def __init__(self, html_body: str = "", text_body: str = "", 
                 available_fields: List[str] = None, parent=None):
        """
        Initialize the email body editor dialog.
        
        Args:
            html_body: Initial HTML body content
            text_body: Initial plain text body content
            available_fields: List of available variable fields
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Email Body")
        self.resize(900, 700)
        self.setMinimumSize(700, 500)
        
        # Default variables always available
        default_vars = ['name', 'email', 'company', 'unsubscribe_link']
        
        # Combine with available fields from recipients
        self.available_fields = available_fields or []
        all_fields = default_vars + [f for f in self.available_fields if f not in default_vars]
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # ===== HTML Body Section =====
        html_group = QGroupBox("HTML Body")
        html_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        html_layout = QVBoxLayout()
        html_layout.setContentsMargins(10, 10, 10, 10)
        html_layout.setSpacing(8)
        
        # Variable insertion for HTML
        html_var_layout = QHBoxLayout()
        html_var_label = QLabel("Insert Variable:")
        html_var_layout.addWidget(html_var_label)
        
        self.html_var_combo = QComboBox()
        self.html_var_combo.addItem("Select variable...", None)
        for field in all_fields:
            self.html_var_combo.addItem(f"{{{{{field}}}}}", field)
        self.html_var_combo.currentIndexChanged.connect(self.insert_html_variable)
        self.html_var_combo.setFixedWidth(200)
        html_var_layout.addWidget(self.html_var_combo)
        html_var_layout.addStretch()
        html_layout.addLayout(html_var_layout)
        
        # HTML editor
        self.html_editor = QTextEdit()
        self.html_editor.setPlaceholderText(
            "Enter HTML email body here...\n\n"
            "Use {{variable}} for personalization.\n"
            "Example: <p>Hello {{name}},</p>"
        )
        self.html_editor.setPlainText(html_body)
        self.html_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        html_layout.addWidget(self.html_editor, stretch=1)
        
        html_group.setLayout(html_layout)
        layout.addWidget(html_group, stretch=1)
        
        # ===== Plain Text Body Section =====
        text_group = QGroupBox("Plain Text Body (fallback)")
        text_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 10, 10, 10)
        text_layout.setSpacing(8)
        
        # Variable insertion for text
        text_var_layout = QHBoxLayout()
        text_var_label = QLabel("Insert Variable:")
        text_var_layout.addWidget(text_var_label)
        
        self.text_var_combo = QComboBox()
        self.text_var_combo.addItem("Select variable...", None)
        for field in all_fields:
            self.text_var_combo.addItem(f"{{{{{field}}}}}", field)
        self.text_var_combo.currentIndexChanged.connect(self.insert_text_variable)
        self.text_var_combo.setFixedWidth(200)
        text_var_layout.addWidget(self.text_var_combo)
        text_var_layout.addStretch()
        text_layout.addLayout(text_var_layout)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText(
            "Enter plain text email body here...\n\n"
            "Use {{variable}} for personalization.\n"
            "Example: Hello {{name}},"
        )
        self.text_editor.setPlainText(text_body)
        self.text_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout.addWidget(self.text_editor, stretch=1)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group, stretch=1)
        
        # ===== Buttons =====
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def insert_html_variable(self, index: int):
        """Insert selected variable into HTML editor."""
        if index <= 0:
            return
        
        variable = self.html_var_combo.currentText()
        cursor = self.html_editor.textCursor()
        cursor.insertText(variable)
        self.html_editor.setFocus()
        
        # Reset combo
        self.html_var_combo.setCurrentIndex(0)
    
    def insert_text_variable(self, index: int):
        """Insert selected variable into text editor."""
        if index <= 0:
            return
        
        variable = self.text_var_combo.currentText()
        cursor = self.text_editor.textCursor()
        cursor.insertText(variable)
        self.text_editor.setFocus()
        
        # Reset combo
        self.text_var_combo.setCurrentIndex(0)
    
    def get_html_body(self) -> str:
        """Get the HTML body content."""
        return self.html_editor.toPlainText()
    
    def get_text_body(self) -> str:
        """Get the plain text body content."""
        return self.text_editor.toPlainText()


class UserGuideDialog(QDialog):
    """
    Dialog for displaying the user guide.
    """
    
    def __init__(self, html_content: str, parent=None):
        """
        Initialize the user guide dialog.
        
        Args:
            html_content: HTML content to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("📖 Οδηγίες Χρήσης - Bulk Email Sender")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Content browser
        browser = QTextBrowser()
        browser.setHtml(html_content)
        browser.setOpenExternalLinks(True)
        layout.addWidget(browser)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
