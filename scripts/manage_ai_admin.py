#!/usr/bin/env python3
"""
AI Admin Server Management Script

Универсальный скрипт для управления AI Admin сервером.
Проверяет состояние, запускает, останавливает и показывает логи.
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import psutil
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

def setup_environment():
    """Настраивает окружение для работы скрипта."""
    # Определяем каталог, где находится скрипт
    script_dir = Path(__file__).resolve().parent
    
    # Переходим в каталог скрипта
    os.chdir(script_dir)
    
    # Ищем виртуальное окружение
    venv_path = None
    
    # Проверяем стандартные места
    possible_venv_paths = [
        script_dir / ".venv",
        script_dir / "venv",
        script_dir / "env",
        script_dir.parent / ".venv",
        script_dir.parent / "venv",
        script_dir.parent / "env"
    ]
    
    for venv_path in possible_venv_paths:
        if venv_path.exists() and (venv_path / "bin" / "python").exists():
            break
    else:
        venv_path = None
    
    # Если нашли виртуальное окружение, активируем его
    if venv_path:
        python_path = venv_path / "bin" / "python"
        if python_path.exists():
            # Обновляем sys.executable для использования Python из venv
            sys.executable = str(python_path)
            # Обновляем PATH
            venv_bin = str(venv_path / "bin")
            if venv_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{venv_bin}:{os.environ.get('PATH', '')}"
            return str(python_path)
    
    # Если виртуальное окружение не найдено, используем системный Python
    return "python"

# Настраиваем окружение при импорте
PYTHON_CMD = setup_environment()

# Конфигурация
CONFIG_FILE = "../config/config.json"
PID_FILE = "/tmp/ai_admin_server.pid"
LOG_FILE = "/tmp/ai_admin_server.log"
SERVER_MODULE = "ai_admin.server"

def load_config():
    """Загружает конфигурацию из файла."""
    try:
        # Получаем абсолютный путь к конфигурационному файлу
        config_path = os.path.abspath(CONFIG_FILE)
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Извлекаем настройки сервера
            server_config = config.get("server", {})
            default_port = server_config.get("port", 8060)  # Изменено с 8000 на 8060
            default_host = server_config.get("host", "0.0.0.0")
            
            return {
                "port": default_port,
                "host": default_host,
                "debug": server_config.get("debug", False),
                "log_level": server_config.get("log_level", "INFO"),
                "full_config": config
            }
        else:
            # Возвращаем значения по умолчанию, если файл не найден
            return {
                "port": 8060,  # Изменено с 8000 на 8060
                "host": "0.0.0.0",
                "debug": False,
                "log_level": "INFO",
                "full_config": {}
            }
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        return {
            "port": 8000,
            "host": "0.0.0.0",
            "debug": False,
            "log_level": "INFO",
            "full_config": {}
        }

# Загружаем конфигурацию
CONFIG = load_config()
DEFAULT_PORT = CONFIG["port"]
DEFAULT_HOST = CONFIG["host"]

class Colors:
    """Цвета для вывода в терминал."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AIServerManager:
    """Менеджер для управления AI Admin сервером."""
    
    def __init__(self, port: int = DEFAULT_PORT, host: str = DEFAULT_HOST):
        self.port = port
        self.host = host
        self.pid_file = PID_FILE
        self.log_file = LOG_FILE
        self.config_file = CONFIG_FILE
        
    def print_status(self, message: str, color: str = Colors.WHITE, bold: bool = False):
        """Выводит сообщение с цветом."""
        style = Colors.BOLD if bold else ""
        print(f"{style}{color}{message}{Colors.END}")
    
    def print_header(self, title: str):
        """Выводит заголовок."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{Colors.END}\n")
    
    def check_port_usage(self) -> Optional[Dict[str, Any]]:
        """Проверяет использование порта."""
        try:
            # Проверяем через netstat
            result = subprocess.run(
                ["netstat", "-tlnp"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f":{self.port}" in line and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 7:
                            pid = parts[6].split('/')[0]
                            return {
                                "port": self.port,
                                "pid": pid,
                                "status": "occupied"
                            }
            
            # Альтернативная проверка через ss
            result = subprocess.run(
                ["ss", "-tlnp"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f":{self.port}" in line and "LISTEN" in line:
                        # Извлекаем PID из строки
                        import re
                        pid_match = re.search(r'pid=(\d+)', line)
                        if pid_match:
                            pid = pid_match.group(1)
                            return {
                                "port": self.port,
                                "pid": pid,
                                "status": "occupied"
                            }
            
            # Дополнительная проверка через curl для порта 8060
            if self.port == 8060:
                try:
                    result = subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                         f"http://localhost:{self.port}/health"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip() in ["200", "404", "405"]:
                        # Порт отвечает, но нужно найти PID
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                cmdline = " ".join(proc.info['cmdline'])
                                if "ai_admin" in cmdline and "8060" in cmdline:
                                    return {
                                        "port": self.port,
                                        "pid": proc.info['pid'],
                                        "status": "occupied"
                                    }
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return {"port": self.port, "status": "free"}
    
    def get_server_pid(self) -> Optional[int]:
        """Получает PID сервера из PID файла или ищет процесс."""
        # Сначала пробуем PID файл
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        return pid
        except (ValueError, IOError):
            pass
        
        # Если PID файл не помог, ищем процесс по команде
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = " ".join(proc.info['cmdline'])
                    if "ai_admin" in cmdline and "8060" in cmdline:
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return None
    
    def is_server_running(self) -> bool:
        """Проверяет, запущен ли сервер."""
        # Сначала проверяем через PID файл
        pid = self.get_server_pid()
        if pid:
            try:
                process = psutil.Process(pid)
                # Проверяем, что это действительно наш сервер
                cmdline = " ".join(process.cmdline())
                if "ai_admin" in cmdline or "python" in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Если PID файл не помог, ищем процесс по порту и команде
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = " ".join(proc.info['cmdline'])
                    # Проверяем, что это наш сервер
                    if ("ai_admin" in cmdline or "python -m ai_admin" in cmdline) and proc.info['pid'] == self.port_info.get('pid'):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Получает полную информацию о сервере."""
        port_status = self.check_port_usage()
        
        info = {
            "running": False,
            "pid": None,
            "port_status": port_status,
            "pid_file_exists": os.path.exists(self.pid_file),
            "log_file_exists": os.path.exists(self.log_file),
            "config_file_exists": os.path.exists(self.config_file),
            "uptime": None,
            "memory_usage": None,
            "cpu_usage": None
        }
        
        # Проверяем, запущен ли сервер
        if self.is_server_running():
            pid = self.get_server_pid()
            info["running"] = True
            info["pid"] = pid
        elif port_status["status"] == "occupied":
            # Если порт занят, но мы не нашли сервер через PID файл,
            # попробуем найти процесс по PID из порта
            try:
                port_pid = int(port_status["pid"])
                process = psutil.Process(port_pid)
                cmdline = " ".join(process.cmdline())
                if "ai_admin" in cmdline or "python -m ai_admin" in cmdline:
                    info["running"] = True
                    info["pid"] = port_pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                pass
        
        # Если сервер запущен, получаем дополнительную информацию
        if info["running"] and info["pid"]:
            try:
                process = psutil.Process(info["pid"])
                info["uptime"] = time.time() - process.create_time()
                info["memory_usage"] = process.memory_info().rss
                info["cpu_usage"] = process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return info
    
    def show_status(self):
        """Показывает статус сервера."""
        self.print_header("AI Admin Server Status")
        
        info = self.get_server_info()
        
        # Основной статус
        if info["running"]:
            self.print_status("🟢 Сервер ЗАПУЩЕН", Colors.GREEN, bold=True)
        else:
            self.print_status("🔴 Сервер ОСТАНОВЛЕН", Colors.RED, bold=True)
        
        print()
        
        # Детальная информация
        if info["pid"]:
            self.print_status(f"PID: {info['pid']}", Colors.CYAN)
            
            if info["uptime"]:
                uptime_seconds = int(info["uptime"])
                hours = uptime_seconds // 3600
                minutes = (uptime_seconds % 3600) // 60
                seconds = uptime_seconds % 60
                self.print_status(f"Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}", Colors.CYAN)
            
            if info["memory_usage"]:
                memory_mb = info["memory_usage"] / 1024 / 1024
                self.print_status(f"Использование памяти: {memory_mb:.1f} MB", Colors.CYAN)
            
            if info["cpu_usage"] is not None:
                self.print_status(f"Использование CPU: {info['cpu_usage']:.1f}%", Colors.CYAN)
        
        # Статус порта
        port_info = info["port_status"]
        if port_info["status"] == "occupied":
            if info["running"] and str(info["pid"]) == str(port_info["pid"]):
                self.print_status(f"Порт {self.port}: ЗАНЯТ (наш сервер)", Colors.GREEN)
            else:
                self.print_status(f"Порт {self.port}: ЗАНЯТ (PID: {port_info['pid']})", Colors.RED)
        else:
            self.print_status(f"Порт {self.port}: СВОБОДЕН", Colors.YELLOW)
        
        # Файлы
        print()
        self.print_status("Файлы:", Colors.BLUE, bold=True)
        self.print_status(f"PID файл: {'✅' if info['pid_file_exists'] else '❌'} {self.pid_file}")
        self.print_status(f"Лог файл: {'✅' if info['log_file_exists'] else '❌'} {self.log_file}")
        self.print_status(f"Конфиг файл: {'✅' if info['config_file_exists'] else '❌'} {self.config_file}")
        
        # Окружение
        print()
        self.print_status("Окружение:", Colors.BLUE, bold=True)
        self.print_status(f"Python: {PYTHON_CMD}")
        self.print_status(f"Рабочий каталог: {os.getcwd()}")
        
        # Проверяем виртуальное окружение
        venv_active = "VIRTUAL_ENV" in os.environ
        if venv_active:
            self.print_status(f"Виртуальное окружение: ✅ {os.environ['VIRTUAL_ENV']}", Colors.GREEN)
        else:
            # Проверяем, используем ли мы Python из venv
            if ".venv" in PYTHON_CMD or "venv" in PYTHON_CMD:
                self.print_status(f"Виртуальное окружение: ✅ {PYTHON_CMD}", Colors.GREEN)
            else:
                self.print_status("Виртуальное окружение: ❌ Не найдено", Colors.YELLOW)
        
        # Конфигурация
        print()
        self.print_status("Конфигурация:", Colors.BLUE, bold=True)
        self.print_status(f"Порт: {CONFIG['port']}")
        self.print_status(f"Хост: {CONFIG['host']}")
        self.print_status(f"Debug: {'✅' if CONFIG['debug'] else '❌'}")
        self.print_status(f"Log Level: {CONFIG['log_level']}")
    
    def show_logs(self, lines: int = 50, follow: bool = False):
        """Показывает логи сервера."""
        if not os.path.exists(self.log_file):
            self.print_status(f"❌ Лог файл не найден: {self.log_file}", Colors.RED)
            return
        
        self.print_header(f"AI Admin Server Logs (последние {lines} строк)")
        
        try:
            if follow:
                # Следим за логами в реальном времени
                self.print_status("Следим за логами в реальном времени (Ctrl+C для выхода)...", Colors.YELLOW)
                subprocess.run(["tail", "-f", "-n", str(lines), self.log_file])
            else:
                # Показываем последние строки
                result = subprocess.run(
                    ["tail", "-n", str(lines), self.log_file],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    print(result.stdout)
                else:
                    self.print_status("Лог файл пуст", Colors.YELLOW)
                    
        except KeyboardInterrupt:
            print("\n")
            self.print_status("Остановлено пользователем", Colors.YELLOW)
        except Exception as e:
            self.print_status(f"Ошибка чтения логов: {e}", Colors.RED)
    
    def start_server(self, background: bool = True):
        """Запускает сервер."""
        if self.is_server_running():
            self.print_status("⚠️  Сервер уже запущен!", Colors.YELLOW)
            return False
        
        port_info = self.check_port_usage()
        if port_info["status"] == "occupied":
            self.print_status(f"❌ Порт {self.port} уже занят (PID: {port_info['pid']})", Colors.RED)
            return False
        
        self.print_header("Запуск AI Admin Server")
        
        # Проверяем наличие конфигурации
        if not os.path.exists(self.config_file):
            self.print_status(f"⚠️  Конфигурационный файл не найден: {self.config_file}", Colors.YELLOW)
        
        # Команда запуска
        cmd = [
            PYTHON_CMD, "-m", SERVER_MODULE
        ]
        
        # Добавляем параметры конфигурации, если они отличаются от значений по умолчанию
        if CONFIG["debug"]:
            cmd.extend(["--debug"])
        
        # Добавляем конфигурационный файл, если он существует
        if os.path.exists(self.config_file):
            cmd.extend(["--config", self.config_file])
        
        # Добавляем информацию о Python и конфигурации
        self.print_status(f"Используется Python: {PYTHON_CMD}", Colors.CYAN)
        self.print_status(f"Рабочий каталог: {os.getcwd()}", Colors.CYAN)
        self.print_status(f"Конфигурация: порт {self.port}, хост {self.host}", Colors.CYAN)
        
        try:
            if background:
                # Запуск в фоне
                with open(self.log_file, 'a') as log_file:
                    # Переходим в корневую директорию проекта для запуска сервера
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    process = subprocess.Popen(
                        cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setsid,
                        cwd=project_root
                    )
                
                # Сохраняем PID
                with open(self.pid_file, 'w') as f:
                    f.write(str(process.pid))
                
                self.print_status(f"✅ Сервер запущен в фоне (PID: {process.pid})", Colors.GREEN)
                self.print_status(f"Логи: {self.log_file}", Colors.CYAN)
                
                # Ждем немного и проверяем
                time.sleep(2)
                if self.is_server_running():
                    self.print_status("✅ Сервер успешно запущен и работает", Colors.GREEN)
                else:
                    self.print_status("⚠️  Сервер может не запуститься, проверьте логи", Colors.YELLOW)
                    
            else:
                # Запуск в foreground
                self.print_status("Запуск сервера в foreground режиме...", Colors.CYAN)
                # Переходим в корневую директорию проекта для запуска сервера
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                subprocess.run(cmd, cwd=project_root)
                
        except Exception as e:
            self.print_status(f"❌ Ошибка запуска сервера: {e}", Colors.RED)
            return False
        
        return True
    
    def stop_server(self, force: bool = False):
        """Останавливает сервер."""
        # Получаем информацию о сервере
        info = self.get_server_info()
        
        if not info["running"]:
            self.print_status("⚠️  Сервер не запущен", Colors.YELLOW)
            return False
        
        pid = info["pid"]
        if not pid:
            self.print_status("❌ Не удалось получить PID сервера", Colors.RED)
            return False
        
        self.print_header("Остановка AI Admin Server")
        self.print_status(f"Остановка процесса PID: {pid}", Colors.CYAN)
        
        try:
            process = psutil.Process(pid)
            
            if force:
                # Принудительная остановка
                self.print_status("Отправка SIGKILL...", Colors.RED)
                process.kill()
            else:
                # Graceful остановка
                self.print_status("Отправка SIGTERM...", Colors.YELLOW)
                process.terminate()
                
                # Ждем завершения
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    self.print_status("Процесс не завершился, отправка SIGKILL...", Colors.RED)
                    process.kill()
                    process.wait()
            
            # Удаляем PID файл
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            self.print_status("✅ Сервер остановлен", Colors.GREEN)
            return True
            
        except psutil.NoSuchProcess:
            self.print_status("✅ Процесс уже завершен", Colors.GREEN)
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            return True
        except Exception as e:
            self.print_status(f"❌ Ошибка остановки сервера: {e}", Colors.RED)
            return False
    
    def restart_server(self):
        """Перезапускает сервер."""
        self.print_header("Перезапуск AI Admin Server")
        
        # Получаем информацию о сервере
        info = self.get_server_info()
        
        if info["running"]:
            self.print_status("Останавливаем сервер...", Colors.YELLOW)
            if not self.stop_server():
                return False
        
        time.sleep(2)  # Ждем завершения
        
        self.print_status("Запускаем сервер...", Colors.YELLOW)
        return self.start_server()
    
    def show_help(self):
        """Показывает справку."""
        self.print_header("AI Admin Server Management")
        
        script_path = Path(__file__).resolve()
        
        help_text = f"""
{Colors.BOLD}Использование:{Colors.END}
  python manage_ai_admin.py [команда] [опции]
  ./manage_ai_admin.py [команда] [опции]

{Colors.BOLD}Команды:{Colors.END}
  status, s     Показать статус сервера
  start         Запустить сервер
  stop          Остановить сервер (graceful)
  kill          Принудительно остановить сервер (SIGKILL)
  restart, r    Перезапустить сервер
  logs, l       Показать логи
  follow, f     Следить за логами в реальном времени

{Colors.BOLD}Опции:{Colors.END}
  --port PORT   Порт сервера (по умолчанию: {CONFIG['port']})
  --host HOST   Хост сервера (по умолчанию: {CONFIG['host']})
  --lines N     Количество строк логов (по умолчанию: 50)
  --foreground  Запустить сервер в foreground режиме
  --help, -h    Показать эту справку

{Colors.BOLD}Примеры:{Colors.END}
  ./manage_ai_admin.py status
  ./manage_ai_admin.py start --port 8080
  ./manage_ai_admin.py logs --lines 100
  ./manage_ai_admin.py follow
  ./manage_ai_admin.py restart

{Colors.BOLD}Файлы:{Colors.END}
  PID файл:     {PID_FILE}
  Лог файл:     {LOG_FILE}
  Конфиг файл:  {CONFIG_FILE}

{Colors.BOLD}Настройка алиаса для bash:{Colors.END}
  Добавьте в ~/.bashrc или ~/.bash_aliases:
  alias aiadmin='{script_path}'
  
  Затем перезагрузите bash:
  source ~/.bashrc
  
  Использование алиаса:
  aiadmin status
  aiadmin start
  aiadmin stop
"""
        print(help_text)
    
    def setup_alias(self):
        """Показывает инструкции по настройке алиаса."""
        self.print_header("Настройка алиаса")
        
        script_path = Path(__file__).resolve()
        
        alias_line = f"alias aiadmin='{script_path}'"
        
        print(f"{Colors.BOLD}Добавьте следующую строку в ваш ~/.bashrc или ~/.bash_aliases:{Colors.END}")
        print(f"{Colors.CYAN}{alias_line}{Colors.END}")
        print()
        print(f"{Colors.BOLD}Затем перезагрузите bash:{Colors.END}")
        print(f"{Colors.CYAN}source ~/.bashrc{Colors.END}")
        print()
        print(f"{Colors.BOLD}После этого вы сможете использовать:{Colors.END}")
        print(f"{Colors.CYAN}aiadmin status{Colors.END}")
        print(f"{Colors.CYAN}aiadmin start{Colors.END}")
        print(f"{Colors.CYAN}aiadmin stop{Colors.END}")
        print()
        print(f"{Colors.BOLD}Автоматическая настройка:{Colors.END}")
        print(f"{Colors.YELLOW}Выполните: echo '{alias_line}' >> ~/.bashrc{Colors.END}")

def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="AI Admin Server Management Script",
        add_help=False  # Отключаем автоматический help
    )
    
    parser.add_argument("command", nargs="?", default="help", 
                       choices=["status", "s", "start", "stop", "kill", "restart", "r", "logs", "l", "follow", "f", "help", "alias"],
                       help="Команда для выполнения")
    
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                       help=f"Порт сервера (по умолчанию: {DEFAULT_PORT})")
    parser.add_argument("--host", default=DEFAULT_HOST,
                       help=f"Хост сервера (по умолчанию: {DEFAULT_HOST})")
    parser.add_argument("--lines", type=int, default=50,
                       help="Количество строк логов (по умолчанию: 50)")
    parser.add_argument("--foreground", action="store_true",
                       help="Запустить сервер в foreground режиме")
    parser.add_argument("--help", "-h", action="store_true",
                       help="Показать справку")
    
    args = parser.parse_args()
    
    # Показываем help по умолчанию или если запрошен
    if args.command == "help" or args.help:
        manager = AIServerManager(args.port, args.host)
        manager.show_help()
        return
    
    # Создаем менеджер
    manager = AIServerManager(args.port, args.host)
    
    # Выполняем команду
    if args.command in ["status", "s"]:
        manager.show_status()
    
    elif args.command == "start":
        manager.start_server(background=not args.foreground)
    
    elif args.command == "stop":
        manager.stop_server(force=False)
    
    elif args.command == "kill":
        manager.stop_server(force=True)
    
    elif args.command in ["restart", "r"]:
        manager.restart_server()
    
    elif args.command in ["logs", "l"]:
        manager.show_logs(lines=args.lines, follow=False)
    
    elif args.command in ["follow", "f"]:
        manager.show_logs(lines=args.lines, follow=True)
    
    elif args.command == "alias":
        manager.setup_alias()

if __name__ == "__main__":
    main() 