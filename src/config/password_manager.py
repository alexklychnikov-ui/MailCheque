"""
Модуль для безопасного хранения паролей с шифрованием
"""
import os
import base64
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordManager:
    """Менеджер для шифрования/дешифрования паролей"""
    
    def __init__(self, key_file: str = ".key"):
        self.key_file = Path(key_file)
        self._cipher = None
    
    def _get_machine_id(self) -> bytes:
        """Получить уникальный идентификатор машины"""
        machine_id = os.environ.get('COMPUTERNAME', '') + os.environ.get('USERNAME', '')
        if not machine_id:
            import platform
            machine_id = platform.node() + platform.system()
        return machine_id.encode()
    
    def _derive_key(self, salt: bytes) -> bytes:
        """Создать ключ шифрования на основе машины"""
        machine_id = self._get_machine_id()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))
        return key
    
    def _ensure_key(self) -> None:
        """Убедиться что ключ существует"""
        if not self.key_file.exists():
            salt = os.urandom(16)
            self.key_file.write_bytes(salt)
        
        if self._cipher is None:
            salt = self.key_file.read_bytes()
            key = self._derive_key(salt)
            self._cipher = Fernet(key)
    
    def encrypt(self, password: str) -> str:
        """Зашифровать пароль"""
        if not password:
            return ""
        self._ensure_key()
        encrypted = self._cipher.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_password: str) -> str:
        """Расшифровать пароль"""
        if not encrypted_password:
            return ""
        try:
            self._ensure_key()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            return ""
    
    def is_encrypted(self, password: str) -> bool:
        """Проверить зашифрован ли пароль"""
        if not password:
            return False
        try:
            decrypted = self.decrypt(password)
            return decrypted != "" and decrypted != password
        except Exception:
            return False

