import os
import time
import random
import string
import subprocess
from pathlib import Path as P
from pywinauto import Application

# Строго 30 минут в секундах
SECONDS = 1800

def super_secure_delete(path):
    """ Намертво уничтожает физический файл на диске, затирая его случайным мусором """
    try:
        path = P(path)
        if path.is_file():
            file_size = path.stat().st_size
            if file_size > 0:
                with open(path, 'wb', buffering=0) as f:
                    f.write(os.urandom(file_size))
                with open(path, 'wb') as f:
                    f.truncate(1)
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            shredded_path = path.with_name(random_name)
            path.rename(shredded_path)
            shredded_path.unlink()
            return 1
    except OSError:
        pass
    return 0

def remove_recent_downloads(cutoff):
    """ Удаляет новые файлы из папки Загрузки """
    folder = P.home() / 'Downloads'
    count = 0
    if folder.exists():
        for path in folder.rglob('*'):
            try:
                if path.is_file() and path.stat().st_mtime >= cutoff:
                    count += super_secure_delete(path)
            except OSError:
                pass
    return count

def click_wyczysc_in_opera():
    """ Находит запущенную Оперу и программно кликает по кнопке Wyczyść """
    try:
        # Подключаемся к уже запущенному процессу Opera
        app = Application(backend="uia").connect(title_re=".*Opera.*", timeout=3)
        opera_window = app.window(title_re=".*Opera.*")
        
        # Находим кнопку очистки по тексту на польском/английском/русском
        # Скрипт ищет элемент интерфейса с текстом "Wyczyść"
        button = opera_window.child_window(title="Wyczyść", control_type="Button")
        
        if button.exists():
            # Нажимаем её системно, без физического движения курсора мыши
            button.invoke()
            print("[+] Кнопка 'Wyczyść' успешно нажата программно!")
            return True
        else:
            # Если панель скрыта, сначала откроем панель загрузок (Ctrl + J)
            opera_window.set_focus()
            import pyautogui
            pyautogui.hotkey('ctrl', 'j')
            time.sleep(0.5)
            button.invoke()
            pyautogui.hotkey('ctrl', 'w') # Закрываем вкладку загрузок обратно
            print("[+] Панель была скрыта, но мы её открыли и нажали 'Wyczyść'!")
            return True
            
    except Exception as e:
        print(f"[-] Не удалось нажать кнопку через интерфейс: {e}")
        return False

def main():
    cutoff = time.time() - SECONDS
    
    # Шаг 1: Стираем сам физический файл намертво, чтобы не восстановили софтом
    files_count = remove_recent_downloads(cutoff)
    print(f'Физических файлов уничтожено: {files_count}')
    
    # Шаг 2: Нажимаем кнопку очистки в интерфейсе запущенной Оперы
    click_wyczysc_in_opera()
    
    # Шаг 3: Аппаратный TRIM для SSD (гарантия невосстановимости файла)
    if files_count > 0:
        try:
            subprocess.run(['powershell', '-Command', 'Optimize-Volume -DriveLetter C -ReTrim'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

if __name__ == '__main__':
    main()
