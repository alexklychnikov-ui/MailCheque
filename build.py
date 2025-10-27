#!/usr/bin/env python3
"""
Скрипт для сборки приложения в .exe файл
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """Проверяем установлен ли PyInstaller"""
    try:
        import PyInstaller
        print(f"PyInstaller версия: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller не установлен. Устанавливаем...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller успешно установлен")
            return True
        except subprocess.CalledProcessError:
            print("Ошибка установки PyInstaller")
            return False


def clean_build_dirs():
    """Очищаем директории сборки"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Удаляем директорию {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Удаляем .spec файлы
    for spec_file in Path('.').glob('*.spec'):
        print(f"Удаляем файл {spec_file}...")
        spec_file.unlink()


def create_icon():
    """Создаем простую иконку если её нет"""
    icon_path = Path("icon.ico")
    
    if not icon_path.exists():
        print("Иконка не найдена. Создаем простую иконку...")
        
        # Создаем простую иконку с помощью PIL или используем встроенную
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Создаем изображение 64x64
            img = Image.new('RGBA', (64, 64), (70, 130, 180, 255))  # Steel blue
            draw = ImageDraw.Draw(img)
            
            # Рисуем простую иконку (конверт)
            draw.rectangle([10, 15, 54, 49], outline='white', width=2)
            draw.polygon([(10, 15), (32, 30), (54, 15)], fill='white')
            
            # Сохраняем как ICO
            img.save(icon_path, format='ICO')
            print(f"Иконка создана: {icon_path}")
            
        except ImportError:
            print("PIL не установлен. Создаем текстовую иконку...")
            
            # Создаем простую текстовую иконку
            with open("icon.ico", "wb") as f:
                # Минимальная ICO структура
                f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00')
                f.write(b'\x00' * 1128)  # Заполнитель
            
            print(f"Простая иконка создана: {icon_path}")


def build_executable():
    """Собираем исполняемый файл"""
    
    # Параметры сборки
    main_script = "main.py"
    app_name = "MailCheque"
    
    # Команда PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",  # Один файл
        "--windowed",  # Без консоли
        "--name", app_name,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        "--clean",  # Очистить кеш
        "--noconfirm",  # Не спрашивать подтверждение
    ]
    
    # Добавляем иконку если есть
    if Path("icon.ico").exists():
        cmd.extend(["--icon", "icon.ico"])
    
    # Добавляем скрытые импорты
    hidden_imports = [
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.simpledialog",
        "imaplib",
        "email",
        "email.mime.text",
        "email.mime.multipart",
        "ssl",
        "json",
        "threading",
        "datetime",
        "re",
        "pathlib",
        "tempfile",
        "dataclasses",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Добавляем данные
    data_files = [
        ("src", "src"),  # Исходный код
        ("config.json", "."),  # Конфигурация
    ]
    
    for src, dst in data_files:
        if Path(src).exists():
            cmd.extend(["--add-data", f"{src};{dst}"])
    
    # Основной скрипт
    cmd.append(main_script)
    
    print("Команда сборки:")
    print(" ".join(cmd))
    print()
    
    # Запускаем сборку
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Сборка успешно завершена!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("Ошибка сборки:")
        print(e.stdout)
        print(e.stderr)
        return False


def create_portable_package():
    """Создаем портативный пакет"""
    
    dist_dir = Path("dist")
    package_dir = Path("MailCheque_Portable")
    
    if not dist_dir.exists():
        print("Директория dist не найдена!")
        return False
    
    # Создаем директорию пакета
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Копируем исполняемый файл
    exe_files = list(dist_dir.glob("*.exe"))
    if exe_files:
        exe_file = exe_files[0]
        shutil.copy2(exe_file, package_dir / exe_file.name)
        print(f"Скопирован: {exe_file.name}")
    else:
        print("Исполняемый файл не найден в dist!")
        return False
    
    # Копируем дополнительные файлы
    additional_files = [
        "README.md",
        "config.json",
        "requirements.txt"
    ]
    
    for file_name in additional_files:
        if Path(file_name).exists():
            shutil.copy2(file_name, package_dir / file_name)
            print(f"Скопирован: {file_name}")
    
    # Создаем директории для логов и конфигурации
    (package_dir / "logs").mkdir()
    (package_dir / "config").mkdir()
    
    print(f"Портативный пакет создан: {package_dir}")
    return True


def main():
    """Главная функция"""
    
    print("=== Сборка MailCheque в .exe ===")
    print()
    
    # Проверяем PyInstaller
    if not check_pyinstaller():
        return 1
    
    print()
    
    # Очищаем старые файлы сборки
    print("Очистка старых файлов сборки...")
    clean_build_dirs()
    print()
    
    # Создаем иконку
    create_icon()
    print()
    
    # Собираем исполняемый файл
    print("Сборка исполняемого файла...")
    if not build_executable():
        return 1
    
    print()
    
    # Создаем портативный пакет
    print("Создание портативного пакета...")
    if not create_portable_package():
        return 1
    
    print()
    print("=== Сборка завершена успешно! ===")
    print("Исполняемый файл находится в директории: dist/")
    print("Портативный пакет: MailCheque_Portable/")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


