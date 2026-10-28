import os
import subprocess
import time
import sys

root = r"e:\App\AI-CCTV"
python_exe = os.path.join(root, ".venv", "Scripts", "python.exe")
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(root, "src")
env["EXCAVATOR_CONFIG"] = os.path.join(root, "config.excavator.yaml")

log_path = os.path.join(root, "data", "engine.log")
with open(log_path, "a", encoding="utf-8") as log_file:
    p = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "excavator.web.main:app", "--host", "127.0.0.1", "--port", "8010"],
        cwd=root,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    print(f"Spawned Uvicorn PID: {p.pid}")

time.sleep(3)
ret = p.poll()
print(f"Process status after 3s: {'Terminated with code ' + str(ret) if ret is not None else 'Running normally'}")
