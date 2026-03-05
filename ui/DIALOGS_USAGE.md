# Reusable Dialogs Usage Guide

This document provides examples and best practices for using the reusable dialog components in the Bulk Email Sender application.

## Overview

The `ui/dialogs.py` module provides four standardized dialog types:

1. **PreviewDialog** - Display HTML email previews
2. **ErrorDialog** - Show error messages with optional technical details
3. **ConfirmationDialog** - Confirm dangerous or irreversible operations
4. **ProgressDialog** - Track progress of long-running operations

All dialogs follow consistent design patterns and provide a uniform user experience.

## PreviewDialog

Use `PreviewDialog` to display rendered email content before sending.

### Basic Usage

```python
from ui.dialogs import PreviewDialog

# Render email template
rendered_html = template_renderer.preview(template, recipient)

# Show preview
dialog = PreviewDialog(rendered_html, parent=self)
dialog.exec()
```

### Features

- Displays HTML content with proper formatting
- Scrollable for long emails
- Close button for dismissal
- Non-modal by default (can view multiple previews)

### When to Use

- Email template preview
- Rendered content verification
- Before sending test emails

## ErrorDialog

Use `ErrorDialog` to display error messages with clear, user-friendly text and optional technical details.

### Basic Usage

```python
from ui.dialogs import ErrorDialog

# Simple error
dialog = ErrorDialog(
    "Connection Failed",
    "Could not connect to SMTP server.",
    parent=self
)
dialog.exec()
```

### With Technical Details

```python
# Error with technical details for debugging
dialog = ErrorDialog(
    "SMTP Error",
    "Authentication failed. Please check your credentials.",
    details=f"SMTP Error Code: {error.smtp_code}\n{str(error)}",
    parent=self
)
dialog.exec()
```

### Features

- Clear error icon
- User-friendly message
- Optional expandable technical details
- Modal (requires acknowledgment)

### When to Use

- SMTP connection failures
- File parsing errors
- Validation failures
- Any error requiring user acknowledgment

### Best Practices

- Keep main message user-friendly (no technical jargon)
- Put stack traces and error codes in `details` parameter
- Suggest solutions when possible
- Use specific titles ("SMTP Connection Failed" not "Error")

## ConfirmationDialog

Use `ConfirmationDialog` for operations that are dangerous, irreversible, or have significant consequences.

### Basic Usage

```python
from ui.dialogs import ConfirmationDialog

dialog = ConfirmationDialog(
    "Confirm Send",
    "Send emails to 1,234 recipients?",
    parent=self
)

if dialog.exec() == dialog.DialogCode.Accepted:
    # User confirmed - proceed with send
    start_bulk_send()
else:
    # User cancelled
    return
```

### With Warning

```python
dialog = ConfirmationDialog(
    "Stop Sending",
    "Stop the current send operation?",
    warning="All remaining emails will be cancelled. This cannot be undone.",
    confirm_text="Stop",
    cancel_text="Continue Sending",
    parent=self
)

if dialog.exec() == dialog.DialogCode.Accepted:
    worker.stop()
```

### Features

- Warning icon
- Optional prominent warning text
- Customizable button labels
- Cancel button is default (safer)
- Modal (requires decision)

### When to Use

- Starting bulk email send
- Stopping send operation (cancels remaining)
- Deleting data
- Overwriting files
- Any irreversible action

### Best Practices

- Make consequences clear in message
- Use warning parameter for critical information
- Make confirm button text specific ("Delete", "Send", "Stop")
- Make cancel button the default (safer option)
- Include relevant details (recipient count, time estimate)

## ProgressDialog

Use `ProgressDialog` to show progress of long-running operations and keep users informed.

### Indeterminate Progress

```python
from ui.dialogs import ProgressDialog

# Start operation with unknown duration
dialog = ProgressDialog(
    "Importing Recipients",
    "Parsing Excel file...",
    cancellable=True,
    parent=self
)

# Connect cancel signal
dialog.cancelled.connect(self.cancel_import)

# Show dialog
dialog.show()

# Update status as operation progresses
dialog.set_status("Reading file...")
# ... do work ...
dialog.set_status("Validating emails...")
# ... do work ...

# Close when done
dialog.accept()
```

### Determinate Progress

```python
dialog = ProgressDialog(
    "Sending Emails",
    "Sending to recipients...",
    cancellable=True,
    parent=self
)

dialog.cancelled.connect(self.cancel_send)
dialog.show()

# Update progress as you go
total = len(recipients)
for i, recipient in enumerate(recipients):
    send_email(recipient)
    
    # Update progress
    dialog.set_progress(i + 1, total)
    dialog.set_status(f"Sent {i + 1} of {total} emails...")
    
    # Check if cancelled
    if dialog.result() == dialog.DialogCode.Rejected:
        break

dialog.accept()
```

### Non-Cancellable Operations

```python
# Critical operations that must complete
dialog = ProgressDialog(
    "Updating Database",
    "Migrating database schema...",
    cancellable=False,  # No cancel button
    parent=self
)

dialog.show()

# Perform critical operation
migrate_database()

dialog.accept()
```

### Features

- Indeterminate or determinate progress bar
- Status message updates
- Optional cancel button
- Modal (prevents other interactions)
- Emits `cancelled` signal when user cancels

### When to Use

- Excel file parsing (large files)
- Bulk email sending
- Database operations
- File uploads/downloads
- Any operation taking > 2 seconds

### Best Practices

- Show dialog immediately when operation starts
- Update progress regularly (but not too frequently)
- Update status message to show current step
- Make cancellable when safe to do so
- Handle cancel signal properly (clean up resources)
- Close dialog when operation completes

### Progress Update Frequency

```python
# Good: Update every N items
for i, item in enumerate(items):
    process(item)
    
    if i % 10 == 0:  # Update every 10 items
        dialog.set_progress(i, len(items))
        dialog.set_status(f"Processing {i}/{len(items)}...")
        QApplication.processEvents()  # Keep UI responsive

# Bad: Update every item (too frequent for large lists)
for i, item in enumerate(items):
    process(item)
    dialog.set_progress(i, len(items))  # Too many updates!
```

## Integration Examples

### Complete Send Workflow

```python
def start_send(self):
    """Start bulk email send with proper dialogs."""
    
    # 1. Confirm before starting
    confirm = ConfirmationDialog(
        "Confirm Bulk Send",
        f"Send emails to {len(self.recipients)} recipients?",
        warning="This action cannot be undone.",
        confirm_text="Start Send",
        parent=self
    )
    
    if confirm.exec() != confirm.DialogCode.Accepted:
        return
    
    # 2. Show progress dialog
    self.progress_dialog = ProgressDialog(
        "Sending Emails",
        "Preparing to send...",
        cancellable=True,
        parent=self
    )
    
    self.progress_dialog.cancelled.connect(self.cancel_send)
    self.progress_dialog.show()
    
    # 3. Start worker
    self.worker = SendWorker(...)
    self.worker.progress_updated.connect(self.update_progress)
    self.worker.job_completed.connect(self.send_completed)
    self.worker.error_occurred.connect(self.send_error)
    self.worker.start()

def update_progress(self, sent, failed, remaining):
    """Update progress dialog."""
    total = sent + failed + remaining
    self.progress_dialog.set_progress(sent + failed, total)
    self.progress_dialog.set_status(
        f"Sent: {sent}, Failed: {failed}, Remaining: {remaining}"
    )

def send_completed(self):
    """Handle send completion."""
    self.progress_dialog.accept()
    
    # Show success message
    QMessageBox.information(
        self,
        "Send Complete",
        f"Successfully sent {self.worker.sent_count} emails."
    )

def send_error(self, error_message):
    """Handle send error."""
    self.progress_dialog.accept()
    
    # Show error dialog
    error = ErrorDialog(
        "Send Failed",
        "An error occurred during sending.",
        details=error_message,
        parent=self
    )
    error.exec()
```

### Excel Import Workflow

```python
def import_excel(self, filepath):
    """Import Excel file with progress tracking."""
    
    # Show progress dialog
    progress = ProgressDialog(
        "Importing Recipients",
        "Loading Excel file...",
        cancellable=True,
        parent=self
    )
    
    progress.show()
    
    try:
        # Load file
        progress.set_status("Reading file...")
        df = self.importer.load_file(filepath)
        
        # Validate
        progress.set_status("Validating emails...")
        progress.set_progress(50, 100)
        recipients = self.importer.map_columns(df, mapping)
        
        # Remove duplicates
        progress.set_status("Removing duplicates...")
        progress.set_progress(75, 100)
        recipients = self.importer.remove_duplicates(recipients)
        
        # Complete
        progress.set_progress(100, 100)
        progress.accept()
        
        # Show success
        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {len(recipients)} recipients."
        )
        
    except Exception as e:
        progress.accept()
        
        # Show error
        error = ErrorDialog(
            "Import Failed",
            "Could not import Excel file.",
            details=str(e),
            parent=self
        )
        error.exec()
```

## Styling and Customization

All dialogs use standard Qt styling and will respect the application theme. They use:

- Standard Qt icons (SP_MessageBoxCritical, SP_MessageBoxWarning)
- System fonts and colors
- Consistent spacing and layout

To customize appearance, modify the dialog classes in `ui/dialogs.py`.

## Testing

All dialogs have comprehensive unit tests in `tests/test_dialogs.py` and integration tests in `tests/test_dialogs_integration.py`.

When adding new dialog functionality:

1. Add unit tests for the new feature
2. Add integration tests showing real-world usage
3. Update this documentation with examples

## Requirements Mapping

These dialogs fulfill the following requirements:

- **Requirement 7.3**: Clear error messages near relevant fields
- **Requirement 7.5**: Progress indicator for long-running operations

## See Also

- `ui/dialogs.py` - Dialog implementations
- `tests/test_dialogs.py` - Unit tests
- `tests/test_dialogs_integration.py` - Integration tests
