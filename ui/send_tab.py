"""
Send Tab for Bulk Email Sender Application

This module implements the send control interface with throttle configuration,
dry run mode, progress tracking, real-time logging, and send controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QSlider, QSpinBox, QCheckBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import Optional, List
from datetime import datetime
import csv

from models.send_job import SendJob
from models.recipient import Recipient
from models.template import EmailTemplate
from models.smtp_config import SMTPConfig
from core.smtp_manager import SMTPManager
from core.queue_manager import QueueManager
from core.template_renderer import TemplateRenderer
from core.worker import SendWorker
from storage.database import Database


class SendTab(QWidget):
    """
    Send tab widget.
    
    Provides:
    - Throttle rate configuration (slider + spinbox)
    - Max retries configuration
    - "Dry Run" checkbox
    - "Send to Self First" button
    - "Start Send" button
    - Progress bar and status labels (sent, failed, remaining, rate)
    - Pause/resume/stop buttons
    - Real-time log display (QTableView)
    - "Export Log to CSV" button
    - Summary report display on completion
    - Connection to SendWorker signals for progress updates
    
    Validates Requirements: 4.4, 4.7, 5.1, 5.2, 5.4, 5.5, 6.1, 6.4, 7.2, 7.5, 
                           11.1, 11.2, 11.3, 11.4
    """
    
    def __init__(self, database: Database):
        """
        Initialize the Send tab.
        
        Args:
            database: Database instance for logging and queue management
        """
        super().__init__()
        self.database = database
        self.queue_manager = QueueManager(database)
        self.template_renderer = TemplateRenderer()
        
        # State
        self.recipients: List[Recipient] = []
        self.template: Optional[EmailTemplate] = None
        self.smtp_config: Optional[SMTPConfig] = None
        self.current_job: Optional[SendJob] = None
        self.worker: Optional[SendWorker] = None
        
        # Statistics
        self.sent_count = 0
        self.failed_count = 0
        self.remaining_count = 0
        self.start_time: Optional[datetime] = None
        
        # Rate tracking
        self.rate_timer = QTimer()
        self.rate_timer.timeout.connect(self.update_rate)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Configuration Group
        config_group = self.create_configuration_group()
        config_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(config_group)
        
        # Send Controls Group
        controls_group = self.create_send_controls_group()
        controls_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(controls_group)
        
        # Progress Group
        progress_group = self.create_progress_group()
        progress_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(progress_group)
        
        # Log Display Group - this should expand
        log_group = self.create_log_display_group()
        log_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def create_configuration_group(self) -> QGroupBox:
        """Create the configuration group box."""
        group = QGroupBox("Send Configuration")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        # Throttle rate configuration (slider + spinbox)
        throttle_label = QLabel("Throttle Rate:*")
        throttle_label.setMinimumWidth(100)
        throttle_layout = QHBoxLayout()
        throttle_layout.setSpacing(8)
        
        self.throttle_slider = QSlider(Qt.Orientation.Horizontal)
        self.throttle_slider.setMinimum(1000)  # 1 second minimum
        self.throttle_slider.setMaximum(10000)  # 10 seconds maximum
        self.throttle_slider.setValue(2000)  # 2 seconds default
        self.throttle_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.throttle_slider.setTickInterval(1000)
        self.throttle_slider.setToolTip("Delay between consecutive email sends (1-10 seconds)")
        self.throttle_slider.valueChanged.connect(self.on_throttle_changed)
        self.throttle_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        throttle_layout.addWidget(self.throttle_slider)
        
        self.throttle_spinbox = QSpinBox()
        self.throttle_spinbox.setMinimum(1000)
        self.throttle_spinbox.setMaximum(10000)
        self.throttle_spinbox.setValue(2000)
        self.throttle_spinbox.setSuffix(" ms")
        self.throttle_spinbox.setToolTip("Delay in milliseconds between sends")
        self.throttle_spinbox.valueChanged.connect(self.on_throttle_spinbox_changed)
        throttle_layout.addWidget(self.throttle_spinbox)
        
        form_layout.addRow(throttle_label, throttle_layout)
        
        # Throttle warning label
        self.throttle_warning_label = QLabel()
        self.throttle_warning_label.setWordWrap(True)
        self.throttle_warning_label.setStyleSheet(
            "QLabel { "
            "color: #856404; "
            "background-color: #fff3cd; "
            "border: 1px solid #ffc107; "
            "padding: 8px; "
            "border-radius: 4px; "
            "}"
        )
        self.throttle_warning_label.hide()
        form_layout.addRow("", self.throttle_warning_label)
        
        # Max retries configuration
        max_retries_label = QLabel("Max Retries:")
        max_retries_label.setMinimumWidth(100)
        self.max_retries_spinbox = QSpinBox()
        self.max_retries_spinbox.setMinimum(0)
        self.max_retries_spinbox.setMaximum(10)
        self.max_retries_spinbox.setValue(3)
        self.max_retries_spinbox.setToolTip("Maximum retry attempts for transient errors")
        self.max_retries_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow(max_retries_label, self.max_retries_spinbox)
        
        # Dry run checkbox
        self.dry_run_checkbox = QCheckBox("Dry Run Mode")
        self.dry_run_checkbox.setToolTip(
            "Validate templates and SMTP without sending to real recipients"
        )
        form_layout.addRow("", self.dry_run_checkbox)
        
        group.setLayout(form_layout)
        return group
    
    def create_send_controls_group(self) -> QGroupBox:
        """Create the send controls group box."""
        group = QGroupBox("Send Controls")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Recipient count display
        self.recipient_count_label = QLabel("No recipients selected")
        self.recipient_count_label.setStyleSheet(
            "QLabel { font-weight: bold; color: #0066cc; padding: 5px; }"
        )
        self.recipient_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.recipient_count_label)
        
        # Top row: Send to Self First and Start Send buttons
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(10)
        
        self.send_to_self_button = QPushButton("Send to Self First")
        self.send_to_self_button.setToolTip(
            "Send a test email to yourself using the first recipient's data"
        )
        self.send_to_self_button.clicked.connect(self.send_to_self)
        self.send_to_self_button.setEnabled(False)
        self.send_to_self_button.setMinimumHeight(40)
        self.send_to_self_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.send_to_self_button.setStyleSheet(
            "QPushButton { padding: 10px; font-size: 11pt; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        top_button_layout.addWidget(self.send_to_self_button)
        
        self.start_send_button = QPushButton("Start Send")
        self.start_send_button.setToolTip("Start bulk email sending")
        self.start_send_button.clicked.connect(self.start_send)
        self.start_send_button.setEnabled(False)
        self.start_send_button.setMinimumHeight(40)
        self.start_send_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.start_send_button.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 10px; font-size: 11pt; }"
            "QPushButton:hover { background-color: #218838; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        top_button_layout.addWidget(self.start_send_button)
        
        layout.addLayout(top_button_layout)
        
        # Bottom row: Pause/Resume/Stop buttons
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.setSpacing(10)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setToolTip("Pause sending after current email")
        self.pause_button.clicked.connect(self.pause_send)
        self.pause_button.setEnabled(False)
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.pause_button.setStyleSheet(
            "QPushButton { padding: 10px; font-size: 11pt; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        bottom_button_layout.addWidget(self.pause_button)
        
        self.resume_button = QPushButton("Resume")
        self.resume_button.setToolTip("Resume sending from paused state")
        self.resume_button.clicked.connect(self.resume_send)
        self.resume_button.setEnabled(False)
        self.resume_button.setMinimumHeight(40)
        self.resume_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.resume_button.setStyleSheet(
            "QPushButton { padding: 10px; font-size: 11pt; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        bottom_button_layout.addWidget(self.resume_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Stop sending and cancel remaining emails")
        self.stop_button.clicked.connect(self.stop_send)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; padding: 10px; font-size: 11pt; }"
            "QPushButton:hover { background-color: #c82333; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        bottom_button_layout.addWidget(self.stop_button)
        
        layout.addLayout(bottom_button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_progress_group(self) -> QGroupBox:
        """Create the progress tracking group box."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.progress_bar)
        
        # Status labels
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)
        
        self.sent_label = QLabel("Sent: 0")
        self.sent_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        status_layout.addWidget(self.sent_label)
        
        self.failed_label = QLabel("Failed: 0")
        self.failed_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        status_layout.addWidget(self.failed_label)
        
        self.remaining_label = QLabel("Remaining: 0")
        self.remaining_label.setStyleSheet("QLabel { font-weight: bold; }")
        status_layout.addWidget(self.remaining_label)
        
        self.rate_label = QLabel("Rate: 0 emails/min")
        self.rate_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        status_layout.addWidget(self.rate_label)
        
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        # Summary report label (hidden until completion)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            "QLabel { background-color: #d4edda; border: 1px solid #c3e6cb; "
            "padding: 10px; border-radius: 4px; }"
        )
        self.summary_label.hide()
        layout.addWidget(self.summary_label)
        
        group.setLayout(layout)
        return group
    
    def create_log_display_group(self) -> QGroupBox:
        """Create the log display group box."""
        group = QGroupBox("Send Log")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Log table - make it expand to fill available space
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Email", "Status", "Error"])
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_table.setMinimumHeight(150)
        
        # Set column widths
        self.log_table.setColumnWidth(0, 150)  # Timestamp
        self.log_table.setColumnWidth(1, 200)  # Email
        self.log_table.setColumnWidth(2, 100)  # Status
        
        layout.addWidget(self.log_table)
        
        # Export button
        export_layout = QHBoxLayout()
        
        self.export_log_button = QPushButton("Export Log to CSV")
        self.export_log_button.setToolTip("Export send log to CSV file")
        self.export_log_button.clicked.connect(self.export_log_to_csv)
        self.export_log_button.setEnabled(False)
        export_layout.addWidget(self.export_log_button)
        
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        
        group.setLayout(layout)
        return group
    
    def on_throttle_changed(self, value: int):
        """Handle throttle slider change."""
        self.throttle_spinbox.blockSignals(True)
        self.throttle_spinbox.setValue(value)
        self.throttle_spinbox.blockSignals(False)
        self.check_throttle_warning(value)
    
    def on_throttle_spinbox_changed(self, value: int):
        """Handle throttle spinbox change."""
        self.throttle_slider.blockSignals(True)
        self.throttle_slider.setValue(value)
        self.throttle_slider.blockSignals(False)
        self.check_throttle_warning(value)
    
    def check_throttle_warning(self, throttle_ms: int):
        """
        Check throttle rate and display warning if too fast.
        
        Validates Requirements:
        - 6.1: Enforce minimum throttle rate of 1 second
        - 6.4: Display warning when throttle rate exceeds 100 emails per minute
        """
        # Calculate emails per minute
        emails_per_minute = 60000 / throttle_ms
        
        # Warning threshold: > 100 emails/min (< 600ms)
        if emails_per_minute > 100:
            self.throttle_warning_label.setText(
                f"⚠️ Warning: Rate of {emails_per_minute:.0f} emails/min may trigger spam filters. "
                f"Consider increasing throttle delay."
            )
            self.throttle_warning_label.show()
        else:
            self.throttle_warning_label.hide()
    
    def set_recipients(self, recipients: List[Recipient]):
        """
        Set the recipients for sending.
        
        Args:
            recipients: List of Recipient objects (should be only selected recipients)
        """
        self.recipients = recipients
        self.remaining_count = len(recipients)
        self.remaining_label.setText(f"Remaining: {self.remaining_count}")
        self.update_send_button_state()
        self.update_recipient_count_display()
    
    def set_template(self, template: EmailTemplate):
        """
        Set the email template for sending.
        
        Args:
            template: EmailTemplate object
        """
        self.template = template
        self.update_send_button_state()
    
    def set_smtp_config(self, config: SMTPConfig):
        """
        Set the SMTP configuration for sending.
        
        Args:
            config: SMTPConfig object
        """
        self.smtp_config = config
        self.update_send_button_state()
    
    def load_job_for_resume(self, job: SendJob):
        """
        Load an incomplete job for resuming.
        
        This method is called during crash recovery to restore a job
        that was interrupted. It sets up the send tab with the job's
        configuration and prepares it for resuming.
        
        Args:
            job: SendJob to resume
        
        Validates Requirement: 8.3 (crash recovery)
        """
        # Store the job
        self.current_job = job
        
        # Set configuration from job
        self.smtp_config = job.smtp_config
        self.template = job.template
        self.recipients = job.recipients
        
        # Set throttle and max retries from job
        self.throttle_spinbox.setValue(job.throttle_ms)
        self.max_retries_spinbox.setValue(job.max_retries)
        
        # Calculate statistics from job
        self.sent_count = sum(1 for r in job.recipients if r.status == "SENT")
        self.failed_count = sum(1 for r in job.recipients if r.status == "FAILED")
        self.remaining_count = sum(1 for r in job.recipients if r.status in ("PENDING", "FAILED") and r.attempts < job.max_retries)
        
        # Update progress display
        self.update_progress_display()
        
        # Load send history into log table
        self._load_job_history(job.id)
        
        # Update button states
        self.update_send_button_state()
        
        # Enable start button to allow resuming
        self.start_send_button.setText("Resume Send")
        self.start_send_button.setEnabled(True)
    
    def _load_job_history(self, job_id: str):
        """
        Load send history for a job into the log table.
        
        Args:
            job_id: ID of the job to load history for
        """
        try:
            # Get send history from database
            history = self.database.get_send_history({"job_id": job_id})
            
            # Clear log table
            self.log_table.setRowCount(0)
            
            # Populate log table
            for record in reversed(history):  # Reverse to show oldest first
                self.add_log_entry(
                    email=record['recipient_email'],
                    status=record['status'],
                    error=record.get('error_message', '')
                )
        
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error loading job history: {e}", exc_info=True)
    
    def add_log_entry(self, email: str, status: str, error: str = ""):
        """
        Add an entry to the log table.
        
        This method is used to populate the log table with historical records
        during crash recovery, as well as for adding new entries during sending.
        
        Args:
            email: Recipient email address
            status: Send status (SENT, FAILED, CANCELLED)
            error: Error message if applicable
        """
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        
        # Timestamp - use current time for historical records
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_item = QTableWidgetItem(timestamp)
        self.log_table.setItem(row, 0, timestamp_item)
        
        # Email
        email_item = QTableWidgetItem(email)
        self.log_table.setItem(row, 1, email_item)
        
        # Status
        status_item = QTableWidgetItem(status)
        if status == "SENT":
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        elif status == "FAILED":
            status_item.setForeground(Qt.GlobalColor.red)
        else:  # CANCELLED
            status_item.setForeground(Qt.GlobalColor.gray)
        self.log_table.setItem(row, 2, status_item)
        
        # Error
        error_item = QTableWidgetItem(error)
        self.log_table.setItem(row, 3, error_item)
    
    def update_send_button_state(self):
        """Update the enabled state of send buttons based on configuration."""
        has_all_config = (
            len(self.recipients) > 0 and
            self.template is not None and
            self.smtp_config is not None
        )
        
        self.send_to_self_button.setEnabled(has_all_config)
        self.start_send_button.setEnabled(has_all_config)
    
    def update_recipient_count_display(self):
        """
        Update the recipient count display label.
        
        Shows "X recipients selected for sending" or appropriate message.
        
        Validates Requirements:
        - 5.1: Display selected count vs total count
        """
        count = len(self.recipients)
        
        if count == 0:
            self.recipient_count_label.setText("⚠️ No recipients selected for sending")
            self.recipient_count_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #d9534f; padding: 5px; "
                "background-color: #f2dede; border: 1px solid #ebccd1; border-radius: 4px; }"
            )
        elif count == 1:
            self.recipient_count_label.setText("1 recipient selected for sending")
            self.recipient_count_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #0066cc; padding: 5px; }"
            )
        else:
            self.recipient_count_label.setText(f"{count} recipients selected for sending")
            self.recipient_count_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #0066cc; padding: 5px; }"
            )

    
    def send_to_self(self):
        """
        Send a test email to self using first recipient's data.
        
        Validates Requirements:
        - 11.2: Support "send to self first" verification workflow
        """
        if not self.recipients or not self.template or not self.smtp_config:
            QMessageBox.warning(
                self,
                "Configuration Incomplete",
                "Please configure SMTP, load recipients, and create a template first."
            )
            return
        
        # Use first recipient's data
        test_recipient = self.recipients[0]
        
        # Create a test recipient with user's email but first recipient's data
        test_recipient_copy = Recipient(
            email=self.smtp_config.username,  # Send to self
            fields=test_recipient.fields.copy()
        )
        
        try:
            # Disable button during send
            self.send_to_self_button.setEnabled(False)
            self.send_to_self_button.setText("Sending...")
            
            # Create SMTP manager
            smtp_manager = SMTPManager(self.smtp_config)
            
            # Connect
            smtp_manager.connect()
            
            # Render template
            rendered = self.template_renderer.render(self.template, test_recipient_copy)
            
            # Update template with rendered content
            rendered_template = self.template
            rendered_template.subject = rendered.subject
            rendered_template.html_body = rendered.html_body
            rendered_template.text_body = rendered.text_body
            
            # Send email
            result = smtp_manager.send_email(test_recipient_copy, rendered_template)
            
            # Disconnect
            smtp_manager.disconnect()
            
            if result.success:
                QMessageBox.information(
                    self,
                    "Test Email Sent",
                    f"Test email sent successfully to {self.smtp_config.username}\n\n"
                    f"Please check your inbox to verify the email looks correct before "
                    f"starting the bulk send."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Test Email Failed",
                    f"Failed to send test email:\n\n{result.error_message}"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Email Error",
                f"An error occurred while sending test email:\n\n{str(e)}"
            )
        
        finally:
            # Re-enable button
            self.send_to_self_button.setEnabled(True)
            self.send_to_self_button.setText("Send to Self First")
    
    def start_send(self):
        """
        Start bulk email sending.
        
        Validates Requirements:
        - 4.1: Create send queue with all recipients
        - 4.2: Process send queue in background worker thread
        - 11.1: Support dry run mode
        """
        if not self.recipients or not self.template or not self.smtp_config:
            QMessageBox.warning(
                self,
                "Configuration Incomplete",
                "Please configure SMTP, load recipients, and create a template first."
            )
            return
        
        # Check if no recipients are selected
        if len(self.recipients) == 0:
            QMessageBox.warning(
                self,
                "No Recipients Selected",
                "No recipients are selected for sending.\n\n"
                "Please select at least one recipient in the Recipients tab before starting the send."
            )
            return
        
        # Check if dry run mode
        is_dry_run = self.dry_run_checkbox.isChecked()
        
        if is_dry_run:
            # Dry run mode - validate without sending
            QMessageBox.information(
                self,
                "Dry Run Mode",
                "Dry run mode is enabled. Emails will be validated but not actually sent.\n\n"
                "This feature is not yet fully implemented."
            )
            return
        
        # Confirm before starting
        reply = QMessageBox.question(
            self,
            "Confirm Send",
            f"Are you sure you want to send to {len(self.recipients)} selected recipient(s)?\n\n"
            f"Throttle rate: {self.throttle_spinbox.value()} ms\n"
            f"Max retries: {self.max_retries_spinbox.value()}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Create send job
            self.current_job = self.queue_manager.create_job(
                recipients=self.recipients,
                template=self.template,
                config=self.smtp_config,
                throttle_ms=self.throttle_spinbox.value(),
                max_retries=self.max_retries_spinbox.value()
            )
            
            # Reset statistics
            self.sent_count = 0
            self.failed_count = 0
            self.remaining_count = len(self.current_job.recipients)
            self.start_time = datetime.now()
            
            # Clear log table
            self.log_table.setRowCount(0)
            
            # Hide summary
            self.summary_label.hide()
            
            # Update UI
            self.update_progress_display()
            
            # Create SMTP manager
            smtp_manager = SMTPManager(self.smtp_config)
            
            # Create worker
            self.worker = SendWorker(
                job=self.current_job,
                smtp_manager=smtp_manager,
                queue_manager=self.queue_manager,
                template_renderer=self.template_renderer
            )
            
            # Connect signals
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.email_sent.connect(self.on_email_sent)
            self.worker.job_completed.connect(self.on_job_completed)
            
            # Update button states
            self.start_send_button.setEnabled(False)
            self.send_to_self_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.export_log_button.setEnabled(True)
            
            # Start rate timer
            self.rate_timer.start(1000)  # Update every second
            
            # Start worker
            self.worker.start()
        
        except ValueError as e:
            error_msg = str(e)
            
            # Check if it's an opt-out error
            if "opt-out list" in error_msg.lower():
                # Show custom dialog with option to manage opt-out list
                reply = QMessageBox.critical(
                    self,
                    "Send Error",
                    f"Failed to start send:\n\n{error_msg}\n\n"
                    f"Would you like to open the Opt-Out List Management to remove recipients?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Open opt-out management dialog
                    self.open_optout_management()
            else:
                QMessageBox.critical(
                    self,
                    "Send Error",
                    f"Failed to start send:\n\n{error_msg}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
    
    def pause_send(self):
        """
        Pause sending after current email.
        
        Validates Requirement: 4.7 (pause/resume/stop controls)
        """
        if self.worker:
            self.worker.pause()
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)
    
    def resume_send(self):
        """
        Resume sending from paused state.
        
        Validates Requirement: 4.7 (pause/resume/stop controls)
        """
        if self.worker:
            self.worker.resume()
            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)
    
    def stop_send(self):
        """
        Stop sending and cancel remaining emails.
        
        Validates Requirement: 4.7 (pause/resume/stop controls)
        """
        if self.worker:
            reply = QMessageBox.question(
                self,
                "Confirm Stop",
                "Are you sure you want to stop sending?\n\n"
                "All remaining emails will be cancelled.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.pause_button.setEnabled(False)
                self.resume_button.setEnabled(False)
                self.stop_button.setEnabled(False)
    
    def on_progress_updated(self, sent: int, failed: int, remaining: int):
        """
        Handle progress update from worker.
        
        Validates Requirements:
        - 5.1: Display real-time progress (sent, failed, remaining)
        
        Args:
            sent: Number of emails sent successfully
            failed: Number of emails that failed
            remaining: Number of emails remaining
        """
        self.sent_count = sent
        self.failed_count = failed
        self.remaining_count = remaining
        
        self.update_progress_display()
    
    def on_email_sent(self, email: str, success: bool, error_msg: str):
        """
        Handle email sent notification from worker.
        
        Validates Requirements:
        - 5.3: Log each send attempt with timestamp, recipient, status, error
        
        Args:
            email: Recipient email address
            success: Whether send was successful
            error_msg: Error message if failed
        """
        # Add to log table
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_item = QTableWidgetItem(timestamp)
        self.log_table.setItem(row, 0, timestamp_item)
        
        # Email
        email_item = QTableWidgetItem(email)
        self.log_table.setItem(row, 1, email_item)
        
        # Status
        status = "SUCCESS" if success else "FAILED"
        status_item = QTableWidgetItem(status)
        if success:
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        else:
            status_item.setForeground(Qt.GlobalColor.red)
        self.log_table.setItem(row, 2, status_item)
        
        # Error
        error_item = QTableWidgetItem(error_msg if not success else "")
        self.log_table.setItem(row, 3, error_item)
        
        # Scroll to bottom
        self.log_table.scrollToBottom()
    
    def on_job_completed(self):
        """
        Handle job completion from worker.
        
        Validates Requirements:
        - 5.4: Display summary report on completion
        """
        # Stop rate timer
        self.rate_timer.stop()
        
        # Update button states
        self.start_send_button.setEnabled(True)
        self.send_to_self_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        # Calculate duration
        if self.start_time:
            duration = datetime.now() - self.start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
        else:
            duration_str = "Unknown"
        
        # Calculate success rate
        total = self.sent_count + self.failed_count
        success_rate = (self.sent_count / total * 100) if total > 0 else 0
        
        # Display summary
        summary_text = (
            f"<b>Send Complete!</b><br><br>"
            f"Total: {total}<br>"
            f"Sent: {self.sent_count}<br>"
            f"Failed: {self.failed_count}<br>"
            f"Success Rate: {success_rate:.1f}%<br>"
            f"Duration: {duration_str}"
        )
        
        self.summary_label.setText(summary_text)
        self.summary_label.show()
        
        # Show completion message
        QMessageBox.information(
            self,
            "Send Complete",
            f"Bulk send completed!\n\n"
            f"Sent: {self.sent_count}\n"
            f"Failed: {self.failed_count}\n"
            f"Duration: {duration_str}"
        )
    
    def update_progress_display(self):
        """Update progress bar and status labels."""
        total = self.sent_count + self.failed_count + self.remaining_count
        
        if total > 0:
            progress = int((self.sent_count + self.failed_count) / total * 100)
            self.progress_bar.setValue(progress)
        
        self.sent_label.setText(f"Sent: {self.sent_count}")
        self.failed_label.setText(f"Failed: {self.failed_count}")
        self.remaining_label.setText(f"Remaining: {self.remaining_count}")
    
    def update_rate(self):
        """
        Update sending rate display.
        
        Validates Requirement: 5.2 (display current sending rate)
        """
        if not self.start_time:
            return
        
        # Calculate elapsed time in minutes
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        
        if elapsed > 0:
            # Calculate emails per minute
            emails_sent = self.sent_count + self.failed_count
            rate = emails_sent / elapsed
            self.rate_label.setText(f"Rate: {rate:.1f} emails/min")
    
    def export_log_to_csv(self):
        """
        Export send log to CSV file.
        
        Validates Requirement: 5.5 (allow users to export send log as CSV)
        """
        if self.log_table.rowCount() == 0:
            QMessageBox.information(
                self,
                "No Log Data",
                "There is no log data to export."
            )
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log to CSV",
            f"send_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                headers = []
                for col in range(self.log_table.columnCount()):
                    headers.append(self.log_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write rows
                for row in range(self.log_table.rowCount()):
                    row_data = []
                    for col in range(self.log_table.columnCount()):
                        item = self.log_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Log exported successfully to:\n{file_path}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export log:\n\n{str(e)}"
            )

    
    def open_optout_management(self):
        """
        Open the Opt-Out List Management dialog.
        
        This allows users to view and manage the opt-out list,
        including removing recipients that were accidentally added.
        """
        from ui.dialogs import OptOutListDialog
        
        dialog = OptOutListDialog(self.database, self)
        dialog.exec()
