"""
Configuration Manager for JSON config persistence.

This module provides configuration management for non-sensitive settings
such as SMTP configuration (without password), user preferences, and
application settings. Sensitive data like passwords are stored separately
using the CredentialStore.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigManager:
    """
    Manages application configuration in JSON format.
    
    Handles non-sensitive settings including:
    - SMTP configuration (host, port, username, encryption settings)
    - User preferences (window size, last used paths)
    - Application defaults (throttle rate, max retries)
    - Email template (subject, body, attachments)
    
    Sensitive data (passwords) are NOT stored here - use CredentialStore instead.
    """
    
    DEFAULT_CONFIG = {
        "smtp": {
            "host": "",
            "port": 587,
            "username": "",
            "use_ssl": False,
            "use_starttls": True,
            "from_name": "",
            "reply_to": "",
            "validate_certs": True
        },
        "preferences": {
            "window_width": 1024,
            "window_height": 768,
            "last_excel_path": "",
            "default_throttle_ms": 2000,
            "max_retries": 3
        },
        "template": {
            "subject": "",
            "html_body": "",
            "text_body": "",
            "unsubscribe_link": "",
            "attachments": []
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to config file. If not provided,
                        uses default location: ~/.bulk_email_sender/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default location
            config_dir = Path.home() / ".bulk_email_sender"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"
        
        # Load existing config or create default
        self.config = self._load_or_create_default()
    
    def _load_or_create_default(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if not exists.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_with_defaults(config)
            except (json.JSONDecodeError, IOError) as e:
                # If config is corrupted, create backup and use defaults
                if self.config_path.exists():
                    backup_path = self.config_path.with_suffix('.json.bak')
                    self.config_path.rename(backup_path)
                import copy
                return copy.deepcopy(self.DEFAULT_CONFIG)
        else:
            # Create default config
            import copy
            return copy.deepcopy(self.DEFAULT_CONFIG)
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults to ensure all keys exist.
        
        Args:
            config: Loaded configuration dictionary
        
        Returns:
            Merged configuration with all default keys
        """
        import copy
        merged = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # Deep merge for nested dictionaries
        for section, values in config.items():
            if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        
        return merged
    
    def save_config(self):
        """
        Save current configuration to JSON file.
        
        Raises:
            IOError: If unable to write to config file
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write config with pretty formatting
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Failed to save configuration: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Reload configuration from file.
        
        Returns:
            Current configuration dictionary
        """
        self.config = self._load_or_create_default()
        return self.config
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Configuration section (e.g., "smtp", "preferences")
            key: Optional key within section. If None, returns entire section
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Examples:
            >>> config.get("smtp", "host")
            "smtp.gmail.com"
            >>> config.get("smtp")
            {"host": "smtp.gmail.com", "port": 587, ...}
        """
        if section not in self.config:
            return default
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            section: Configuration section (e.g., "smtp", "preferences")
            key: Key within section
            value: Value to set
        
        Note:
            This only updates the in-memory config. Call save_config() to persist.
        
        Examples:
            >>> config.set("smtp", "host", "smtp.gmail.com")
            >>> config.save_config()
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def set_section(self, section: str, values: Dict[str, Any]):
        """
        Set entire configuration section.
        
        Args:
            section: Configuration section (e.g., "smtp", "preferences")
            values: Dictionary of values to set
        
        Note:
            This only updates the in-memory config. Call save_config() to persist.
        
        Examples:
            >>> config.set_section("smtp", {
            ...     "host": "smtp.gmail.com",
            ...     "port": 587,
            ...     "username": "user@example.com"
            ... })
            >>> config.save_config()
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
    
    def reset_to_defaults(self):
        """
        Reset configuration to default values.
        
        Note:
            This only updates the in-memory config. Call save_config() to persist.
        """
        import copy
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """
        Get SMTP configuration section.
        
        Returns:
            SMTP configuration dictionary (without password)
        """
        return self.config.get("smtp", {}).copy()
    
    def set_smtp_config(self, host: str, port: int, username: str,
                       use_ssl: bool = False, use_starttls: bool = True,
                       from_name: str = "", reply_to: str = "",
                       validate_certs: bool = True):
        """
        Set SMTP configuration.
        
        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP username/email
            use_ssl: Whether to use SSL encryption
            use_starttls: Whether to use STARTTLS encryption
            from_name: Optional "From" name
            reply_to: Optional "Reply-To" email address
            validate_certs: Whether to validate TLS certificates
        
        Note:
            Password is NOT stored here. Use CredentialStore.save_password() instead.
            This only updates the in-memory config. Call save_config() to persist.
        """
        self.config["smtp"] = {
            "host": host,
            "port": port,
            "username": username,
            "use_ssl": use_ssl,
            "use_starttls": use_starttls,
            "from_name": from_name,
            "reply_to": reply_to,
            "validate_certs": validate_certs
        }
    
    def get_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences section.
        
        Returns:
            Preferences dictionary
        """
        return self.config.get("preferences", {}).copy()
    
    def set_preference(self, key: str, value: Any):
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        
        Note:
            This only updates the in-memory config. Call save_config() to persist.
        """
        if "preferences" not in self.config:
            self.config["preferences"] = {}
        
        self.config["preferences"][key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if key not found
        
        Returns:
            Preference value or default
        """
        return self.config.get("preferences", {}).get(key, default)

    def get_template_config(self) -> Dict[str, Any]:
        """
        Get saved template configuration.
        
        Returns:
            Template configuration dictionary
        """
        return self.config.get("template", {}).copy()
    
    def set_template_config(self, subject: str, html_body: str, text_body: str,
                           unsubscribe_link: str = "", attachments: List[str] = None):
        """
        Set template configuration.
        
        Args:
            subject: Email subject
            html_body: HTML body content
            text_body: Plain text body content
            unsubscribe_link: Unsubscribe link URL
            attachments: List of attachment file paths
        
        Note:
            This only updates the in-memory config. Call save_config() to persist.
        """
        self.config["template"] = {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "unsubscribe_link": unsubscribe_link,
            "attachments": attachments or []
        }
