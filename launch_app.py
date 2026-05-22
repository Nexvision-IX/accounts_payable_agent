#!/usr/bin/env python
import subprocess
import sys
import os

os.chdir(r"c:\Users\kastu\Downloads\accounts_payable_agent")

try:
    subprocess.run([sys.executable, "-m", "streamlit", "run", 
                   "accounts_payable_agent/streamlit_app.py",
                   "--logger.level=debug"], check=True)
except Exception as e:
    print(f"Error launching Streamlit app: {e}")
    input("Press Enter to exit...")
