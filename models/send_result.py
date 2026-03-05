"""Send result data model for bulk email sender."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SendResult:
    """Represents the result of a single email send attempt.
    
    Attributes:
        success: Whether the send was successful
        recipient_email: Email address of the recipient
        error_message: Error message if send failed
        is_transient: True if error is retryable (4xx codes, timeouts, etc.)
        timestamp: When the send attempt occurred
    """
    success: bool
    recipient_email: str
    error_message: Optional[str] = None
    is_transient: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate send result data."""
        # Validate recipient_email is not empty
        if not self.recipient_email or not self.recipient_email.strip():
            raise ValueError("Recipient email cannot be empty")
        
        # Validate timestamp is a datetime
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")
        
        # Validate consistency: if success is True, error_message should be None
        if self.success and self.error_message is not None:
            raise ValueError("Successful send should not have an error_message")
        
        # Validate consistency: if success is False, error_message should be provided
        if not self.success and not self.error_message:
            raise ValueError("Failed send must have an error_message")
        
        # Validate consistency: is_transient should only be True for failures
        if self.success and self.is_transient:
            raise ValueError("Successful send cannot have is_transient=True")
