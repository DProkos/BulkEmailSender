"""Application logging utilities with credential redaction.

This module provides logging functionality for the bulk email sender
with automatic credential redaction to prevent sensitive data leakage.
"""

import logging
import re
from typing import Any, Dict


class CredentialRedactor(logging.Filter):
    """Logging filter that redacts sensitive credentials from log messages.
    
    This filter automatically redacts:
    - Passwords in various formats
    - SMTP credentials
    - Email bodies (to prevent accidental logging of sensitive content)
    - Authorization headers
    - API keys and tokens
    """
    
    # Patterns to match and redact - using lambda functions for dynamic replacement
    PATTERNS = [
        # Password patterns - capture the separator and quotes to preserve format
        # Handle double-quoted values: "password": "value" (non-greedy match)
        (re.compile(r'(password["\']?\s*[:=]\s*)(")(.+?)(")', re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        # Handle single-quoted values: password='value' (non-greedy match)
        (re.compile(r"(password[\"']?\s*[:=]\s*)(')(.+?)(')", re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        # Handle unquoted values: password=value or password: value
        (re.compile(r'(password["\']?\s*[:=]\s*)([^"\'\s,}]+)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        
        (re.compile(r'(passwd["\']?\s*[:=]\s*)(")(.+?)(")', re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        (re.compile(r"(passwd[\"']?\s*[:=]\s*)(')(.+?)(')", re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        (re.compile(r'(passwd["\']?\s*[:=]\s*)([^"\'\s,}]+)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        
        (re.compile(r'(pwd["\']?\s*[:=]\s*)(")(.+?)(")', re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        (re.compile(r"(pwd[\"']?\s*[:=]\s*)(')(.+?)(')", re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]{m.group(4)}'),
        (re.compile(r'(pwd["\']?\s*[:=]\s*)([^"\'\s,}]+)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        
        # SMTP credentials
        (re.compile(r'(SMTPConfig\([^)]*password=)(["\']?)([^"\',)]+)(["\']?)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]{m.group(4)}'),
        
        # Authorization headers - match the entire value after the header
        (re.compile(r'(Authorization:\s*)(\S+\s+\S+)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        (re.compile(r'(Bearer\s+)(\S+)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        
        # API keys and tokens - handle both "api_key:" and "API key:" formats
        (re.compile(r'(api[\s_\-]*key["\']?\s*)([:=]\s*)(["\']?)([^"\'\s,}]+)(["\']?)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]'),
        (re.compile(r'(token["\']?\s*)([:=]\s*)(["\']?)([^"\'\s,}]+)(["\']?)', re.IGNORECASE), 
         lambda m: f'{m.group(1)}{m.group(2)}[REDACTED]'),
        
        # Email body content (to prevent logging sensitive email content)
        (re.compile(r'(html_body["\']?\s*[:=]\s*)(["\'])([^"\']{50,})(["\'])', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
        (re.compile(r'(text_body["\']?\s*[:=]\s*)(["\'])([^"\']{50,})(["\'])', re.IGNORECASE), 
         lambda m: f'{m.group(1)}[REDACTED]'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to redact sensitive information.
        
        Args:
            record: Log record to filter
            
        Returns:
            True (always allows the record through after redaction)
        """
        # Redact message
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        
        # Redact args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) if isinstance(v, str) else v 
                              for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) if isinstance(arg, str) else arg 
                                   for arg in record.args)
        
        return True
    
    @classmethod
    def redact(cls, text: str) -> str:
        """Redact sensitive information from text.
        
        Args:
            text: Text that may contain sensitive information
            
        Returns:
            Text with sensitive information redacted
        """
        if not text:
            return text
        
        result = text
        for pattern, replacement in cls.PATTERNS:
            # replacement can be either a string or a callable (lambda)
            if callable(replacement):
                result = pattern.sub(replacement, result)
            else:
                result = pattern.sub(replacement, result)
        
        return result


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Setup application logger with credential redaction.
    
    Creates a logger with:
    - Console handler for INFO and above
    - Optional file handler for DEBUG and above
    - Credential redaction filter on all handlers
    - Structured formatting with timestamps
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create credential redactor filter
    redactor = CredentialRedactor()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redactor)
    logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(redactor)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create log file handler: {e}")
    
    return logger


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive fields from a dictionary.
    
    Useful for logging configuration objects or data structures
    that may contain sensitive information.
    
    Args:
        data: Dictionary that may contain sensitive fields
        
    Returns:
        New dictionary with sensitive fields redacted
    """
    if not isinstance(data, dict):
        return data
    
    # Fields to redact
    sensitive_fields = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key',
        'authorization', 'auth', 'credential', 'private_key'
    }
    
    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive field name
        if any(sensitive in key_lower for sensitive in sensitive_fields):
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            # Recursively redact nested dictionaries
            result[key] = redact_dict(value)
        elif isinstance(value, str) and len(value) > 50:
            # Redact long strings (might be email bodies)
            if 'body' in key_lower or 'content' in key_lower:
                result[key] = '[REDACTED]'
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result
