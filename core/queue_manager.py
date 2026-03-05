"""Queue manager for bulk email sender.

This module manages send queues and job state persistence:
- Creating send jobs with recipients
- Tracking recipient status (PENDING, SENT, FAILED, CANCELLED)
- Persisting queue state for crash recovery
- Managing job lifecycle (pause, resume, cancel)
"""

import uuid
from datetime import datetime
from typing import Dict, List

from models.recipient import Recipient
from models.send_job import SendJob
from models.send_result import SendResult
from models.smtp_config import SMTPConfig
from models.template import EmailTemplate
from storage.database import Database
from utils.logger import setup_logger


class JobStatus:
    """Represents current job statistics.
    
    Attributes:
        sent: Number of successfully sent emails
        failed: Number of failed emails
        pending: Number of pending emails
        cancelled: Number of cancelled emails
        total: Total number of recipients
    """
    
    def __init__(self, sent: int, failed: int, pending: int, cancelled: int, total: int):
        """Initialize job status.
        
        Args:
            sent: Number of successfully sent emails
            failed: Number of failed emails
            pending: Number of pending emails
            cancelled: Number of cancelled emails
            total: Total number of recipients
        """
        self.sent = sent
        self.failed = failed
        self.pending = pending
        self.cancelled = cancelled
        self.total = total


class QueueManager:
    """Manages send queues and job state persistence.
    
    Responsibilities:
    - Create send jobs with recipients
    - Track recipient status throughout send process
    - Persist queue state after each send attempt
    - Support pause/resume/cancel operations
    - Provide job status and statistics
    """
    
    def __init__(self, db: Database):
        """Initialize queue manager with database connection.
        
        Args:
            db: Database instance for persistence
        """
        self.db = db
        self.logger = setup_logger(__name__)
    
    def create_job(
        self,
        recipients: List[Recipient],
        template: EmailTemplate,
        config: SMTPConfig,
        throttle_ms: int,
        max_retries: int = 3
    ) -> SendJob:
        """Create a new send job and persist to database.
        
        Creates a SendJob with all recipients in PENDING status and
        persists it to the database for crash recovery.
        
        Filters out any recipients whose email addresses are in the opt-out list.
        
        Args:
            recipients: List of recipients to send to
            template: Email template to use
            config: SMTP configuration
            throttle_ms: Delay in milliseconds between sends
            max_retries: Maximum retry attempts for transient errors
        
        Returns:
            SendJob with unique ID and PENDING status
        
        Raises:
            ValueError: If recipients list is empty or throttle_ms < 1000
        """
        # Validate inputs
        if not recipients:
            raise ValueError("Recipients list cannot be empty")
        
        if throttle_ms < 1000:
            raise ValueError("throttle_ms must be at least 1000ms (1 second)")
        
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        # Filter out opted-out recipients
        original_count = len(recipients)
        filtered_recipients = []
        
        for recipient in recipients:
            if self.db.is_opted_out(recipient.email):
                self.logger.info(f"Filtering out opted-out recipient: {recipient.email}")
            else:
                filtered_recipients.append(recipient)
        
        filtered_count = original_count - len(filtered_recipients)
        
        if filtered_count > 0:
            self.logger.info(f"Filtered out {filtered_count} opted-out recipient(s) from queue")
        
        # Validate we still have recipients after filtering
        if not filtered_recipients:
            raise ValueError("All recipients are in the opt-out list")
        
        # Create job with unique ID
        job = SendJob(
            id=str(uuid.uuid4()),
            created_at=datetime.now(),
            smtp_config=config,
            template=template,
            recipients=filtered_recipients.copy(),  # Create snapshot
            throttle_ms=throttle_ms,
            max_retries=max_retries,
            status="PENDING"
        )
        
        # Persist to database
        self.db.save_queue_state(job)
        
        return job
    
    def get_pending_recipients(self, job_id: str) -> List[Recipient]:
        """Get recipients that haven't been sent yet.
        
        Returns recipients with status PENDING or FAILED (with attempts < max_retries).
        
        Args:
            job_id: ID of the send job
        
        Returns:
            List of recipients that need to be sent
        
        Raises:
            ValueError: If job_id is not found
        """
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Filter recipients that need to be sent
        pending = []
        for recipient in job.recipients:
            if recipient.status == "PENDING":
                pending.append(recipient)
            elif recipient.status == "FAILED" and recipient.attempts < job.max_retries:
                pending.append(recipient)
        
        return pending
    
    def mark_sent(self, job_id: str, recipient_email: str, result: SendResult):
        """Mark recipient as sent and persist result.
        
        Updates recipient status to SENT, records the send result in the
        audit log, and persists the updated queue state.
        
        Args:
            job_id: ID of the send job
            recipient_email: Email address of the recipient
            result: SendResult containing send details
        
        Raises:
            ValueError: If job_id is not found or recipient not found
        """
        self.logger.info(f"Marking {recipient_email} as SENT in job {job_id}")
        
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Find recipient and update status
        recipient_found = False
        recipient_name = None
        
        for recipient in job.recipients:
            if recipient.email == recipient_email:
                recipient.status = "SENT"
                recipient.attempts += 1
                recipient.last_sent_at = result.timestamp
                recipient.last_error = None
                recipient_name = recipient.fields.get('name')
                recipient_found = True
                break
        
        if not recipient_found:
            raise ValueError(f"Recipient not found in job: {recipient_email}")
        
        # Save send record to audit log
        self.logger.debug(f"Saving send record to audit log for {recipient_email}")
        self.db.save_send_record(job_id, result, recipient_name, recipient.attempts)
        
        # Persist updated queue state
        self.db.save_queue_state(job)
    
    def mark_failed(self, job_id: str, recipient_email: str, error: str, attempts: int):
        """Mark recipient as failed and persist error.
        
        Updates recipient status to FAILED, records the error message,
        and persists the updated queue state.
        
        Args:
            job_id: ID of the send job
            recipient_email: Email address of the recipient
            error: Error message describing the failure
            attempts: Number of attempts made
        
        Raises:
            ValueError: If job_id is not found or recipient not found
        """
        self.logger.warning(f"Marking {recipient_email} as FAILED in job {job_id}: {error}")
        
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Find recipient and update status
        recipient_found = False
        recipient_name = None
        
        for recipient in job.recipients:
            if recipient.email == recipient_email:
                recipient.status = "FAILED"
                recipient.attempts = attempts
                recipient.last_error = error
                recipient.last_sent_at = datetime.now()
                recipient_name = recipient.fields.get('name')
                recipient_found = True
                break
        
        if not recipient_found:
            raise ValueError(f"Recipient not found in job: {recipient_email}")
        
        # Create SendResult for failed send
        result = SendResult(
            success=False,
            recipient_email=recipient_email,
            error_message=error,
            is_transient=False,
            timestamp=datetime.now()
        )
        
        # Save send record to audit log
        self.logger.debug(f"Saving failed send record to audit log for {recipient_email}")
        self.db.save_send_record(job_id, result, recipient_name, attempts)
        
        # Persist updated queue state
        self.db.save_queue_state(job)
    
    def pause_job(self, job_id: str):
        """Mark job as paused.
        
        Updates job status to PAUSED and persists to database.
        Flushes any pending batch inserts to ensure all records are saved.
        
        Args:
            job_id: ID of the send job
        
        Raises:
            ValueError: If job_id is not found
        """
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update job status
        job.status = "PAUSED"
        
        # Persist updated state
        self.db.save_queue_state(job)
        
        # Flush any pending batch inserts
        self.db.flush_pending_records()
    
    def resume_job(self, job_id: str):
        """Mark job as resumed.
        
        Updates job status to RUNNING and persists to database.
        
        Args:
            job_id: ID of the send job
        
        Raises:
            ValueError: If job_id is not found
        """
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update job status
        job.status = "RUNNING"
        
        # Persist updated state
        self.db.save_queue_state(job)
    
    def cancel_job(self, job_id: str):
        """Mark remaining recipients as cancelled.
        
        Updates all PENDING and FAILED recipients to CANCELLED status,
        updates job status to CANCELLED, and persists to database.
        Flushes any pending batch inserts to ensure all records are saved.
        
        Args:
            job_id: ID of the send job
        
        Raises:
            ValueError: If job_id is not found
        """
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Mark all pending/failed recipients as cancelled
        for recipient in job.recipients:
            if recipient.status in ("PENDING", "FAILED"):
                recipient.status = "CANCELLED"
        
        # Update job status
        job.status = "CANCELLED"
        
        # Persist updated state
        self.db.save_queue_state(job)
        
        # Flush any pending batch inserts
        self.db.flush_pending_records()
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """Get current job statistics.
        
        Counts recipients by status and returns statistics.
        
        Args:
            job_id: ID of the send job
        
        Returns:
            JobStatus with counts of sent, failed, pending, cancelled, and total
        
        Raises:
            ValueError: If job_id is not found
        """
        # Load job from database
        job = self.db.load_queue_state(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Count recipients by status
        sent = 0
        failed = 0
        pending = 0
        cancelled = 0
        
        for recipient in job.recipients:
            if recipient.status == "SENT":
                sent += 1
            elif recipient.status == "FAILED":
                failed += 1
            elif recipient.status == "PENDING":
                pending += 1
            elif recipient.status == "CANCELLED":
                cancelled += 1
        
        total = len(job.recipients)
        
        return JobStatus(
            sent=sent,
            failed=failed,
            pending=pending,
            cancelled=cancelled,
            total=total
        )
