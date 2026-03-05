"""SMTP manager for handling email connections and sending."""

import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
import os

from models.smtp_config import SMTPConfig
from models.recipient import Recipient
from models.template import EmailTemplate
from models.send_result import SendResult
from utils.logger import setup_logger, redact_dict


class SMTPManager:
    """Manages SMTP connections and email sending operations.
    
    This class handles:
    - Establishing SMTP connections with SSL/STARTTLS support
    - Sending individual emails with error handling
    - Testing SMTP configuration
    - Classifying errors as transient or permanent
    """
    
    def __init__(self, config: SMTPConfig):
        """Initialize SMTP manager with configuration.
        
        Args:
            config: SMTP configuration including host, port, credentials, etc.
        """
        self.config = config
        self._smtp: Optional[smtplib.SMTP] = None
        self._connected = False
        
        # Setup logger with credential redaction
        self.logger = setup_logger(__name__)
    
    def connect(self) -> bool:
        """Establish SMTP connection with configured settings.
        
        Supports both SSL (direct) and STARTTLS (upgrade) connections.
        Validates TLS certificates by default unless disabled in config.
        
        Returns:
            True if connection successful, False otherwise.
            
        Raises:
            smtplib.SMTPAuthenticationError: If authentication fails
            smtplib.SMTPException: For other SMTP-related errors
            socket.error: For network-related errors
        """
        self.logger.info(f"Connecting to SMTP server: {self.config.host}:{self.config.port}")
        
        try:
            # Close existing connection if any
            if self._smtp is not None:
                try:
                    self._smtp.quit()
                except:
                    pass
                self._smtp = None
                self._connected = False
            
            # Create SSL context for certificate validation
            context = ssl.create_default_context()
            if not self.config.validate_certs:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.logger.warning("TLS certificate validation disabled")
            
            # Connect using SSL or STARTTLS
            if self.config.use_ssl:
                # Direct SSL connection (typically port 465)
                self.logger.debug(f"Using SSL connection to {self.config.host}:{self.config.port}")
                self._smtp = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    context=context,
                    timeout=30
                )
            else:
                # Plain connection with STARTTLS upgrade (typically port 587)
                self.logger.debug(f"Using STARTTLS connection to {self.config.host}:{self.config.port}")
                self._smtp = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=30
                )
                self._smtp.ehlo()
                
                if self.config.use_starttls:
                    self._smtp.starttls(context=context)
                    self._smtp.ehlo()
            
            # Authenticate
            self.logger.debug(f"Authenticating as {self.config.username}")
            self._smtp.login(self.config.username, self.config.password)
            
            self._connected = True
            self.logger.info("Successfully connected to SMTP server")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self._connected = False
            self._smtp = None
            self.logger.error(f"SMTP authentication failed for {self.config.username}: {str(e)}")
            raise
        except smtplib.SMTPException as e:
            self._connected = False
            self._smtp = None
            self.logger.error(f"SMTP error: {str(e)}")
            raise
        except (socket.error, socket.timeout) as e:
            self._connected = False
            self._smtp = None
            self.logger.error(f"Network error connecting to {self.config.host}:{self.config.port}: {str(e)}")
            raise
        except Exception as e:
            self._connected = False
            self._smtp = None
            self.logger.error(f"Unexpected error connecting to SMTP server: {str(e)}")
            raise
    
    def disconnect(self):
        """Close SMTP connection gracefully."""
        if self._smtp is not None:
            try:
                self._smtp.quit()
                self.logger.info("Disconnected from SMTP server")
            except Exception as e:
                # Ignore errors during disconnect
                self.logger.debug(f"Error during disconnect: {str(e)}")
            finally:
                self._smtp = None
                self._connected = False
    
    def send_email(self, recipient: Recipient, template: EmailTemplate, attachment_cache: Optional[dict] = None) -> SendResult:
        """Send a single email to a recipient using the template.
        
        Args:
            recipient: Recipient with email and field data
            template: Email template with subject, body, and attachments
            attachment_cache: Optional dict mapping attachment paths to cached data
                             Format: {path: {'filename': str, 'data': bytes}}
            
        Returns:
            SendResult with success status and error details if applicable
            
        Raises:
            RuntimeError: If not connected to SMTP server
        """
        if not self._connected or self._smtp is None:
            raise RuntimeError("Not connected to SMTP server. Call connect() first.")
        
        self.logger.info(f"Sending email to {recipient.email}")
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            
            # Set headers
            msg['Subject'] = template.subject
            msg['From'] = f"{self.config.from_name} <{self.config.username}>" if self.config.from_name else self.config.username
            msg['To'] = recipient.email
            
            if self.config.reply_to:
                msg['Reply-To'] = self.config.reply_to
            
            self.logger.debug(f"Email subject: {template.subject}")
            
            # Add text body if provided
            if template.text_body:
                text_part = MIMEText(template.text_body, 'plain', 'utf-8')
                msg.attach(text_part)
                self.logger.debug("Added plain text body")
            
            # Add HTML body if provided
            if template.html_body:
                html_part = MIMEText(template.html_body, 'html', 'utf-8')
                msg.attach(html_part)
                self.logger.debug("Added HTML body")
            
            # Add attachments
            for attachment_path in template.attachments:
                # Check if we have cached data
                if attachment_cache and attachment_path in attachment_cache:
                    # Use cached attachment data
                    try:
                        cached = attachment_cache[attachment_path]
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(cached['data'])
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {cached["filename"]}'
                        )
                        msg.attach(part)
                        self.logger.debug(f"Added cached attachment: {cached['filename']}")
                    except Exception as e:
                        error_msg = f"Failed to attach cached file {attachment_path}: {str(e)}"
                        self.logger.error(error_msg)
                        return SendResult(
                            success=False,
                            recipient_email=recipient.email,
                            error_message=error_msg,
                            is_transient=False
                        )
                else:
                    # Read attachment from disk (fallback for backward compatibility)
                    if not os.path.exists(attachment_path):
                        error_msg = f"Attachment not found: {attachment_path}"
                        self.logger.error(error_msg)
                        return SendResult(
                            success=False,
                            recipient_email=recipient.email,
                            error_message=error_msg,
                            is_transient=False
                        )
                    
                    try:
                        with open(attachment_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        
                        encoders.encode_base64(part)
                        filename = os.path.basename(attachment_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
                        self.logger.debug(f"Added attachment: {filename}")
                    except Exception as e:
                        error_msg = f"Failed to attach file {attachment_path}: {str(e)}"
                        self.logger.error(error_msg)
                        return SendResult(
                            success=False,
                            recipient_email=recipient.email,
                            error_message=error_msg,
                            is_transient=False
                        )
            
            # Send email
            self._smtp.send_message(msg)
            
            self.logger.info(f"Successfully sent email to {recipient.email}")
            return SendResult(
                success=True,
                recipient_email=recipient.email
            )
            
        except smtplib.SMTPException as e:
            # SMTP-specific errors
            is_transient = self.is_transient_error(e)
            error_type = "transient" if is_transient else "permanent"
            self.logger.error(f"SMTP error ({error_type}) sending to {recipient.email}: {str(e)}")
            return SendResult(
                success=False,
                recipient_email=recipient.email,
                error_message=str(e),
                is_transient=is_transient
            )
        except (socket.timeout, ConnectionResetError, socket.error) as e:
            # Network errors - always transient
            self.logger.warning(f"Network error (transient) sending to {recipient.email}: {str(e)}")
            return SendResult(
                success=False,
                recipient_email=recipient.email,
                error_message=str(e),
                is_transient=True
            )
        except Exception as e:
            # Other errors - permanent
            self.logger.error(f"Unexpected error (permanent) sending to {recipient.email}: {str(e)}")
            return SendResult(
                success=False,
                recipient_email=recipient.email,
                error_message=str(e),
                is_transient=False
            )
    
    def test_connection(self) -> SendResult:
        """Test SMTP configuration by connecting and authenticating.
        
        This method attempts to connect and authenticate with the SMTP server
        without sending any email. Useful for validating configuration.
        
        Returns:
            SendResult indicating success or failure of the test
        """
        try:
            # Try to connect
            success = self.connect()
            
            if success:
                # Disconnect after successful test
                self.disconnect()
                
                return SendResult(
                    success=True,
                    recipient_email=self.config.username,
                    error_message=None
                )
            else:
                return SendResult(
                    success=False,
                    recipient_email=self.config.username,
                    error_message="Connection failed",
                    is_transient=False
                )
                
        except smtplib.SMTPAuthenticationError as e:
            return SendResult(
                success=False,
                recipient_email=self.config.username,
                error_message=f"Authentication failed: {str(e)}",
                is_transient=False
            )
        except smtplib.SMTPException as e:
            is_transient = self.is_transient_error(e)
            return SendResult(
                success=False,
                recipient_email=self.config.username,
                error_message=f"SMTP error: {str(e)}",
                is_transient=is_transient
            )
        except (socket.timeout, socket.error) as e:
            return SendResult(
                success=False,
                recipient_email=self.config.username,
                error_message=f"Connection error: {str(e)}",
                is_transient=True
            )
        except Exception as e:
            return SendResult(
                success=False,
                recipient_email=self.config.username,
                error_message=f"Unexpected error: {str(e)}",
                is_transient=False
            )
    
    def is_transient_error(self, error: Exception) -> bool:
        """Determine if an error is transient (retryable) or permanent.
        
        Transient errors include:
        - SMTP 4xx response codes (temporary failures)
        - Network timeouts
        - Connection resets
        - Temporary DNS failures
        
        Permanent errors include:
        - SMTP 5xx response codes (permanent failures)
        - Authentication failures (535)
        - Invalid recipient address (550)
        - Message rejected by server
        
        Args:
            error: Exception that occurred during SMTP operation
            
        Returns:
            True if error is transient (should retry), False if permanent
        """
        # Authentication errors are always permanent
        if isinstance(error, smtplib.SMTPAuthenticationError):
            return False
        
        # Check SMTP error codes
        if isinstance(error, smtplib.SMTPException):
            # Try to extract SMTP error code
            error_str = str(error)
            
            # Check for specific error codes in the error message
            # 4xx codes are transient
            if hasattr(error, 'smtp_code'):
                code = error.smtp_code
                if 400 <= code < 500:
                    return True
                elif 500 <= code < 600:
                    return False
            
            # Parse error string for codes
            # Common format: "(code, 'message')" or "code message"
            try:
                # Try to find a 3-digit code in the error string
                import re
                match = re.search(r'\b([45]\d{2})\b', error_str)
                if match:
                    code = int(match.group(1))
                    if 400 <= code < 500:
                        return True
                    elif 500 <= code < 600:
                        return False
            except:
                pass
        
        # Network errors are transient
        if isinstance(error, (socket.timeout, ConnectionResetError, socket.error)):
            return True
        
        # Default to permanent for unknown errors
        return False
    
    def __enter__(self):
        """Context manager entry - connect to SMTP server."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from SMTP server."""
        self.disconnect()
        return False
