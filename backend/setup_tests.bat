@echo off
REM Script d'installation de la suite de tests pour Windows
REM Usage: setup_tests.bat

echo ========================================
echo Installation suite de tests img_optimize
echo ========================================
echo.

REM Créer le dossier tests
if not exist "tests" (
    mkdir tests
    echo [OK] Cree: tests\
) else (
    echo [OK] Existe deja: tests\
)

REM Créer __init__.py
echo """Tests unitaires et d'integration pour img_optimize backend""" > tests\__init__.py
echo [OK] Cree: tests\__init__.py

REM Copier les fichiers de tests
if exist "tests_conftest.py" (
    copy /Y tests_conftest.py tests\conftest.py > nul
    echo [OK] Copie: tests_conftest.py -^> tests\conftest.py
)

if exist "tests_test_main.py" (
    copy /Y tests_test_main.py tests\test_main.py > nul
    echo [OK] Copie: tests_test_main.py -^> tests\test_main.py
)

if exist "tests_test_optimize_images.py" (
    copy /Y tests_test_optimize_images.py tests\test_optimize_images.py > nul
    echo [OK] Copie: tests_test_optimize_images.py -^> tests\test_optimize_images.py
)

if exist "tests_test_security.py" (
    copy /Y tests_test_security.py tests\test_security.py > nul
    echo [OK] Copie: tests_test_security.py -^> tests\test_security.py
)

if exist "tests_README.md" (
    copy /Y tests_README.md tests\README.md > nul
    echo [OK] Copie: tests_README.md -^> tests\README.md
)

echo.
echo ========================================
echo Installation terminee !
echo ========================================
echo.
echo Prochaines etapes:
echo 1. pip install -r requirements-dev.txt
echo 2. pytest -v
echo 3. type tests\README.md
echo.
pause
