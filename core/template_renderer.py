"""Template rendering functionality using Jinja2."""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from jinja2 import Environment, BaseLoader, Template, Undefined

from models.template import EmailTemplate
from models.recipient import Recipient
from models.validation_result import ValidationResult


@dataclass
class RenderedEmail:
    """Represents a rendered email ready to send.
    
    Attributes:
        subject: Rendered subject line
        html_body: Rendered HTML body
        text_body: Rendered plain text body
    """
    subject: str
    html_body: str
    text_body: str


class TemplateRenderer:
    """Handles email template rendering with Jinja2.
    
    This class provides functionality to:
    - Render templates with recipient data
    - Extract template variables
    - Validate that all variables have corresponding data
    - Generate previews of rendered emails
    - Support company settings variables (company.*)
    """
    
    def __init__(self):
        """Initialize Jinja2 environment with autoescape enabled."""
        # Create environment for HTML templates with autoescape
        self.html_env = Environment(
            loader=BaseLoader(),
            autoescape=True,  # Always autoescape for HTML
            undefined=Undefined  # Missing variables become empty string
        )
        
        # Create environment for text templates without autoescape
        self.text_env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # No autoescape for plain text
            undefined=Undefined  # Missing variables become empty string
        )
        
        # Company settings (optional)
        self.company_settings = None
    
    def render(self, template: EmailTemplate, recipient: Recipient) -> RenderedEmail:
        """Render template with recipient data.
        
        Args:
            template: The email template to render
            recipient: The recipient whose data will be used for rendering
            
        Returns:
            RenderedEmail with subject, html_body, and text_body rendered
            
        Note:
            Missing variables are replaced with empty strings.
            The recipient's email is automatically included in the context.
            Company settings are available as company.* variables.
        """
        # Prepare context with recipient fields
        context = dict(recipient.fields)
        # Ensure email is always available
        context['email'] = recipient.email
        
        # Add company settings if available
        if self.company_settings:
            from dataclasses import asdict
            context['company'] = asdict(self.company_settings)
        
        # Render subject (use HTML env for safety)
        subject_template = self.html_env.from_string(template.subject)
        rendered_subject = subject_template.render(**context)
        
        # Render HTML body (use HTML env with autoescape)
        html_template = self.html_env.from_string(template.html_body)
        rendered_html = html_template.render(**context)
        
        # Render text body (use text env without autoescape)
        text_template = self.text_env.from_string(template.text_body)
        rendered_text = text_template.render(**context)
        
        return RenderedEmail(
            subject=rendered_subject,
            html_body=rendered_html,
            text_body=rendered_text
        )
    
    def find_variables(self, template_text: str) -> List[str]:
        """Extract all {{variable}} placeholders from template text.
        
        Args:
            template_text: The template text to search for variables
            
        Returns:
            List of unique variable names found in the template
            
        Note:
            Returns variables without the {{ }} delimiters.
            Duplicates are removed and order is preserved.
        """
        # Pattern to match {{variable_name}} with optional whitespace
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        matches = re.findall(pattern, template_text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_vars = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                unique_vars.append(var)
        
        return unique_vars
    
    def validate_variables(self, template: EmailTemplate, recipients: List[Recipient]) -> ValidationResult:
        """Check if all template variables exist in recipient data.
        
        Args:
            template: The email template to validate
            recipients: List of recipients to check against
            
        Returns:
            ValidationResult with warnings for missing variables
            
        Note:
            This checks all recipients and reports which variables are missing
            from at least one recipient's data.
        """
        # Extract variables from all template parts
        all_vars = set()
        all_vars.update(self.find_variables(template.subject))
        all_vars.update(self.find_variables(template.html_body))
        all_vars.update(self.find_variables(template.text_body))
        
        # Check which variables are missing from recipient data
        missing_vars = set()
        
        for recipient in recipients:
            # Create context with recipient fields and email
            available_fields = set(recipient.fields.keys())
            available_fields.add('email')  # email is always available
            
            # Find variables not in this recipient's data
            recipient_missing = all_vars - available_fields
            missing_vars.update(recipient_missing)
        
        # Generate warnings
        warnings = []
        if missing_vars:
            sorted_missing = sorted(missing_vars)
            warnings.append(
                f"The following variables are missing from at least one recipient: "
                f"{', '.join(sorted_missing)}"
            )
        
        # Validation is always "valid" but may have warnings
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=warnings
        )
    
    def preview(self, template: EmailTemplate, recipient: Recipient) -> str:
        """Generate HTML preview of rendered email.
        
        Args:
            template: The email template to preview
            recipient: The recipient whose data will be used
            
        Returns:
            HTML string showing the rendered email preview
        """
        rendered = self.render(template, recipient)
        
        # Create a simple HTML preview with subject and body
        preview_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .preview-container {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .subject {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
            color: #333;
        }}
        .body {{
            margin-top: 20px;
            line-height: 1.6;
        }}
        .recipient-info {{
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 3px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="recipient-info">
            <strong>Preview for:</strong> {recipient.email}
        </div>
        <div class="subject">
            Subject: {rendered.subject}
        </div>
        <div class="body">
            {rendered.html_body}
        </div>
    </div>
</body>
</html>
"""
        return preview_html
    
    def set_company_settings(self, company_settings):
        """
        Set company settings for template rendering.
        
        Args:
            company_settings: CompanySettings object
        """
        self.company_settings = company_settings
