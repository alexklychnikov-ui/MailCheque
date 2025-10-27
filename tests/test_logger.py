import unittest
import sys
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app_logging.logger import JSONLogger


class TestJSONLogger(unittest.TestCase):
    
    def setUp(self):
        # Создаем временный файл для логов
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.logger = JSONLogger(self.temp_file.name)
        
    def tearDown(self):
        # Удаляем временный файл и директорию
        try:
            os.unlink(self.temp_file.name)
            # Удаляем директорию логов если она пустая
            logs_dir = Path(self.temp_file.name).parent
            if logs_dir.exists() and not any(logs_dir.iterdir()):
                logs_dir.rmdir()
        except:
            pass
            
    def test_log_request_success(self):
        """Тест логирования успешного запроса"""
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="success",
            receipts_count=5,
            total_amount=1250.75,
            duration_seconds=10.5
        )
        
        logs = self.logger.get_recent_logs(1)
        self.assertEqual(len(logs), 1)
        
        log = logs[0]
        self.assertEqual(log["request"]["email"], "test@yandex.ru")
        self.assertEqual(log["request"]["folder"], "INBOX")
        self.assertEqual(log["result"]["status"], "success")
        self.assertEqual(log["result"]["receipts_count"], 5)
        self.assertEqual(log["result"]["total_amount"], 1250.75)
        self.assertEqual(log["result"]["duration_seconds"], 10.5)
        
    def test_log_request_error(self):
        """Тест логирования запроса с ошибкой"""
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="error",
            error_message="Connection failed"
        )
        
        logs = self.logger.get_recent_logs(1)
        self.assertEqual(len(logs), 1)
        
        log = logs[0]
        self.assertEqual(log["result"]["status"], "error")
        self.assertEqual(log["error"]["message"], "Connection failed")
        
    def test_multiple_logs(self):
        """Тест записи нескольких логов"""
        for i in range(5):
            self.logger.log_request(
                email=f"test{i}@yandex.ru",
                folder="INBOX",
                start_date="2024-01-01",
                end_date="2024-01-31",
                status="success",
                receipts_count=i,
                total_amount=i * 100.0
            )
            
        logs = self.logger.get_recent_logs(10)
        self.assertEqual(len(logs), 5)
        
        # Проверяем, что логи отсортированы по времени
        timestamps = [log["timestamp"] for log in logs]
        self.assertEqual(timestamps, sorted(timestamps))
        
    def test_get_logs_by_date(self):
        """Тест получения логов за определенный дату"""
        # Добавляем логи с разными датами
        self.logger.log_request(
            email="test1@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-01",
            status="success"
        )
        
        self.logger.log_request(
            email="test2@yandex.ru",
            folder="INBOX",
            start_date="2024-01-02",
            end_date="2024-01-02",
            status="success"
        )
        
        # Получаем логи за 1 января
        logs = self.logger.get_logs_by_date("2024-01-01T00:00:00", "2024-01-01T23:59:59")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["request"]["start_date"], "2024-01-01")
        
    def test_statistics(self):
        """Тест получения статистики"""
        # Добавляем тестовые логи
        self.logger.log_request(
            email="test1@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="success",
            receipts_count=5,
            total_amount=1000.0,
            duration_seconds=10.0
        )
        
        self.logger.log_request(
            email="test2@yandex.ru",
            folder="INBOX",
            start_date="2024-02-01",
            end_date="2024-02-28",
            status="success",
            receipts_count=3,
            total_amount=500.0,
            duration_seconds=5.0
        )
        
        self.logger.log_request(
            email="test3@yandex.ru",
            folder="INBOX",
            start_date="2024-03-01",
            end_date="2024-03-31",
            status="error",
            duration_seconds=2.0
        )
        
        stats = self.logger.get_statistics()
        
        self.assertEqual(stats["total_requests"], 3)
        self.assertEqual(stats["successful_requests"], 2)
        self.assertEqual(stats["failed_requests"], 1)
        self.assertEqual(stats["success_rate"], 66.66666666666666)
        self.assertEqual(stats["total_receipts"], 8)
        self.assertEqual(stats["total_amount"], 1500.0)
        self.assertEqual(stats["average_duration"], 5.666666666666667)
        
    def test_empty_statistics(self):
        """Тест статистики для пустого лога"""
        stats = self.logger.get_statistics()
        
        expected = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_receipts": 0,
            "total_amount": 0.0,
            "average_duration": 0.0
        }
        
        self.assertEqual(stats, expected)
        
    def test_clear_old_logs(self):
        """Тест очистки старых логов"""
        # Добавляем старый лог
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2020-01-01",
            end_date="2020-01-31",
            status="success"
        )
        
        # Добавляем новый лог
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="success"
        )
        
        # Очищаем логи старше 30 дней
        deleted_count = self.logger.clear_old_logs(30)
        
        self.assertEqual(deleted_count, 1)
        
        logs = self.logger.get_recent_logs(10)
        self.assertEqual(len(logs), 1)
        
    def test_export_logs_json(self):
        """Тест экспорта логов в JSON"""
        # Добавляем тестовый лог
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="success",
            receipts_count=2,
            total_amount=300.0
        )
        
        # Экспортируем в временный файл
        export_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        export_file.close()
        
        try:
            result = self.logger.export_logs(export_file.name, "json")
            self.assertTrue(result)
            
            # Проверяем содержимое экспортированного файла
            with open(export_file.name, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
                
            self.assertIn("logs", exported_data)
            self.assertEqual(len(exported_data["logs"]), 1)
            self.assertEqual(exported_data["logs"][0]["request"]["email"], "test@yandex.ru")
            
        finally:
            os.unlink(export_file.name)
            
    def test_export_logs_csv(self):
        """Тест экспорта логов в CSV"""
        # Добавляем тестовый лог
        self.logger.log_request(
            email="test@yandex.ru",
            folder="INBOX",
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="success",
            receipts_count=1,
            total_amount=150.0
        )
        
        # Экспортируем в временный файл
        export_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        export_file.close()
        
        try:
            result = self.logger.export_logs(export_file.name, "csv")
            self.assertTrue(result)
            
            # Проверяем, что файл создался и содержит данные
            self.assertTrue(os.path.exists(export_file.name))
            with open(export_file.name, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("test@yandex.ru", content)
                self.assertIn("150.0", content)
                
        finally:
            os.unlink(export_file.name)


if __name__ == '__main__':
    unittest.main()
