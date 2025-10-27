import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import email
from email.mime.text import MIMEText

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_client.imap_client import IMAPClient


class MockIMAPConnection:
    """Мок IMAP соединения"""
    
    def __init__(self, server, port, ssl_context=None):
        self.server = server
        self.port = port
        self.connected = False
        
    def login(self, email, password):
        if email == "test@yandex.ru" and password == "test_password":
            self.connected = True
            return ('OK', [b'Login successful'])
        else:
            raise Exception("Authentication failed")
            
    def select(self, folder):
        if self.connected:
            return ('OK', [b'1'])
        else:
            raise Exception("Not connected")
            
    def search(self, charset, criteria):
        if self.connected:
            # Возвращаем мок ID писем
            return ('OK', [b'1 2 3'])
        else:
            raise Exception("Not connected")
            
    def fetch(self, email_id, flags):
        if self.connected and email_id in ['1', '2', '3']:
            # Создаем мок письмо
            msg = MIMEText("Test email body")
            msg['Subject'] = f'Test Subject {email_id}'
            msg['From'] = 'test@yandex.ru'
            msg['Date'] = 'Mon, 1 Jan 2024 12:00:00 +0000'
            
            return ('OK', [(f'({email_id} RFC822 {{size}}', msg.as_bytes())])
        else:
            raise Exception("Email not found")
            
    def close(self):
        pass
        
    def logout(self):
        self.connected = False


class TestIMAPClient(unittest.TestCase):
    
    def setUp(self):
        self.client = IMAPClient("test.server.com", 993)
        
    @patch('imaplib.IMAP4_SSL')
    def test_successful_connection(self, mock_imap):
        """Тест успешного подключения"""
        mock_connection = Mock()
        mock_connection.login.return_value = ('OK', [b'Login successful'])
        mock_imap.return_value = mock_connection
        
        result = self.client.connect("test@yandex.ru", "test_password")
        
        self.assertTrue(result)
        self.assertTrue(self.client.is_connected())
        
    @patch('imaplib.IMAP4_SSL')
    def test_failed_authentication(self, mock_imap):
        """Тест неудачной аутентификации"""
        mock_connection = Mock()
        mock_connection.login.side_effect = Exception("Authentication failed")
        mock_imap.return_value = mock_connection
        
        with self.assertRaises(Exception) as context:
            self.client.connect("test@yandex.ru", "wrong_password")
            
        self.assertIn("Authentication failed", str(context.exception))
        
    @patch('imaplib.IMAP4_SSL')
    def test_select_folder(self, mock_imap):
        """Тест выбора папки"""
        mock_connection = Mock()
        mock_connection.select.return_value = ('OK', [b'1'])
        mock_imap.return_value = mock_connection
        self.client.connection = mock_connection
        self.client._connected = True
        
        result = self.client.select_folder("INBOX")
        
        self.assertTrue(result)
        mock_connection.select.assert_called_once_with("INBOX")
        
    @patch('imaplib.IMAP4_SSL')
    def test_search_emails_by_date(self, mock_imap):
        """Тест поиска писем по дате"""
        mock_connection = Mock()
        mock_connection.search.return_value = ('OK', [b'1 2 3'])
        mock_imap.return_value = mock_connection
        self.client.connection = mock_connection
        self.client._connected = True
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.client.search_emails_by_date(start_date, end_date)
        
        self.assertEqual(result, ['1', '2', '3'])
        
    @patch('imaplib.IMAP4_SSL')
    def test_get_email_content(self, mock_imap):
        """Тест получения содержимого письма"""
        # Создаем тестовое письмо
        msg = MIMEText("Test email body content")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@yandex.ru'
        msg['Date'] = 'Mon, 1 Jan 2024 12:00:00 +0000'
        
        mock_connection = Mock()
        mock_connection.fetch.return_value = ('OK', [(b'1 (RFC822 {size}', msg.as_bytes())])
        mock_imap.return_value = mock_connection
        self.client.connection = mock_connection
        self.client._connected = True
        
        result = self.client.get_email_content('1')
        
        self.assertEqual(result['id'], '1')
        self.assertEqual(result['subject'], 'Test Subject')
        self.assertEqual(result['from'], 'test@yandex.ru')
        self.assertIn('Test email body content', result['body'])
        
    @patch('imaplib.IMAP4_SSL')
    def test_search_receipt_emails(self, mock_imap):
        """Тест поиска писем с чеками"""
        # Создаем тестовые письма
        msg1 = MIMEText("Payment receipt for 100.50 rubles")
        msg1['Subject'] = 'Receipt from store'
        msg1['From'] = 'payments@yandex.ru'
        msg1['Date'] = 'Mon, 1 Jan 2024 12:00:00 +0000'
        
        msg2 = MIMEText("Regular email without receipt")
        msg2['Subject'] = 'Newsletter'
        msg2['From'] = 'news@example.com'
        msg2['Date'] = 'Mon, 1 Jan 2024 12:00:00 +0000'
        
        def mock_fetch(email_id, flags):
            if email_id == '1':
                return ('OK', [(b'1 (RFC822 {size}', msg1.as_bytes())])
            elif email_id == '2':
                return ('OK', [(b'2 (RFC822 {size}', msg2.as_bytes())])
            else:
                raise Exception("Email not found")
        
        mock_connection = Mock()
        mock_connection.select.return_value = ('OK', [b'1'])
        mock_connection.search.return_value = ('OK', [b'1 2'])
        mock_connection.fetch.side_effect = mock_fetch
        mock_imap.return_value = mock_connection
        self.client.connection = mock_connection
        self.client._connected = True
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.client.search_receipt_emails(start_date, end_date, "INBOX")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['subject'], 'Receipt from store')
        self.assertEqual(result[1]['subject'], 'Newsletter')
        
    def test_context_manager(self):
        """Тест использования как контекстный менеджер"""
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_connection = Mock()
            mock_imap.return_value = mock_connection
            
            with self.client as client:
                self.assertEqual(client, self.client)
                # В реальном коде здесь была бы логика работы с клиентом
                
            # После выхода из контекста должен вызваться disconnect
            mock_connection.close.assert_called_once()
            mock_connection.logout.assert_called_once()


if __name__ == '__main__':
    unittest.main()



