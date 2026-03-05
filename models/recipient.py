"""Recipient data model for bulk email sender."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Recipient:
    """Represents an email recipient with their data fields.
    
    Attributes:
        email: Required, normalized (lowercase, trimmed) email address
        fields: All other fields from Excel (name, company, custom fields)
        status: Current status (PENDING, SENT, FAILED, CANCELLED)
        attempts: Number of send attempts made
        last_error: Error message from last failed attempt
        last_sent_at: Timestamp of last send attempt
    """
    email: str
    fields: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"
    attempts: int = 0
    last_error: Optional[str] = None
    last_sent_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize recipient data."""
        # Normalize email: trim whitespace and convert to lowercase
        if self.email:
            self.email = self.email.strip().lower()
        
        # Validate email is not empty
        if not self.email:
            raise ValueError("Email address cannot be empty")
        
        # Validate status is one of the allowed values
        valid_statuses = {"PENDING", "SENT", "FAILED", "CANCELLED"}
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, got: {self.status}")
        
        # Validate attempts is non-negative
        if self.attempts < 0:
            raise ValueError(f"Attempts must be non-negative, got: {self.attempts}")
