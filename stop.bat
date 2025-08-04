@echo off
REM Stop script for Insurance Plan AI Assistant API (Windows)

echo Stopping Insurance Plan AI Assistant API...

REM Find and kill the FastAPI process
echo Looking for running FastAPI server processes...

REM Check for python main.py process
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr "main.py"') do (
    set PID=%%i
    goto :found_main
)

REM Check for uvicorn processes
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr "uvicorn"') do (
    set PID=%%i
    goto :found_uvicorn
)

REM If no specific process found, try to find any python process on port 8081
netstat -ano | findstr :8081 | findstr LISTENING >nul
if %ERRORLEVEL% == 0 (
    echo Found service running on port 8081
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8081 ^| findstr LISTENING') do (
        set PID=%%i
        goto :found_port
    )
) else (
    echo No FastAPI server found running.
    echo Server may not be running or already stopped.
    goto :cleanup
)

:found_main
echo Found FastAPI server process with PID: %PID%
goto :kill_process

:found_uvicorn
echo Found uvicorn process with PID: %PID%
goto :kill_process

:found_port
echo Found process using port 8081 with PID: %PID%
goto :kill_process

:kill_process
echo Stopping server process...

REM Try graceful shutdown first
taskkill /PID %PID% /T >nul 2>&1

REM Wait a moment for graceful shutdown
timeout /t 3 /nobreak >nul

REM Check if process is still running
tasklist /FI "PID eq %PID%" | findstr %PID% >nul
if %ERRORLEVEL% == 0 (
    echo Process still running. Force killing...
    taskkill /PID %PID% /T /F >nul 2>&1
)

echo Server stopped successfully.

:cleanup
REM Kill any remaining related processes
echo Cleaning up any remaining related processes...

REM Kill any python processes that might be related to our API
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH') do (
    set CURRENT_PID=%%i
    REM Remove quotes from PID
    set CURRENT_PID=!CURRENT_PID:"=!
    
    REM Check if this process is using port 8081
    netstat -ano | findstr :8081 | findstr !CURRENT_PID! >nul
    if !ERRORLEVEL! == 0 (
        echo Found additional process !CURRENT_PID! using port 8081
        taskkill /PID !CURRENT_PID! /T /F >nul 2>&1
    )
)

echo Cleanup completed.

REM Optional: Show if port 8081 is still in use
netstat -ano | findstr :8081 | findstr LISTENING >nul
if %ERRORLEVEL% == 0 (
    echo Warning: Port 8081 is still in use by another process:
    netstat -ano | findstr :8081 | findstr LISTENING
) else (
    echo Port 8081 is now free.
)

echo Stop script finished.
pause
