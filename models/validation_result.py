"""Validation result data model for bulk email sender."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """Represents the result of a validation operation.
    
    Attributes:
        valid: Whether the validation passed
        errors: List of error messages (validation failures)
        warnings: List of warning messages (non-critical issues)
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate validation result data."""
        # Ensure errors is a list
        if not isinstance(self.errors, list):
            raise TypeError("errors must be a list")
        
        # Ensure warnings is a list
        if not isinstance(self.warnings, list):
            raise TypeError("warnings must be a list")
        
        # Validate consistency: if valid is False, there should be at least one error
        if not self.valid and not self.errors:
            raise ValueError("Invalid validation result must have at least one error")
        
        # Validate consistency: if there are errors, valid should be False
        if self.errors and self.valid:
            raise ValueError("Validation result with errors must have valid=False")
