# Bulk Email Sender

A desktop application for sending bulk personalized emails via SMTP with advanced features like throttling, queue management, crash recovery, and comprehensive logging.

## Features

- **Dark Theme Support**: Modern dark theme that works perfectly with Windows dark mode
- **SMTP Configuration**: Support for SSL/STARTTLS with secure credential storage in OS keyring
- **Excel Import**: Import recipient lists from .xlsx files with flexible column mapping
- **Predefined Templates**: Professional Greek business email templates ready to use
- **Company Settings**: Configure company information for email personalization
- **Template Editor**: Create personalized emails with variable substitution using Jinja2
- **Bulk Sending**: Send to thousands of recipients with configurable throttling
- **Queue Management**: Pause, resume, and stop operations with automatic crash recovery
- **Progress Tracking**: Real-time progress updates and comprehensive logging
- **Compliance Features**: Opt-out list management, rate limiting warnings, and unsubscribe links
- **Error Handling**: Automatic retry for transient errors, detailed error reporting
- **Recipient Persistence**: Manually added emails are saved across sessions

## Installation

### Prerequisites
- Python 3.10 or higher
- Windows, macOS, or Linux

### Setup

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## User Guide

### 1. SMTP Configuration

Configure your email server settings in the **SMTP Settings** tab:

1. **Host**: Your SMTP server address (e.g., `smtp.gmail.com`)
2. **Port**: SMTP port (587 for STARTTLS, 465 for SSL)
3. **Username**: Your email address
4. **Password**: Your email password (stored securely in OS keyring)
5. **Encryption**: Choose SSL or STARTTLS
6. **From Name** (optional): Display name for sender
7. **Reply-To** (optional): Reply-to email address

**Test your configuration** using the "Test Connection" button before proceeding.

#### Common SMTP Providers

**Gmail**:
- Host: `smtp.gmail.com`
- Port: 587 (STARTTLS) or 465 (SSL)
- Note: Enable "Less secure app access" or use App Password

**Outlook/Office 365**:
- Host: `smtp.office365.com`
- Port: 587 (STARTTLS)

**Yahoo Mail**:
- Host: `smtp.mail.yahoo.com`
- Port: 587 (STARTTLS) or 465 (SSL)

**Custom SMTP**:
- Contact your email provider for SMTP settings

### 2. Import Recipients

Import your recipient list from an Excel file in the **Recipients** tab:

1. Click "Select Excel File" and choose your .xlsx file
2. Map columns to recipient fields:
   - **Email** (required): Column containing email addresses
   - **Name** (optional): Column containing recipient names
   - **Company** (optional): Column containing company names
   - Additional columns will be available as custom variables
3. Click "Load Recipients" to import and validate
4. Review validation results (valid, invalid, duplicate counts)
5. Use "Remove Duplicates" if needed

#### Excel File Format

Your Excel file should have:
- **Header row** with column names
- **Email column** (required)
- **Additional columns** for personalization (name, company, etc.)

Example:
```
Email                | Name        | Company      | Custom1
---------------------|-------------|--------------|--------
john@example.com     | John Doe    | Acme Corp    | Value1
jane@example.com     | Jane Smith  | Tech Inc     | Value2
```

### 3. Create Email Template

Design your email in the **Template** tab:

1. **Subject**: Enter subject line (can include variables)
2. **HTML Body**: Create HTML version of your email
3. **Text Body**: Create plain text version (fallback)
4. **Variables**: Use `{{variable_name}}` syntax for personalization
5. **Attachments**: Add files to attach to all emails
6. **Unsubscribe Link**: Configure global URL or map from Excel

#### Using Variables

Variables are replaced with recipient data:
- `{{name}}` → Recipient's name
- `{{email}}` → Recipient's email
- `{{company}}` → Recipient's company
- `{{custom_field}}` → Any custom Excel column

Example template:
```html
<p>Dear {{name}},</p>
<p>Thank you for your interest in our services at {{company}}.</p>
<p>Best regards,<br>The Team</p>
<p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
```

**Preview** your email using the "Preview Email" button to see how it will look.

### 4. Send Emails

Configure and start sending in the **Send** tab:

1. **Throttle Rate**: Set delay between emails (minimum 1 second)
   - Recommended: 2-5 seconds to avoid spam filters
   - Warning shown if > 100 emails/minute
2. **Max Retries**: Set retry attempts for transient errors (default: 3)
3. **Dry Run Mode**: Test without actually sending emails
4. **Send to Self First**: Send test email to yourself

#### Sending Process

1. Click "Start Send" to begin
2. Monitor progress:
   - Sent count
   - Failed count
   - Remaining count
   - Current sending rate
3. Use controls:
   - **Pause**: Pause after current email
   - **Resume**: Continue from paused state
   - **Stop**: Cancel remaining emails
4. View real-time log of send attempts
5. Export log to CSV when complete

#### Crash Recovery

If the application crashes during sending:
1. Restart the application
2. You'll be prompted to resume incomplete jobs
3. Already-sent emails will be skipped automatically
4. Sending continues from where it left off

### 5. Compliance and Safety

#### Rate Limiting
- Minimum throttle: 1 second between emails
- Warning displayed if rate > 100 emails/minute
- Helps avoid spam filters and server rate limits

#### Opt-Out List
- Manage opt-out list via File menu
- Opted-out emails are automatically excluded from sends
- Persistent across sessions

#### Unsubscribe Links
- Add `{{unsubscribe_link}}` to templates
- Configure global URL or map from Excel column
- Required for compliance with anti-spam laws

#### Attachment Size
- Warning displayed if total attachments > 50MB
- Large attachments may cause delivery issues
- Consider using file sharing links instead

## Troubleshooting

### SMTP Connection Errors

**"Authentication failed"**:
- Verify username and password are correct
- Check if 2FA is enabled (use app password instead)
- Ensure "less secure apps" is enabled (Gmail)

**"Connection timeout"**:
- Check your internet connection
- Verify SMTP host and port are correct
- Check if firewall is blocking SMTP ports

**"Certificate verification failed"**:
- Try disabling "Validate TLS certificates" (not recommended)
- Update your system's CA certificates

### Excel Import Errors

**"Failed to parse Excel file"**:
- Ensure file is valid .xlsx format
- Try opening and re-saving in Excel
- Check for file corruption

**"Email column not found"**:
- Verify you've mapped the email column
- Check that Excel file has header row
- Ensure email column is not empty

### Sending Errors

**"Permanent error" (5xx codes)**:
- Email address is invalid or rejected
- Message content triggered spam filter
- Recipient's mailbox is full

**"Transient error" (4xx codes)**:
- Temporary server issue (will retry automatically)
- Rate limit exceeded (increase throttle delay)
- Network connectivity issue

## Advanced Features

### Background Processing
- Excel parsing runs in background thread
- UI remains responsive during long operations
- Progress updates shown for all operations

### Database Storage
- Send history stored in SQLite database
- Queue state persisted for crash recovery
- Opt-out list maintained persistently
- Location: `~/.bulk_email_sender/data.db`

### Logging
- Comprehensive logging of all operations
- Credentials automatically redacted from logs
- Export send history to CSV for analysis

### Performance
- Supports 10,000+ recipients without UI freeze
- Efficient memory usage with large attachments
- Optimized database operations with indexing

## Project Structure

```
bulk_email_sender/
├── ui/                     # PyQt6 user interface components
│   ├── main_window.py      # Main application window
│   ├── smtp_tab.py         # SMTP configuration UI
│   ├── recipients_tab.py   # Excel import and mapping UI
│   ├── template_tab.py     # Template editor UI
│   ├── send_tab.py         # Send control and progress UI
│   └── dialogs.py          # Reusable dialogs
├── core/                   # Core business logic
│   ├── smtp_manager.py     # SMTP connection and sending
│   ├── template_renderer.py # Jinja2 template rendering
│   ├── excel_importer.py   # Excel parsing and validation
│   ├── queue_manager.py    # Send queue management
│   ├── worker.py           # Background send worker thread
│   └── validator.py        # Input validation utilities
├── models/                 # Data models
│   ├── recipient.py        # Recipient data model
│   ├── template.py         # Email template model
│   ├── smtp_config.py      # SMTP configuration model
│   ├── send_job.py         # Send job model
│   └── send_result.py      # Send result model
├── storage/                # Database and credential storage
│   ├── database.py         # SQLite database manager
│   ├── credential_store.py # OS keyring integration
│   └── config_manager.py   # JSON config file manager
├── utils/                  # Utility functions
│   └── logger.py           # Application logging
├── tests/                  # Comprehensive test suite
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── pytest.ini              # Pytest configuration
└── README.md              # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_smtp_manager.py      # SMTP tests
pytest tests/test_excel_importer.py    # Excel import tests
pytest tests/test_template_renderer.py # Template tests
pytest tests/test_worker.py            # Worker thread tests
pytest tests/test_performance.py       # Performance tests

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Categories
- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Property-Based Tests**: Test with generated inputs (Hypothesis)
- **Performance Tests**: Test with large datasets (10,000+ recipients)
- **Error Scenario Tests**: Test error handling and recovery

## Requirements

- Python 3.10+
- PyQt6 (GUI framework)
- pandas (Excel data manipulation)
- openpyxl (Excel file reading)
- Jinja2 (Template rendering)
- keyring (Secure credential storage)
- pytest (Testing framework)
- hypothesis (Property-based testing)

## Security

- **Passwords**: Stored securely in OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Config Files**: Never contain plaintext passwords
- **Logs**: Credentials automatically redacted
- **TLS**: Certificate validation enabled by default
- **Encryption**: Support for SSL and STARTTLS

## License

TBD

## Support

For issues, questions, or feature requests, please open an issue on the project repository.
