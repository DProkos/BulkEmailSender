"""Email template data model for bulk email sender."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EmailTemplate:
    """Represents an email template with subject, body, and attachments.
    
    Attributes:
        subject: Email subject line (can contain {{variables}})
        html_body: HTML version of email body
        text_body: Plain text fallback version
        attachments: List of file paths to attach
        variables: List of extracted {{variable}} placeholders
    """
    subject: str
    html_body: str
    text_body: str
    attachments: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate template data."""
        # Validate subject is not empty
        if not self.subject or not self.subject.strip():
            raise ValueError("Email subject cannot be empty")
        
        # Validate at least one body type is provided
        if not self.html_body and not self.text_body:
            raise ValueError("Email must have at least html_body or text_body")
        
        # Ensure attachments is a list
        if not isinstance(self.attachments, list):
            raise TypeError("Attachments must be a list")
        
        # Ensure variables is a list
        if not isinstance(self.variables, list):
            raise TypeError("Variables must be a list")
