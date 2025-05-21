import subprocess
import sys
from setup_logging import setup_logging

if __name__ == "__main__":
    setup_logging()
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.runOnSave=true"])