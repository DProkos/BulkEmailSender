"""Company settings data model for bulk email sender."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanySettings:
    """Represents company/business information for email templates.
    
    These settings can be used as variables in email templates using
    the format {{company.field_name}}, e.g., {{company.name}}, {{company.phone}}
    
    Attributes:
        name: Company name
        address: Physical address
        city: City
        postal_code: Postal/ZIP code
        country: Country
        phone: Phone number
        email: Company email address
        website: Company website URL
        logo_url: URL to company logo (optional)
        facebook: Facebook page URL (optional)
        twitter: Twitter handle (optional)
        linkedin: LinkedIn page URL (optional)
        instagram: Instagram handle (optional)
    """
    name: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    country: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    logo_url: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for template rendering."""
        return {
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'country': self.country,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'logo_url': self.logo_url or '',
            'facebook': self.facebook or '',
            'twitter': self.twitter or '',
            'linkedin': self.linkedin or '',
            'instagram': self.instagram or '',
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CompanySettings':
        """Create CompanySettings from dictionary."""
        return cls(
            name=data.get('name', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            postal_code=data.get('postal_code', ''),
            country=data.get('country', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            website=data.get('website', ''),
            logo_url=data.get('logo_url'),
            facebook=data.get('facebook'),
            twitter=data.get('twitter'),
            linkedin=data.get('linkedin'),
            instagram=data.get('instagram'),
        )
