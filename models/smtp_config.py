"""SMTP configuration data model for bulk email sender."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SMTPConfig:
    """Represents SMTP server configuration.
    
    Attributes:
        host: SMTP server hostname
        port: SMTP server port
        username: SMTP authentication username
        password: SMTP authentication password (retrieved from keyring)
        use_ssl: Whether to use SSL (port 465)
        use_starttls: Whether to use STARTTLS (port 587)
        from_name: Optional display name for sender
        reply_to: Optional reply-to email address
        validate_certs: Whether to validate TLS certificates
    """
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool
    use_starttls: bool
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    validate_certs: bool = True
    
    def __post_init__(self):
        """Validate SMTP configuration."""
        # Validate host is not empty
        if not self.host or not self.host.strip():
            raise ValueError("SMTP host cannot be empty")
        
        # Validate port is in valid range
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise ValueError(f"SMTP port must be between 1 and 65535, got: {self.port}")
        
        # Validate username is not empty
        if not self.username or not self.username.strip():
            raise ValueError("SMTP username cannot be empty")
        
        # Validate password is not empty
        if not self.password:
            raise ValueError("SMTP password cannot be empty")
        
        # Validate SSL and STARTTLS are not both enabled
        if self.use_ssl and self.use_starttls:
            raise ValueError("Cannot use both SSL and STARTTLS simultaneously")
        
        # Validate at least one encryption method is enabled
        if not self.use_ssl and not self.use_starttls:
            raise ValueError("Must enable either SSL or STARTTLS for secure connection")
