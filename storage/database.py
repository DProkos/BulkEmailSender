"""SQLite database manager for bulk email sender.

This module provides database operations for:
- Send history logging (immutable audit trail)
- Send job persistence
- Opt-out list management
- Queue state persistence for crash recovery
"""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.recipient import Recipient
from models.send_job import SendJob
from models.send_result import SendResult
from models.smtp_config import SMTPConfig
from models.template import EmailTemplate
from utils.logger import setup_logger


class Database:
    """SQLite database manager for persistent storage.
    
    Manages:
    - send_history: Immutable audit log of all send attempts
    - send_jobs: Job metadata and configuration
    - optout_list: Emails that have opted out
    - queue_state: Current state of each recipient in a job
    """
    
    # Batch size for bulk inserts
    BATCH_SIZE = 100
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Setup logger
        self.logger = setup_logger(__name__)
        self.logger.info(f"Database initialized at {db_path}")
        
        # Initialize batch buffer for send_history
        self._send_history_batch = []
        
        # Create tables if they don't exist
        self.create_tables()
    
    def create_tables(self):
        """Create database schema if not exists.
        
        Tables:
        - send_history: Immutable audit log (INSERT only)
        - send_jobs: Job metadata
        - optout_list: Opted-out email addresses
        - queue_state: Current state of recipients in jobs
        """
        cursor = self.conn.cursor()
        
        # Send history table - immutable audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS send_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                recipient_name TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                attempts INTEGER DEFAULT 1
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_send_history_job_id 
            ON send_history(job_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_send_history_timestamp 
            ON send_history(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_send_history_recipient_email 
            ON send_history(recipient_email)
        """)
        
        # Composite index for common query patterns (job_id + status)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_send_history_job_status 
            ON send_history(job_id, status)
        """)
        
        # Index for status queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_send_history_status 
            ON send_history(status)
        """)
        
        # Send jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS send_jobs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                smtp_config TEXT NOT NULL,
                template TEXT NOT NULL,
                recipients TEXT NOT NULL,
                throttle_ms INTEGER NOT NULL,
                max_retries INTEGER NOT NULL,
                status TEXT NOT NULL
            )
        """)
        
        # Opt-out list table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optout_list (
                email TEXT PRIMARY KEY,
                added_at TEXT NOT NULL
            )
        """)
        
        # Queue state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue_state (
                job_id TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_error TEXT,
                last_attempt_at TEXT,
                PRIMARY KEY (job_id, recipient_email)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_state_job_id 
            ON queue_state(job_id)
        """)
        
        # Composite index for common query patterns (job_id + status)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_state_job_status 
            ON queue_state(job_id, status)
        """)
        
        # Saved recipients table - for manually added recipients
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                fields TEXT NOT NULL,
                added_at TEXT NOT NULL,
                source TEXT DEFAULT 'manual'
            )
        """)
        
        # Create index for faster email lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_saved_recipients_email 
            ON saved_recipients(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_saved_recipients_source 
            ON saved_recipients(source)
        """)
        
        self.conn.commit()
    
    def save_send_record(self, job_id: str, result: SendResult, recipient_name: Optional[str] = None, attempts: int = 1):
        """Save immutable send record for audit trail.
        
        This method only performs INSERT operations to maintain audit log immutability.
        Uses batch inserts for better performance - records are buffered and committed
        in batches of BATCH_SIZE.
        
        Args:
            job_id: ID of the send job
            result: SendResult containing send attempt details
            recipient_name: Optional name of recipient
            attempts: Number of attempts made for this send
        """
        # Determine status from result
        status = "SENT" if result.success else "FAILED"
        
        # Log the send record (credentials are already redacted by logger)
        self.logger.info(f"Saving send record: job={job_id}, recipient={result.recipient_email}, status={status}, attempts={attempts}")
        if not result.success and result.error_message:
            self.logger.debug(f"Error message: {result.error_message}")
        
        # Add to batch buffer
        record = (
            job_id,
            result.timestamp.isoformat(),
            result.recipient_email,
            recipient_name,
            status,
            result.error_message,
            attempts
        )
        self._send_history_batch.append(record)
        
        # Flush batch if it reaches BATCH_SIZE
        if len(self._send_history_batch) >= self.BATCH_SIZE:
            self._flush_send_history_batch()
    
    def _flush_send_history_batch(self):
        """Flush buffered send_history records to database.
        
        This method performs a batch insert of all buffered records
        for better performance.
        """
        if not self._send_history_batch:
            return
        
        cursor = self.conn.cursor()
        
        cursor.executemany("""
            INSERT INTO send_history 
            (job_id, timestamp, recipient_email, recipient_name, status, error_message, attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, self._send_history_batch)
        
        self.conn.commit()
        
        # Clear the batch buffer
        batch_size = len(self._send_history_batch)
        self._send_history_batch.clear()
        
        self.logger.debug(f"Flushed {batch_size} send_history records to database")
    
    def flush_pending_records(self):
        """Flush any pending batch inserts to database.
        
        This should be called when a job completes, is paused, or when
        you need to ensure all records are persisted immediately.
        """
        self._flush_send_history_batch()
    
    def get_send_history(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Query send history with optional filters.
        
        Args:
            filters: Optional dictionary with filter criteria:
                - job_id: Filter by job ID
                - recipient_email: Filter by recipient email
                - status: Filter by status (SENT, FAILED, CANCELLED)
                - start_date: Filter by start date (ISO format)
                - end_date: Filter by end date (ISO format)
        
        Returns:
            List of send history records as dictionaries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM send_history WHERE 1=1"
        params = []
        
        if filters:
            if "job_id" in filters:
                query += " AND job_id = ?"
                params.append(filters["job_id"])
            
            if "recipient_email" in filters:
                query += " AND recipient_email = ?"
                params.append(filters["recipient_email"])
            
            if "status" in filters:
                query += " AND status = ?"
                params.append(filters["status"])
            
            if "start_date" in filters:
                query += " AND timestamp >= ?"
                params.append(filters["start_date"])
            
            if "end_date" in filters:
                query += " AND timestamp <= ?"
                params.append(filters["end_date"])
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        return [dict(row) for row in rows]
    
    def export_to_csv(self, records: List[Dict], filepath: str):
        """Export send records to CSV file.
        
        Args:
            records: List of send history records
            filepath: Path to output CSV file
        """
        if not records:
            # Create empty CSV with headers
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'recipient_email', 'recipient_name', 'status', 'error_message', 'attempts'])
            return
        
        # Write records to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            # Get field names from first record
            fieldnames = ['timestamp', 'recipient_email', 'recipient_name', 'status', 'error_message', 'attempts']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for record in records:
                writer.writerow(record)
    
    def add_to_optout(self, email: str):
        """Add email to opt-out list.
        
        Args:
            email: Email address to add to opt-out list
        """
        cursor = self.conn.cursor()
        
        # Normalize email
        email = email.strip().lower()
        
        cursor.execute("""
            INSERT OR IGNORE INTO optout_list (email, added_at)
            VALUES (?, ?)
        """, (email, datetime.now().isoformat()))
        
        self.conn.commit()
    
    def is_opted_out(self, email: str) -> bool:
        """Check if email is in opt-out list.
        
        Args:
            email: Email address to check
        
        Returns:
            True if email is in opt-out list, False otherwise
        """
        cursor = self.conn.cursor()
        
        # Normalize email
        email = email.strip().lower()
        
        cursor.execute("""
            SELECT 1 FROM optout_list WHERE email = ?
        """, (email,))
        
        return cursor.fetchone() is not None
    
    def get_optout_list(self) -> list[tuple[str, str]]:
        """Get all emails in opt-out list.
        
        Returns:
            List of tuples (email, added_at)
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT email, added_at FROM optout_list
            ORDER BY added_at DESC
        """)
        
        return cursor.fetchall()
    
    def remove_from_optout(self, email: str):
        """Remove email from opt-out list.
        
        Args:
            email: Email address to remove from opt-out list
        """
        cursor = self.conn.cursor()
        
        # Normalize email
        email = email.strip().lower()
        
        cursor.execute("""
            DELETE FROM optout_list WHERE email = ?
        """, (email,))
        
        self.conn.commit()
    
    def save_queue_state(self, job: SendJob):
        """Persist queue state for recovery.
        
        Saves the current state of all recipients in the job to enable
        crash recovery without duplicate sends.
        
        Args:
            job: SendJob with current recipient states
        """
        cursor = self.conn.cursor()
        
        # First, save or update the job itself
        cursor.execute("""
            INSERT OR REPLACE INTO send_jobs 
            (id, created_at, smtp_config, template, recipients, throttle_ms, max_retries, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.id,
            job.created_at.isoformat(),
            json.dumps(self._smtp_config_to_dict(job.smtp_config)),
            json.dumps(self._template_to_dict(job.template)),
            json.dumps([self._recipient_to_dict(r) for r in job.recipients]),
            job.throttle_ms,
            job.max_retries,
            job.status
        ))
        
        # Save queue state for each recipient
        for recipient in job.recipients:
            cursor.execute("""
                INSERT OR REPLACE INTO queue_state 
                (job_id, recipient_email, status, attempts, last_error, last_attempt_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                recipient.email,
                recipient.status,
                recipient.attempts,
                recipient.last_error,
                recipient.last_sent_at.isoformat() if recipient.last_sent_at else None
            ))
        
        self.conn.commit()
    
    def get_incomplete_jobs(self) -> List[Dict]:
        """Get all incomplete jobs from database.
        
        Returns jobs with status PENDING, RUNNING, or PAUSED that have
        at least one recipient not yet sent.
        
        Returns:
            List of job dictionaries with id, created_at, status, and recipient counts
        """
        cursor = self.conn.cursor()
        
        # Get jobs that are not completed or cancelled
        cursor.execute("""
            SELECT id, created_at, status, recipients
            FROM send_jobs
            WHERE status IN ('PENDING', 'RUNNING', 'PAUSED')
            ORDER BY created_at DESC
        """)
        
        jobs = cursor.fetchall()
        incomplete_jobs = []
        
        for job_row in jobs:
            job_dict = dict(job_row)
            job_id = job_dict['id']
            
            # Get queue state to count pending recipients
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM queue_state
                WHERE job_id = ?
                GROUP BY status
            """, (job_id,))
            
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # If no queue state exists, count from recipients JSON
            if not status_counts:
                recipients_data = json.loads(job_dict['recipients'])
                total = len(recipients_data)
                status_counts = {'PENDING': total}
            
            # Only include if there are pending or failed recipients
            pending = status_counts.get('PENDING', 0)
            failed = status_counts.get('FAILED', 0)
            
            if pending > 0 or failed > 0:
                incomplete_jobs.append({
                    'id': job_id,
                    'created_at': job_dict['created_at'],
                    'status': job_dict['status'],
                    'sent': status_counts.get('SENT', 0),
                    'failed': failed,
                    'pending': pending,
                    'cancelled': status_counts.get('CANCELLED', 0),
                    'total': sum(status_counts.values())
                })
        
        return incomplete_jobs
    
    def load_queue_state(self, job_id: str) -> Optional[SendJob]:
        """Load queue state from database.
        
        Restores a SendJob with all recipient states from the database.
        
        Args:
            job_id: ID of the job to load
        
        Returns:
            SendJob with restored state, or None if job not found
        """
        cursor = self.conn.cursor()
        
        # Load job metadata
        cursor.execute("""
            SELECT * FROM send_jobs WHERE id = ?
        """, (job_id,))
        
        job_row = cursor.fetchone()
        if not job_row:
            return None
        
        # Parse job data
        job_dict = dict(job_row)
        
        # Load queue state for recipients
        cursor.execute("""
            SELECT * FROM queue_state WHERE job_id = ?
        """, (job_id,))
        
        queue_rows = cursor.fetchall()
        
        # Reconstruct recipients from stored data
        recipients_data = json.loads(job_dict['recipients'])
        
        # Create a map of email to queue state
        queue_state_map = {row['recipient_email']: dict(row) for row in queue_rows}
        
        # Reconstruct recipients with updated state
        recipients = []
        for recipient_data in recipients_data:
            email = recipient_data['email']
            
            # Get queue state if available
            queue_state = queue_state_map.get(email, {})
            
            # Create recipient with updated state
            recipient = Recipient(
                email=email,
                fields=recipient_data.get('fields', {}),
                status=queue_state.get('status', recipient_data.get('status', 'PENDING')),
                attempts=queue_state.get('attempts', recipient_data.get('attempts', 0)),
                last_error=queue_state.get('last_error', recipient_data.get('last_error')),
                last_sent_at=datetime.fromisoformat(queue_state['last_attempt_at']) if queue_state.get('last_attempt_at') else None
            )
            recipients.append(recipient)
        
        # Reconstruct SendJob
        smtp_config = self._dict_to_smtp_config(json.loads(job_dict['smtp_config']))
        template = self._dict_to_template(json.loads(job_dict['template']))
        
        job = SendJob(
            id=job_dict['id'],
            created_at=datetime.fromisoformat(job_dict['created_at']),
            smtp_config=smtp_config,
            template=template,
            recipients=recipients,
            throttle_ms=job_dict['throttle_ms'],
            max_retries=job_dict['max_retries'],
            status=job_dict['status']
        )
        
        return job
    
    def _smtp_config_to_dict(self, config: SMTPConfig) -> Dict:
        """Convert SMTPConfig to dictionary for JSON serialization."""
        return {
            'host': config.host,
            'port': config.port,
            'username': config.username,
            'password': config.password,
            'use_ssl': config.use_ssl,
            'use_starttls': config.use_starttls,
            'from_name': config.from_name,
            'reply_to': config.reply_to,
            'validate_certs': config.validate_certs
        }
    
    def _dict_to_smtp_config(self, data: Dict) -> SMTPConfig:
        """Convert dictionary to SMTPConfig."""
        return SMTPConfig(
            host=data['host'],
            port=data['port'],
            username=data['username'],
            password=data['password'],
            use_ssl=data['use_ssl'],
            use_starttls=data['use_starttls'],
            from_name=data.get('from_name'),
            reply_to=data.get('reply_to'),
            validate_certs=data.get('validate_certs', True)
        )
    
    def _template_to_dict(self, template: EmailTemplate) -> Dict:
        """Convert EmailTemplate to dictionary for JSON serialization."""
        return {
            'subject': template.subject,
            'html_body': template.html_body,
            'text_body': template.text_body,
            'attachments': template.attachments,
            'variables': template.variables
        }
    
    def _dict_to_template(self, data: Dict) -> EmailTemplate:
        """Convert dictionary to EmailTemplate."""
        return EmailTemplate(
            subject=data['subject'],
            html_body=data['html_body'],
            text_body=data['text_body'],
            attachments=data.get('attachments', []),
            variables=data.get('variables', [])
        )
    
    def _recipient_to_dict(self, recipient: Recipient) -> Dict:
        """Convert Recipient to dictionary for JSON serialization."""
        return {
            'email': recipient.email,
            'fields': recipient.fields,
            'status': recipient.status,
            'attempts': recipient.attempts,
            'last_error': recipient.last_error,
            'last_sent_at': recipient.last_sent_at.isoformat() if recipient.last_sent_at else None
        }
    
    
    def save_recipient(self, recipient: Recipient, source: str = 'manual') -> bool:
        """
        Save a recipient to the database.
        
        Args:
            recipient: Recipient object to save
            source: Source of the recipient ('manual', 'excel', etc.)
            
        Returns:
            True if saved successfully, False if already exists
        """
        try:
            cursor = self.conn.cursor()
            
            # Serialize fields to JSON
            fields_json = json.dumps(recipient.fields)
            
            cursor.execute("""
                INSERT OR REPLACE INTO saved_recipients (email, fields, added_at, source)
                VALUES (?, ?, ?, ?)
            """, (
                recipient.email,
                fields_json,
                datetime.now().isoformat(),
                source
            ))
            
            self.conn.commit()
            self.logger.info(f"Saved recipient: {recipient.email} (source: {source})")
            return True
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"Recipient already exists: {recipient.email}")
            return False
        except Exception as e:
            self.logger.error(f"Error saving recipient: {e}", exc_info=True)
            return False
    
    def save_recipients_batch(self, recipients: List[Recipient], source: str = 'manual'):
        """
        Save multiple recipients in a batch operation.
        
        Args:
            recipients: List of Recipient objects to save
            source: Source of the recipients ('manual', 'excel', etc.)
        """
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
            
            # Prepare batch data
            batch_data = [
                (r.email, json.dumps(r.fields), timestamp, source)
                for r in recipients
            ]
            
            cursor.executemany("""
                INSERT OR REPLACE INTO saved_recipients (email, fields, added_at, source)
                VALUES (?, ?, ?, ?)
            """, batch_data)
            
            self.conn.commit()
            self.logger.info(f"Saved {len(recipients)} recipients in batch (source: {source})")
            
        except Exception as e:
            self.logger.error(f"Error saving recipients batch: {e}", exc_info=True)
    
    def load_saved_recipients(self, source: Optional[str] = None) -> List[Recipient]:
        """
        Load saved recipients from the database.
        
        Args:
            source: Optional filter by source ('manual', 'excel', etc.)
                   If None, loads all recipients
        
        Returns:
            List of Recipient objects
        """
        try:
            cursor = self.conn.cursor()
            
            if source:
                cursor.execute("""
                    SELECT email, fields FROM saved_recipients
                    WHERE source = ?
                    ORDER BY added_at DESC
                """, (source,))
            else:
                cursor.execute("""
                    SELECT email, fields FROM saved_recipients
                    ORDER BY added_at DESC
                """)
            
            recipients = []
            for row in cursor.fetchall():
                email = row[0]
                fields = json.loads(row[1])
                recipient = Recipient(email=email, fields=fields)
                recipients.append(recipient)
            
            self.logger.info(f"Loaded {len(recipients)} saved recipients" + 
                           (f" (source: {source})" if source else ""))
            return recipients
            
        except Exception as e:
            self.logger.error(f"Error loading saved recipients: {e}", exc_info=True)
            return []
    
    def delete_recipient(self, email: str) -> bool:
        """
        Delete a saved recipient by email.
        
        Args:
            email: Email address to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM saved_recipients WHERE email = ?", (email,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"Deleted recipient: {email}")
                return True
            else:
                self.logger.warning(f"Recipient not found: {email}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting recipient: {e}", exc_info=True)
            return False
    
    def clear_saved_recipients(self, source: Optional[str] = None):
        """
        Clear all saved recipients or recipients from a specific source.
        
        Args:
            source: Optional filter by source. If None, clears all recipients
        """
        try:
            cursor = self.conn.cursor()
            
            if source:
                cursor.execute("DELETE FROM saved_recipients WHERE source = ?", (source,))
                self.logger.info(f"Cleared all recipients from source: {source}")
            else:
                cursor.execute("DELETE FROM saved_recipients")
                self.logger.info("Cleared all saved recipients")
            
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error clearing saved recipients: {e}", exc_info=True)
    
    def get_recipient_count(self, source: Optional[str] = None) -> int:
        """
        Get count of saved recipients.
        
        Args:
            source: Optional filter by source
            
        Returns:
            Number of saved recipients
        """
        try:
            cursor = self.conn.cursor()
            
            if source:
                cursor.execute("SELECT COUNT(*) FROM saved_recipients WHERE source = ?", (source,))
            else:
                cursor.execute("SELECT COUNT(*) FROM saved_recipients")
            
            return cursor.fetchone()[0]
            
        except Exception as e:
            self.logger.error(f"Error getting recipient count: {e}", exc_info=True)
            return 0
    
    def close(self):
        """Close database connection.
        
        Flushes any pending batch inserts before closing.
        """
        # Flush any pending send_history records
        self._flush_send_history_batch()
        
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
