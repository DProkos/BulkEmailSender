"""
SMTP Settings Tab for Bulk Email Sender Application

This module implements the SMTP configuration interface with input fields,
validation, test connection functionality, and secure credential storage.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QPushButton, QRadioButton, QCheckBox,
    QLabel, QMessageBox, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional
import smtplib
import socket

from models.smtp_config import SMTPConfig
from storage.config_manager import ConfigManager
from storage.credential_store import CredentialStore
from core.validator import Validator
from core.smtp_manager import SMTPManager


class SMTPTab(QWidget):
    """
    SMTP Settings tab widget.
    
    Provides:
    - Input fields for SMTP configuration (host, port, username, password, etc.)
    - Radio buttons for SSL/STARTTLS selection
    - Checkbox for certificate validation
    - Test Connection button
    - Save/Load from config and credential store
    - Validation with error messages
    
    Validates Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.2, 7.3, 9.4, 9.5
    """
    
    # Signal emitted when configuration is successfully saved
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, credential_store: CredentialStore):
        """
        Initialize the SMTP Settings tab.
        
        Args:
            config_manager: Configuration manager for non-sensitive settings
            credential_store: Credential store for secure password storage
        """
        super().__init__()
        self.config_manager = config_manager
        self.credential_store = credential_store
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Server Settings Group
        server_group = self.create_server_settings_group()
        server_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(server_group)
        
        # Authentication Group
        auth_group = self.create_authentication_group()
        auth_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(auth_group)
        
        # Encryption Settings Group
        encryption_group = self.create_encryption_group()
        encryption_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(encryption_group)
        
        # Optional Settings Group
        optional_group = self.create_optional_settings_group()
        optional_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(optional_group)
        
        # Validation Messages
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("QLabel { color: red; }")
        self.validation_label.hide()
        layout.addWidget(self.validation_label)
        
        # Action Buttons
        button_layout = self.create_action_buttons()
        layout.addLayout(button_layout)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_server_settings_group(self) -> QGroupBox:
        """Create the server settings group box."""
        group = QGroupBox("Server Settings")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        # Host input
        host_label = QLabel("Host:*")
        host_label.setMinimumWidth(100)
        self.host_input = QLineEdit()
        self.host_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.host_input.setPlaceholderText("e.g., smtp.gmail.com")
        self.host_input.setToolTip("SMTP server hostname or IP address")
        form_layout.addRow(host_label, self.host_input)
        
        # Port input
        port_label = QLabel("Port:*")
        port_label.setMinimumWidth(100)
        self.port_input = QSpinBox()
        self.port_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(587)
        self.port_input.setToolTip("SMTP server port (587 for STARTTLS, 465 for SSL)")
        form_layout.addRow(port_label, self.port_input)
        
        group.setLayout(form_layout)
        return group
    
    def create_authentication_group(self) -> QGroupBox:
        """Create the authentication settings group box."""
        group = QGroupBox("Authentication")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        # Username input
        username_label = QLabel("Username:*")
        username_label.setMinimumWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.username_input.setPlaceholderText("e.g., user@example.com")
        self.username_input.setToolTip("SMTP authentication username (usually your email address)")
        form_layout.addRow(username_label, self.username_input)
        
        # Password input
        password_label = QLabel("Password:*")
        password_label.setMinimumWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setToolTip("SMTP authentication password (stored securely in OS keyring)")
        form_layout.addRow(password_label, self.password_input)
        
        group.setLayout(form_layout)
        return group
    
    def create_encryption_group(self) -> QGroupBox:
        """Create the encryption settings group box."""
        group = QGroupBox("Encryption")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Radio buttons for SSL/STARTTLS
        self.ssl_radio = QRadioButton("SSL (port 465)")
        self.ssl_radio.setToolTip("Use direct SSL connection (typically port 465)")
        self.ssl_radio.toggled.connect(self.on_encryption_changed)
        
        self.starttls_radio = QRadioButton("STARTTLS (port 587)")
        self.starttls_radio.setToolTip("Use STARTTLS to upgrade connection (typically port 587)")
        self.starttls_radio.setChecked(True)  # Default to STARTTLS
        self.starttls_radio.toggled.connect(self.on_encryption_changed)
        
        # Button group to ensure mutual exclusivity
        self.encryption_group = QButtonGroup()
        self.encryption_group.addButton(self.ssl_radio)
        self.encryption_group.addButton(self.starttls_radio)
        
        layout.addWidget(self.ssl_radio)
        layout.addWidget(self.starttls_radio)
        
        # Certificate validation checkbox
        self.validate_certs_checkbox = QCheckBox("Validate TLS certificates (recommended)")
        self.validate_certs_checkbox.setChecked(True)
        self.validate_certs_checkbox.setToolTip(
            "Verify server TLS certificates for security. "
            "Disable only if you trust the server and have certificate issues."
        )
        layout.addWidget(self.validate_certs_checkbox)
        
        group.setLayout(layout)
        return group
    
    def create_optional_settings_group(self) -> QGroupBox:
        """Create the optional settings group box."""
        group = QGroupBox("Optional Settings")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        # From Name input
        from_name_label = QLabel("From Name:")
        from_name_label.setMinimumWidth(100)
        self.from_name_input = QLineEdit()
        self.from_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.from_name_input.setPlaceholderText("e.g., John Doe")
        self.from_name_input.setToolTip("Display name for the sender (optional)")
        form_layout.addRow(from_name_label, self.from_name_input)
        
        # Reply-To input
        reply_to_label = QLabel("Reply-To:")
        reply_to_label.setMinimumWidth(100)
        self.reply_to_input = QLineEdit()
        self.reply_to_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reply_to_input.setPlaceholderText("e.g., reply@example.com")
        self.reply_to_input.setToolTip("Reply-To email address (optional)")
        form_layout.addRow(reply_to_label, self.reply_to_input)
        
        group.setLayout(form_layout)
        return group
    
    def create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons layout."""
        layout = QHBoxLayout()
        
        # Test Connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.setToolTip("Send a test email to verify SMTP configuration")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        # Save button
        self.save_button = QPushButton("Save Configuration")
        self.save_button.setToolTip("Save SMTP settings")
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button)
        
        layout.addStretch()
        
        # Clear Config button (right side)
        self.clear_button = QPushButton("🗑️ Clear All Settings")
        self.clear_button.setToolTip("Clear all saved settings (SMTP, template, recipients)")
        self.clear_button.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; }"
            "QPushButton:hover { background-color: #c82333; }"
        )
        self.clear_button.clicked.connect(self.clear_all_settings)
        layout.addWidget(self.clear_button)
        
        return layout
    
    def on_encryption_changed(self):
        """Handle encryption method change and update port accordingly."""
        if self.ssl_radio.isChecked():
            # SSL typically uses port 465
            if self.port_input.value() == 587:
                self.port_input.setValue(465)
        elif self.starttls_radio.isChecked():
            # STARTTLS typically uses port 587
            if self.port_input.value() == 465:
                self.port_input.setValue(587)
    
    def validate_inputs(self) -> tuple[bool, list[str], list[str]]:
        """
        Validate all input fields.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate host
        host = self.host_input.text().strip()
        if not host:
            errors.append("Host is required")
        
        # Validate port
        port = self.port_input.value()
        if port < 1 or port > 65535:
            errors.append(f"Port must be between 1 and 65535")
        
        # Validate username
        username = self.username_input.text().strip()
        if not username:
            errors.append("Username is required")
        
        # Validate password
        password = self.password_input.text()
        if not password:
            errors.append("Password is required")
        
        # Validate reply-to email format if provided
        reply_to = self.reply_to_input.text().strip()
        if reply_to and not Validator.validate_email(reply_to):
            errors.append(f"Invalid reply-to email format: {reply_to}")
        
        # Warning for certificate validation disabled
        if not self.validate_certs_checkbox.isChecked():
            warnings.append("TLS certificate validation is disabled - this is insecure")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def show_validation_messages(self, errors: list[str], warnings: list[str]):
        """
        Display validation errors and warnings.
        
        Args:
            errors: List of error messages
            warnings: List of warning messages
        """
        messages = []
        
        if errors:
            messages.append("<b>Errors:</b>")
            for error in errors:
                messages.append(f"• {error}")
        
        if warnings:
            if messages:
                messages.append("")
            messages.append("<b>Warnings:</b>")
            for warning in warnings:
                messages.append(f"• {warning}")
        
        if messages:
            self.validation_label.setText("<br>".join(messages))
            self.validation_label.show()
        else:
            self.validation_label.hide()
    
    def get_smtp_config(self) -> Optional[SMTPConfig]:
        """
        Get SMTP configuration from input fields.
        
        Returns:
            SMTPConfig object if inputs are valid, None otherwise
        """
        is_valid, errors, warnings = self.validate_inputs()
        
        if not is_valid:
            return None
        
        try:
            config = SMTPConfig(
                host=self.host_input.text().strip(),
                port=self.port_input.value(),
                username=self.username_input.text().strip(),
                password=self.password_input.text(),
                use_ssl=self.ssl_radio.isChecked(),
                use_starttls=self.starttls_radio.isChecked(),
                from_name=self.from_name_input.text().strip() or None,
                reply_to=self.reply_to_input.text().strip() or None,
                validate_certs=self.validate_certs_checkbox.isChecked()
            )
            return config
        except ValueError as e:
            errors.append(str(e))
            self.show_validation_messages(errors, warnings)
            return None
    
    def save_config(self):
        """
        Save SMTP configuration to config manager and credential store.
        
        Validates Requirements:
        - 1.7: Persist non-sensitive SMTP configuration in local config files
        - 1.6: Store SMTP password using OS secure credential storage
        - 7.2: Validate all required fields before allowing the user to proceed
        - 7.3: Display clear error messages near the relevant fields
        """
        is_valid, errors, warnings = self.validate_inputs()
        
        if not is_valid:
            self.show_validation_messages(errors, warnings)
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fix the errors before saving."
            )
            return
        
        try:
            # Get configuration
            host = self.host_input.text().strip()
            port = self.port_input.value()
            username = self.username_input.text().strip()
            password = self.password_input.text()
            use_ssl = self.ssl_radio.isChecked()
            use_starttls = self.starttls_radio.isChecked()
            from_name = self.from_name_input.text().strip()
            reply_to = self.reply_to_input.text().strip()
            validate_certs = self.validate_certs_checkbox.isChecked()
            
            # Save non-sensitive config to config manager
            self.config_manager.set_smtp_config(
                host=host,
                port=port,
                username=username,
                use_ssl=use_ssl,
                use_starttls=use_starttls,
                from_name=from_name,
                reply_to=reply_to,
                validate_certs=validate_certs
            )
            self.config_manager.save_config()
            
            # Save password to credential store
            self.credential_store.save_password("smtp", username, password)
            
            # Clear validation messages
            self.validation_label.hide()
            
            # Show success message
            message = "SMTP configuration saved successfully."
            if warnings:
                message += "\n\nWarnings:\n" + "\n".join(f"• {w}" for w in warnings)
            
            QMessageBox.information(
                self,
                "Configuration Saved",
                message
            )
            
            # Emit signal
            self.config_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save configuration: {str(e)}"
            )
    
    def load_config(self):
        """
        Load SMTP configuration from config manager and credential store.
        
        Validates Requirements:
        - 1.7: Persist non-sensitive SMTP configuration in local config files
        - 1.6: Store SMTP password using OS secure credential storage
        """
        try:
            # Load SMTP config from config manager
            smtp_config = self.config_manager.get_smtp_config()
            
            # Populate fields
            self.host_input.setText(smtp_config.get("host", ""))
            self.port_input.setValue(smtp_config.get("port", 587))
            self.username_input.setText(smtp_config.get("username", ""))
            self.from_name_input.setText(smtp_config.get("from_name", ""))
            self.reply_to_input.setText(smtp_config.get("reply_to", ""))
            
            # Set encryption method
            use_ssl = smtp_config.get("use_ssl", False)
            use_starttls = smtp_config.get("use_starttls", True)
            
            if use_ssl:
                self.ssl_radio.setChecked(True)
            else:
                self.starttls_radio.setChecked(True)
            
            # Set certificate validation
            validate_certs = smtp_config.get("validate_certs", True)
            self.validate_certs_checkbox.setChecked(validate_certs)
            
            # Load password from credential store
            username = smtp_config.get("username", "")
            if username:
                password = self.credential_store.get_password("smtp", username)
                if password:
                    self.password_input.setText(password)
            
        except Exception as e:
            # If loading fails, just use empty fields (first run scenario)
            pass
    
    def set_smtp_config(self, config: SMTPConfig):
        """
        Set SMTP configuration from a SMTPConfig object.
        
        This method is used during crash recovery to restore SMTP settings.
        
        Args:
            config: SMTPConfig object to load
        """
        # Populate fields from config object
        self.host_input.setText(config.host)
        self.port_input.setValue(config.port)
        self.username_input.setText(config.username)
        self.password_input.setText(config.password)
        self.from_name_input.setText(config.from_name or "")
        self.reply_to_input.setText(config.reply_to or "")
        
        # Set encryption method
        if config.use_ssl:
            self.ssl_radio.setChecked(True)
        else:
            self.starttls_radio.setChecked(True)
        
        # Set certificate validation
        self.validate_certs_checkbox.setChecked(config.validate_certs)
    
    def test_connection(self):
        """
        Test SMTP connection with current configuration.
        
        Validates Requirements:
        - 1.4: Send a test email to verify SMTP configuration
        - 1.5: Return descriptive authentication error when credentials are invalid
        - 7.3: Display clear error messages
        """
        # Validate inputs first
        is_valid, errors, warnings = self.validate_inputs()
        
        if not is_valid:
            self.show_validation_messages(errors, warnings)
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fix the errors before testing connection."
            )
            return
        
        # Get SMTP config
        config = self.get_smtp_config()
        if not config:
            return
        
        # Show warnings if any
        if warnings:
            self.show_validation_messages([], warnings)
        
        # Disable button during test
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")
        
        try:
            # Create SMTP manager and test connection
            smtp_manager = SMTPManager(config)
            
            # Try to connect
            success = smtp_manager.connect()
            
            if success:
                # Disconnect after successful test
                smtp_manager.disconnect()
                
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to {config.host}:{config.port}\n\n"
                    f"SMTP configuration is valid and ready to use."
                )
                self.validation_label.hide()
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    "Failed to connect to SMTP server. Please check your settings."
                )
        
        except smtplib.SMTPAuthenticationError as e:
            # Authentication error - provide descriptive message
            QMessageBox.critical(
                self,
                "Authentication Failed",
                f"SMTP authentication failed. Please check your username and password.\n\n"
                f"Error: {str(e)}"
            )
        
        except smtplib.SMTPException as e:
            # Other SMTP errors
            QMessageBox.critical(
                self,
                "SMTP Error",
                f"SMTP error occurred:\n\n{str(e)}"
            )
        
        except socket.timeout:
            QMessageBox.critical(
                self,
                "Connection Timeout",
                f"Connection to SMTP server timed out. Please check:\n"
                f"• Your network connection\n"
                f"• The host and port are correct\n"
                f"• Firewall settings"
            )
        
        except socket.error as e:
            QMessageBox.critical(
                self,
                "Network Error",
                f"Network error occurred:\n\n{str(e)}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
        
        finally:
            # Re-enable button
            self.test_button.setEnabled(True)
            self.test_button.setText("Test Connection")

    def clear_all_settings(self):
        """
        Clear all saved settings including SMTP, template, and recipients.
        
        This resets the application to a fresh state.
        """
        from PyQt6.QtWidgets import QMessageBox
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Clear All Settings",
            "This will clear ALL saved settings:\n\n"
            "• SMTP configuration\n"
            "• Saved password\n"
            "• Email template\n"
            "• Company settings\n"
            "• Saved recipients\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Clear SMTP fields in UI
            self.host_input.clear()
            self.port_input.setValue(587)
            self.username_input.clear()
            self.password_input.clear()
            self.from_name_input.clear()
            self.reply_to_input.clear()
            self.starttls_radio.setChecked(True)
            self.validate_certs_checkbox.setChecked(True)
            
            # Clear password from credential store
            old_username = self.config_manager.get("smtp", "username")
            if old_username:
                try:
                    self.credential_store.delete_password("smtp", old_username)
                except:
                    pass
            
            # Reset config to defaults
            self.config_manager.reset_to_defaults()
            self.config_manager.save_config()
            
            # Clear database (recipients, jobs, etc.)
            import os
            from pathlib import Path
            db_path = Path.home() / ".bulk_email_sender" / "data.db"
            if db_path.exists():
                try:
                    os.remove(db_path)
                except:
                    pass
            
            QMessageBox.information(
                self,
                "Settings Cleared",
                "All settings have been cleared.\n\n"
                "Please restart the application for changes to take full effect."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear settings:\n\n{str(e)}"
            )
