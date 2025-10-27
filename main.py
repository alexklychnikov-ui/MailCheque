#!/usr/bin/env python3
"""
MailCheque - Приложение для поиска чеков в почте Yandex
"""

import sys
import os
from pathlib import Path

# Добавляем проект в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.app import main
    main()
except Exception as e:
    print(f"Ошибка запуска приложения: {e}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)



