@echo off
cd /d "%~dp0"
python -m streamlit run accounts_payable_agent/streamlit_app.py --logger.level=debug
pause
