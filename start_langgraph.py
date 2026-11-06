"""Start the project interpreter, wait for readiness, then open the chat UI."""

import argparse
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / '.venv' / 'Scripts' / 'python.exe'
URL = 'http://127.0.0.1:2024'
LOG_PATH = PROJECT_DIR / '.cache' / 'last_startup.log'


def server_ready() -> bool:
    try:
        with urllib.request.urlopen(URL + '/ok', timeout=1) as response:
            if response.status != 200:
                return False
        with urllib.request.urlopen(URL, timeout=1) as response:
            return b'/static/app.js' in response.read()
    except (OSError, urllib.error.URLError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description='Khoi dong web chatbot LangGraph')
    parser.add_argument('--no-browser', action='store_true', help='Khong tu mo trinh duyet')
    parser.add_argument('--restart', action='store_true', help='Dung may chu cua du an nay va khoi dong lai')
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    if args.restart:
        from server_process import restart_server

        print('Dang khoi dong lai may chu chatbot...', flush=True)
        restart_server(PROJECT_DIR)
    if server_ready():
        print(f'Chatbot da chay tai: {URL}', flush=True)
        if not args.no_browser:
            webbrowser.open(URL)
        return 0

    python = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f'Dang khoi dong chatbot. Vui long giu cua so nay mo.\nNhat ky: {LOG_PATH}', flush=True)

    # -m avoids broken executable launchers after moving or renaming a checkout.
    with LOG_PATH.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(
            [str(python), '-m', 'langgraph_cli', 'dev', '--host', '127.0.0.1', '--no-browser'],
            cwd=PROJECT_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        stopped = threading.Event()

        def wait_and_open():
            while not stopped.wait(.5):
                if process.poll() is not None:
                    return
                if server_ready():
                    print(f'\nCHATBOT SAN SANG: {URL}\nNhan Ctrl+C de dung.\n', flush=True)
                    if not args.no_browser:
                        webbrowser.open(URL)
                    return

        watcher = threading.Thread(target=wait_and_open, daemon=True)
        watcher.start()
        try:
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            code = process.wait()
        except KeyboardInterrupt:
            print('\nDang dung chatbot...', flush=True)
            if os.name == 'nt':
                # Include the venv launcher and spawned runtime worker; terminating
                # just the parent can leave a worker holding port 2024 open.
                subprocess.run(
                    ['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                )
            else:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            code = 0
        finally:
            stopped.set()
            watcher.join(timeout=2)
            if process.stdout:
                process.stdout.close()
        if code:
            print(f'\nKhong khoi dong duoc. Xem loi ben tren hoac file: {LOG_PATH}', file=sys.stderr)
        return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'Loi khi khoi dong LangGraph: {exc}', file=sys.stderr)
        raise SystemExit(1)
