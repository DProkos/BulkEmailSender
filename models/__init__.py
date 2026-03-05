"""Data models for bulk email sender application."""

from models.recipient import Recipient
from models.template import EmailTemplate
from models.smtp_config import SMTPConfig
from models.send_job import SendJob
from models.send_result import SendResult
from models.validation_result import ValidationResult

__all__ = [
    "Recipient",
    "EmailTemplate",
    "SMTPConfig",
    "SendJob",
    "SendResult",
    "ValidationResult",
]
