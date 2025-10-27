import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Receipt:
    """Структура данных для чека"""
    name: str
    date: str
    amount: float
    email_id: str
    email_subject: str


class ReceiptParser:
    def __init__(self):
        # Паттерны для поиска сумм
        self.amount_patterns = [
            # YooMoney
            r'Пришло\s*(\d+[\s\.]?\d*)\s*₽',
            
            # Best2Pay / Taxcom / OFD кассовые чеки
            r'(\d+)\s+[xX]\s+(\d+[\.,]\d{2})\s+(\d+[\.,]\d{2})',  # "1 x 207000.00 207000.00"
            r'(\d+)\s+[xX]\s+(\d+[\.,]\d{2})',  # "1 X 2908.16"
            
            # Платформа ОФД / chek.pofd.ru / noreply@ofd.ru
            r'Безналичными\s*(\d+[\s\.]?\d*[\.,]\d{2})',
            r'(?:БЕЗНАЛИЧНЫМИ|ИТОГО):\s*(\d+[\s\.]?\d*[\.,]\d{2})',
            r'(?:БЕЗНАЛИЧНЫМИ|ИТОГ)\s*[=]?\s*(\d+[\s\.]?\d*[\.,]\d{2})',
            r'(\d+)\s+шт\.\s+x\s+(\d+[\.,]\d{2})',
            
            # Zerocoder / Paygine
            r'Сумма\s*(\d+[\s\.]?\d*[\.,]?\d*)\s*руб',  # "Сумма 207 000.00 руб" или "Сумма 207000 руб"
            r'(\d{3,}[\s\.]?\d{3,}[\.,]\d{2})\s*руб',  # "207 000.00 руб" или "207000.00 руб"
            
            # Sberbank ecom
            r'(\d+[\.,]\d{2})\s+RUB',
            
            # Яндекс.Касса
            r'чек.*?(\d+[\.,]\d{2})\s*руб',
            r'сумма.*?(\d+[\.,]\d{2})\s*руб',
            r'оплата.*?(\d+[\.,]\d{2})\s*руб',
            r'(\d+[\.,]\d{2})\s*руб.*?чек',
            
            # Общие паттерны сумм
            r'(\d+[\.,]\d{2})\s*₽',
            r'(\d+[\s\.]?\d*[\.,]\d{2})\s*руб',
            r'сумма.*?(\d+[\s\.]?\d*[\.,]\d{2})',
            r'итого.*?(\d+[\s\.]?\d*[\.,]\d{2})',
            r'payment.*?(\d+[\.,]\d{2})',
            
            # Паттерны для разных сервисов
            r'qiwi.*?(\d+[\.,]\d{2})',
            r'webmoney.*?(\d+[\.,]\d{2})',
            r'paypal.*?(\d+[\.,]\d{2})',
            r'сбер.*?(\d+[\.,]\d{2})',
            r'втб.*?(\d+[\.,]\d{2})',
        ]
        
        # Ключевые слова для определения чеков
        self.receipt_keywords = [
            'чек', 'receipt', 'платеж', 'оплата', 'перевод', 'покупка',
            'payment', 'transaction', 'bill', 'invoice', 'квитанция',
            'списание', 'пополнение', 'возврат', 'refund',
            'кассовый чек', 'успешная оплата', 'заказ успешно оплачен',
            'безналичными', 'итог', 'сумма по чеку', 'фискальный'
        ]
        
        # Паттерны для извлечения дат
        self.date_patterns = [
            r'\b(\d{4}[./]\d{1,2}[./]\d{1,2})\b',
            r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
            r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4})',
            r'(\d{1,2}\s+(?:янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)\s+\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})'
        ]
        
        # Словарь месяцев
        self.month_names = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
            'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
            'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12',
            'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
            'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
            'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }

    def is_receipt_email(self, email_data: Dict[str, Any]) -> bool:
        """Проверить, является ли письмо чеком"""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        from_addr = email_data.get('from', '').lower()
        
        # Проверяем отправителя (популярные платежные системы)
        payment_senders = [
            'yandex', 'qiwi', 'webmoney', 'paypal', 'sberbank',
            'vtb', 'tinkoff', 'alfa', 'gazprombank', 'raiffeisen',
            'mail.ru', 'my.mail.ru', 'money.mail.ru', 'cloud.mail.ru', 
            'chek.pofd.ru', 'noreply@chek.pofd.ru', 'platformaofd',
            'paygine.net', 'noreply@paygine.net',
            'ecom.sberbank.ru', 'info@ecom.sberbank.ru', 'sberprime',
            'yoomoney.ru', 'inform@yoomoney.ru', 'yandex.money',
            'taxcom.ru', 'noreply@taxcom.ru', 'sbis.ru',
            'best2pay.net', 'info@best2pay.net',
            'ofd.ru', 'noreply@ofd.ru', 'check.ofd.ru',
            'irkutskenergo', 'iesk.ru', 'энергосбыт'
        ]
        
        if any(sender in from_addr for sender in payment_senders):
            return True
        
        # Проверяем содержимое
        text_to_check = f"{subject} {body}"
        
        # Ищем ключевые слова
        if any(keyword in text_to_check for keyword in self.receipt_keywords):
            return True
        
        # Ищем суммы денег
        for pattern in self.amount_patterns:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return True
        
        return False

    def extract_amount(self, text: str) -> Optional[float]:
        """Извлечь сумму из текста"""
        text = text.replace(',', '.')
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Обрабатываем кортежи (для паттернов с несколькими группами)
                    if isinstance(matches[0], tuple):
                        # Для "N шт. x M.MM" (2 группы) - перемножаем
                        if len(matches[0]) == 2:
                            qty = float(matches[0][0].replace(' ', '').replace(',', '.'))
                            price = float(matches[0][1].replace(' ', '').replace(',', '.'))
                            return qty * price
                        # Для "1 x 207000.00 207000.00" (3 группы) - берем последнюю (итог)
                        elif len(matches[0]) == 3:
                            amount_str = matches[0][2]
                        else:
                            # Берем первую непустую группу
                            amount_str = next((g for g in matches[0] if g), None)
                            if not amount_str:
                                continue
                    else:
                        amount_str = matches[0]
                    
                    # Убираем пробелы из чисел типа "207 000.00"
                    amount_str = amount_str.replace(' ', '').replace(',', '.')
                    return float(amount_str)
                except (ValueError, AttributeError):
                    continue
        
        return None

    def extract_date(self, text: str) -> Optional[str]:
        """Извлечь дату из текста"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                try:
                    # Попытка парсинга разных форматов
                    return self._parse_date(date_str)
                except ValueError:
                    continue
        
        return None

    def _parse_date(self, date_str: str) -> str:
        """Парсить дату в разных форматах"""
        date_str = date_str.strip().lower()
        
        # Обработка формата с названием месяца
        for month_name, month_num in self.month_names.items():
            if month_name in date_str:
                # Заменяем название месяца на номер
                date_str = date_str.replace(month_name, month_num)
                break
        
        # Разные разделители
        for separator in ['/', '.', ' ', '-']:
            if separator in date_str:
                parts = date_str.split(separator)
                if len(parts) == 3:
                    try:
                        a, b, c = parts
                        # Определяем, что является годом
                        if len(a) == 4:
                            y, m, d = a, b, c
                        elif len(c) == 4:
                            # d.m.yyyy или m.d.yyyy — будем различать по допустимости дня/месяца
                            # Сначала пробуем d m yyyy, иначе m d yyyy
                            first_d, first_m = int(a), int(b)
                            if 1 <= first_d <= 31 and 1 <= first_m <= 12:
                                d, m, y = a, b, c
                            else:
                                m, d, y = a, b, c
                        else:
                            # Двузначный год -> приводим к 2000+год
                            yy = int(c)
                            y = f"20{yy:02d}"
                            # различаем d/m vs m/d по допустимости
                            first_d, first_m = int(a), int(b)
                            # При двузначном годе предпочтительно интерпретировать как d.m.yy, если допустимо
                            if 1 <= first_d <= 31 and 1 <= first_m <= 12:
                                d, m = a, b
                            else:
                                m, d = a, b
                        # Нормализуем ведущие нули
                        y = f"{int(y):04d}"
                        m = f"{int(m):02d}"
                        d = f"{int(d):02d}"
                        return f"{y}-{m}-{d}"
                    except:
                        continue
        
        # Если ничего не сработало, возвращаем как есть
        return date_str

    def extract_receipt_name(self, email_data: Dict[str, Any]) -> str:
        """Извлечь название чека"""
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Пытаемся найти название в теме
        if subject:
            # Убираем служебную информацию
            name = re.sub(r'\s*,\s*\d+[\.,]\d{2}\s*[₽руб].*$', '', subject, flags=re.IGNORECASE)
            name = re.sub(r'\s*\d+[\.,]\d{2}\s*руб.*$', '', name, flags=re.IGNORECASE)
            # name = re.sub(r'\s*-\s*\d+\s*$', '', name, flags=re.IGNORECASE)  # Оставляем номера заказов
            name = re.sub(r'\s*\+\s*\(\d+\)\s*подарок.*$', '', name, flags=re.IGNORECASE)  # Убираем "+ (1) подарок"
            name = re.sub(r'\s*чек.*$', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s*платеж.*$', '', name, flags=re.IGNORECASE)
            # Убираем висящие служебные части типа "на" в конце
            name = re.sub(r'\s+на\s*$', '', name, flags=re.IGNORECASE)
            name = name.strip()
            
            # Игнорируем слишком общие названия из темы
            generic_subjects = ['успешная оплата', 'ваш заказ оплачен', 'оплата заказа', 'платеж выполнен']
            if name and name.lower() not in generic_subjects:
                return name
        
        # Если в теме ничего не нашли, берем первые слова из тела
        if body:
            lines = body.split('\n')
            for line in lines[:5]:  # Проверяем первые 5 строк
                line = line.strip()
                if line and len(line) > 3:
                    # Убираем служебную информацию
                    clean_line = re.sub(r'\s*\d+[\.,]\d{2}\s*руб.*', '', line, flags=re.IGNORECASE)
                    clean_line = clean_line.strip()
                    if clean_line:
                        return clean_line[:50]  # Ограничиваем длину
        
        return "Неизвестный чек"

    def parse_receipts(self, emails: List[Dict[str, Any]]) -> List[Receipt]:
        """Парсить чеки из списка писем"""
        receipts = []
        
        for email_data in emails:
            if not self.is_receipt_email(email_data):
                continue
            
            try:
                # Извлекаем данные
                name = self.extract_receipt_name(email_data)
                amount = self.extract_amount(f"{email_data.get('subject', '')} {email_data.get('body', '')}")
                receipt_date = self.extract_date(f"{email_data.get('subject', '')} {email_data.get('body', '')}")
                
                # Если не удалось извлечь дату, используем дату письма
                if not receipt_date:
                    receipt_date = email_data.get('date', '')
                
                # Если не удалось извлечь сумму, пропускаем
                if amount is None:
                    continue
                
                receipt = Receipt(
                    name=name,
                    date=receipt_date,
                    amount=amount,
                    email_id=email_data.get('id', ''),
                    email_subject=email_data.get('subject', '')
                )
                
                receipts.append(receipt)
                
            except Exception as e:
                # Пропускаем проблемные письма
                continue
        
        return receipts

    def calculate_total(self, receipts: List[Receipt]) -> float:
        """Подсчитать общую сумму"""
        return sum(receipt.amount for receipt in receipts)

    def sort_receipts(self, receipts: List[Receipt], sort_by: str = 'date') -> List[Receipt]:
        """Сортировка чеков"""
        if sort_by == 'date':
            return sorted(receipts, key=lambda x: x.date, reverse=True)
        elif sort_by == 'amount':
            return sorted(receipts, key=lambda x: x.amount, reverse=True)
        elif sort_by == 'name':
            return sorted(receipts, key=lambda x: x.name)
        else:
            return receipts
