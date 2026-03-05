"""Input validation utilities for bulk email sender."""

import re
from typing import Optional
from models.smtp_config import SMTPConfig
from models.template import EmailTemplate
from models.validation_result import ValidationResult


class Validator:
    """Provides validation methods for email addresses, SMTP config, templates, and throttle rates."""
    
    # RFC 5322 compliant email regex
    # This regex validates the basic structure of an email address
    # Pattern breakdown:
    # - Local part: alphanumeric, dots, hyphens, underscores, plus signs
    # - @ symbol
    # - Domain: alphanumeric, dots, hyphens
    # - TLD: at least 2 characters
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Minimum throttle rate in milliseconds (1 second)
    MIN_THROTTLE_MS = 1000
    
    # Warning threshold for throttle rate (100 emails/minute = 600ms)
    THROTTLE_WARNING_MS = 600
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format using RFC 5322 compliant regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid, False otherwise
            
        Requirements:
            - Validates: Requirement 2.3 (email format validation)
        """
        if not email or not isinstance(email, str):
            return False
        
        # Normalize: trim whitespace and convert to lowercase for validation
        email = email.strip().lower()
        
        # Check if email is empty after trimming
        if not email:
            return False
        
        # Validate using regex
        return bool(Validator.EMAIL_REGEX.match(email))
    
    @staticmethod
    def validate_smtp_config(config: SMTPConfig) -> ValidationResult:
        """Validate SMTP configuration completeness.
        
        Args:
            config: SMTPConfig object to validate
            
        Returns:
            ValidationResult with validation status and any errors/warnings
            
        Requirements:
            - Validates: Requirement 7.2 (validate required fields before proceeding)
            - Validates: Requirement 8.5 (validate all user inputs)
        """
        errors = []
        warnings = []
        
        # Validate host
        if not config.host or not config.host.strip():
            errors.append("SMTP host is required")
        
        # Validate port
        if config.port < 1 or config.port > 65535:
            errors.append(f"SMTP port must be between 1 and 65535, got: {config.port}")
        
        # Validate username
        if not config.username or not config.username.strip():
            errors.append("SMTP username is required")
        
        # Validate password
        if not config.password:
            errors.append("SMTP password is required")
        
        # Validate encryption settings
        if config.use_ssl and config.use_starttls:
            errors.append("Cannot use both SSL and STARTTLS simultaneously")
        
        if not config.use_ssl and not config.use_starttls:
            errors.append("Must enable either SSL or STARTTLS for secure connection")
        
        # Validate reply_to email format if provided
        if config.reply_to and not Validator.validate_email(config.reply_to):
            errors.append(f"Invalid reply-to email format: {config.reply_to}")
        
        # Warning for certificate validation disabled
        if not config.validate_certs:
            warnings.append("TLS certificate validation is disabled - this is insecure")
        
        # Determine if valid
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    @staticmethod
    def validate_template(template: EmailTemplate) -> ValidationResult:
        """Validate template has required fields.
        
        Args:
            template: EmailTemplate object to validate
            
        Returns:
            ValidationResult with validation status and any errors/warnings
            
        Requirements:
            - Validates: Requirement 7.2 (validate required fields before proceeding)
            - Validates: Requirement 8.5 (validate all user inputs)
        """
        errors = []
        warnings = []
        
        # Validate subject
        if not template.subject or not template.subject.strip():
            errors.append("Email subject is required")
        
        # Validate body content
        if not template.html_body and not template.text_body:
            errors.append("Email must have at least html_body or text_body")
        elif not template.html_body:
            warnings.append("No HTML body provided - email will be plain text only")
        elif not template.text_body:
            warnings.append("No plain text body provided - some email clients may not display the email properly")
        
        # Validate attachments exist (if any)
        if template.attachments:
            import os
            for attachment_path in template.attachments:
                if not os.path.exists(attachment_path):
                    errors.append(f"Attachment file not found: {attachment_path}")
                elif not os.path.isfile(attachment_path):
                    errors.append(f"Attachment path is not a file: {attachment_path}")
        
        # Determine if valid
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    @staticmethod
    def validate_throttle_rate(rate_ms: int) -> ValidationResult:
        """Validate throttle rate is within safe limits.
        
        Args:
            rate_ms: Throttle rate in milliseconds
            
        Returns:
            ValidationResult with validation status and any errors/warnings
            
        Requirements:
            - Validates: Requirement 6.1 (minimum throttle rate of 1 second)
            - Validates: Requirement 6.4 (warning for rates > 100 emails/minute)
            - Validates: Requirement 8.5 (validate all user inputs)
        """
        errors = []
        warnings = []
        
        # Validate rate is a positive integer
        if not isinstance(rate_ms, int):
            errors.append(f"Throttle rate must be an integer, got: {type(rate_ms).__name__}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        if rate_ms < 0:
            errors.append(f"Throttle rate must be positive, got: {rate_ms}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # Enforce minimum throttle rate
        if rate_ms < Validator.MIN_THROTTLE_MS:
            errors.append(
                f"Throttle rate must be at least {Validator.MIN_THROTTLE_MS}ms (1 second), "
                f"got: {rate_ms}ms"
            )
        
        # Warning for high send rates
        if rate_ms < Validator.THROTTLE_WARNING_MS and rate_ms >= Validator.MIN_THROTTLE_MS:
            emails_per_minute = 60000 / rate_ms
            warnings.append(
                f"Throttle rate of {rate_ms}ms allows {emails_per_minute:.1f} emails per minute. "
                f"This may trigger spam filters. Consider increasing the delay."
            )
        
        # Determine if valid
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
