"""
Predefined email templates for common use cases.

These templates can be used as starting points and customized by users.
All templates support variables for personalization.

Standard Variables (available in all templates):
- {{name}} - Recipient name
- {{email}} - Recipient email
- {{company}} - Recipient company
- {{subject_prefix}} - Email subject prefix (e.g., [My Company])
- {{sender_name}} - Sender name
- {{reply_to}} - Reply-to email
- {{unsubscribe_link}} - Unsubscribe link
- {{tracking_id}} - Tracking ID for logs/queue
"""

from typing import Dict, List


class PredefinedTemplates:
    """Collection of predefined email templates."""
    
    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Get all predefined templates organized by category.
        
        Returns:
            Dictionary with template categories and their templates
        """
        return {
            'Marketing': {
                'Επαγγελματικό Ενημερωτικό': {
                    'subject': '{{subject_prefix}} {{name}} Νέα ενημέρωση για {{company}}',
                    'html_body': '''<!doctype html>
<html>
<body style="font-family:Arial, sans-serif; line-height:1.5;">
<p>Καλημέρα {{name}},</p>
<p>Επικοινωνώ για μια σύντομη ενημέρωση σχετικά με <b>{{company}}</b>.</p>
<p>
✅ Σημείο 1: {{point1}}<br>
✅ Σημείο 2: {{point2}}<br>
✅ Σημείο 3: {{point3}}
</p>
<p>Αν θέλετε, μπορώ να σας στείλω μια προτεινόμενη λύση/προσφορά με βάση αυτό που χρειάζεστε.</p>
<p>Με εκτίμηση,<br><b>{{sender_name}}</b></p>
<hr>
<p style="font-size:12px; color:#666;">
Reference: {{tracking_id}} | <a href="{{unsubscribe_link}}">Διαγραφή από τη λίστα</a>
</p>
</body>
</html>''',
                    'text_body': '''Καλημέρα {{name}},

Επικοινωνώ για μια σύντομη ενημέρωση σχετικά με {{company}}.

- Σημείο 1: {{point1}}
- Σημείο 2: {{point2}}
- Σημείο 3: {{point3}}

Με εκτίμηση,
{{sender_name}}

Reference: {{tracking_id}}
Διαγραφή από τη λίστα: {{unsubscribe_link}}'''
                }
            },
            'Follow-up': {
                'Υπενθύμιση / Follow-up': {
                    'subject': '{{subject_prefix}} Follow-up: {{topic}}',
                    'html_body': '''<!doctype html>
<html>
<body style="font-family:Arial, sans-serif; line-height:1.5;">
<p>Καλησπέρα {{name}},</p>
<p>Επανέρχομαι σχετικά με {{topic}}.</p>
<p>Αν θέλετε, μπορώ:</p>
<ol>
<li>να σας προτείνω την καλύτερη λύση,</li>
<li>να σας στείλω ενδεικτική προσφορά,</li>
<li>ή να κλείσουμε ένα σύντομο 10λεπτο τηλεφώνημα.</li>
</ol>
<p>Ευχαριστώ,<br>{{sender_name}}</p>
<hr>
<p style="font-size:12px; color:#666;">
<a href="{{unsubscribe_link}}">Unsubscribe</a> | Ref: {{tracking_id}}
</p>
</body>
</html>''',
                    'text_body': '''Καλησπέρα {{name}},

Επανέρχομαι σχετικά με {{topic}}.

Αν θέλετε, μπορώ:
1) να σας προτείνω την καλύτερη λύση,
2) να σας στείλω ενδεικτική προσφορά,
3) ή να κλείσουμε ένα σύντομο 10λεπτο τηλεφώνημα.

Ευχαριστώ,
{{sender_name}}

Unsubscribe: {{unsubscribe_link}}
Ref: {{tracking_id}}'''
                }
            },
            'Business': {
                'Τιμολόγιο / Invoice': {
                    'subject': '{{subject_prefix}} Invoice {{invoice_no}} | {{company}}',
                    'html_body': '''<!doctype html>
<html>
<body style="font-family:Arial,sans-serif;">
<p>Γεια σας {{name}},</p>
<p>Σας αποστέλλουμε το invoice <b>#{{invoice_no}}</b> για την υπηρεσία <b>{{service_name}}</b>.</p>
<p>
Ποσό: <b>{{amount}} {{currency}}</b><br>
Ημερομηνία: {{invoice_date}}<br>
Λήξη: {{due_date}}
</p>
<p>Επισυνάπτεται το παραστατικό (PDF). Για διευκρινίσεις απαντήστε σε αυτό το email.</p>
<p>Με εκτίμηση,<br><b>{{sender_name}}</b></p>
<hr>
<p style="font-size:12px;color:#666;">Ref: {{tracking_id}}</p>
</body>
</html>''',
                    'text_body': '''Γεια σας {{name}},

Σας αποστέλλουμε το invoice #{{invoice_no}} για την υπηρεσία {{service_name}}.

Ποσό: {{amount}} {{currency}}
Ημερομηνία: {{invoice_date}}
Λήξη: {{due_date}}

Επισυνάπτεται το παραστατικό (PDF). Για διευκρινίσεις απαντήστε σε αυτό το email.

Με εκτίμηση,
{{sender_name}}

Ref: {{tracking_id}}'''
                }
            },
            'Support': {
                'Support / Ticket Update': {
                    'subject': '{{subject_prefix}} Ticket #{{ticket_id}} – {{status}}',
                    'html_body': '''<!doctype html>
<html>
<body style="font-family:Arial,sans-serif;">
<p>Γεια σας {{name}},</p>
<p>Ενημέρωση για το ticket <b>#{{ticket_id}}</b>:</p>
<p>
<b>Κατάσταση:</b> {{status}}<br>
<b>Σημείωση τεχνικού:</b> {{note}}
</p>
<p><b>Επόμενο βήμα:</b> {{next_step}}</p>
<p>Με εκτίμηση,<br>{{sender_name}}</p>
<hr>
<p style="font-size:12px;color:#666;">Ref: {{tracking_id}}</p>
</body>
</html>''',
                    'text_body': '''Γεια σας {{name}},

Ενημέρωση για το ticket #{{ticket_id}}:

Κατάσταση: {{status}}
Σημείωση τεχνικού: {{note}}

Επόμενο βήμα: {{next_step}}

Με εκτίμηση,
{{sender_name}}

Ref: {{tracking_id}}'''
                }
            },
            'Events': {
                'Πρόσκληση σε Ραντεβού / Event': {
                    'subject': '{{subject_prefix}} Πρόσκληση: {{event_title}} ({{event_date}})',
                    'html_body': '''<!doctype html>
<html>
<body style="font-family:Arial,sans-serif;">
<p>Γεια σας {{name}},</p>
<p>Θα χαρούμε να σας δούμε στο <b>{{event_title}}</b>.</p>
<p>
📅 {{event_date}}<br>
🕒 {{event_time}}<br>
📍 {{event_location}}
</p>
<p>
<a href="{{rsvp_link}}" style="display:inline-block;padding:10px 14px;text-decoration:none;border:1px solid #333;border-radius:8px;">
Επιβεβαίωση συμμετοχής
</a>
</p>
<p>Με εκτίμηση,<br><b>{{sender_name}}</b></p>
<hr>
<p style="font-size:12px;color:#666;">
Unsubscribe: <a href="{{unsubscribe_link}}">Διαγραφή</a> | Ref: {{tracking_id}}
</p>
</body>
</html>''',
                    'text_body': '''Γεια σας {{name}},

Θα χαρούμε να σας δούμε στο {{event_title}}.

📅 {{event_date}}
🕒 {{event_time}}
📍 {{event_location}}

Επιβεβαίωση συμμετοχής: {{rsvp_link}}

Με εκτίμηση,
{{sender_name}}

Unsubscribe: {{unsubscribe_link}}
Ref: {{tracking_id}}'''
                }
            }
        }
    
    @staticmethod
    def get_template_list() -> List[Dict[str, str]]:
        """
        Get a flat list of all templates with their metadata.
        
        Returns:
            List of dictionaries with template information
        """
        templates = []
        all_templates = PredefinedTemplates.get_all_templates()
        
        for category, category_templates in all_templates.items():
            for name, template in category_templates.items():
                templates.append({
                    'category': category,
                    'name': name,
                    'subject': template['subject'],
                    'html_body': template['html_body'],
                    'text_body': template['text_body']
                })
        
        return templates
    
    @staticmethod
    def get_excel_header_template() -> str:
        """
        Get recommended Excel header template for importing recipients.
        
        Returns:
            Comma-separated header string
        """
        return "email,name,company,subject_prefix,point1,point2,point3,topic,invoice_no,service_name,amount,currency,invoice_date,due_date,ticket_id,status,note,next_step,event_title,event_date,event_time,event_location,rsvp_link,sender_name,tracking_id"
    
    @staticmethod
    def get_standard_variables() -> List[Dict[str, str]]:
        """
        Get list of standard variables available in all templates.
        
        Returns:
            List of dictionaries with variable information
        """
        return [
            {'name': 'name', 'description': 'Όνομα παραλήπτη'},
            {'name': 'email', 'description': 'Email παραλήπτη'},
            {'name': 'company', 'description': 'Εταιρεία παραλήπτη'},
            {'name': 'subject_prefix', 'description': 'Πρόθεμα θέματος (π.χ. [My Company])'},
            {'name': 'sender_name', 'description': 'Όνομα αποστολέα'},
            {'name': 'reply_to', 'description': 'Reply-to email'},
            {'name': 'unsubscribe_link', 'description': 'Link διαγραφής από λίστα'},
            {'name': 'tracking_id', 'description': 'ID παρακολούθησης για logs'},
        ]
