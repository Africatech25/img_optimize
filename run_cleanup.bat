@echo off
echo Nettoyage des fichiers temporaires...
cd /d "%~dp0"
python cleanup_temp.py
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
