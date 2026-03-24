@echo off
echo Starting Shoe Store Application...
echo.
echo Installing dependencies (if needed)...
pip install -r requirements.txt
echo.
echo Starting server...
echo Open http://localhost:5000 in your browser
echo.
python app.py
pause
