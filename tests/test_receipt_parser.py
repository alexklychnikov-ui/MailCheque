import unittest
import sys
from pathlib import Path
from datetime import date

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.receipt_parser import ReceiptParser, Receipt


class TestReceiptParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = ReceiptParser()
        
    def test_is_receipt_email_payment_senders(self):
        """Тест определения чека по отправителю"""
        email_data = {
            'subject': 'Test',
            'body': 'Test body',
            'from': 'payments@yandex.ru'
        }
        
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
    def test_is_receipt_email_keywords(self):
        """Тест определения чека по ключевым словам"""
        email_data = {
            'subject': 'Чек на покупку',
            'body': 'Обычное письмо',
            'from': 'test@example.com'
        }
        
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
    def test_is_receipt_email_amount_patterns(self):
        """Тест определения чека по паттернам сумм"""
        email_data = {
            'subject': 'Payment 150.75 rub',
            'body': 'Regular email',
            'from': 'test@example.com'
        }
        
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
    def test_is_receipt_email_not_receipt(self):
        """Тест что обычное письмо не определяется как чек"""
        email_data = {
            'subject': 'Newsletter',
            'body': 'Regular newsletter content',
            'from': 'news@example.com'
        }
        
        self.assertFalse(self.parser.is_receipt_email(email_data))
        
    def test_extract_amount_various_formats(self):
        """Тест извлечения сумм в разных форматах"""
        test_cases = [
            ("чек на 150.50 руб", 150.50),
            ("сумма 250,75 рублей", 250.75),
            ("оплата 1000.00 ₽", 1000.00),
            ("итого: 75.25", 75.25),
            ("payment 500.00", 500.00),
            ("нет суммы", None),
            ("", None)
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.parser.extract_amount(text)
                self.assertEqual(result, expected)
                
    def test_extract_date_various_formats(self):
        """Тест извлечения дат в разных форматах"""
        test_cases = [
            ("01.01.2024", "2024-01-01"),
            ("2024/12/31", "2024-12-31"),
            ("15 июн 2024", "2024-06-15"),
            ("1 jan 2024", "2024-01-01"),
            ("нет даты", None),
            ("", None)
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.parser.extract_date(text)
                if expected:
                    self.assertEqual(result, expected)
                else:
                    self.assertIsNone(result)
                    
    def test_extract_receipt_name_from_subject(self):
        """Тест извлечения названия чека из темы"""
        email_data = {
            'subject': 'Покупка в магазине на 150.50 руб',
            'body': ''
        }
        
        result = self.parser.extract_receipt_name(email_data)
        self.assertEqual(result, "Покупка в магазине")
        
    def test_extract_receipt_name_from_body(self):
        """Тест извлечения названия чека из тела письма"""
        email_data = {
            'subject': 'Чек',
            'body': 'Оплата за услуги связи\nСумма: 500 руб\nДата: 01.01.2024'
        }
        
        result = self.parser.extract_receipt_name(email_data)
        self.assertEqual(result, "Оплата за услуги связи")
        
    def test_parse_receipts_valid_emails(self):
        """Тест парсинга валидных писем с чеками"""
        emails = [
            {
                'id': '1',
                'subject': 'Покупка в магазине на 150.50 руб',
                'body': 'Дата: 01.01.2024\nСпасибо за покупку',
                'from': 'store@example.com',
                'date': 'Mon, 1 Jan 2024 12:00:00 +0000'
            },
            {
                'id': '2',
                'subject': 'Оплата услуг 250.75 рублей',
                'body': 'Чек на оплату коммунальных услуг\nДата: 15.06.2024',
                'from': 'utilities@example.com',
                'date': 'Mon, 15 Jun 2024 12:00:00 +0000'
            }
        ]
        
        result = self.parser.parse_receipts(emails)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "Покупка в магазине")
        self.assertEqual(result[0].amount, 150.50)
        self.assertEqual(result[1].name, "Оплата услуг")
        self.assertEqual(result[1].amount, 250.75)
        
    def test_parse_receipts_no_receipts(self):
        """Тест парсинга писем без чеков"""
        emails = [
            {
                'id': '1',
                'subject': 'Newsletter',
                'body': 'Regular newsletter content',
                'from': 'news@example.com',
                'date': 'Mon, 1 Jan 2024 12:00:00 +0000'
            }
        ]
        
        result = self.parser.parse_receipts(emails)
        self.assertEqual(len(result), 0)
        
    def test_calculate_total(self):
        """Тест подсчета общей суммы"""
        receipts = [
            Receipt("Чек 1", "2024-01-01", 100.50, "1", "Subject 1"),
            Receipt("Чек 2", "2024-01-02", 250.75, "2", "Subject 2"),
            Receipt("Чек 3", "2024-01-03", 75.25, "3", "Subject 3")
        ]
        
        total = self.parser.calculate_total(receipts)
        self.assertEqual(total, 426.50)
        
    def test_sort_receipts_by_date(self):
        """Тест сортировки чеков по дате"""
        receipts = [
            Receipt("Чек 1", "2024-01-01", 100.50, "1", "Subject 1"),
            Receipt("Чек 2", "2024-01-03", 250.75, "2", "Subject 2"),
            Receipt("Чек 3", "2024-01-02", 75.25, "3", "Subject 3")
        ]
        
        sorted_receipts = self.parser.sort_receipts(receipts, 'date')
        
        self.assertEqual(sorted_receipts[0].date, "2024-01-03")
        self.assertEqual(sorted_receipts[1].date, "2024-01-02")
        self.assertEqual(sorted_receipts[2].date, "2024-01-01")
        
    def test_sort_receipts_by_amount(self):
        """Тест сортировки чеков по сумме"""
        receipts = [
            Receipt("Чек 1", "2024-01-01", 100.50, "1", "Subject 1"),
            Receipt("Чек 2", "2024-01-02", 250.75, "2", "Subject 2"),
            Receipt("Чек 3", "2024-01-03", 75.25, "3", "Subject 3")
        ]
        
        sorted_receipts = self.parser.sort_receipts(receipts, 'amount')
        
        self.assertEqual(sorted_receipts[0].amount, 250.75)
        self.assertEqual(sorted_receipts[1].amount, 100.50)
        self.assertEqual(sorted_receipts[2].amount, 75.25)
        
    def test_sort_receipts_by_name(self):
        """Тест сортировки чеков по названию"""
        receipts = [
            Receipt("Чек C", "2024-01-01", 100.50, "1", "Subject 1"),
            Receipt("Чек A", "2024-01-02", 250.75, "2", "Subject 2"),
            Receipt("Чек B", "2024-01-03", 75.25, "3", "Subject 3")
        ]
        
        sorted_receipts = self.parser.sort_receipts(receipts, 'name')
        
        self.assertEqual(sorted_receipts[0].name, "Чек A")
        self.assertEqual(sorted_receipts[1].name, "Чек B")
        self.assertEqual(sorted_receipts[2].name, "Чек C")


if __name__ == '__main__':
    unittest.main()



