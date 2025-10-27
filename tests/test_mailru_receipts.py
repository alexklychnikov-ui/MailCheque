import unittest
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.receipt_parser import ReceiptParser


class TestMailRuReceipts(unittest.TestCase):
    """Тесты для реальных писем с чеками из Mail.ru"""
    
    def setUp(self):
        self.parser = ReceiptParser()
    
    def test_platformaofd_sberprime_receipt(self):
        """Тест чека от Платформы ОФД - SberPrime"""
        email_data = {
            'id': '1',
            'subject': 'Ваш чек + (1) подарок. АО ЦПЛ, 2,99 ₽',
            'from': 'noreply@chek.pofd.ru',
            'body': '''
АКЦИОНЕРНОЕ ОБЩЕСТВО "ЦЕНТР ПРОГРАММ ЛОЯЛЬНОСТИ"
109316, 77, Москва г., Остаповский проезд, д.22, стр. 16
ИНН 7702770003
Место расчётов: http://sber.ru/sberprime
 
КАССОВЫЙ ЧЕК №2214
Приход
13.10.2025 04:51
Смена 73
Кассир Администратор
Телефон или электронный адрес покупателя
ALEXANDR_KLYCHNIKOV@MAIL.RU
Признак расчета в «Интернет»: Да
Электронный адрес отправителя: noreply@chek.pofd.ru
Применяемая система налогообложения: ОСН
признак ККТ для расчетов только в Интернет: Да

1: Подписка СберПрайм
1 шт. x 2.99
Общая стоимость позиции с учетом скидок и наценок: 2.99
Ставка НДС: ставка 20%
Способ расчета: ПОЛНЫЙ РАСЧЕТ
Признак предмета расчета: Услуга

ИТОГ = 2.99
НАЛИЧНЫМИ 0.00
БЕЗНАЛИЧНЫМИ 2.99
ЗАЧЕТ ПРЕДОПЛАТЫ (АВАНСА) 0.00
СУММА ПО ЧЕКУ (БСО) В КРЕДИТ 0.00
СУММА ПО ЧЕКУ (БСО) ВСТРЕЧНЫМ ПРЕДОСТАВЛЕНИЕМ 0.00
СУММА НДС ЧЕКА ПО СТАВКЕ 20% 0.50

N ФН 7382440900151358
Регистрационный номер ККТ 0007919614030306
N ФД 247662
ФПД 3661499184
Версия ФФД 1.2

Адрес для проверки чека: platformaofd.ru
Сайт ФНС: nalog.gov.ru
СПАСИБО ЗА ПОКУПКУ!
            ''',
            'date': 'Sun, 13 Oct 2025 09:52:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[Платформа ОФД] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 2.99)
        self.assertEqual(receipt.date, '2025-10-13')
        self.assertTrue('ЦПЛ' in receipt.name or 'Ваш' in receipt.name)
    
    def test_zerocoder_payment_receipt(self):
        """Тест чека от Zerocoder через Paygine"""
        email_data = {
            'id': '2',
            'subject': 'Успешная оплата',
            'from': 'noreply@paygine.net',
            'body': '''
Logo

Успешная оплата

Спасибо за оплату в ZEROCODER

Сумма
207 000.00 руб.

Номер заказа
699845423_15360

Описание
university.zerocoder.ru. Оплата заказа №699845423

Дата платежа
05 октября 2025 16:53

Способ оплаты
sbp

Кассовый чек
            ''',
            'date': 'Sat, 5 Oct 2025 21:53:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[Zerocoder] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 207000.00)
        self.assertEqual(receipt.date, '2025-10-05')
        self.assertTrue('ZEROCODER' in receipt.name.upper() or 'LOGO' in receipt.name.upper())
    
    def test_sberbank_ecom_receipt(self):
        """Тест чека от Сбербанк ecom - SberPrime"""
        email_data = {
            'id': '3',
            'subject': 'Ваш заказ успешно оплачен - 357961682',
            'from': 'info@ecom.sberbank.ru',
            'body': '''
Уведомление о заказе 357961682

4a17520d-30b8-47a8-bac6-911b3c008265_0f6ed179-5f4b-4447-9fa4-0504f8d52371

SberPrime

2.99 RUB

Оплата успешно проведена
13.08.2025 10:48:38 по карте 5469 **** **** 1240.
            ''',
            'date': 'Tue, 13 Aug 2025 15:48:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[Sberbank] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 2.99)
        self.assertEqual(receipt.date, '2025-08-13')
        self.assertIn('357961682', receipt.name)
    
    def test_all_receipts_batch(self):
        """Тест пакетной обработки всех писем"""
        emails = [
            {
                'id': '1',
                'subject': 'Ваш чек + (1) подарок. АО ЦПЛ, 2,99 ₽',
                'from': 'noreply@chek.pofd.ru',
                'body': 'КАССОВЫЙ ЧЕК №2214\n13.10.2025 04:51\nБЕЗНАЛИЧНЫМИ 2.99',
                'date': 'Sun, 13 Oct 2025 09:52:00 +0000'
            },
            {
                'id': '2',
                'subject': 'Успешная оплата',
                'from': 'noreply@paygine.net',
                'body': 'Сумма\n207 000.00 руб.\nДата платежа\n05 октября 2025 16:53',
                'date': 'Sat, 5 Oct 2025 21:53:00 +0000'
            },
            {
                'id': '3',
                'subject': 'Ваш заказ успешно оплачен - 357961682',
                'from': 'info@ecom.sberbank.ru',
                'body': 'SberPrime\n2.99 RUB\n13.08.2025 10:48:38',
                'date': 'Tue, 13 Aug 2025 15:48:00 +0000'
            }
        ]
        
        receipts = self.parser.parse_receipts(emails)
        
        print("\n=== Все чеки ===")
        for receipt in receipts:
            print(f"Дата: {receipt.date} | Название: {receipt.name} | Сумма: {receipt.amount} руб")
        
        # Проверяем, что все чеки распознаны
        self.assertEqual(len(receipts), 3)
        
        # Проверяем суммы
        amounts = [r.amount for r in receipts]
        self.assertIn(2.99, amounts)
        self.assertIn(207000.00, amounts)
        
        # Проверяем общую сумму
        total = self.parser.calculate_total(receipts)
        self.assertEqual(total, 207005.98)


if __name__ == '__main__':
    unittest.main()

