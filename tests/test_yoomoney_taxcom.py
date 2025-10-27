import unittest
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.receipt_parser import ReceiptParser


class TestYooMoneyTaxcom(unittest.TestCase):
    """Тесты для писем от YooMoney и Taxcom/Best2Pay"""
    
    def setUp(self):
        self.parser = ReceiptParser()
    
    def test_yoomoney_incoming_payment(self):
        """Тест перевода от YooMoney"""
        email_data = {
            'id': '1',
            'subject': 'В кошелёк пришли деньги',
            'from': 'inform@yoomoney.ru',
            'body': '''
Ваш кошелёк *7765
Способ По номеру телефона (Сервис быстрых платежей)
Дата и время 11 октября 2025, 09:08 мск
Пришло 5 000 ₽
Баланс после операции 5 000 ₽
            ''',
            'date': 'Fri, 11 Oct 2025 09:08:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[YooMoney] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 5000.0)
        self.assertEqual(receipt.date, '2025-10-11')
    
    def test_best2pay_taxcom_receipt(self):
        """Тест кассового чека от Best2Pay/Taxcom"""
        email_data = {
            'id': '2',
            'subject': 'КАССОВЫЙ ЧЕК №: 4993',
            'from': 'noreply@taxcom.ru',
            'body': '''
ООО "БЕСТ2ПЕЙ"
КАССОВЫЙ ЧЕК №: 4993 05.10.25 16:53
СМЕНА: 24
ИНН 7813531811
127410, Москва г, Алтуфьевское ш, дом № 33Г
https://www.best2pay.net/
ПРИХОД
[vibe-code-pro] Тариф "VIP"
1 x 207000.00 207000.00
без НДС
Признак способа расчета ПРЕДОПЛАТА 100%
Признак предмета расчета УСЛУГА
Поставщик ООО <ЗЕРОКОДЕР>
ТЛФ.ПОСТ. +79269104992
ИНН ПОСТАВЩИКА 9715401631
ИТОГО:
207000.00
БЕЗНАЛИЧНЫМИ: 207000.00
ИТОГО без НДС: 207000.00
ТЛФ. ПОСТ.: +79269104992
ЭЛ.АДР.ОТПРАВИТЕЛЯ: info@best2pay.net
АГЕНТ АГЕНТ
САЙТ ФНС: www.nalog.gov.ru
ЭЛ.АДР.ПОКУПАТЕЛЯ alexandr_klychnikov@mail.ru
№ АВТ.: 3010001
СНО: ОСН
№ ККТ: 0007959695040547
№ ФН: 7384440900909661
№ ФД: 99138
ФП 2848648584
            ''',
            'date': 'Sat, 5 Oct 2025 16:53:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[Best2Pay] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 207000.0)
        self.assertEqual(receipt.date, '2025-10-05')
        self.assertTrue('4993' in receipt.name or 'КАССОВЫЙ' in receipt.name.upper())


    def test_irkutskenergo_ofd_receipt(self):
        """Тест чека за электричество от ОФД/Иркутскэнерго"""
        email_data = {
            'id': '3',
            'subject': 'Кассовый чек + (1) подарок. ООО "ИРКУТСКАЯ ЭНЕРГОСБЫТОВАЯ КОМПАНИЯ" 2908,16 руб',
            'from': 'noreply@ofd.ru',
            'body': '''
Кассовый чек / Приход
ООО "ИРКУТСКАЯ ЭНЕРГОСБЫТОВАЯ КОМПАНИЯ"
Номер ФД: #63525
ДАТА ВЫДАЧИ: 02.10.25 23:49
АДРЕС РАСЧЁТОВ: 664009 г.Иркутск ул.Красноярская д.35
МЕСТО РАСЧЁТОВ: офис
КАССИР: СИС. АДМИНИСТРАТОР
НОМЕР СМЕНЫ: #28
Номер чека за смену: #3644
ЭЛ. АДР. ПОКУПАТЕЛЯ: alexandr_klychnikov@mail.ru
ВЕРСИЯ ФФД: 1.05
Регистрационный номер ККТ: 0003732367058054
ИНН 3808166404
ФН 7384440900744688
ФПД 3540083616
ОФД: ООО ПС СТ
Адрес проверки чека в ОФД: check.ofd.ru

ЛС: ИЭСБК0068198 За услуги ООО "Иркутскэнергосбыт"
1 X 2908.16
в т.ч. СУММА НДС 20% = 2908.16
ПРИЗНАК ПРЕДМЕТА РАСЧЕТА: УСЛУГА

ИТОГ: 2908.16
Сумма по чеку (БСО) встречным предоставлением: 0.00
Наличными: 0.00
Безналичными: 2908.16
в т.ч. налоги СУММА НДС 20%: 484.69
Система налогообложения: ОСН
            ''',
            'date': 'Wed, 2 Oct 2025 23:49:00 +0000'
        }
        
        # Проверяем, что письмо определяется как чек
        self.assertTrue(self.parser.is_receipt_email(email_data))
        
        # Парсим чек
        receipts = self.parser.parse_receipts([email_data])
        self.assertEqual(len(receipts), 1)
        
        receipt = receipts[0]
        print(f"\n[Иркутскэнерго/ОФД] Дата: {receipt.date}, Тема: {receipt.name}, Сумма: {receipt.amount} руб")
        
        # Проверяем извлеченные данные
        self.assertEqual(receipt.amount, 2908.16)
        self.assertEqual(receipt.date, '2025-10-02')
        self.assertTrue('ИРКУТСКАЯ' in receipt.name.upper() or 'ЭНЕРГОСБЫТОВАЯ' in receipt.name.upper() or 'КАССОВЫЙ' in receipt.name.upper())


if __name__ == '__main__':
    unittest.main()

