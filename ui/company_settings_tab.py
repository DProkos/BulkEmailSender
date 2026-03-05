"""
Company Settings Tab for Bulk Email Sender Application

This module implements the company/business information interface where users
can configure their company details to be used as variables in email templates.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QLabel, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional
import json

from models.company_settings import CompanySettings
from storage.config_manager import ConfigManager


class CompanySettingsTab(QWidget):
    """
    Company Settings tab widget.
    
    Provides:
    - Input fields for company information
    - Save/Load functionality
    - Integration with email templates via {{company.field}} variables
    """
    
    # Signal emitted when settings are saved
    settings_saved = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the Company Settings tab.
        
        Args:
            config_manager: ConfigManager instance for persisting settings
        """
        super().__init__()
        self.config_manager = config_manager
        self.settings: Optional[CompanySettings] = None
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Info label
        info_label = QLabel(
            "Συμπληρώστε τα στοιχεία της επιχείρησής σας. Αυτά θα είναι διαθέσιμα "
            "ως μεταβλητές στα email templates (π.χ. {{company.name}}, {{company.phone}})."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }")
        layout.addWidget(info_label)
        
        # Basic Information Group
        basic_group = self.create_basic_info_group()
        basic_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(basic_group)
        
        # Contact Information Group
        contact_group = self.create_contact_info_group()
        contact_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(contact_group)
        
        # Social Media Group
        social_group = self.create_social_media_group()
        social_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(social_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("💾 Αποθήκευση")
        self.save_button.setToolTip("Αποθήκευση στοιχείων επιχείρησης")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; padding: 10px 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #218838; }"
        )
        button_layout.addWidget(self.save_button)
        
        self.clear_button = QPushButton("🗑️ Καθαρισμός")
        self.clear_button.setToolTip("Καθαρισμός όλων των πεδίων")
        self.clear_button.clicked.connect(self.clear_fields)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Add stretch at the end
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_basic_info_group(self) -> QGroupBox:
        """Create the basic information group box."""
        group = QGroupBox("Βασικές Πληροφορίες")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        name_label = QLabel("Όνομα Επιχείρησης:*")
        name_label.setMinimumWidth(140)
        self.name_input = QLineEdit()
        self.name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_input.setPlaceholderText("π.χ. My Company")
        self.name_input.setToolTip("Όνομα επιχείρησης ({{company.name}})")
        form_layout.addRow(name_label, self.name_input)
        
        address_label = QLabel("Διεύθυνση:")
        address_label.setMinimumWidth(140)
        self.address_input = QLineEdit()
        self.address_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.address_input.setPlaceholderText("π.χ. Οδός Παραδείσου 123")
        self.address_input.setToolTip("Διεύθυνση ({{company.address}})")
        form_layout.addRow(address_label, self.address_input)
        
        city_label = QLabel("Πόλη:")
        city_label.setMinimumWidth(140)
        self.city_input = QLineEdit()
        self.city_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.city_input.setPlaceholderText("π.χ. Κέρκυρα")
        self.city_input.setToolTip("Πόλη ({{company.city}})")
        form_layout.addRow(city_label, self.city_input)
        
        postal_label = QLabel("Τ.Κ.:")
        postal_label.setMinimumWidth(140)
        self.postal_code_input = QLineEdit()
        self.postal_code_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.postal_code_input.setPlaceholderText("π.χ. 49100")
        self.postal_code_input.setToolTip("Ταχυδρομικός Κώδικας ({{company.postal_code}})")
        form_layout.addRow(postal_label, self.postal_code_input)
        
        country_label = QLabel("Χώρα:")
        country_label.setMinimumWidth(140)
        self.country_input = QLineEdit()
        self.country_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.country_input.setPlaceholderText("π.χ. Ελλάδα")
        self.country_input.setToolTip("Χώρα ({{company.country}})")
        form_layout.addRow(country_label, self.country_input)
        
        group.setLayout(form_layout)
        return group
    
    def create_contact_info_group(self) -> QGroupBox:
        """Create the contact information group box."""
        group = QGroupBox("Στοιχεία Επικοινωνίας")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        phone_label = QLabel("Τηλέφωνο:")
        phone_label.setMinimumWidth(140)
        self.phone_input = QLineEdit()
        self.phone_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.phone_input.setPlaceholderText("π.χ. +30 26610 12345")
        self.phone_input.setToolTip("Τηλέφωνο ({{company.phone}})")
        form_layout.addRow(phone_label, self.phone_input)
        
        email_label = QLabel("Email:")
        email_label.setMinimumWidth(140)
        self.email_input = QLineEdit()
        self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.email_input.setPlaceholderText("π.χ. info@mycompany.com")
        self.email_input.setToolTip("Email επιχείρησης ({{company.email}})")
        form_layout.addRow(email_label, self.email_input)
        
        website_label = QLabel("Website:")
        website_label.setMinimumWidth(140)
        self.website_input = QLineEdit()
        self.website_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.website_input.setPlaceholderText("π.χ. https://www.mycompany.com")
        self.website_input.setToolTip("Website ({{company.website}})")
        form_layout.addRow(website_label, self.website_input)
        
        logo_label = QLabel("Logo URL:")
        logo_label.setMinimumWidth(140)
        self.logo_url_input = QLineEdit()
        self.logo_url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.logo_url_input.setPlaceholderText("π.χ. https://www.example.com/logo.png")
        self.logo_url_input.setToolTip("URL λογότυπου ({{company.logo_url}})")
        form_layout.addRow(logo_label, self.logo_url_input)
        
        group.setLayout(form_layout)
        return group
    
    def create_social_media_group(self) -> QGroupBox:
        """Create the social media group box."""
        group = QGroupBox("Social Media (Προαιρετικά)")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        facebook_label = QLabel("Facebook:")
        facebook_label.setMinimumWidth(140)
        self.facebook_input = QLineEdit()
        self.facebook_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.facebook_input.setPlaceholderText("π.χ. https://facebook.com/mycompany")
        self.facebook_input.setToolTip("Facebook page ({{company.facebook}})")
        form_layout.addRow(facebook_label, self.facebook_input)
        
        twitter_label = QLabel("Twitter:")
        twitter_label.setMinimumWidth(140)
        self.twitter_input = QLineEdit()
        self.twitter_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.twitter_input.setPlaceholderText("π.χ. @mycompany")
        self.twitter_input.setToolTip("Twitter handle ({{company.twitter}})")
        form_layout.addRow(twitter_label, self.twitter_input)
        
        linkedin_label = QLabel("LinkedIn:")
        linkedin_label.setMinimumWidth(140)
        self.linkedin_input = QLineEdit()
        self.linkedin_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.linkedin_input.setPlaceholderText("π.χ. https://linkedin.com/company/mycompany")
        self.linkedin_input.setToolTip("LinkedIn page ({{company.linkedin}})")
        form_layout.addRow(linkedin_label, self.linkedin_input)
        
        instagram_label = QLabel("Instagram:")
        instagram_label.setMinimumWidth(140)
        self.instagram_input = QLineEdit()
        self.instagram_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.instagram_input.setPlaceholderText("π.χ. @mycompany")
        self.instagram_input.setToolTip("Instagram handle ({{company.instagram}})")
        form_layout.addRow(instagram_label, self.instagram_input)
        
        group.setLayout(form_layout)
        return group
    
    def save_settings(self):
        """Save company settings to configuration."""
        # Validate required fields
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Απαιτούμενο Πεδίο",
                "Το όνομα της επιχείρησης είναι υποχρεωτικό."
            )
            self.name_input.setFocus()
            return
        
        # Create settings object
        self.settings = CompanySettings(
            name=self.name_input.text().strip(),
            address=self.address_input.text().strip(),
            city=self.city_input.text().strip(),
            postal_code=self.postal_code_input.text().strip(),
            country=self.country_input.text().strip(),
            phone=self.phone_input.text().strip(),
            email=self.email_input.text().strip(),
            website=self.website_input.text().strip(),
            logo_url=self.logo_url_input.text().strip() or None,
            facebook=self.facebook_input.text().strip() or None,
            twitter=self.twitter_input.text().strip() or None,
            linkedin=self.linkedin_input.text().strip() or None,
            instagram=self.instagram_input.text().strip() or None,
        )
        
        # Save to config
        try:
            settings_dict = self.settings.to_dict()
            self.config_manager.set('company_settings', json.dumps(settings_dict))
            
            QMessageBox.information(
                self,
                "Επιτυχία",
                "Τα στοιχεία της επιχείρησης αποθηκεύτηκαν επιτυχώς!\n\n"
                "Μπορείτε τώρα να χρησιμοποιήσετε μεταβλητές όπως {{company.name}}, "
                "{{company.phone}}, κλπ. στα email templates σας."
            )
            
            # Emit signal
            self.settings_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Σφάλμα",
                f"Αποτυχία αποθήκευσης στοιχείων:\n\n{str(e)}"
            )
    
    def load_settings(self):
        """Load company settings from configuration."""
        try:
            settings_json = self.config_manager.get('company_settings')
            if settings_json:
                settings_dict = json.loads(settings_json)
                self.settings = CompanySettings.from_dict(settings_dict)
                
                # Populate fields
                self.name_input.setText(self.settings.name)
                self.address_input.setText(self.settings.address)
                self.city_input.setText(self.settings.city)
                self.postal_code_input.setText(self.settings.postal_code)
                self.country_input.setText(self.settings.country)
                self.phone_input.setText(self.settings.phone)
                self.email_input.setText(self.settings.email)
                self.website_input.setText(self.settings.website)
                self.logo_url_input.setText(self.settings.logo_url or '')
                self.facebook_input.setText(self.settings.facebook or '')
                self.twitter_input.setText(self.settings.twitter or '')
                self.linkedin_input.setText(self.settings.linkedin or '')
                self.instagram_input.setText(self.settings.instagram or '')
        
        except Exception as e:
            # No settings saved yet or error loading
            pass
    
    def clear_fields(self):
        """Clear all input fields."""
        reply = QMessageBox.question(
            self,
            "Επιβεβαίωση",
            "Είστε σίγουροι ότι θέλετε να καθαρίσετε όλα τα πεδία;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.name_input.clear()
            self.address_input.clear()
            self.city_input.clear()
            self.postal_code_input.clear()
            self.country_input.clear()
            self.phone_input.clear()
            self.email_input.clear()
            self.website_input.clear()
            self.logo_url_input.clear()
            self.facebook_input.clear()
            self.twitter_input.clear()
            self.linkedin_input.clear()
            self.instagram_input.clear()
    
    def get_settings(self) -> Optional[CompanySettings]:
        """
        Get current company settings.
        
        Returns:
            CompanySettings object or None if not configured
        """
        return self.settings
