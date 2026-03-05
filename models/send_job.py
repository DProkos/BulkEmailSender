"""Send job data model for bulk email sender."""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from models.recipient import Recipient
from models.smtp_config import SMTPConfig
from models.template import EmailTemplate


@dataclass
class SendJob:
    """Represents a bulk email send job.
    
    Attributes:
        id: Unique identifier (UUID)
        created_at: Timestamp when job was created
        smtp_config: SMTP configuration for sending
        template: Email template to use
        recipients: Snapshot of recipients at job creation
        throttle_ms: Delay in milliseconds between consecutive sends
        max_retries: Maximum number of retry attempts for transient errors
        status: Current job status (PENDING, RUNNING, PAUSED, COMPLETED, CANCELLED)
    """
    id: str
    created_at: datetime
    smtp_config: SMTPConfig
    template: EmailTemplate
    recipients: List[Recipient]
    throttle_ms: int
    max_retries: int
    status: str = "PENDING"
    
    def __post_init__(self):
        """Validate send job data."""
        # Validate id is not empty
        if not self.id or not self.id.strip():
            raise ValueError("Job ID cannot be empty")
        
        # Validate created_at is a datetime
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime object")
        
        # Validate smtp_config is an SMTPConfig instance
        if not isinstance(self.smtp_config, SMTPConfig):
            raise TypeError("smtp_config must be an SMTPConfig instance")
        
        # Validate template is an EmailTemplate instance
        if not isinstance(self.template, EmailTemplate):
            raise TypeError("template must be an EmailTemplate instance")
        
        # Validate recipients is a list
        if not isinstance(self.recipients, list):
            raise TypeError("recipients must be a list")
        
        # Validate recipients list is not empty
        if not self.recipients:
            raise ValueError("Recipients list cannot be empty")
        
        # Validate all recipients are Recipient instances
        for i, recipient in enumerate(self.recipients):
            if not isinstance(recipient, Recipient):
                raise TypeError(f"Recipient at index {i} must be a Recipient instance")
        
        # Validate throttle_ms is positive
        if not isinstance(self.throttle_ms, int) or self.throttle_ms < 0:
            raise ValueError(f"throttle_ms must be a non-negative integer, got: {self.throttle_ms}")
        
        # Validate throttle_ms meets minimum requirement (1000ms = 1 second)
        if self.throttle_ms < 1000:
            raise ValueError(f"throttle_ms must be at least 1000ms (1 second), got: {self.throttle_ms}")
        
        # Validate max_retries is non-negative
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ValueError(f"max_retries must be a non-negative integer, got: {self.max_retries}")
        
        # Validate status is one of the allowed values
        valid_statuses = {"PENDING", "RUNNING", "PAUSED", "COMPLETED", "CANCELLED"}
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, got: {self.status}")
