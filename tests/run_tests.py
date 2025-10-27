#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь для импортов
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """Запуск всех тестов"""
    
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем код выхода
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name):
    """Запуск конкретного теста"""
    
    # Маппинг имен тестов
    test_modules = {
        'config': 'tests.test_config',
        'imap': 'tests.test_imap_client', 
        'parser': 'tests.test_receipt_parser',
        'logger': 'tests.test_logger'
    }
    
    if test_name not in test_modules:
        print(f"Доступные тесты: {', '.join(test_modules.keys())}")
        return 1
        
    module_name = test_modules[test_name]
    
    try:
        # Импортируем модуль тестов
        test_module = __import__(module_name, fromlist=[''])
        
        # Создаем тестовый набор
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Запускаем тесты
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"Ошибка импорта тестов: {e}")
        return 1

def main():
    """Главная функция"""
    
    if len(sys.argv) > 1:
        # Запуск конкретного теста
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        # Запуск всех тестов
        print("Запуск всех тестов...")
        return run_all_tests()

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
