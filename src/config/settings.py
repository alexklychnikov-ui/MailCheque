import json
import os
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path
from .password_manager import PasswordManager


class Config:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        key_file = self.config_file.parent / ".key" if self.config_file.parent != Path(".") else Path(".key")
        self.password_manager = PasswordManager(str(key_file))
        self.default_config = {
            "email": "",
            "password": "",
            "folder": "INBOX",
            "last_start_date": self._get_month_start().isoformat(),
            "last_end_date": date.today().isoformat(),
            "imap_server": "imap.mail.ru",
            "imap_port": 993
        }
        self._config = self._load_config()
        self._migrate_plain_password()

    def _get_month_start(self) -> date:
        """Получить первый день текущего месяца"""
        today = date.today()
        return today.replace(day=1)

    def _load_config(self) -> Dict[str, Any]:
        """Загрузить конфигурацию из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except (json.JSONDecodeError, IOError):
                pass
        return self.default_config.copy()
    
    def _migrate_plain_password(self) -> None:
        """Мигрировать незашифрованный пароль в зашифрованный"""
        password = self._config.get("password", "")
        if password and not self._is_encrypted_format(password):
            encrypted = self.password_manager.encrypt(password)
            self._config["password"] = encrypted
            self.save_config()

    def _is_encrypted_format(self, password: str) -> bool:
        """Проверить является ли пароль зашифрованным"""
        if not password or len(password) < 20:
            return False
        try:
            decrypted = self.password_manager.decrypt(password)
            return decrypted != "" and decrypted != password
        except Exception:
            return False
    
    def save_config(self) -> None:
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise Exception(f"Ошибка сохранения конфигурации: {e}")

    @property
    def email(self) -> str:
        return self._config.get("email", "")

    @email.setter
    def email(self, value: str) -> None:
        self._config["email"] = value

    @property
    def password(self) -> str:
        encrypted = self._config.get("password", "")
        if encrypted:
            return self.password_manager.decrypt(encrypted)
        return ""

    @password.setter
    def password(self, value: str) -> None:
        if value:
            encrypted = self.password_manager.encrypt(value)
            self._config["password"] = encrypted
        else:
            self._config["password"] = ""

    @property
    def folder(self) -> str:
        return self._config.get("folder", "INBOX")

    @folder.setter
    def folder(self, value: str) -> None:
        self._config["folder"] = value

    @property
    def start_date(self) -> date:
        date_str = self._config.get("last_start_date", "")
        if date_str:
            try:
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                pass
        return self._get_month_start()

    @start_date.setter
    def start_date(self, value: date) -> None:
        self._config["last_start_date"] = value.isoformat()

    @property
    def end_date(self) -> date:
        date_str = self._config.get("last_end_date", "")
        if date_str:
            try:
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                pass
        return date.today()

    @end_date.setter
    def end_date(self, value: date) -> None:
        self._config["last_end_date"] = value.isoformat()

    @property
    def imap_server(self) -> str:
        return self._config.get("imap_server", "imap.yandex.ru")

    @property
    def imap_port(self) -> int:
        return self._config.get("imap_port", 993)

    def get_all(self) -> Dict[str, Any]:
        """Получить всю конфигурацию"""
        return self._config.copy()

    def update(self, **kwargs) -> None:
        """Обновить несколько параметров конфигурации"""
        for key, value in kwargs.items():
            if key in self._config:
                self._config[key] = value
