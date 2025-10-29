import imaplib
import email
import ssl
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import chardet
from email.header import decode_header

def detect_charset(data: bytes) -> str:
    result = chardet.detect(data)
    return result['encoding'] or 'utf-8'

def decode_email_header(header):
    decoded_parts = decode_header(header)
    return ''.join([
        part.decode(encoding or detect_charset(part) if isinstance(part, bytes) else 'utf-8')
        if isinstance(part, bytes)
        else part
        for part, encoding in decoded_parts
    ])

def decode_email_body(raw_body: bytes) -> str:
    charset = detect_charset(raw_body)
    return raw_body.decode(charset, errors='replace')


class IMAPClient:
    def __init__(self, server: str = "imap.yandex.ru", port: int = 993):
        self.server = server
        self.port = port
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self._connected = False

    def connect(self, email: str, password: str) -> bool:
        """Подключиться к IMAP серверу"""
        try:
            # Создаем SSL контекст
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Подключаемся к серверу
            self.connection = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)
            
            # Логинимся (убираем лишние пробелы)
            clean_email = email.strip()
            clean_password = password.strip()
            self.connection.login(clean_email, clean_password)
            self._connected = True
            return True
            
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            # Для Mail.ru добавляем подсказку о пароле приложения
            if 'mail.ru' in self.server.lower():
                # Добавляем информацию о используемых параметрах (без пароля!)
                password_len = len(password.strip())
                raise Exception(
                    f"Ошибка аутентификации Mail.ru\n\n"
                    f"Используемые параметры:\n"
                    f"• Сервер: {self.server}:{self.port}\n"
                    f"• Email: {email.strip()}\n"
                    f"• Длина пароля: {password_len} символов\n\n"
                    f"Проверьте:\n"
                    f"✓ Email ПОЛНОСТЬЮ: логин@mail.ru (не просто 'логин')\n"
                    f"✓ Пароль приложения: должен быть 16 символов\n"
                    f"✓ IMAP включен: mail.ru → Настройки → Почтовые программы\n"
                    f"✓ Используется пароль ПРИЛОЖЕНИЯ, не основной\n\n"
                    f"Создать пароль: https://account.mail.ru/user/2-step-auth/passwords/\n\n"
                    f"Ошибка сервера: {error_msg}"
                )
            raise Exception(f"Ошибка аутентификации: {error_msg}\n\nПроверьте правильность email и пароля.")
        except ConnectionError as e:
            raise Exception(f"Ошибка подключения к серверу: {e}")
        except Exception as e:
            raise Exception(f"Неожиданная ошибка подключения: {e}")

    def disconnect(self) -> None:
        """Отключиться от сервера"""
        if self.connection and self._connected:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            finally:
                self._connected = False
                self.connection = None

    def is_connected(self) -> bool:
        """Проверить статус подключения"""
        return self._connected and self.connection is not None

    def select_folder(self, folder: str = "INBOX") -> bool:
        """Выбрать папку для работы"""
        if not self.is_connected():
            raise Exception("Нет подключения к серверу")
        
        try:
            status, messages = self.connection.select(folder)
            return status == 'OK'
        except Exception as e:
            raise Exception(f"Ошибка выбора папки {folder}: {e}")

    def search_emails_by_date(self, start_date: date, end_date: date) -> List[str]:
        """Поиск писем по дате"""
        if not self.is_connected():
            raise Exception("Нет подключения к серверу")

        try:
            from datetime import timedelta
            
            # Форматируем даты для поиска
            start_str = start_date.strftime("%d-%b-%Y")
            # Добавляем 1 день к конечной дате, чтобы включить её (BEFORE исключает указанную дату)
            end_date_inclusive = end_date + timedelta(days=1)
            end_str = end_date_inclusive.strftime("%d-%b-%Y")
            
            # Ищем письма в диапазоне дат (SINCE включает start_date, BEFORE исключает end_date_inclusive)
            search_criteria = f'(SINCE "{start_str}" BEFORE "{end_str}")'
            status, messages = self.connection.search(None, search_criteria)
            
            if status == 'OK':
                return messages[0].decode().split()
            else:
                raise Exception(f"Ошибка поиска писем: {messages}")
                
        except Exception as e:
            raise Exception(f"Ошибка поиска писем по дате: {e}")

    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Получить содержимое письма"""
        if not self.is_connected():
            raise Exception("Нет подключения к серверу")

        try:
            status, msg_data = self.connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                raise Exception(f"Ошибка получения письма {email_id}")
            
            # Парсим письмо
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Извлекаем данные
            subject = decode_email_header(email_message.get('Subject', ''))
            from_addr = decode_email_header(email_message.get('From', ''))
            date_str = email_message.get('Date', '')
            
            # Получаем тело письма
            body = self._extract_email_body(email_message)
            
            return {
                'id': email_id,
                'subject': subject,
                'from': from_addr,
                'date': date_str,
                'body': body,
                'raw_message': email_message
            }
            
        except Exception as e:
            raise Exception(f"Ошибка получения содержимого письма {email_id}: {e}")

    def _extract_email_body(self, email_message) -> str:
        """Извлечь текст из письма"""
        body = ""
        html_body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = decode_email_body(part.get_payload(decode=True))
                    except:
                        continue
                        
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        html_body = decode_email_body(part.get_payload(decode=True))
                    except:
                        continue
        else:
            try:
                content_type = email_message.get_content_type()
                if content_type == "text/plain":
                    body = decode_email_body(email_message.get_payload(decode=True))
                elif content_type == "text/html":
                    html_body = decode_email_body(email_message.get_payload(decode=True))
            except:
                pass
        
        # Если есть plain text, используем его, иначе HTML (очищенный от тегов)
        if body:
            return body
        elif html_body:
            # Удаляем HTML теги для извлечения текста
            import re
            text = re.sub(r'<[^>]+>', ' ', html_body)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        return ""

    def search_receipt_emails(self, start_date: date, end_date: date, folder: str = "INBOX") -> List[Dict[str, Any]]:
        """Поиск писем с чеками за указанный период"""
        try:
            # Выбираем папку
            if not self.select_folder(folder):
                raise Exception(f"Не удалось выбрать папку {folder}")
            
            # Ищем письма по дате
            email_ids = self.search_emails_by_date(start_date, end_date)
            
            if not email_ids:
                return []
            
            # Получаем содержимое писем
            emails = []
            for email_id in email_ids:
                try:
                    email_content = self.get_email_content(email_id)
                    emails.append(email_content)
                except Exception as e:
                    # Пропускаем проблемные письма
                    continue
            
            return emails
            
        except Exception as e:
            raise Exception(f"Ошибка поиска писем с чеками: {e}")

    def __enter__(self):
        # Обеспечиваем наличие соединения для контекст-менеджера, даже без логина
        if self.connection is None:
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.connection = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)
            except Exception:
                # Игнорируем ошибки создания соединения в __enter__
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Явно закрываем соединение, если объект соединения существует
        try:
            if self.connection is not None:
                try:
                    self.connection.close()
                except Exception:
                    pass
                try:
                    self.connection.logout()
                except Exception:
                    pass
        finally:
            self._connected = False
            self.connection = None
