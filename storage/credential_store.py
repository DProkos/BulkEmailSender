"""
Credential Store for secure password management.

This module provides secure credential storage using OS keyring services
(Windows Credential Manager, macOS Keychain, Linux Secret Service) with
a fallback to encrypted local storage if keyring is unavailable.
"""

import keyring
import keyring.errors
from typing import Optional
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class CredentialStore:
    """
    Manages secure storage and retrieval of credentials.
    
    Uses OS keyring as primary storage method, with encrypted local
    storage as fallback when keyring is unavailable.
    """
    
    SERVICE_NAME = "BulkEmailSender"
    
    def __init__(self):
        """Initialize the credential store."""
        # Evaluate paths at runtime, not at class definition time
        self.FALLBACK_DIR = Path.home() / ".bulk_email_sender"
        self.FALLBACK_FILE = self.FALLBACK_DIR / "credentials.enc"
        self.KEY_FILE = self.FALLBACK_DIR / ".key"
        
        self._keyring_available = self._check_keyring_availability()
        if not self._keyring_available:
            self._setup_fallback_storage()
    
    def _check_keyring_availability(self) -> bool:
        """
        Check if OS keyring is available and functional.
        
        Returns:
            True if keyring is available, False otherwise.
        """
        try:
            # Try to get the current keyring backend
            backend = keyring.get_keyring()
            # Check if it's not the fail keyring (null backend)
            if backend.__class__.__name__ == 'fail.Keyring':
                return False
            
            # Try a test operation to verify it works
            test_service = f"{self.SERVICE_NAME}_test"
            test_username = "test_user"
            keyring.set_password(test_service, test_username, "test")
            result = keyring.get_password(test_service, test_username)
            keyring.delete_password(test_service, test_username)
            
            return result == "test"
        except (keyring.errors.KeyringError, Exception):
            return False
    
    def _setup_fallback_storage(self):
        """Setup encrypted local storage as fallback."""
        # Create directory if it doesn't exist
        self.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate or load encryption key
        if not self.KEY_FILE.exists():
            self._generate_encryption_key()
    
    def _generate_encryption_key(self):
        """Generate a new encryption key for fallback storage."""
        # Use machine-specific information to derive a key
        # This is not perfect security but better than plaintext
        import platform
        import getpass
        
        # Combine machine ID and username as salt
        machine_id = platform.node()
        username = getpass.getuser()
        salt = f"{machine_id}:{username}".encode()
        
        # Derive key using PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(salt))
        
        # Save key to file with restricted permissions
        self.KEY_FILE.write_bytes(key)
        # Set file permissions to owner read/write only (Unix-like systems)
        try:
            os.chmod(self.KEY_FILE, 0o600)
        except (OSError, AttributeError):
            # Windows doesn't support chmod in the same way
            pass
    
    def _get_encryption_key(self) -> bytes:
        """Load the encryption key for fallback storage."""
        if not self.KEY_FILE.exists():
            self._generate_encryption_key()
        return self.KEY_FILE.read_bytes()
    
    def _load_fallback_credentials(self) -> dict:
        """Load credentials from encrypted fallback storage."""
        if not self.FALLBACK_FILE.exists():
            return {}
        
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            encrypted_data = self.FALLBACK_FILE.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception:
            # If decryption fails, return empty dict
            return {}
    
    def _save_fallback_credentials(self, credentials: dict):
        """Save credentials to encrypted fallback storage."""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            json_data = json.dumps(credentials).encode()
            encrypted_data = fernet.encrypt(json_data)
            
            self.FALLBACK_FILE.write_bytes(encrypted_data)
            # Set file permissions to owner read/write only
            try:
                os.chmod(self.FALLBACK_FILE, 0o600)
            except (OSError, AttributeError):
                pass
        except Exception as e:
            raise RuntimeError(f"Failed to save credentials: {e}")
    
    def is_available(self) -> bool:
        """
        Check if credential storage is available.
        
        Returns:
            True if either keyring or fallback storage is available.
        """
        return self._keyring_available or self.FALLBACK_DIR.exists()
    
    def save_password(self, service: str, username: str, password: str):
        """
        Save password to secure storage.
        
        Args:
            service: Service identifier (e.g., "smtp")
            username: Username/email for the service
            password: Password to store
            
        Raises:
            RuntimeError: If storage operation fails
        """
        full_service = f"{self.SERVICE_NAME}:{service}"
        
        if self._keyring_available:
            try:
                keyring.set_password(full_service, username, password)
                return
            except keyring.errors.KeyringError as e:
                # If keyring fails, fall back to encrypted storage
                self._keyring_available = False
                self._setup_fallback_storage()
        
        # Use fallback storage
        credentials = self._load_fallback_credentials()
        if full_service not in credentials:
            credentials[full_service] = {}
        credentials[full_service][username] = password
        self._save_fallback_credentials(credentials)
    
    def get_password(self, service: str, username: str) -> Optional[str]:
        """
        Retrieve password from secure storage.
        
        Args:
            service: Service identifier (e.g., "smtp")
            username: Username/email for the service
            
        Returns:
            Password if found, None otherwise
        """
        full_service = f"{self.SERVICE_NAME}:{service}"
        
        if self._keyring_available:
            try:
                password = keyring.get_password(full_service, username)
                if password is not None:
                    return password
            except keyring.errors.KeyringError:
                # If keyring fails, fall back to encrypted storage
                self._keyring_available = False
                self._setup_fallback_storage()
        
        # Try fallback storage
        credentials = self._load_fallback_credentials()
        return credentials.get(full_service, {}).get(username)
    
    def delete_password(self, service: str, username: str):
        """
        Delete password from secure storage.
        
        Args:
            service: Service identifier (e.g., "smtp")
            username: Username/email for the service
            
        Raises:
            RuntimeError: If deletion fails
        """
        full_service = f"{self.SERVICE_NAME}:{service}"
        
        if self._keyring_available:
            try:
                keyring.delete_password(full_service, username)
                return
            except keyring.errors.PasswordDeleteError:
                # Password doesn't exist in keyring, try fallback
                pass
            except keyring.errors.KeyringError:
                # Keyring failed, switch to fallback
                self._keyring_available = False
                self._setup_fallback_storage()
        
        # Delete from fallback storage
        credentials = self._load_fallback_credentials()
        if full_service in credentials and username in credentials[full_service]:
            del credentials[full_service][username]
            if not credentials[full_service]:
                del credentials[full_service]
            self._save_fallback_credentials(credentials)
