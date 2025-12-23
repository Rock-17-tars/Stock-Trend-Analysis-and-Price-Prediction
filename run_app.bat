@echo off
echo Creating virtual environment (first run may take some time)...
py -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Starting Streamlit app...
streamlit run app.py
pause
