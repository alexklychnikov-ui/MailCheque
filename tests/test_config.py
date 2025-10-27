import unittest
import sys
import tempfile
import os
from datetime import date
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Создаем временный файл конфигурации
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.config = Config(self.temp_file.name)
        
    def tearDown(self):
        # Удаляем временный файл
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
            
    def test_default_config(self):
        """Тест значений по умолчанию"""
        self.assertEqual(self.config.email, "")
        self.assertEqual(self.config.password, "")
        self.assertEqual(self.config.folder, "INBOX")
        self.assertEqual(self.config.imap_server, "imap.mail.ru")
        self.assertEqual(self.config.imap_port, 993)
        
    def test_save_and_load(self):
        """Тест сохранения и загрузки конфигурации"""
        # Устанавливаем значения
        self.config.email = "test@yandex.ru"
        self.config.password = "test_password"
        self.config.folder = "TestFolder"
        self.config.start_date = date(2024, 1, 1)
        self.config.end_date = date(2024, 12, 31)
        
        # Сохраняем
        self.config.save_config()
        
        # Создаем новый объект конфигурации
        new_config = Config(self.temp_file.name)
        
        # Проверяем, что значения загрузились
        self.assertEqual(new_config.email, "test@yandex.ru")
        self.assertEqual(new_config.password, "test_password")
        self.assertEqual(new_config.folder, "TestFolder")
        self.assertEqual(new_config.start_date, date(2024, 1, 1))
        self.assertEqual(new_config.end_date, date(2024, 12, 31))
        
    def test_date_properties(self):
        """Тест работы с датами"""
        test_date = date(2024, 6, 15)
        self.config.start_date = test_date
        self.assertEqual(self.config.start_date, test_date)
        
        # Проверяем, что дата сохранилась в конфиге
        self.assertEqual(self.config._config["last_start_date"], "2024-06-15")
        
    def test_update_method(self):
        """Тест метода update"""
        self.config.update(email="new@test.ru", folder="NewFolder")
        
        self.assertEqual(self.config.email, "new@test.ru")
        self.assertEqual(self.config.folder, "NewFolder")
        # Остальные параметры должны остаться без изменений
        self.assertEqual(self.config.password, "")
        
    def test_get_all(self):
        """Тест метода get_all"""
        all_config = self.config.get_all()
        
        self.assertIsInstance(all_config, dict)
        self.assertIn("email", all_config)
        self.assertIn("password", all_config)
        self.assertIn("folder", all_config)
        self.assertIn("imap_server", all_config)
        self.assertIn("imap_port", all_config)


if __name__ == '__main__':
    unittest.main()



