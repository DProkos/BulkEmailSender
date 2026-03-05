"""Excel import and recipient management for bulk email sender."""

import pandas as pd
from typing import Dict, List
from models.recipient import Recipient
from models.validation_result import ValidationResult
from core.validator import Validator


class ExcelImporter:
    """Handles Excel file import, column mapping, and recipient validation.
    
    This class provides functionality to:
    - Load Excel files using pandas and openpyxl
    - Extract column headers
    - Map Excel columns to Recipient fields
    - Validate email addresses and detect duplicates
    - Remove duplicate recipients
    
    Requirements:
        - 2.1: Parse .xlsx files and extract column headers
        - 2.2: Map Excel columns to recipient fields
        - 2.3: Validate email addresses
        - 2.4: Remove duplicates and notify user
        - 2.6: Reject imports with missing/empty email column
    """
    
    def load_file(self, filepath: str) -> pd.DataFrame:
        """Load Excel file and return pandas DataFrame.
        
        Args:
            filepath: Path to the .xlsx file
            
        Returns:
            pandas DataFrame containing the Excel data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be parsed as Excel
            
        Requirements:
            - Validates: Requirement 2.1 (parse .xlsx file)
        """
        try:
            # Load Excel file using pandas with openpyxl engine
            df = pd.read_excel(filepath, engine='openpyxl')
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            return df
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
    
    def get_columns(self, df: pd.DataFrame) -> List[str]:
        """Extract column headers from DataFrame.
        
        Args:
            df: pandas DataFrame
            
        Returns:
            List of column names as strings
            
        Requirements:
            - Validates: Requirement 2.1 (extract column headers)
        """
        return df.columns.tolist()
    
    def map_columns(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[Recipient]:
        """Map Excel columns to Recipient fields and create Recipient objects.
        
        Args:
            df: pandas DataFrame containing Excel data
            mapping: Dictionary mapping field names to Excel column names
                    Example: {'email': 'Email Address', 'name': 'Full Name', 'company': 'Company'}
                    The 'email' key is required.
            
        Returns:
            List of Recipient objects created from the mapped data
            
        Raises:
            ValueError: If 'email' is not in mapping or mapped column doesn't exist
            
        Requirements:
            - Validates: Requirement 2.2 (map Excel columns to recipient fields)
            - Validates: Requirement 2.6 (reject if email column not mapped)
        """
        # Validate that email column is mapped
        if 'email' not in mapping:
            raise ValueError("Email column must be mapped")
        
        email_column = mapping['email']
        
        # Validate that the mapped email column exists in the DataFrame
        if email_column not in df.columns:
            raise ValueError(f"Mapped email column '{email_column}' not found in Excel file")
        
        recipients = []
        
        # Iterate through DataFrame rows
        for _, row in df.iterrows():
            # Get email value
            email_value = row[email_column]
            
            # Skip rows with empty email
            if pd.isna(email_value) or str(email_value).strip() == '':
                continue
            
            # Normalize email: trim whitespace and convert to lowercase
            email = str(email_value).strip().lower()
            
            # Create fields dictionary with all mapped columns
            fields = {}
            for field_name, column_name in mapping.items():
                if field_name != 'email' and column_name in df.columns:
                    value = row[column_name]
                    # Convert NaN to None, otherwise keep the value
                    if pd.isna(value):
                        fields[field_name] = None
                    else:
                        fields[field_name] = value
            
            # Add any unmapped columns as custom fields
            for column in df.columns:
                if column not in mapping.values():
                    value = row[column]
                    if not pd.isna(value):
                        # Use column name as field name for unmapped columns
                        fields[column] = value
            
            # Create Recipient object
            try:
                recipient = Recipient(email=email, fields=fields)
                recipients.append(recipient)
            except ValueError:
                # Skip recipients with invalid email (empty after normalization)
                continue
        
        return recipients
    
    def validate_recipients(self, recipients: List[Recipient]) -> ValidationResult:
        """Validate email formats and check for duplicates.
        
        Args:
            recipients: List of Recipient objects to validate
            
        Returns:
            ValidationResult with validation status, errors, and warnings
            
        Requirements:
            - Validates: Requirement 2.3 (validate email format)
            - Validates: Requirement 2.4 (detect duplicates)
        """
        errors = []
        warnings = []
        
        # Validate email formats
        invalid_emails = []
        for recipient in recipients:
            if not Validator.validate_email(recipient.email):
                invalid_emails.append(recipient.email)
        
        if invalid_emails:
            errors.append(
                f"Found {len(invalid_emails)} invalid email address(es): "
                f"{', '.join(invalid_emails[:5])}"
                + (f" and {len(invalid_emails) - 5} more" if len(invalid_emails) > 5 else "")
            )
        
        # Check for duplicates
        email_counts = {}
        for recipient in recipients:
            email = recipient.email
            email_counts[email] = email_counts.get(email, 0) + 1
        
        duplicates = {email: count for email, count in email_counts.items() if count > 1}
        
        if duplicates:
            duplicate_count = sum(count - 1 for count in duplicates.values())
            warnings.append(
                f"Found {duplicate_count} duplicate email address(es). "
                f"Duplicates will be removed, keeping first occurrence."
            )
        
        # Validation is successful if there are no errors
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    def remove_duplicates(self, recipients: List[Recipient]) -> List[Recipient]:
        """Remove duplicate email addresses, keeping first occurrence.
        
        Args:
            recipients: List of Recipient objects (may contain duplicates)
            
        Returns:
            List of Recipient objects with duplicates removed
            
        Requirements:
            - Validates: Requirement 2.4 (remove duplicates, keep first occurrence)
        """
        seen_emails = set()
        unique_recipients = []
        
        for recipient in recipients:
            # Email is already normalized in Recipient.__post_init__
            email = recipient.email
            
            if email not in seen_emails:
                seen_emails.add(email)
                unique_recipients.append(recipient)
        
        return unique_recipients
