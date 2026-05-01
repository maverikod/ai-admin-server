# Scripts

Эта папка содержит различные скрипты для тестирования и отладки.

## GPU Testing Scripts

- `gpu_test_script.py` - Основной скрипт для тестирования GPU
- `gpu_test_local.py` - Локальное тестирование GPU
- `cuda_ftp_test.py` - Тестирование CUDA с FTP загрузкой результатов
- `test_cuda.py` - Базовое тестирование CUDA
- `vast_monitor.py` - Мониторинг Vast.ai инстансов
- `run_vast_gpu_test.py` - Запуск GPU тестов на Vast.ai

## FTP Testing Scripts

- `check_ftp.py` - Проверка FTP соединения
- `download_ftp_file.py` - Скачивание файлов с FTP
- `full_ftp_debug.sh` - Bash скрипт для отладки FTP

## Debug Scripts

- `debug_queue.py` - Отладка системы очередей

## Usage

```bash
# Запуск GPU теста
python scripts/gpu_test_script.py

# Проверка FTP
python scripts/check_ftp.py

# Отладка очереди
python scripts/debug_queue.py
``` 