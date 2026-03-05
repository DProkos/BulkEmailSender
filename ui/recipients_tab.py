"""
Recipients Tab for Bulk Email Sender Application

This module implements the recipient import interface with Excel file selection,
column mapping, validation, and preview functionality.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QProgressDialog, QHeaderView, QDialog,
    QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Optional, List, Dict, Set
import pandas as pd

from core.excel_importer import ExcelImporter
from models.recipient import Recipient
from models.validation_result import ValidationResult


class RecipientMapperThread(QThread):
    """
    Background thread for mapping Excel columns to recipients.
    
    This thread handles the potentially slow process of creating
    Recipient objects from DataFrame rows, especially for large files.
    
    Validates Requirements:
    - 10.1: Support at least 10,000 recipients without UI freeze
    - 10.2: Use background processing to keep UI responsive
    """
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)  # Status message
    mapping_completed = pyqtSignal(list, object)  # recipients, validation_result
    mapping_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, df: pd.DataFrame, mapping: Dict[str, str], importer: ExcelImporter):
        """
        Initialize the mapper thread.
        
        Args:
            df: pandas DataFrame containing Excel data
            mapping: Column mapping dictionary
            importer: ExcelImporter instance
        """
        super().__init__()
        self.df = df
        self.mapping = mapping
        self.importer = importer
        self._is_cancelled = False
    
    def cancel(self):
        """Request cancellation of the mapping operation."""
        self._is_cancelled = True
    
    def run(self):
        """
        Map columns and create recipients in background.
        
        This method runs in a separate thread to keep the UI responsive
        when processing large Excel files.
        """
        try:
            # Phase 1: Mapping columns (0-50%)
            self.status_updated.emit("Mapping Excel columns to recipient fields...")
            self.progress_updated.emit(10)
            
            if self._is_cancelled:
                return
            
            # Map columns to recipients
            recipients = self.importer.map_columns(self.df, self.mapping)
            
            self.progress_updated.emit(50)
            
            if self._is_cancelled:
                return
            
            # Check if any recipients were loaded
            if not recipients:
                self.mapping_failed.emit(
                    "No valid recipients found in the Excel file.\n\n"
                    "Please ensure the email column contains valid email addresses."
                )
                return
            
            # Phase 2: Validating recipients (50-100%)
            self.status_updated.emit(f"Validating {len(recipients):,} recipients...")
            self.progress_updated.emit(70)
            
            if self._is_cancelled:
                return
            
            # Validate recipients
            validation_result = self.importer.validate_recipients(recipients)
            
            self.progress_updated.emit(90)
            
            if self._is_cancelled:
                return
            
            self.status_updated.emit("Validation complete")
            self.progress_updated.emit(100)
            
            # Emit completion signal
            self.mapping_completed.emit(recipients, validation_result)
            
        except ValueError as e:
            self.mapping_failed.emit(f"Mapping error:\n\n{str(e)}")
        except Exception as e:
            self.mapping_failed.emit(f"An unexpected error occurred:\n\n{str(e)}")


class ExcelParserThread(QThread):
    """
    Background thread for parsing Excel files.
    
    Emits signals for progress updates and completion.
    Provides detailed progress feedback for large files (10,000+ rows).
    
    Validates Requirements:
    - 10.1: Support at least 10,000 recipients without UI freeze
    - 10.2: Use background processing to keep UI responsive
    """
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)  # Status message
    parsing_completed = pyqtSignal(pd.DataFrame)  # Parsed DataFrame
    parsing_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, filepath: str, importer: ExcelImporter):
        """
        Initialize the parser thread.
        
        Args:
            filepath: Path to the Excel file
            importer: ExcelImporter instance
        """
        super().__init__()
        self.filepath = filepath
        self.importer = importer
        self._is_cancelled = False
    
    def cancel(self):
        """Request cancellation of the parsing operation."""
        self._is_cancelled = True
    
    def run(self):
        """
        Parse the Excel file in background with detailed progress updates.
        
        This method runs in a separate thread to keep the UI responsive
        when processing large Excel files (10,000+ recipients).
        """
        try:
            # Phase 1: Opening file (0-20%)
            self.status_updated.emit("Opening Excel file...")
            self.progress_updated.emit(5)
            
            if self._is_cancelled:
                return
            
            # Load the Excel file
            # For large files, pandas may take some time to read
            df = self.importer.load_file(self.filepath)
            
            self.progress_updated.emit(20)
            
            if self._is_cancelled:
                return
            
            # Phase 2: Analyzing data (20-40%)
            row_count = len(df)
            col_count = len(df.columns)
            self.status_updated.emit(f"Analyzing data: {row_count:,} rows, {col_count} columns...")
            self.progress_updated.emit(30)
            
            if self._is_cancelled:
                return
            
            # Phase 3: Processing rows (40-80%)
            # For large files, provide more granular progress updates
            if row_count > 1000:
                self.status_updated.emit(f"Processing {row_count:,} rows...")
                
                # Simulate processing in chunks for progress feedback
                # In reality, pandas has already loaded the data, but we provide
                # visual feedback for user experience
                chunk_size = max(1000, row_count // 10)
                for i in range(0, row_count, chunk_size):
                    if self._is_cancelled:
                        return
                    
                    progress = 40 + int((i / row_count) * 40)
                    self.progress_updated.emit(progress)
                    
                    # Small delay to allow UI updates and cancellation checks
                    self.msleep(10)
            else:
                self.status_updated.emit("Processing rows...")
                self.progress_updated.emit(60)
            
            if self._is_cancelled:
                return
            
            # Phase 4: Finalizing (80-100%)
            self.status_updated.emit("Finalizing...")
            self.progress_updated.emit(90)
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(100)
            self.status_updated.emit(f"Successfully loaded {row_count:,} rows")
            
            # Emit completion signal
            self.parsing_completed.emit(df)
            
        except FileNotFoundError as e:
            self.parsing_failed.emit(f"File not found: {str(e)}")
        except PermissionError as e:
            self.parsing_failed.emit(f"Permission denied: {str(e)}\n\nPlease ensure the file is not open in another application.")
        except Exception as e:
            # Provide detailed error message
            error_msg = str(e)
            if "not a valid Excel file" in error_msg.lower() or "unsupported format" in error_msg.lower():
                self.parsing_failed.emit(f"Invalid Excel file format.\n\nPlease ensure the file is a valid .xlsx file.")
            else:
                self.parsing_failed.emit(f"Failed to parse Excel file:\n\n{error_msg}")


class RecipientsTab(QWidget):
    """
    Recipients tab widget.
    
    Provides:
    - "Select Excel File" button with file dialog
    - Column mapping interface (dropdowns for email, name, company, custom fields)
    - Recipient preview table (first 100 rows)
    - Validation status display (valid count, duplicate count, invalid count)
    - Background Excel parsing with progress bar
    - "Remove Duplicates" button
    
    Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 7.2, 7.3, 10.1, 10.2
    """
    
    # Signal emitted when recipients are loaded
    recipients_loaded = pyqtSignal()
    
    # Signal emitted when recipient selection changes
    selection_changed = pyqtSignal()
    
    def __init__(self, database=None):
        """Initialize the Recipients tab.
        
        Args:
            database: Optional Database instance for persisting recipients
        """
        super().__init__()
        print("RECIPIENTS_TAB VERSION 2.0 - Form Layout Global Fix Applied")
        self.database = database
        self.importer = ExcelImporter()
        self.df: Optional[pd.DataFrame] = None
        self.recipients: List[Recipient] = []
        self.excel_columns: List[str] = []
        self.parser_thread: Optional[ExcelParserThread] = None
        self.mapper_thread: Optional[RecipientMapperThread] = None
        
        # Selection state tracking
        # Maps recipient email to selection state (True = selected, False = not selected)
        self.selection_state: Dict[str, bool] = {}
        self.header_checkbox: Optional[QCheckBox] = None
        
        self.init_ui()
        
        # Load saved recipients from database if available
        if self.database:
            self.load_saved_recipients_from_db()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main scroll area to handle small window sizes
        from PyQt6.QtWidgets import QScrollArea
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # File Selection Group
        file_group = self.create_file_selection_group()
        layout.addWidget(file_group)
        
        # Column Mapping Group (full width like Company Settings)
        self.mapping_group = self.create_column_mapping_group()
        self.mapping_group.setEnabled(False)  # Disabled until file is loaded
        self.mapping_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.mapping_group)
        
        # Validation Status Group
        self.validation_group = self.create_validation_status_group()
        self.validation_group.setEnabled(False)  # Disabled until recipients are loaded
        layout.addWidget(self.validation_group)
        
        # Preview Table Group
        self.preview_group = self.create_preview_table_group()
        self.preview_group.setEnabled(False)  # Disabled until recipients are loaded
        layout.addWidget(self.preview_group)
        
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        
        # Main layout with scroll area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def create_file_selection_group(self) -> QGroupBox:
        """Create the file selection group box."""
        group = QGroupBox("Excel File")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Row 1: File path label (full width)
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.file_path_label)
        
        # Row 2: Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        # Select file button
        self.select_file_button = QPushButton("Select Excel File")
        self.select_file_button.setToolTip("Select an .xlsx file containing recipient data")
        self.select_file_button.clicked.connect(self.select_excel_file)
        btn_row.addWidget(self.select_file_button)
        
        # Add Email Manually button
        self.add_email_button = QPushButton("Add Email Manually")
        self.add_email_button.setToolTip("Manually add a single email recipient")
        self.add_email_button.clicked.connect(self.add_email_manually)
        btn_row.addWidget(self.add_email_button)
        
        # Add Multiple Emails button
        self.add_multiple_emails_button = QPushButton("Add Multiple Emails")
        self.add_multiple_emails_button.setToolTip("Paste multiple email addresses or CSV data")
        self.add_multiple_emails_button.clicked.connect(self.add_multiple_emails)
        btn_row.addWidget(self.add_multiple_emails_button)
        
        btn_row.addStretch()
        
        layout.addLayout(btn_row)
        
        group.setLayout(layout)
        return group
    
    def create_column_mapping_group(self) -> QGroupBox:
        """Create the column mapping group box."""
        group = QGroupBox("Column Mapping")
        form_layout = QFormLayout()
        
        # Configure form layout for proper alignment and responsiveness
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setContentsMargins(12, 10, 12, 12)
        
        # Email column mapping (required)
        email_label = QLabel("Email Column:*")
        email_label.setMinimumWidth(120)
        self.email_combo = QComboBox()
        self.email_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.email_combo.setToolTip("Select the column containing email addresses (required)")
        self.email_combo.currentIndexChanged.connect(self.on_mapping_changed)
        form_layout.addRow(email_label, self.email_combo)
        
        # Name column mapping (optional)
        name_label = QLabel("Name Column:")
        name_label.setMinimumWidth(120)
        self.name_combo = QComboBox()
        self.name_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_combo.addItem("(None)", None)
        self.name_combo.setToolTip("Select the column containing recipient names (optional)")
        self.name_combo.currentIndexChanged.connect(self.on_mapping_changed)
        form_layout.addRow(name_label, self.name_combo)
        
        # Company column mapping (optional)
        company_label = QLabel("Company Column:")
        company_label.setMinimumWidth(120)
        self.company_combo = QComboBox()
        self.company_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.company_combo.addItem("(None)", None)
        self.company_combo.setToolTip("Select the column containing company names (optional)")
        self.company_combo.currentIndexChanged.connect(self.on_mapping_changed)
        form_layout.addRow(company_label, self.company_combo)
        
        # Custom fields info label
        self.custom_fields_label = QLabel(
            "Note: All unmapped columns will be available as custom fields in templates."
        )
        self.custom_fields_label.setWordWrap(True)
        self.custom_fields_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        form_layout.addRow("", self.custom_fields_label)
        
        # Load recipients button (aligned to the right like Save button in Company Settings)
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.load_recipients_button = QPushButton("Load Recipients")
        self.load_recipients_button.setToolTip("Load recipients with the current column mapping")
        self.load_recipients_button.clicked.connect(self.load_recipients)
        button_row.addWidget(self.load_recipients_button)
        form_layout.addRow("", button_row)
        
        group.setLayout(form_layout)
        return group
    
    def create_validation_status_group(self) -> QGroupBox:
        """Create the validation status group box."""
        group = QGroupBox("Validation Status")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Status labels
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)
        
        self.total_label = QLabel("Total: 0")
        self.total_label.setStyleSheet("QLabel { font-weight: bold; }")
        status_layout.addWidget(self.total_label)
        
        self.valid_label = QLabel("Valid: 0")
        self.valid_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        status_layout.addWidget(self.valid_label)
        
        self.duplicate_label = QLabel("Duplicates: 0")
        self.duplicate_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        status_layout.addWidget(self.duplicate_label)
        
        self.invalid_label = QLabel("Invalid: 0")
        self.invalid_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        status_layout.addWidget(self.invalid_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Validation messages
        self.validation_messages_label = QLabel()
        self.validation_messages_label.setWordWrap(True)
        self.validation_messages_label.hide()
        layout.addWidget(self.validation_messages_label)
        
        # Remove duplicates button
        self.remove_duplicates_button = QPushButton("Remove Duplicates")
        self.remove_duplicates_button.setToolTip("Remove duplicate email addresses, keeping first occurrence")
        self.remove_duplicates_button.clicked.connect(self.remove_duplicates)
        self.remove_duplicates_button.setEnabled(False)
        layout.addWidget(self.remove_duplicates_button)
        
        group.setLayout(layout)
        return group
    
    def create_preview_table_group(self) -> QGroupBox:
        """Create the preview table group box."""
        group = QGroupBox("Recipient Preview (First 100 Rows)")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        
        # Selection info and controls row
        selection_row = QHBoxLayout()
        selection_row.setSpacing(8)
        
        # Select All checkbox
        self.header_checkbox = QCheckBox("Select All")
        self.header_checkbox.setTristate(True)  # Enable partial state
        self.header_checkbox.setToolTip("Select All / Deselect All recipients")
        self.header_checkbox.stateChanged.connect(self.on_header_checkbox_changed)
        selection_row.addWidget(self.header_checkbox)
        
        # Selection info label
        self.selection_info_label = QLabel("0 of 0 recipients selected")
        self.selection_info_label.setStyleSheet("QLabel { font-weight: bold; color: #0066cc; }")
        selection_row.addWidget(self.selection_info_label)
        
        selection_row.addStretch()
        
        # Selection management buttons
        self.select_by_criteria_button = QPushButton("Select by Criteria")
        self.select_by_criteria_button.setToolTip("Select recipients based on field criteria")
        self.select_by_criteria_button.clicked.connect(self.select_by_criteria)
        selection_row.addWidget(self.select_by_criteria_button)
        
        self.invert_selection_button = QPushButton("Invert Selection")
        self.invert_selection_button.setToolTip("Invert the current selection")
        self.invert_selection_button.clicked.connect(self.invert_selection)
        selection_row.addWidget(self.invert_selection_button)
        
        self.clear_selection_button = QPushButton("Clear Selection")
        self.clear_selection_button.setToolTip("Deselect all recipients")
        self.clear_selection_button.clicked.connect(self.clear_selection)
        selection_row.addWidget(self.clear_selection_button)
        
        layout.addLayout(selection_row)
        
        # Preview table - make it expand to fill available space
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_table.setMinimumHeight(200)
        
        # Connect cell changed signal to handle checkbox clicks
        self.preview_table.cellChanged.connect(self.on_cell_changed)
        
        layout.addWidget(self.preview_table)
        
        group.setLayout(layout)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return group
    
    def select_excel_file(self):
        """
        Open file dialog to select Excel file.
        
        Uses background thread for parsing to keep UI responsive with large files.
        
        Validates Requirements:
        - 2.1: Parse .xlsx file and extract column headers
        - 10.1: Support at least 10,000 recipients without UI freeze
        - 10.2: Use background processing for large Excel files
        """
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Update file path label
        self.file_path_label.setText(file_path)
        
        # Create progress dialog with status label
        progress_dialog = QProgressDialog(
            "Preparing to parse Excel file...",
            "Cancel",
            0,
            100,
            self
        )
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setWindowTitle("Loading Excel File")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setMinimumWidth(400)
        progress_dialog.setValue(0)
        
        # Create and start parser thread
        self.parser_thread = ExcelParserThread(file_path, self.importer)
        
        # Connect signals
        self.parser_thread.progress_updated.connect(progress_dialog.setValue)
        self.parser_thread.status_updated.connect(progress_dialog.setLabelText)
        self.parser_thread.parsing_completed.connect(
            lambda df: self.on_parsing_completed(df, progress_dialog)
        )
        self.parser_thread.parsing_failed.connect(
            lambda error: self.on_parsing_failed(error, progress_dialog)
        )
        
        # Handle cancel - properly stop the thread
        def on_cancel():
            progress_dialog.setLabelText("Cancelling...")
            self.parser_thread.cancel()
            # Give thread a moment to finish
            self.parser_thread.wait(1000)
            if self.parser_thread.isRunning():
                self.parser_thread.terminate()
                self.parser_thread.wait()
        
        progress_dialog.canceled.connect(on_cancel)
        
        # Start parsing
        self.parser_thread.start()
    
    def on_parsing_completed(self, df: pd.DataFrame, progress_dialog: QProgressDialog):
        """
        Handle successful Excel parsing.
        
        Args:
            df: Parsed DataFrame
            progress_dialog: Progress dialog to close
        """
        # Close progress dialog
        progress_dialog.close()
        
        # Store DataFrame
        self.df = df
        
        # Extract column headers
        self.excel_columns = self.importer.get_columns(df)
        
        # Populate column mapping dropdowns
        self.populate_column_dropdowns()
        
        # Enable column mapping group
        self.mapping_group.setEnabled(True)
        
        # Show success message
        QMessageBox.information(
            self,
            "File Loaded",
            f"Successfully loaded Excel file with {len(df)} rows and {len(self.excel_columns)} columns."
        )
    
    def on_parsing_failed(self, error: str, progress_dialog: QProgressDialog):
        """
        Handle Excel parsing failure.
        
        Args:
            error: Error message
            progress_dialog: Progress dialog to close
        """
        # Close progress dialog
        progress_dialog.close()
        
        # Show error message
        QMessageBox.critical(
            self,
            "File Load Error",
            f"Failed to load Excel file:\n\n{error}\n\n"
            f"Please ensure the file is a valid .xlsx file and is not open in another application."
        )
    
    def populate_column_dropdowns(self):
        """Populate column mapping dropdowns with Excel column headers."""
        # Clear existing items
        self.email_combo.clear()
        self.name_combo.clear()
        self.company_combo.clear()
        
        # Add "(None)" option for optional fields
        self.name_combo.addItem("(None)", None)
        self.company_combo.addItem("(None)", None)
        
        # Add column headers to dropdowns
        for column in self.excel_columns:
            self.email_combo.addItem(column, column)
            self.name_combo.addItem(column, column)
            self.company_combo.addItem(column, column)
        
        # Try to auto-detect common column names
        self.auto_detect_columns()
        
        # Trigger mapping changed to update button state
        self.on_mapping_changed()
    
    def auto_detect_columns(self):
        """Auto-detect common column names for email, name, and company."""
        # Common email column names
        email_patterns = ['email', 'e-mail', 'mail', 'email address', 'e-mail address']
        for i, column in enumerate(self.excel_columns):
            if column.lower() in email_patterns:
                self.email_combo.setCurrentIndex(i)
                break
        
        # Common name column names
        name_patterns = ['name', 'full name', 'fullname', 'recipient', 'contact']
        for i, column in enumerate(self.excel_columns):
            if column.lower() in name_patterns:
                # +1 because of "(None)" option
                self.name_combo.setCurrentIndex(i + 1)
                break
        
        # Common company column names
        company_patterns = ['company', 'organization', 'organisation', 'business']
        for i, column in enumerate(self.excel_columns):
            if column.lower() in company_patterns:
                # +1 because of "(None)" option
                self.company_combo.setCurrentIndex(i + 1)
                break
    
    def on_mapping_changed(self):
        """Handle column mapping changes."""
        # Enable load button only if email column is selected
        email_column = self.email_combo.currentData()
        self.load_recipients_button.setEnabled(email_column is not None)
    
    def load_recipients(self):
        """
        Load recipients with current column mapping.
        
        Uses background thread for mapping and validation to keep UI responsive.
        
        Validates Requirements:
        - 2.2: Map Excel columns to recipient fields
        - 2.3: Validate email addresses
        - 2.4: Detect duplicates
        - 2.5: Display preview of recipient list
        - 2.6: Reject import if email column not mapped or contains empty values
        - 10.1: Support at least 10,000 recipients without UI freeze
        - 10.2: Use background processing to keep UI responsive
        """
        if self.df is None:
            QMessageBox.warning(
                self,
                "No File Loaded",
                "Please select an Excel file first."
            )
            return
        
        # Get column mapping
        email_column = self.email_combo.currentData()
        name_column = self.name_combo.currentData()
        company_column = self.company_combo.currentData()
        
        # Validate email column is selected
        if not email_column:
            QMessageBox.warning(
                self,
                "Email Column Required",
                "Please select the email column before loading recipients."
            )
            return
        
        # Build mapping dictionary
        mapping = {'email': email_column}
        if name_column:
            mapping['name'] = name_column
        if company_column:
            mapping['company'] = company_column
        
        # Create progress dialog
        progress_dialog = QProgressDialog(
            "Preparing to load recipients...",
            "Cancel",
            0,
            100,
            self
        )
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setWindowTitle("Loading Recipients")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setMinimumWidth(400)
        progress_dialog.setValue(0)
        
        # Create and start mapper thread
        self.mapper_thread = RecipientMapperThread(self.df, mapping, self.importer)
        
        # Connect signals
        self.mapper_thread.progress_updated.connect(progress_dialog.setValue)
        self.mapper_thread.status_updated.connect(progress_dialog.setLabelText)
        self.mapper_thread.mapping_completed.connect(
            lambda recipients, validation_result: self.on_mapping_completed(
                recipients, validation_result, progress_dialog
            )
        )
        self.mapper_thread.mapping_failed.connect(
            lambda error: self.on_mapping_failed(error, progress_dialog)
        )
        
        # Handle cancel - properly stop the thread
        def on_cancel():
            progress_dialog.setLabelText("Cancelling...")
            self.mapper_thread.cancel()
            # Give thread a moment to finish
            self.mapper_thread.wait(1000)
            if self.mapper_thread.isRunning():
                self.mapper_thread.terminate()
                self.mapper_thread.wait()
        
        progress_dialog.canceled.connect(on_cancel)
        
        # Start mapping
        self.mapper_thread.start()
    
    def on_mapping_completed(self, recipients: List[Recipient], 
                            validation_result: ValidationResult,
                            progress_dialog: QProgressDialog):
        """
        Handle successful recipient mapping.
        
        Args:
            recipients: List of mapped recipients
            validation_result: Validation result
            progress_dialog: Progress dialog to close
        """
        # Close progress dialog
        progress_dialog.close()
        
        # Store recipients
        self.recipients = recipients
        
        # Initialize selection state for new recipients (all selected by default)
        for recipient in self.recipients:
            if recipient.email not in self.selection_state:
                self.selection_state[recipient.email] = True
        
        # Update validation status display
        self.update_validation_status(validation_result)
        
        # Update preview table
        self.update_preview_table()
        
        # Enable validation and preview groups
        self.validation_group.setEnabled(True)
        self.preview_group.setEnabled(True)
        
        # Show validation messages if any
        if validation_result.errors or validation_result.warnings:
            self.show_validation_messages(validation_result)
        
        # Emit signal that recipients are loaded
        self.recipients_loaded.emit()
    
    def on_mapping_failed(self, error: str, progress_dialog: QProgressDialog):
        """
        Handle recipient mapping failure.
        
        Args:
            error: Error message
            progress_dialog: Progress dialog to close
        """
        # Close progress dialog
        progress_dialog.close()
        
        # Show error message
        QMessageBox.critical(
            self,
            "Load Error",
            error
        )
    
    def update_validation_status(self, validation_result: ValidationResult):
        """
        Update validation status display.
        
        Args:
            validation_result: Validation result from ExcelImporter
            
        Validates Requirements:
        - 2.3: Display validation status
        - 2.4: Display duplicate count
        """
        # Count statistics
        total_count = len(self.recipients)
        
        # Count invalid emails
        invalid_count = 0
        for recipient in self.recipients:
            from core.validator import Validator
            if not Validator.validate_email(recipient.email):
                invalid_count += 1
        
        # Count duplicates by checking for repeated emails
        email_counts = {}
        for recipient in self.recipients:
            email = recipient.email
            email_counts[email] = email_counts.get(email, 0) + 1
        
        # Duplicate count is the number of extra occurrences (total - unique)
        duplicate_count = sum(count - 1 for count in email_counts.values() if count > 1)
        
        # Calculate valid count (unique valid emails)
        unique_valid_count = len([email for email, count in email_counts.items() 
                                  if Validator.validate_email(email)])
        
        # Update labels
        self.total_label.setText(f"Total: {total_count}")
        self.valid_label.setText(f"Valid: {unique_valid_count}")
        self.duplicate_label.setText(f"Duplicates: {duplicate_count}")
        self.invalid_label.setText(f"Invalid: {invalid_count}")
        
        # Enable remove duplicates button if there are duplicates
        self.remove_duplicates_button.setEnabled(duplicate_count > 0)
    
    def show_validation_messages(self, validation_result: ValidationResult):
        """
        Display validation errors and warnings.
        
        Args:
            validation_result: Validation result with errors and warnings
        """
        messages = []
        
        if validation_result.errors:
            messages.append("<b>Errors:</b>")
            for error in validation_result.errors:
                messages.append(f"• {error}")
        
        if validation_result.warnings:
            if messages:
                messages.append("")
            messages.append("<b>Warnings:</b>")
            for warning in validation_result.warnings:
                messages.append(f"• {warning}")
        
        if messages:
            self.validation_messages_label.setText("<br>".join(messages))
            self.validation_messages_label.setStyleSheet(
                "QLabel { color: #d9534f; background-color: #f2dede; "
                "border: 1px solid #ebccd1; padding: 10px; border-radius: 4px; }"
            )
            self.validation_messages_label.show()
        else:
            self.validation_messages_label.hide()
    
    def update_preview_table(self):
        """
        Update preview table with first 100 recipients.
        
        Includes checkbox column for recipient selection.
        
        Validates Requirements:
        - 2.5: Display preview of recipient list with all mapped fields
        - 7.1: Checkbox selection functionality
        """
        # Temporarily disconnect cell changed signal to avoid triggering during setup
        try:
            self.preview_table.cellChanged.disconnect(self.on_cell_changed)
        except:
            pass
        
        # Clear existing table
        self.preview_table.clear()
        
        # Initialize selection state for ALL recipients (not just visible ones)
        for recipient in self.recipients:
            if recipient.email not in self.selection_state:
                self.selection_state[recipient.email] = True
        
        # Get preview recipients (first 100)
        preview_recipients = self.recipients[:100]
        
        if not preview_recipients:
            # Reconnect signal
            self.preview_table.cellChanged.connect(self.on_cell_changed)
            self.update_selection_info()
            return
        
        # Determine columns to display
        # Start with checkbox column, then email, then add all unique field keys
        columns = ['☑', 'email']  # Checkbox column first
        field_keys = set()
        for recipient in preview_recipients:
            field_keys.update(recipient.fields.keys())
        columns.extend(sorted(field_keys))
        
        # Set table dimensions
        self.preview_table.setRowCount(len(preview_recipients))
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        
        # Set the first column (checkbox) to resize to contents
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # Populate table
        for row_idx, recipient in enumerate(preview_recipients):
            # Checkbox column
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            
            # Use existing selection state
            checkbox_item.setCheckState(
                Qt.CheckState.Checked if self.selection_state[recipient.email] else Qt.CheckState.Unchecked
            )
            self.preview_table.setItem(row_idx, 0, checkbox_item)
            
            # Email column
            email_item = QTableWidgetItem(recipient.email)
            self.preview_table.setItem(row_idx, 1, email_item)
            
            # Field columns
            for col_idx, field_key in enumerate(columns[2:], start=2):
                value = recipient.fields.get(field_key, '')
                if value is None:
                    value = ''
                item = QTableWidgetItem(str(value))
                self.preview_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.preview_table.resizeColumnsToContents()
        
        # Update header checkbox state based on current selection
        self.update_header_checkbox_state()
        
        # Reconnect signal
        self.preview_table.cellChanged.connect(self.on_cell_changed)
        
        # Update selection info
        self.update_selection_info()
    
    def remove_duplicates(self):
        """
        Remove duplicate email addresses from recipients list.
        
        Validates Requirements:
        - 2.4: Remove duplicates and notify user
        """
        if not self.recipients:
            return
        
        # Count duplicates before removal
        original_count = len(self.recipients)
        
        # Remove duplicates
        self.recipients = self.importer.remove_duplicates(self.recipients)
        
        # Count after removal
        new_count = len(self.recipients)
        removed_count = original_count - new_count
        
        # Validate recipients again
        validation_result = self.importer.validate_recipients(self.recipients)
        
        # Update validation status
        self.update_validation_status(validation_result)
        
        # Update preview table
        self.update_preview_table()
        
        # Show success message
        QMessageBox.information(
            self,
            "Duplicates Removed",
            f"Successfully removed {removed_count} duplicate email address(es).\n\n"
            f"Remaining recipients: {new_count}"
        )
        
        # Emit signal that recipients changed
        self.recipients_loaded.emit()
    
    def on_cell_changed(self, row: int, column: int):
        """
        Handle cell changes in the preview table.
        
        This is called when a checkbox is clicked.
        
        Args:
            row: Row index
            column: Column index
        """
        # Only handle checkbox column (column 0)
        if column != 0:
            return
        
        # Get the checkbox item
        checkbox_item = self.preview_table.item(row, 0)
        if not checkbox_item:
            return
        
        # Get the recipient email from the email column (column 1)
        email_item = self.preview_table.item(row, 1)
        if not email_item:
            return
        
        recipient_email = email_item.text()
        
        # Update selection state
        is_checked = checkbox_item.checkState() == Qt.CheckState.Checked
        self.selection_state[recipient_email] = is_checked
        
        # Update header checkbox state
        self.update_header_checkbox_state()
        
        # Update selection info
        self.update_selection_info()
        
        # Emit selection changed signal
        self.selection_changed.emit()
    
    def on_header_checkbox_changed(self, state: int):
        """
        Handle header checkbox state change (Select All / Deselect All).
        
        Args:
            state: Checkbox state (Qt.CheckState)
        """
        # Ignore PartiallyChecked state - it's only set programmatically
        # When user clicks on PartiallyChecked, Qt cycles to Unchecked, then Checked
        if state == Qt.CheckState.PartiallyChecked.value:
            return
        
        # Temporarily disconnect cell changed signal to avoid triggering for each cell
        try:
            self.preview_table.cellChanged.disconnect(self.on_cell_changed)
        except:
            pass
        
        is_checked = (state == Qt.CheckState.Checked.value)
        
        # Update all visible checkboxes in the table
        for row in range(self.preview_table.rowCount()):
            checkbox_item = self.preview_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(
                    Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
                )
                
                # Update selection state for this recipient
                email_item = self.preview_table.item(row, 1)
                if email_item:
                    recipient_email = email_item.text()
                    self.selection_state[recipient_email] = is_checked
        
        # Also update selection state for all recipients (not just visible ones)
        for recipient in self.recipients:
            self.selection_state[recipient.email] = is_checked
        
        # Reconnect signal
        self.preview_table.cellChanged.connect(self.on_cell_changed)
        
        # Update selection info
        self.update_selection_info()
        
        # Emit selection changed signal
        self.selection_changed.emit()
    
    def update_header_checkbox_state(self):
        """
        Update the header checkbox state based on current selection.
        
        - If all visible recipients are selected: Checked
        - If no visible recipients are selected: Unchecked
        - If some visible recipients are selected: PartiallyChecked
        """
        # Check if header checkbox exists and is valid
        if not self.header_checkbox or not self.header_checkbox.parent():
            return
        
        # Temporarily disconnect to avoid triggering the handler
        try:
            self.header_checkbox.stateChanged.disconnect(self.on_header_checkbox_changed)
        except:
            pass
        
        # Count selected checkboxes in the visible table
        total_visible = self.preview_table.rowCount()
        if total_visible == 0:
            try:
                self.header_checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.header_checkbox.stateChanged.connect(self.on_header_checkbox_changed)
            except RuntimeError:
                # Header checkbox was deleted, ignore
                pass
            return
        
        selected_count = 0
        for row in range(total_visible):
            checkbox_item = self.preview_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                selected_count += 1
        
        # Set header checkbox state
        try:
            if selected_count == 0:
                self.header_checkbox.setCheckState(Qt.CheckState.Unchecked)
            elif selected_count == total_visible:
                self.header_checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                self.header_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            
            # Reconnect signal
            self.header_checkbox.stateChanged.connect(self.on_header_checkbox_changed)
        except RuntimeError:
            # Header checkbox was deleted, ignore
            pass
    
    def update_selection_info(self):
        """
        Update the selection info label showing how many recipients are selected.
        """
        total_count = len(self.recipients)
        selected_count = sum(1 for recipient in self.recipients 
                           if self.selection_state.get(recipient.email, True))
        
        self.selection_info_label.setText(f"{selected_count} of {total_count} recipients selected")
    
    def get_selected_recipients(self) -> List[Recipient]:
        """
        Get the list of selected recipients.
        
        Returns:
            List of Recipient objects that are currently selected
        """
        return [recipient for recipient in self.recipients 
                if self.selection_state.get(recipient.email, True)]
    
    def get_recipients(self) -> List[Recipient]:
        """
        Get the current list of recipients.
        
        Returns:
            List of Recipient objects
        """
        return self.recipients
    
    def set_recipients(self, recipients: List[Recipient]):
        """
        Set the recipients list.
        
        This method is used during crash recovery to restore recipients.
        
        Args:
            recipients: List of Recipient objects
        """
        self.recipients = recipients
        
        # Update the preview table
        self.update_preview_table()
        
        # Update status
        self.update_status()
        
        # Emit signal
        self.recipients_loaded.emit()
    
    def update_status(self):
        """
        Update validation status display after recipients are set.
        
        This method is called during crash recovery to update the validation
        status display when recipients are restored.
        """
        if self.recipients:
            # Validate recipients
            validation_result = self.importer.validate_recipients(self.recipients)
            
            # Update validation status display
            self.update_validation_status(validation_result)
            
            # Enable validation and preview groups
            self.validation_group.setEnabled(True)
            self.preview_group.setEnabled(True)
        else:
            # Disable groups if no recipients
            self.validation_group.setEnabled(False)
            self.preview_group.setEnabled(False)
    
    def has_recipients(self) -> bool:
        """
        Check if recipients have been loaded.
        
        Returns:
            True if recipients are loaded, False otherwise
        """
        return len(self.recipients) > 0
    
    def add_email_manually(self):
        """
        Open dialog to manually add a single email recipient.
        
        Validates Requirements:
        - 2.3: Validate email format before adding
        - 7.1: Manual email entry functionality
        """
        from ui.dialogs import AddEmailManuallyDialog
        
        # Get existing custom field names from current recipients
        existing_custom_fields = set()
        for recipient in self.recipients:
            existing_custom_fields.update(recipient.fields.keys())
        
        # Remove standard fields
        existing_custom_fields.discard('name')
        existing_custom_fields.discard('company')
        
        # Create and show dialog
        dialog = AddEmailManuallyDialog(
            existing_custom_fields=sorted(existing_custom_fields),
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipient_data = dialog.get_recipient_data()
            
            if recipient_data:
                # Create Recipient object
                new_recipient = Recipient(
                    email=recipient_data['email'],
                    fields=recipient_data['fields']
                )
                
                # Check for duplicate
                duplicate_found = False
                for existing_recipient in self.recipients:
                    if existing_recipient.email == new_recipient.email:
                        duplicate_found = True
                        break
                
                if duplicate_found:
                    # Ask user if they want to replace or skip
                    from ui.dialogs import ConfirmationDialog
                    confirm = ConfirmationDialog(
                        "Duplicate Email",
                        f"The email address '{new_recipient.email}' already exists in the recipient list.",
                        "Do you want to replace the existing recipient with the new data?",
                        confirm_text="Replace",
                        cancel_text="Skip",
                        parent=self
                    )
                    
                    if confirm.exec() == QDialog.DialogCode.Accepted:
                        # Replace existing recipient
                        for i, recipient in enumerate(self.recipients):
                            if recipient.email == new_recipient.email:
                                self.recipients[i] = new_recipient
                                break
                        
                        QMessageBox.information(
                            self,
                            "Recipient Updated",
                            f"Successfully updated recipient: {new_recipient.email}"
                        )
                    else:
                        # User chose to skip
                        return
                else:
                    # Add new recipient
                    self.recipients.append(new_recipient)
                    
                    # Initialize selection state (selected by default)
                    self.selection_state[new_recipient.email] = True
                    
                    # Save to database
                    self.save_recipient_to_db(new_recipient)
                    
                    QMessageBox.information(
                        self,
                        "Recipient Added",
                        f"Successfully added recipient: {new_recipient.email}"
                    )
                
                # Update validation status and preview
                validation_result = self.importer.validate_recipients(self.recipients)
                self.update_validation_status(validation_result)
                self.update_preview_table()
                
                # Enable validation and preview groups if not already enabled
                self.validation_group.setEnabled(True)
                self.preview_group.setEnabled(True)
                
                # Emit signal that recipients changed
                self.recipients_loaded.emit()
    
    def add_multiple_emails(self):
        """
        Open dialog to add multiple email recipients via paste.
        
        Supports:
        - Plain email list (one per line)
        - CSV format (email, name, company)
        - Tab-separated values
        
        Validates Requirements:
        - 2.3: Validate email format before adding
        - 7.1: Bulk manual email entry functionality
        """
        from ui.dialogs import AddMultipleEmailsDialog
        
        # Get existing custom field names from current recipients
        existing_custom_fields = set()
        for recipient in self.recipients:
            existing_custom_fields.update(recipient.fields.keys())
        
        # Remove standard fields
        existing_custom_fields.discard('name')
        existing_custom_fields.discard('company')
        
        # Create and show dialog
        dialog = AddMultipleEmailsDialog(
            existing_custom_fields=sorted(existing_custom_fields),
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            parsed_recipients = dialog.get_parsed_recipients()
            
            if not parsed_recipients:
                return
            
            # Track statistics
            added_count = 0
            updated_count = 0
            skipped_count = 0
            
            # Process each parsed recipient
            for recipient_data in parsed_recipients:
                # Create Recipient object
                new_recipient = Recipient(
                    email=recipient_data['email'],
                    fields=recipient_data['fields']
                )
                
                # Check for duplicate
                duplicate_found = False
                for i, existing_recipient in enumerate(self.recipients):
                    if existing_recipient.email == new_recipient.email:
                        duplicate_found = True
                        # Update existing recipient (merge fields)
                        # Keep existing fields, add new ones
                        for key, value in new_recipient.fields.items():
                            if key not in existing_recipient.fields or not existing_recipient.fields[key]:
                                existing_recipient.fields[key] = value
                        self.recipients[i] = existing_recipient
                        updated_count += 1
                        break
                
                if not duplicate_found:
                    # Add new recipient
                    self.recipients.append(new_recipient)
                    
                    # Initialize selection state (selected by default)
                    self.selection_state[new_recipient.email] = True
                    
                    added_count += 1
            
            # Update validation status and preview
            validation_result = self.importer.validate_recipients(self.recipients)
            self.update_validation_status(validation_result)
            self.update_preview_table()
            
            # Save all recipients to database
            if added_count > 0:
                self.save_all_recipients_to_db()
            
            # Enable validation and preview groups if not already enabled
            self.validation_group.setEnabled(True)
            self.preview_group.setEnabled(True)
            
            # Show summary message
            summary_parts = []
            if added_count > 0:
                summary_parts.append(f"{added_count} new recipient(s) added")
            if updated_count > 0:
                summary_parts.append(f"{updated_count} existing recipient(s) updated")
            
            summary = "\n".join(summary_parts) if summary_parts else "No changes made"
            
            QMessageBox.information(
                self,
                "Recipients Added",
                f"Successfully processed {len(parsed_recipients)} email(s):\n\n{summary}"
            )
            
            # Emit signal that recipients changed
            self.recipients_loaded.emit()


    def select_by_criteria(self):
        """
        Open dialog to select recipients based on field criteria.
        
        Allows selecting all recipients where a specific field matches a value.
        For example: select all from "Acme Corp" company.
        
        Validates Requirements:
        - 7.1: Select by criteria functionality
        """
        if not self.recipients:
            QMessageBox.information(
                self,
                "No Recipients",
                "Please load recipients first."
            )
            return
        
        from ui.dialogs import SelectByCriteriaDialog
        
        # Get all available fields from recipients
        available_fields = set()
        for recipient in self.recipients:
            available_fields.update(recipient.fields.keys())
        
        # Add email as a field option
        available_fields.add('email')
        
        # Create and show dialog
        dialog = SelectByCriteriaDialog(
            available_fields=sorted(available_fields),
            recipients=self.recipients,
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            criteria = dialog.get_criteria()
            
            if criteria:
                field_name = criteria['field']
                field_value = criteria['value']
                match_mode = criteria['match_mode']  # 'exact', 'contains', 'starts_with', 'ends_with'
                
                # Apply criteria to select recipients
                selected_count = 0
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
                        self.selection_state[recipient.email] = True
                        selected_count += 1
                
                # Update preview table to reflect new selection (only if visible)
                if self.isVisible():
                    self.update_preview_table()
                
                # Show result message
                QMessageBox.information(
                    self,
                    "Selection Updated",
                    f"Selected {selected_count} recipient(s) matching the criteria."
                )
    
    def invert_selection(self):
        """
        Invert the current selection.
        
        All selected recipients become unselected, and all unselected become selected.
        
        Validates Requirements:
        - 7.1: Invert selection functionality
        """
        if not self.recipients:
            QMessageBox.information(
                self,
                "No Recipients",
                "Please load recipients first."
            )
            return
        
        # Invert selection state for all recipients
        for recipient in self.recipients:
            current_state = self.selection_state.get(recipient.email, True)
            self.selection_state[recipient.email] = not current_state
        
        # Update preview table to reflect new selection (only if visible)
        if self.isVisible():
            self.update_preview_table()
        
        # Show result message
        selected_count = sum(1 for recipient in self.recipients 
                           if self.selection_state.get(recipient.email, True))
        QMessageBox.information(
            self,
            "Selection Inverted",
            f"Selection inverted. Now {selected_count} of {len(self.recipients)} recipients are selected."
        )
    
    def clear_selection(self):
        """
        Clear all selections (deselect all recipients).
        
        Validates Requirements:
        - 7.1: Clear selection functionality
        """
        if not self.recipients:
            QMessageBox.information(
                self,
                "No Recipients",
                "Please load recipients first."
            )
            return
        
        # Deselect all recipients
        for recipient in self.recipients:
            self.selection_state[recipient.email] = False
        
        # Update preview table to reflect new selection (only if visible)
        if self.isVisible():
            self.update_preview_table()
        
        # Show result message
        QMessageBox.information(
            self,
            "Selection Cleared",
            f"All recipients have been deselected."
        )

    
    def load_saved_recipients_from_db(self):
        """
        Load saved recipients from database on startup.
        
        This method is called automatically during initialization if a database
        is provided. It loads all manually added recipients that were saved
        in previous sessions.
        """
        if not self.database:
            return
        
        try:
            # Load recipients from database
            saved_recipients = self.database.load_saved_recipients(source='manual')
            
            if saved_recipients:
                self.recipients = saved_recipients
                
                # Initialize selection state (all selected by default)
                for recipient in self.recipients:
                    self.selection_state[recipient.email] = True
                
                # Update validation status and preview
                validation_result = self.importer.validate_recipients(self.recipients)
                self.update_validation_status(validation_result)
                self.update_preview_table()
                
                # Enable validation and preview groups
                self.validation_group.setEnabled(True)
                self.preview_group.setEnabled(True)
                
                # Emit signal that recipients were loaded
                self.recipients_loaded.emit()
                
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.info(f"Loaded {len(saved_recipients)} saved recipients from database")
        
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error loading saved recipients: {e}", exc_info=True)
    
    def save_recipient_to_db(self, recipient: Recipient):
        """
        Save a single recipient to the database.
        
        Args:
            recipient: Recipient object to save
        """
        if not self.database:
            return
        
        try:
            self.database.save_recipient(recipient, source='manual')
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error saving recipient to database: {e}", exc_info=True)
    
    def save_all_recipients_to_db(self):
        """
        Save all current recipients to the database.
        
        This is useful when loading from Excel - saves all recipients
        so they persist across sessions.
        """
        if not self.database or not self.recipients:
            return
        
        try:
            # Clear existing saved recipients first
            self.database.clear_saved_recipients(source='manual')
            
            # Save all current recipients
            self.database.save_recipients_batch(self.recipients, source='manual')
            
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.info(f"Saved {len(self.recipients)} recipients to database")
        
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error saving recipients to database: {e}", exc_info=True)
    
    def delete_recipient_from_db(self, email: str):
        """
        Delete a recipient from the database.
        
        Args:
            email: Email address to delete
        """
        if not self.database:
            return
        
        try:
            self.database.delete_recipient(email)
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error deleting recipient from database: {e}", exc_info=True)
