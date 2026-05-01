"""Start vast briefly, capture logs, then terminate (for registration diagnostics)."""
import subprocess
import sys
import time


def main() -> None:
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ai_admin.server",
            "--config",
            "config/http_reg.json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(22)
    proc.terminate()
    try:
        out, err = proc.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    sys.stdout.write(out or "")
    sys.stderr.write(err or "")
    print("--- returncode", proc.returncode, flush=True)


if __name__ == "__main__":
    main()
