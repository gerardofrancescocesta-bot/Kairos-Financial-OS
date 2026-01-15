@echo off
cd /d "B:\Personal Agenda"
call venv\Scripts\activate
streamlit run app.py
pause
