import os
import subprocess
import shutil

def build_exe():
    # 1. Находим путь к Рабочему столу текущего пользователя
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # Проверка на случай, если папка пользователя на русском языке
    if not os.path.exists(desktop_path):
        desktop_path = os.path.join(os.path.expanduser("~"), "Рабочий стол")

    # Путь к папке nowalink на Рабочем столе
    target_dir = os.path.join(desktop_path, "nowalink")
    
    # Если папки еще нет, создаем её
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"[+] Создана папка: {target_dir}")
    else:
        print(f"[+] Папка найдена: {target_dir}")

    # Пути к файлам
    script_path = os.path.join(target_dir, "temp_shutdown.py")
    
    # 2. Создаем временный файл с кодом выключения
    shutdown_code = """import subprocess
subprocess.run(["shutdown", "/s", "/f", "/t", "0"])
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(shutdown_code)

    # 3. Запуск компиляции через PyInstaller
    print("[*] Начинаем сборку EXE файла...")
    try:
        subprocess.run([
            "pyinstaller", 
            "--clean",
            "--onefile", 
            f"--name=shutdown",                  # Имя готового файла: shutdown.exe
            f"--distpath={target_dir}",          # Сохранить готовый файл прямо в nowalink
            f"--workpath={os.path.join(target_dir, 'build')}", 
            f"--specpath={target_dir}",
            script_path
        ], check=True)
        
        print(f"\n[+] Готово! Файл 'shutdown.exe' успешно создан в папке 'nowalink'.")
        
        # 4. Полная очистка временного мусора сборщика
        shutil.rmtree(os.path.join(target_dir, 'build'), ignore_errors=True)
        os.remove(os.path.join(target_dir, 'shutdown.spec'))
        os.remove(script_path)
        
    except subprocess.CalledProcessError as e:
        print(f"[-] Ошибка при сборке: {e}")
    except FileNotFoundError:
        print("[-] Ошибка: PyInstaller не установлен в системе. Установи его командой: pip install pyinstaller")

if __name__ == "__main__":
    build_exe()
    # Окно не закроется, пока ты не нажмешь Enter
    input("\nНажми Enter для выхода...")
