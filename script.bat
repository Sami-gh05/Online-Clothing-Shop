@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: ================================================================
:: Django Project Automation Script (Windows)
:: Run from project ROOT (contains .venv, requirements.in, and %DJANGO_ROOT%\manage.py)
:: ================================================================

:: --- CONFIG ---
set "DJANGO_ROOT=women_clothing_shop"
set "VENV_DIR=.venv"
set "PY=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"

:: Management commands (synced with your code)
set "CMD_CREATEADMIN=create_admin"
set "CMD_SEED=seed_products"

:: Paths
set "MANAGE=%DJANGO_ROOT%\manage.py"
set "MEDIA_DIR=%DJANGO_ROOT%\media"

:: ------------------------------------------------------------
:menu
cls
echo ====================================
echo        PROJECT ADMIN MENU
echo ====================================
echo.
echo  Django root : %DJANGO_ROOT%
echo  manage.py   : %MANAGE%
echo  venv        : %VENV_DIR%
echo.
echo ------------------------------------
echo  RESET/SETUP
echo ------------------------------------
echo  0. HARD RESET (Delete venv, DB, migrations, media)
echo  1. Prepare Environment (venv ^& requirements)
echo  2. Prepare Django (migrate, seed, create admin, collectstatic)
echo. + admin info:
echo    username: admin
echo    password: admin123
echo ------------------------------------
echo  COMMON
echo ------------------------------------
echo  3. Run Project (runserver)
echo  4. Exit
echo ====================================
set /p choice="Enter your choice (0-4): "

if "%choice%"=="0" goto full_hard_reset
if "%choice%"=="1" goto env_prep
if "%choice%"=="2" goto django_prep
if "%choice%"=="3" goto run_project
if "%choice%"=="4" goto :eof

echo Invalid choice. Please try again.
pause
goto menu

:: ------------------------------------------------------------
:require_manage
if not exist "%MANAGE%" (
  echo(
  echo !!! ERROR: Cannot find manage.py at: %MANAGE%
  echo Make sure DJANGO_ROOT is correct and you run this from project root.
  echo(
  pause
  goto menu
)
exit /b 0

:: ------------------------------------------------------------
:require_venv
if not exist "%PY%" (
  echo(
  echo !!! ERROR: Virtualenv not found. Run option 1 first.
  echo Expected: %PY%
  echo(
  pause
  goto menu
)
exit /b 0

:: ------------------------------------------------------------
:full_hard_reset
cls
echo ====================================
echo     0. HARD RESET
echo ====================================
echo(
echo This will permanently delete:
echo  - %VENV_DIR% folder
echo  - %DJANGO_ROOT%\db.sqlite3
echo  - __pycache__ folders
echo  - %MEDIA_DIR% contents
echo  - Migration files in: %DJANGO_ROOT%\core\migrations (except __init__.py)
echo(
pause

echo [1/6] Deleting virtual environment: %VENV_DIR% ...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
echo(

echo [2/6] Deleting database: %DJANGO_ROOT%\db.sqlite3 ...
if exist "%DJANGO_ROOT%\db.sqlite3" del /q "%DJANGO_ROOT%\db.sqlite3"
echo(

echo [3/6] Deleting __pycache__ folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo(

echo [4/6] Cleaning media folder contents...
if exist "%MEDIA_DIR%" (
  for /d %%d in ("%MEDIA_DIR%\*") do (
    rem delete subfolders content
    rmdir /s /q "%%d"
  )
  rem keep media root folder
  mkdir "%MEDIA_DIR%" >nul 2>nul
) else (
  echo Media folder not found. Skipping.
)
echo(

echo [5/6] Deleting migration files (except __init__.py)...
if exist "%DJANGO_ROOT%\core\migrations" (
  pushd "%DJANGO_ROOT%\core\migrations"
  for %%f in (*.py) do (
    if /I not "%%~nxf"=="__init__.py" del /q "%%f"
  )
  del /q *.pyc 2>nul
  popd
) else (
  echo Migrations folder not found. Skipping.
)

if exist "%DJANGO_ROOT%\accounts\migrations" (
  pushd "%DJANGO_ROOT%\accounts\migrations"
  for %%f in (*.py) do (
    if /I not "%%~nxf"=="__init__.py" del /q "%%f"
  )
  del /q *.pyc 2>nul
  popd
) else (
  echo Migrations folder not found. Skipping.
)

if exist "%DJANGO_ROOT%\shop\migrations" (
  pushd "%DJANGO_ROOT%\shop\migrations"
  for %%f in (*.py) do (
    if /I not "%%~nxf"=="__init__.py" del /q "%%f"
  )
  del /q *.pyc 2>nul
  popd
) else (
  echo Migrations folder not found. Skipping.
)

if exist "%DJANGO_ROOT%\purchase\migrations" (
  pushd "%DJANGO_ROOT%\purchase\migrations"
  for %%f in (*.py) do (
    if /I not "%%~nxf"=="__init__.py" del /q "%%f"
  )
  del /q *.pyc 2>nul
  popd
) else (
  echo Migrations folder not found. Skipping.
)
echo(

echo [6/6] Removing generated requirements.txt (optional)...
if exist "requirements.txt" del /q "requirements.txt"
echo(

echo ------- HARD RESET complete -------
echo Next: run "1. Prepare Environment"
echo(
pause
goto menu

:: ------------------------------------------------------------
:env_prep
cls
echo ====================================
echo     1. Preparing Python Environment
echo ====================================
echo(

if not exist "requirements.in" (
  echo !!! ERROR: requirements.in not found in project root.
  echo(
  pause
  goto menu
)

echo [1/5] Creating virtual environment (%VENV_DIR%)...
if not exist "%VENV_DIR%" (
  py -3 -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo(
    echo !!! ERROR: Failed to create venv. Ensure Python is installed.
    echo(
    pause
    goto menu
  )
) else (
  echo Virtual environment already exists. Skipping...
)
echo(

echo [2/5] Upgrading pip and installing pip-tools...
"%PY%" -m pip install --upgrade pip pip-tools
if errorlevel 1 (
  echo(
  echo !!! ERROR: Failed to install pip-tools.
  echo(
  pause
  goto menu
)
echo(

echo [3/5] Compiling requirements.in ^> requirements.txt ...
if exist "requirements.txt" del /q "requirements.txt"
"%VENV_DIR%\Scripts\pip-compile.exe" requirements.in -o requirements.txt
if errorlevel 1 (
  echo(
  echo !!! ERROR: Failed to compile requirements.
  echo(
  pause
  goto menu
)
echo(

echo [4/5] Syncing environment with requirements.txt ...
"%VENV_DIR%\Scripts\pip-sync.exe" requirements.txt
if errorlevel 1 (
  echo(
  echo !!! ERROR: Failed to sync requirements.
  echo(
  pause
  goto menu
)
echo(

echo [5/5] Done.
echo(
pause
goto menu

:: ------------------------------------------------------------
:django_prep
cls
echo ====================================
echo     2. Preparing Django DB ^& Data
echo ====================================
echo(

call :require_manage
call :require_venv

echo [1/7] Running makemigrations ...
"%PY%" "%MANAGE%" makemigrations
if errorlevel 1 (
  echo(
  echo !!! ERROR: makemigrations failed.
  echo(
  pause
  goto menu
)
echo(

echo [2/7] Applying migrations...
"%PY%" "%MANAGE%" migrate
if errorlevel 1 (
  echo(
  echo !!! ERROR: migrate failed.
  echo(
  pause
  goto menu
)
echo(

echo [3/7] Seeding product data...
"%PY%" "%MANAGE%" %CMD_SEED% --force
if errorlevel 1 (
  echo(
  echo !!! ERROR: seed_products failed.
  echo(
  pause
  goto menu
)
echo(

echo [4/7] Ensuring media folder exists...
if not exist "%MEDIA_DIR%" mkdir "%MEDIA_DIR%"
echo(

echo [5/7] Creating/Updating default admin (command: %CMD_CREATEADMIN)
"%PY%" "%MANAGE%" %CMD_CREATEADMIN% --update-password
if errorlevel 1 (
  echo(
  echo !!! ERROR: Failed to create or update default admin.
  echo(
  pause
  goto menu
)
echo(

echo [6/7] Collecting static files...
"%PY%" "%MANAGE%" collectstatic --noinput
if errorlevel 1 (
  echo(
  echo !!! ERROR: collectstatic failed.
  echo(
  pause
  goto menu
)
echo(

echo [7/7] Done.
echo(
pause
goto menu

:: ------------------------------------------------------------
:run_project
cls
echo ====================================
echo     3. Running Django Development Server
echo ====================================
echo(
call :require_manage
call :require_venv
"%PY%" "%MANAGE%" runserver
if errorlevel 1 (
  echo(
  echo !!! ERROR: runserver failed.
  echo(
  pause
  goto menu
)
goto menu