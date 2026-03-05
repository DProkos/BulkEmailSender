"""Worker thread for background email sending.

This module implements the SendWorker QThread class that handles
bulk email sending in the background without blocking the UI.
"""

import time
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.smtp_manager import SMTPManager
from core.queue_manager import QueueManager
from core.template_renderer import TemplateRenderer
from models.send_job import SendJob
from utils.logger import setup_logger


class SendWorker(QThread):
    """Background worker thread for sending bulk emails.
    
    This worker processes a send queue in the background, emitting
    progress signals to update the UI. It supports pause/resume/stop
    operations and implements retry logic for transient errors.
    
    Signals:
        progress_updated(sent, failed, remaining): Emitted after each send attempt
        email_sent(email, success, error_msg): Emitted for each email processed
        job_completed(): Emitted when all emails have been processed
    """
    
    # Qt signals for progress updates
    progress_updated = pyqtSignal(int, int, int)  # sent, failed, remaining
    email_sent = pyqtSignal(str, bool, str)       # email, success, error_msg
    job_completed = pyqtSignal()
    
    def __init__(
        self,
        job: SendJob,
        smtp_manager: SMTPManager,
        queue_manager: QueueManager,
        template_renderer: TemplateRenderer
    ):
        """Initialize worker with job details.
        
        Args:
            job: SendJob containing recipients and configuration
            smtp_manager: SMTPManager for sending emails
            queue_manager: QueueManager for tracking progress
            template_renderer: TemplateRenderer for rendering templates
        """
        super().__init__()
        
        self.job = job
        self.smtp_manager = smtp_manager
        self.queue_manager = queue_manager
        self.template_renderer = template_renderer
        
        # Control flags
        self._paused = False
        self._stopped = False
        self._should_pause = False
        self._should_stop = False
        
        # Statistics
        self._sent_count = 0
        self._failed_count = 0
        
        # Attachment cache
        self._attachment_cache = {}
        
        # Setup logger
        self.logger = setup_logger(__name__)
    
    def run(self):
        """Main worker loop - processes send queue.
        
        This method runs in a separate thread and processes the send queue
        sequentially. It handles:
        - Rendering templates with recipient data
        - Sending emails via SMTP
        - Throttling between sends
        - Retry logic for transient errors
        - SMTP reconnection on connection loss
        - Pause/resume/stop control
        """
        self.logger.info(f"Starting send worker for job {self.job.id}")
        
        try:
            # Mark job as running
            self.queue_manager.resume_job(self.job.id)
            
            # Load attachments into cache
            if not self._load_attachments_to_cache():
                # Failed to load attachments - fail all pending
                error_msg = "Failed to load attachments into cache"
                self.logger.error(error_msg)
                self._fail_all_pending(error_msg)
                self.job_completed.emit()
                return
            
            # Connect to SMTP server
            smtp_connected = False
            reconnect_attempts = 0
            max_reconnect_attempts = 3
            
            self.logger.info("Connecting to SMTP server...")
            
            while not smtp_connected and reconnect_attempts < max_reconnect_attempts:
                try:
                    self.smtp_manager.connect()
                    smtp_connected = True
                except Exception as e:
                    reconnect_attempts += 1
                    self.logger.warning(f"SMTP connection attempt {reconnect_attempts} failed: {str(e)}")
                    if reconnect_attempts >= max_reconnect_attempts:
                        # Failed to connect after max attempts
                        error_msg = f"Failed to connect to SMTP server: {str(e)}"
                        self.logger.error(error_msg)
                        self._fail_all_pending(error_msg)
                        self.job_completed.emit()
                        return
                    # Wait before retry with exponential backoff
                    time.sleep(min(2 ** reconnect_attempts, 60))
            
            try:
                # Get pending recipients
                pending_recipients = self.queue_manager.get_pending_recipients(self.job.id)
                self.logger.info(f"Processing {len(pending_recipients)} pending recipients")
                
                # Process each recipient
                for idx, recipient in enumerate(pending_recipients, 1):
                    self.logger.debug(f"Processing recipient {idx}/{len(pending_recipients)}: {recipient.email}")
                    
                    # Check for stop signal
                    if self._should_stop:
                        self.logger.info("Stop signal received, cancelling remaining emails")
                        self._handle_stop()
                        break
                    
                    # Check for pause signal
                    if self._should_pause:
                        self.logger.info("Pause signal received")
                        self._handle_pause()
                        # Wait until resumed or stopped
                        while self._paused and not self._should_stop:
                            time.sleep(0.1)
                        
                        if self._should_stop:
                            self.logger.info("Stop signal received during pause")
                            self._handle_stop()
                            break
                        
                        self.logger.info("Resuming from pause")
                    
                    # Render template with recipient data
                    try:
                        rendered = self.template_renderer.render(
                            self.job.template,
                            recipient
                        )
                        
                        # Update template with rendered content
                        rendered_template = self.job.template
                        rendered_template.subject = rendered.subject
                        rendered_template.html_body = rendered.html_body
                        rendered_template.text_body = rendered.text_body
                        
                    except Exception as e:
                        # Template rendering failed - mark as permanent failure
                        error_msg = f"Template rendering failed: {str(e)}"
                        self.logger.error(f"Template rendering failed for {recipient.email}: {str(e)}")
                        self._handle_send_failure(recipient, error_msg, is_transient=False)
                        continue
                    
                    # Send email with retry logic
                    send_success = False
                    attempts = recipient.attempts
                    
                    while not send_success and attempts < self.job.max_retries:
                        try:
                            # Send email with cached attachments
                            result = self.smtp_manager.send_email(
                                recipient, 
                                rendered_template,
                                attachment_cache=self._attachment_cache
                            )
                            
                            if result.success:
                                # Send successful
                                send_success = True
                                self._handle_send_success(recipient, result)
                            else:
                                # Send failed
                                attempts += 1
                                
                                if result.is_transient and attempts < self.job.max_retries:
                                    # Transient error - retry with exponential backoff
                                    retry_delay = min(2 ** attempts, 60)
                                    self.logger.info(f"Transient error for {recipient.email}, retrying in {retry_delay}s (attempt {attempts}/{self.job.max_retries})")
                                    time.sleep(retry_delay)
                                else:
                                    # Permanent error or max retries reached
                                    self._handle_send_failure(
                                        recipient,
                                        result.error_message,
                                        is_transient=result.is_transient,
                                        attempts=attempts
                                    )
                                    break
                        
                        except Exception as e:
                            # Connection error - attempt to reconnect
                            attempts += 1
                            self.logger.warning(f"Connection error for {recipient.email}: {str(e)}")
                            
                            if self._attempt_reconnect():
                                # Reconnected successfully - retry
                                if attempts < self.job.max_retries:
                                    self.logger.info(f"Reconnected, retrying {recipient.email}")
                                    continue
                                else:
                                    # Max retries reached
                                    self._handle_send_failure(
                                        recipient,
                                        f"Max retries reached: {str(e)}",
                                        is_transient=True,
                                        attempts=attempts
                                    )
                                    break
                            else:
                                # Reconnection failed - fail remaining emails
                                error_msg = f"SMTP connection lost: {str(e)}"
                                self.logger.error(error_msg)
                                self._fail_all_pending(error_msg)
                                self.job_completed.emit()
                                return
                    
                    # Throttle between sends (unless this is the last email)
                    if recipient != pending_recipients[-1]:
                        self._throttle()
                
                # All emails processed
                self.logger.info(f"Job {self.job.id} completed. Sent: {self._sent_count}, Failed: {self._failed_count}")
                self.queue_manager.resume_job(self.job.id)  # Update status
                self.job.status = "COMPLETED"
                
                # Flush any pending batch inserts
                self.queue_manager.db.flush_pending_records()
                
                self.job_completed.emit()
            
            finally:
                # Disconnect from SMTP server
                self.smtp_manager.disconnect()
                
                # Clear attachment cache
                self._clear_attachment_cache()
        
        except Exception as e:
            # Unexpected error - fail all pending
            self.logger.error(f"Unexpected error in worker: {str(e)}", exc_info=True)
            self._fail_all_pending(f"Unexpected error: {str(e)}")
            self.job_completed.emit()
    
    def pause(self):
        """Request pause after current email.
        
        Sets a flag that will be checked before the next email send.
        The current email will complete before pausing.
        """
        self._should_pause = True
    
    def resume(self):
        """Resume from paused state.
        
        Clears the pause flag and allows the worker to continue.
        """
        self._should_pause = False
        self._paused = False
    
    def stop(self):
        """Stop and cancel remaining emails.
        
        Sets a flag that will be checked before the next email send.
        The current email will complete, then remaining emails will be cancelled.
        """
        self._should_stop = True
    
    def _handle_send_success(self, recipient, result):
        """Handle successful email send.
        
        Args:
            recipient: Recipient that was sent to
            result: SendResult from SMTP manager
        """
        self._sent_count += 1
        
        # Mark as sent in queue
        self.queue_manager.mark_sent(self.job.id, recipient.email, result)
        
        # Emit signals
        self.email_sent.emit(recipient.email, True, "")
        self._emit_progress()
    
    def _handle_send_failure(self, recipient, error_msg, is_transient=False, attempts=None):
        """Handle failed email send.
        
        Args:
            recipient: Recipient that failed
            error_msg: Error message
            is_transient: Whether error is transient
            attempts: Number of attempts made (defaults to recipient.attempts + 1)
        """
        self._failed_count += 1
        
        if attempts is None:
            attempts = recipient.attempts + 1
        
        # Mark as failed in queue
        self.queue_manager.mark_failed(
            self.job.id,
            recipient.email,
            error_msg,
            attempts
        )
        
        # Emit signals
        self.email_sent.emit(recipient.email, False, error_msg)
        self._emit_progress()
    
    def _handle_pause(self):
        """Handle pause request.
        
        Marks job as paused and sets internal flag.
        """
        self._paused = True
        self.queue_manager.pause_job(self.job.id)
    
    def _handle_stop(self):
        """Handle stop request.
        
        Cancels all remaining emails and marks job as cancelled.
        """
        self._stopped = True
        self.queue_manager.cancel_job(self.job.id)
    
    def _throttle(self):
        """Implement throttling delay between sends.
        
        Sleeps for the configured throttle_ms duration.
        """
        # Convert milliseconds to seconds
        delay_seconds = self.job.throttle_ms / 1000.0
        time.sleep(delay_seconds)
    
    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to SMTP server.
        
        Tries to reconnect up to 3 times with exponential backoff.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Close existing connection
                self.smtp_manager.disconnect()
                
                # Wait before reconnecting
                time.sleep(min(2 ** attempt, 60))
                
                # Attempt reconnection
                self.smtp_manager.connect()
                return True
            
            except Exception:
                if attempt == max_attempts - 1:
                    return False
        
        return False
    
    def _fail_all_pending(self, error_msg: str):
        """Fail all pending recipients with the same error.
        
        Args:
            error_msg: Error message to record for all failures
        """
        try:
            pending = self.queue_manager.get_pending_recipients(self.job.id)
            
            for recipient in pending:
                self._handle_send_failure(recipient, error_msg, is_transient=False)
        
        except Exception:
            # Ignore errors during cleanup
            pass
    
    def _emit_progress(self):
        """Emit progress update signal with current statistics."""
        # Get current job status
        status = self.queue_manager.get_job_status(self.job.id)
        
        # Emit progress signal
        self.progress_updated.emit(
            status.sent,
            status.failed,
            status.pending
        )

    def _load_attachments_to_cache(self) -> bool:
        """Load all attachments into memory cache.
        
        Reads each attachment file once and stores the binary data
        in memory for reuse across all emails in the batch.
        
        Returns:
            True if all attachments loaded successfully, False otherwise
        """
        if not self.job.template.attachments:
            self.logger.debug("No attachments to cache")
            return True
        
        self.logger.info(f"Loading {len(self.job.template.attachments)} attachments into cache")
        
        for attachment_path in self.job.template.attachments:
            try:
                import os
                
                # Check if file exists
                if not os.path.exists(attachment_path):
                    self.logger.error(f"Attachment not found: {attachment_path}")
                    return False
                
                # Read file into memory
                with open(attachment_path, 'rb') as f:
                    file_data = f.read()
                
                # Store in cache with filename
                filename = os.path.basename(attachment_path)
                self._attachment_cache[attachment_path] = {
                    'filename': filename,
                    'data': file_data
                }
                
                self.logger.debug(f"Cached attachment: {filename} ({len(file_data)} bytes)")
            
            except Exception as e:
                self.logger.error(f"Failed to load attachment {attachment_path}: {str(e)}")
                return False
        
        self.logger.info(f"Successfully cached {len(self._attachment_cache)} attachments")
        return True
    
    def _clear_attachment_cache(self):
        """Clear attachment cache to free memory.
        
        Called after batch completes to release memory used by cached attachments.
        """
        if self._attachment_cache:
            cache_size = sum(len(item['data']) for item in self._attachment_cache.values())
            self.logger.info(f"Clearing attachment cache ({cache_size} bytes)")
            self._attachment_cache.clear()
