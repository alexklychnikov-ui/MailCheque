import threading
import time
from datetime import date, datetime
from typing import List, Dict, Any

from src.config.settings import Config
from src.myEmail.imap_client import IMAPClient
from src.parser.receipt_parser import ReceiptParser, Receipt
from src.app_logging.logger import JSONLogger
from src.gui.main_window import MainWindow


class MailChequeApp:
    def __init__(self):
        self.config = Config()
        self.logger = JSONLogger()
        self.gui = MainWindow()
        
        # Устанавливаем обработчики событий GUI
        self.gui.on_settings_save = self._on_settings_save
        self.gui.on_search_receipts = self._on_search_receipts
        self.gui.on_date_range_change = self._on_date_range_change
        
        # Загружаем конфигурацию в GUI
        self.gui.update_config(self.config.get_all())
        
    def _on_settings_save(self, new_config: Dict[str, Any]):
        """Обработчик сохранения настроек"""
        try:
            self.config.update(**new_config)
            self.config.save_config()
            self.gui.update_config(self.config.get_all())
            self.gui.show_info("Настройки сохранены успешно")
        except Exception as e:
            self.gui.show_error(f"Ошибка сохранения настроек: {e}")
            
    def _on_date_range_change(self, start_date: date, end_date: date):
        """Обработчик изменения периода"""
        try:
            self.config.start_date = start_date
            self.config.end_date = end_date
            self.config.save_config()
            self.gui.update_config(self.config.get_all())
            self.gui.set_status(f"Период изменен: {start_date} - {end_date}")
        except Exception as e:
            self.gui.show_error(f"Ошибка изменения периода: {e}")
            
    def _on_search_receipts(self):
        """Обработчик поиска чеков"""
        # Запускаем поиск в отдельном потоке
        thread = threading.Thread(target=self._search_receipts_thread, daemon=True)
        thread.start()
        
    def _search_receipts_thread(self):
        """Поиск чеков в отдельном потоке"""
        start_time = time.time()
        status = "error"
        receipts_count = 0
        total_amount = 0.0
        error_message = ""
        
        try:
            self.gui.set_status("Подключение к почтовому серверу...", show_progress=True)
            
            # Создаем клиент и подключаемся
            with IMAPClient(self.config.imap_server, self.config.imap_port) as client:
                if not client.connect(self.config.email, self.config.password):
                    raise Exception("Не удалось подключиться к серверу")
                
                self.gui.set_status("Поиск писем за указанный период...")
                
                # Получаем письма из нескольких папок (Mail.ru автосортирует чеки)
                folders_to_check = [self.config.folder]
                
                # Для Mail.ru добавляем специальную папку для чеков
                if 'mail.ru' in self.config.imap_server.lower():
                    folders_to_check.append('INBOX/Receipts')
                
                all_emails = []
                for folder in folders_to_check:
                    try:
                        folder_emails = client.search_receipt_emails(
                            self.config.start_date,
                            self.config.end_date,
                            folder
                        )
                        all_emails.extend(folder_emails)
                    except:
                        # Если папка не существует, пропускаем
                        pass
                
                emails = all_emails
                
                if not emails:
                    self.gui.show_info("Письма за указанный период не найдены")
                    status = "success"
                else:
                    self.gui.set_status(f"Найдено {len(emails)} писем. Анализ чеков...")
                    
                    # Парсим чеки
                    parser = ReceiptParser()
                    receipts = parser.parse_receipts(emails)
                    
                    if receipts:
                        # Удаляем дубликаты (по дате + сумме)
                        receipts = self._remove_duplicates(receipts)
                        
                        # Сортируем по дате
                        receipts = parser.sort_receipts(receipts, 'date')
                        
                        # Подсчитываем общую сумму
                        total_amount = parser.calculate_total(receipts)
                        receipts_count = len(receipts)
                        
                        # Обновляем GUI в главном потоке
                        self.gui.root.after(0, lambda: self.gui.show_receipts(receipts, total_amount))
                        self.gui.root.after(0, lambda: self.gui.set_status(f"Найдено {receipts_count} чеков на сумму {total_amount:.2f} ₽"))
                        status = "success"
                    else:
                        self.gui.root.after(0, lambda: self.gui.show_info("В письмах не найдено чеков"))
                        status = "success"
                        
        except Exception as e:
            error_message = str(e)
            self.gui.root.after(0, lambda: self.gui.show_error(error_message))
            
        finally:
            # Останавливаем прогресс-бар
            self.gui.root.after(0, lambda: self.gui.set_status("Готов к работе"))
            
            # Логируем запрос
            duration = time.time() - start_time
            try:
                self.logger.log_request(
                    email=self.config.email,
                    folder=self.config.folder,
                    start_date=self.config.start_date.isoformat(),
                    end_date=self.config.end_date.isoformat(),
                    status=status,
                    receipts_count=receipts_count,
                    total_amount=total_amount,
                    error_message=error_message,
                    duration_seconds=duration
                )
            except Exception as e:
                # Если не удалось залогировать, просто игнорируем
                pass
                
    def _remove_duplicates(self, receipts: List[Receipt]) -> List[Receipt]:
        """Удаление дубликатов чеков по дате и сумме"""
        seen = set()
        unique_receipts = []
        
        for receipt in receipts:
            # Создаем ключ: дата + сумма (округленная до 2 знаков)
            key = (receipt.date, round(receipt.amount, 2))
            
            if key not in seen:
                seen.add(key)
                unique_receipts.append(receipt)
        
        return unique_receipts
    
    def run(self):
        """Запуск приложения"""
        try:
            self.gui.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Сохраняем конфигурацию
            self.config.save_config()
        except:
            pass


def main():
    """Главная функция"""
    app = MailChequeApp()
    app.run()


if __name__ == "__main__":
    main()
