@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
set ENVIRONMENT=development
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 