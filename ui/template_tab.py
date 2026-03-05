"""
Template Tab for Bulk Email Sender Application

This module implements the email template editor interface with subject line,
HTML/text body editors, variable insertion, attachments, and preview functionality.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QPushButton, QComboBox, QLabel,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QSizePolicy,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter, QFont
from typing import Optional, List
import os
import re

from models.template import EmailTemplate
from models.recipient import Recipient
from core.template_renderer import TemplateRenderer
from ui.dialogs import PreviewDialog


class HTMLSyntaxHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for HTML in QTextEdit."""
    
    def __init__(self, parent=None):
        """Initialize the syntax highlighter."""
        super().__init__(parent)
        
        # Define formats
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#0000FF"))
        self.tag_format.setFontWeight(QFont.Weight.Bold)
        
        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor("#FF6600"))
        self.variable_format.setFontWeight(QFont.Weight.Bold)
        
        self.attribute_format = QTextCharFormat()
        self.attribute_format.setForeground(QColor("#008000"))
    
    def highlightBlock(self, text):
        """Highlight a block of text."""
        # Highlight HTML tags
        tag_pattern = r'<[^>]+>'
        for match in re.finditer(tag_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.tag_format)
        
        # Highlight variables {{variable}}
        var_pattern = r'\{\{[^}]+\}\}'
        for match in re.finditer(var_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.variable_format)


class TemplateTab(QWidget):
    """
    Template tab widget.
    
    Provides:
    - Subject line input
    - HTML body editor with syntax highlighting
    - Plain text body editor
    - "Insert Variable" dropdown with available fields
    - "Add Attachment" button with file dialog
    - Attachment list display with remove buttons
    - "Preview" button that shows rendered email for selected recipient
    - Missing variable warnings display
    - Unsubscribe link configuration (Excel column or global URL)
    
    Validates Requirements: 3.1, 3.2, 3.3, 3.6, 3.7, 3.8, 6.2, 6.3, 7.2, 7.3
    """
    
    # Signal emitted when template is saved/updated
    template_saved = pyqtSignal()
    
    def __init__(self, config_manager=None):
        """Initialize the Template tab.
        
        Args:
            config_manager: Optional ConfigManager for saving/loading templates
        """
        super().__init__()
        self.config_manager = config_manager
        self.renderer = TemplateRenderer()
        self.attachments: List[str] = []
        self.available_fields: List[str] = []
        self.recipients: List[Recipient] = []
        self.company_settings = None
        
        self.init_ui()
        
        # Load saved template if available
        if self.config_manager:
            self.load_saved_template()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Template Actions Group (Load Template button)
        actions_group = self.create_actions_group()
        actions_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(actions_group)
        
        # Subject Group
        subject_group = self.create_subject_group()
        subject_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(subject_group)
        
        # Body Editors Group - this should expand
        body_group = self.create_body_editors_group()
        body_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(body_group)
        
        # Attachments Group
        attachments_group = self.create_attachments_group()
        attachments_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(attachments_group)
        
        # Unsubscribe Link Group
        unsubscribe_group = self.create_unsubscribe_group()
        unsubscribe_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(unsubscribe_group)
        
        # Validation Messages
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        layout.addWidget(self.validation_label)
        
        # Preview Button
        preview_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview Email")
        self.preview_button.setToolTip("Preview rendered email for a selected recipient")
        self.preview_button.clicked.connect(self.preview_email)
        self.preview_button.setEnabled(False)
        preview_layout.addWidget(self.preview_button)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)
        
        self.setLayout(layout)
    
    def create_actions_group(self) -> QGroupBox:
        """Create the template actions group box."""
        group = QGroupBox("Template Actions")
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Load Template button
        self.load_template_button = QPushButton("Φόρτωση Έτοιμου Template")
        self.load_template_button.setToolTip("Επιλέξτε ένα έτοιμο template για να ξεκινήσετε")
        self.load_template_button.clicked.connect(self.load_predefined_template)
        layout.addWidget(self.load_template_button)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_subject_group(self) -> QGroupBox:
        """Create the subject line group box."""
        group = QGroupBox("Email Subject")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        
        # Subject input with variable insertion
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.subject_input = QLineEdit()
        self.subject_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.subject_input.setPlaceholderText("Enter email subject (use {{variable}} for personalization)")
        self.subject_input.setToolTip("Email subject line - can contain variables like {{name}}")
        self.subject_input.textChanged.connect(self.on_template_changed)
        input_layout.addWidget(self.subject_input)
        
        # Insert variable button for subject
        self.subject_var_combo = QComboBox()
        self.subject_var_combo.setToolTip("Insert a variable into the subject")
        self.subject_var_combo.addItem("Insert Variable...", None)
        self.subject_var_combo.currentIndexChanged.connect(
            lambda: self.insert_variable_to_subject()
        )
        input_layout.addWidget(self.subject_var_combo)
        
        layout.addLayout(input_layout)
        
        group.setLayout(layout)
        return group
    
    def create_body_editors_group(self) -> QGroupBox:
        """Create the body editors group box with button to open editor dialog."""
        group = QGroupBox("Email Body")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)
        
        # Info label
        info_label = QLabel("Click the button below to edit HTML and Plain Text email body.")
        info_label.setStyleSheet("QLabel { color: #aaaaaa; }")
        layout.addWidget(info_label)
        
        # Status labels
        status_layout = QHBoxLayout()
        
        self.html_status_label = QLabel("HTML Body: Not set")
        self.html_status_label.setStyleSheet("QLabel { color: #ff9800; }")
        status_layout.addWidget(self.html_status_label)
        
        status_layout.addSpacing(20)
        
        self.text_status_label = QLabel("Plain Text Body: Not set")
        self.text_status_label.setStyleSheet("QLabel { color: #ff9800; }")
        status_layout.addWidget(self.text_status_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Edit button
        btn_layout = QHBoxLayout()
        self.edit_body_button = QPushButton("📝 Edit Email Body...")
        self.edit_body_button.setToolTip("Open editor for HTML and Plain Text email body")
        self.edit_body_button.setStyleSheet(
            "QPushButton { padding: 12px 24px; font-size: 11pt; font-weight: bold; }"
        )
        self.edit_body_button.clicked.connect(self.open_body_editor)
        btn_layout.addWidget(self.edit_body_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Hidden storage for body content
        self.html_body_content = ""
        self.text_body_content = ""
        
        group.setLayout(layout)
        return group
    
    def open_body_editor(self):
        """Open the email body editor dialog."""
        from ui.dialogs import EmailBodyEditorDialog
        
        dialog = EmailBodyEditorDialog(
            html_body=self.html_body_content,
            text_body=self.text_body_content,
            available_fields=self.available_fields,
            parent=self
        )
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.html_body_content = dialog.get_html_body()
            self.text_body_content = dialog.get_text_body()
            self.update_body_status()
            self.on_template_changed()
    
    def update_body_status(self):
        """Update the status labels for body content."""
        if self.html_body_content.strip():
            length = len(self.html_body_content)
            self.html_status_label.setText(f"HTML Body: ✓ Set ({length} chars)")
            self.html_status_label.setStyleSheet("QLabel { color: #4caf50; }")
        else:
            self.html_status_label.setText("HTML Body: Not set")
            self.html_status_label.setStyleSheet("QLabel { color: #ff9800; }")
        
        if self.text_body_content.strip():
            length = len(self.text_body_content)
            self.text_status_label.setText(f"Plain Text Body: ✓ Set ({length} chars)")
            self.text_status_label.setStyleSheet("QLabel { color: #4caf50; }")
        else:
            self.text_status_label.setText("Plain Text Body: Not set")
            self.text_status_label.setStyleSheet("QLabel { color: #ff9800; }")
    
    def create_attachments_group(self) -> QGroupBox:
        """Create the attachments group box."""
        group = QGroupBox("Attachments")
        layout = QVBoxLayout()
        layout.setSpacing(8)  # Add spacing between elements
        
        # Attachment list
        self.attachments_list = QListWidget()
        self.attachments_list.setToolTip("List of files to attach to emails")
        self.attachments_list.setMaximumHeight(100)
        layout.addWidget(self.attachments_list)
        
        # Attachment size label
        self.attachment_size_label = QLabel("Total size: 0 MB")
        self.attachment_size_label.setStyleSheet("QLabel { color: #666; font-size: 10pt; }")
        layout.addWidget(self.attachment_size_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_attachment_button = QPushButton("Add Attachment")
        self.add_attachment_button.setToolTip("Select a file to attach to all emails")
        self.add_attachment_button.clicked.connect(self.add_attachment)
        button_layout.addWidget(self.add_attachment_button)
        
        self.remove_attachment_button = QPushButton("Remove Selected")
        self.remove_attachment_button.setToolTip("Remove selected attachment from list")
        self.remove_attachment_button.clicked.connect(self.remove_attachment)
        self.remove_attachment_button.setEnabled(False)
        button_layout.addWidget(self.remove_attachment_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect selection change to enable/disable remove button
        self.attachments_list.itemSelectionChanged.connect(self.on_attachment_selection_changed)
        
        group.setLayout(layout)
        return group
    
    def create_unsubscribe_group(self) -> QGroupBox:
        """Create the unsubscribe link configuration group box."""
        group = QGroupBox("Unsubscribe Link Configuration")
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add spacing between elements
        
        # Info label
        info_label = QLabel(
            "Configure the {{unsubscribe_link}} variable. "
            "You can either map it to an Excel column or set a global URL."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(info_label)
        
        # Global URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Global Unsubscribe URL:")
        url_layout.addWidget(url_label)
        
        self.unsubscribe_url_input = QLineEdit()
        self.unsubscribe_url_input.setPlaceholderText("e.g., https://example.com/unsubscribe?email={{email}}")
        self.unsubscribe_url_input.setToolTip(
            "Global unsubscribe URL to use for all recipients. "
            "You can use {{email}} or other variables in the URL."
        )
        url_layout.addWidget(self.unsubscribe_url_input)
        
        layout.addLayout(url_layout)
        
        # Excel column mapping
        column_layout = QHBoxLayout()
        column_label = QLabel("Or map to Excel column:")
        column_layout.addWidget(column_label)
        
        self.unsubscribe_column_combo = QComboBox()
        self.unsubscribe_column_combo.addItem("(Use Global URL)", None)
        self.unsubscribe_column_combo.setToolTip(
            "Select an Excel column that contains unsubscribe links for each recipient"
        )
        column_layout.addWidget(self.unsubscribe_column_combo)
        
        layout.addLayout(column_layout)
        
        group.setLayout(layout)
        return group
    
    def set_available_fields(self, fields: List[str]):
        """
        Set the available fields for variable insertion.
        
        Args:
            fields: List of field names available from recipients
        """
        self.available_fields = fields
        
        # Update all variable combo boxes
        self.update_variable_combos()
    
    def set_recipients(self, recipients: List[Recipient]):
        """
        Set the recipients for validation and preview.
        
        Args:
            recipients: List of Recipient objects
        """
        self.recipients = recipients
        
        # Extract available fields from recipients
        if recipients:
            fields = set(['email'])  # email is always available
            for recipient in recipients:
                fields.update(recipient.fields.keys())
            self.set_available_fields(sorted(fields))
        
        # Enable preview button if we have recipients
        self.preview_button.setEnabled(len(recipients) > 0)
        
        # Validate template if we have content
        self.on_template_changed()
    
    def update_variable_combos(self):
        """Update all variable combo boxes with available fields."""
        # Clear existing items (except the first "Insert Variable..." item)
        for combo in [self.subject_var_combo, self.unsubscribe_column_combo]:
            # Store the first item
            first_item_text = combo.itemText(0)
            first_item_data = combo.itemData(0)
            
            # Clear all items
            combo.clear()
            
            # Re-add first item
            combo.addItem(first_item_text, first_item_data)
            
            # Add available fields
            for field in self.available_fields:
                combo.addItem(field, field)
    
    def insert_variable_to_subject(self):
        """Insert selected variable into subject line."""
        field = self.subject_var_combo.currentData()
        if field:
            # Insert at cursor position
            cursor_pos = self.subject_input.cursorPosition()
            current_text = self.subject_input.text()
            new_text = current_text[:cursor_pos] + f"{{{{{field}}}}}" + current_text[cursor_pos:]
            self.subject_input.setText(new_text)
            
            # Reset combo box
            self.subject_var_combo.setCurrentIndex(0)
    
    def insert_variable_to_html(self):
        """Open body editor - variables are inserted there."""
        self.open_body_editor()
    
    def insert_variable_to_text(self):
        """Open body editor - variables are inserted there."""
        self.open_body_editor()
    
    def add_attachment(self):
        """
        Add an attachment file.
        
        Validates Requirements:
        - 3.7: Allow users to attach files to the email template
        """
        # Open file dialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Attachment Files",
            "",
            "All Files (*)"
        )
        
        if not file_paths:
            return
        
        # Add files to attachments list
        for file_path in file_paths:
            if file_path not in self.attachments:
                self.attachments.append(file_path)
                
                # Add to list widget
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setToolTip(file_path)
                self.attachments_list.addItem(item)
        
        # Calculate total attachment size
        self.check_attachment_size()
    
    def remove_attachment(self):
        """Remove selected attachment from list."""
        selected_items = self.attachments_list.selectedItems()
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            # Remove from attachments list
            if file_path in self.attachments:
                self.attachments.remove(file_path)
            
            # Remove from list widget
            row = self.attachments_list.row(item)
            self.attachments_list.takeItem(row)
        
        # Update attachment size display
        self.update_attachment_size_display()
    
    def on_attachment_selection_changed(self):
        """Handle attachment selection change."""
        has_selection = len(self.attachments_list.selectedItems()) > 0
        self.remove_attachment_button.setEnabled(has_selection)
    
    def check_attachment_size(self):
        """
        Check total attachment size and warn if > 50MB.
        
        Validates Requirement: 10.5 (display memory usage warnings)
        """
        total_size_mb = self.calculate_total_attachment_size()
        
        # Update display
        self.update_attachment_size_display()
        
        # Warn if > 50MB
        if total_size_mb > 50:
            QMessageBox.warning(
                self,
                "Large Attachments",
                f"Total attachment size is {total_size_mb:.1f} MB.\n\n"
                f"Large attachments may cause:\n"
                f"• Slower sending performance\n"
                f"• Higher memory usage\n"
                f"• Emails rejected by recipient servers\n\n"
                f"Consider reducing attachment sizes or using file sharing links instead."
            )
    
    def calculate_total_attachment_size(self) -> float:
        """
        Calculate total size of all attachments in MB.
        
        Returns:
            Total size in megabytes
            
        Validates Requirement: 10.5 (calculate total attachment size)
        """
        total_size = 0
        
        for file_path in self.attachments:
            try:
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            except OSError:
                # If we can't read the file size, skip it
                pass
        
        # Convert to MB
        return total_size / (1024 * 1024)
    
    def update_attachment_size_display(self):
        """
        Update the attachment size label display.
        
        Shows total size and applies warning styling if > 50MB.
        """
        total_size_mb = self.calculate_total_attachment_size()
        
        # Update label text
        self.attachment_size_label.setText(f"Total size: {total_size_mb:.2f} MB")
        
        # Apply warning styling if > 50MB
        if total_size_mb > 50:
            self.attachment_size_label.setStyleSheet(
                "QLabel { color: #d9534f; font-size: 10pt; font-weight: bold; }"
            )
        else:
            self.attachment_size_label.setStyleSheet(
                "QLabel { color: #666; font-size: 10pt; }"
            )
    
    def on_template_changed(self):
        """Handle template content changes and validate."""
        # Validate template if we have recipients
        if self.recipients:
            template = self.get_template()
            if template:
                validation_result = self.renderer.validate_variables(template, self.recipients)
                self.show_validation_messages(validation_result.warnings)
            else:
                self.validation_label.hide()
        else:
            self.validation_label.hide()
        
        # Save template to config
        self.save_template_to_config()
        
        # Emit signal to notify that template has changed
        self.template_saved.emit()
    
    def save_template_to_config(self):
        """Save current template to configuration file."""
        if not self.config_manager:
            return
        
        try:
            self.config_manager.set_template_config(
                subject=self.subject_input.text(),
                html_body=self.html_body_content,
                text_body=self.text_body_content,
                unsubscribe_link=self.unsubscribe_url_input.text(),
                attachments=self.attachments.copy()
            )
            self.config_manager.save_config()
        except Exception as e:
            # Silently fail - don't interrupt user workflow
            pass
    
    def load_saved_template(self):
        """Load saved template from configuration file."""
        if not self.config_manager:
            return
        
        try:
            template_config = self.config_manager.get_template_config()
            if template_config:
                # Load subject
                if template_config.get('subject'):
                    self.subject_input.setText(template_config['subject'])
                
                # Load HTML body
                if template_config.get('html_body'):
                    self.html_body_content = template_config['html_body']
                
                # Load text body
                if template_config.get('text_body'):
                    self.text_body_content = template_config['text_body']
                
                # Update status labels
                self.update_body_status()
                
                # Load unsubscribe link
                if template_config.get('unsubscribe_link'):
                    self.unsubscribe_url_input.setText(template_config['unsubscribe_link'])
                
                # Load attachments (only if files still exist)
                saved_attachments = template_config.get('attachments', [])
                import os
                for attachment_path in saved_attachments:
                    if os.path.exists(attachment_path):
                        self.attachments.append(attachment_path)
                
                # Update attachments display
                if self.attachments:
                    self.update_attachments_list()
        except Exception as e:
            # Silently fail - don't interrupt startup
            pass
    
    def show_validation_messages(self, warnings: List[str]):
        """
        Display validation warnings.
        
        Args:
            warnings: List of warning messages
            
        Validates Requirements:
        - 3.6: Warn the user about missing variables
        - 7.3: Display clear error messages
        """
        if warnings:
            messages = ["<b>Warnings:</b>"]
            for warning in warnings:
                messages.append(f"• {warning}")
            
            self.validation_label.setText("<br>".join(messages))
            self.validation_label.setStyleSheet(
                "QLabel { color: #ffcc00; "
                "border: 1px solid #8b7355; padding: 10px; border-radius: 4px; }"
            )
            self.validation_label.show()
        else:
            self.validation_label.setText("")  # Clear the text
            self.validation_label.hide()
    
    def get_template(self) -> Optional[EmailTemplate]:
        """
        Get the current email template.
        
        Returns:
            EmailTemplate object if valid, None otherwise
            
        Validates Requirements:
        - 3.1: Provide an editor for email subject and body
        - 3.2: Support HTML body content with plain text fallback
        - 3.3: Support template variables in the format {{variable_name}}
        """
        subject = self.subject_input.text().strip()
        html_body = self.html_body_content.strip()
        text_body = self.text_body_content.strip()
        
        # Validate required fields
        if not subject:
            return None
        
        if not html_body and not text_body:
            return None
        
        # If HTML body is provided but text body is not, generate simple text version
        if html_body and not text_body:
            # Simple HTML to text conversion (remove tags)
            text_body = re.sub(r'<[^>]+>', '', html_body)
            text_body = re.sub(r'\s+', ' ', text_body).strip()
        
        # If text body is provided but HTML body is not, wrap text in basic HTML
        if text_body and not html_body:
            html_body = f"<html><body><pre>{text_body}</pre></body></html>"
        
        try:
            # Extract variables from all template parts
            all_vars = set()
            all_vars.update(self.renderer.find_variables(subject))
            all_vars.update(self.renderer.find_variables(html_body))
            all_vars.update(self.renderer.find_variables(text_body))
            
            # Handle unsubscribe link
            unsubscribe_column = self.unsubscribe_column_combo.currentData()
            unsubscribe_url = self.unsubscribe_url_input.text().strip()
            
            # If unsubscribe_link is used in template, we need to handle it
            if 'unsubscribe_link' in all_vars:
                # This will be handled during rendering based on configuration
                pass
            
            template = EmailTemplate(
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                attachments=self.attachments.copy(),
                variables=sorted(all_vars)
            )
            return template
        except ValueError as e:
            return None
    
    def update_attachments_list(self):
        """
        Update the attachments list widget with current attachments.
        
        This method is called during crash recovery to restore the attachments
        display when loading a saved template.
        """
        # Clear existing items
        self.attachments_list.clear()
        
        # Add attachments to list widget
        for file_path in self.attachments:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(file_path)
            self.attachments_list.addItem(item)
        
        # Update attachment size display
        self.update_attachment_size_display()
    
    def set_template(self, template: EmailTemplate):
        """
        Set the email template.
        
        This method is used during crash recovery to restore template.
        
        Args:
            template: EmailTemplate object to load
        """
        # Set subject and body
        self.subject_input.setText(template.subject)
        self.html_body_content = template.html_body
        self.text_body_content = template.text_body
        self.update_body_status()
        
        # Set attachments
        self.attachments = template.attachments.copy()
        self.update_attachments_list()
        
        # Validate template
        self.validate_template()
    
    def preview_email(self):
        """
        Preview rendered email for a selected recipient.
        
        Validates Requirements:
        - 3.8: Provide a preview function that shows how the email will look
        """
        if not self.recipients:
            QMessageBox.warning(
                self,
                "No Recipients",
                "Please load recipients first to preview the email."
            )
            return
        
        # Get template
        template = self.get_template()
        if not template:
            QMessageBox.warning(
                self,
                "Invalid Template",
                "Please enter a subject and at least one body (HTML or plain text)."
            )
            return
        
        # For now, use the first recipient for preview
        # In a more advanced version, we could let the user select which recipient
        recipient = self.recipients[0]
        
        # Handle unsubscribe link if present
        if 'unsubscribe_link' in template.variables:
            unsubscribe_column = self.unsubscribe_column_combo.currentData()
            unsubscribe_url = self.unsubscribe_url_input.text().strip()
            
            if unsubscribe_column and unsubscribe_column in recipient.fields:
                # Use value from Excel column
                recipient.fields['unsubscribe_link'] = recipient.fields[unsubscribe_column]
            elif unsubscribe_url:
                # Use global URL (render it with recipient data first)
                url_template = self.renderer.html_env.from_string(unsubscribe_url)
                context = dict(recipient.fields)
                context['email'] = recipient.email
                rendered_url = url_template.render(**context)
                recipient.fields['unsubscribe_link'] = rendered_url
            else:
                # No unsubscribe link configured
                recipient.fields['unsubscribe_link'] = ''
        
        try:
            # Generate preview
            preview_html = self.renderer.preview(template, recipient)
            
            # Show preview dialog
            dialog = PreviewDialog(preview_html, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to generate preview:\n\n{str(e)}"
            )
    
    def validate_template(self) -> tuple[bool, List[str], List[str]]:
        """
        Validate the template.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
            
        Validates Requirement: 7.2 (validate all required fields)
        """
        errors = []
        warnings = []
        
        # Check subject
        subject = self.subject_input.text().strip()
        if not subject:
            errors.append("Email subject is required")
        
        # Check body
        html_body = self.html_body_content.strip()
        text_body = self.text_body_content.strip()
        
        if not html_body and not text_body:
            errors.append("At least one email body (HTML or plain text) is required")
        
        # Check attachments exist
        missing_attachments = []
        for file_path in self.attachments:
            if not os.path.exists(file_path):
                missing_attachments.append(os.path.basename(file_path))
        
        if missing_attachments:
            errors.append(
                f"The following attachments are missing: {', '.join(missing_attachments)}"
            )
        
        # Check for missing variables if we have recipients
        if self.recipients:
            template = self.get_template()
            if template:
                validation_result = self.renderer.validate_variables(template, self.recipients)
                warnings.extend(validation_result.warnings)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def has_template(self) -> bool:
        """
        Check if a valid template has been created.
        
        Returns:
            True if template is valid, False otherwise
        """
        template = self.get_template()
        return template is not None
    
    def get_unsubscribe_config(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get unsubscribe link configuration.
        
        Returns:
            Tuple of (column_name, global_url)
        """
        column = self.unsubscribe_column_combo.currentData()
        url = self.unsubscribe_url_input.text().strip() or None
        return column, url
    
    def set_company_settings(self, company_settings):
        """
        Set company settings for template rendering.
        
        Args:
            company_settings: CompanySettings object
        """
        self.company_settings = company_settings
        
        # Update renderer with company settings
        if company_settings:
            self.renderer.set_company_settings(company_settings)
    
    def load_predefined_template(self):
        """
        Open dialog to select and load a predefined template.
        """
        from ui.dialogs import TemplateSelectionDialog
        
        dialog = TemplateSelectionDialog(self)
        
        if dialog.exec() == TemplateSelectionDialog.DialogCode.Accepted:
            selected = dialog.get_selected_template()
            
            if selected:
                # Load template into editors
                self.subject_input.setText(selected['subject'])
                self.html_body_content = selected['html_body']
                self.text_body_content = selected['text_body']
                self.update_body_status()
                
                # Trigger validation
                self.on_template_changed()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Template Loaded",
                    f"Το template '{selected['name']}' φορτώθηκε επιτυχώς!\n\n"
                    f"Μπορείτε τώρα να το προσαρμόσετε σύμφωνα με τις ανάγκες σας."
                )
