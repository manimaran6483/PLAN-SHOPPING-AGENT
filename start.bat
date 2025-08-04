@echo off
REM Start script for Insurance Plan AI Assistant API (Windows)

echo Starting Insurance Plan AI Assistant API...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Please create one based on .env.example
    echo You can copy .env.example to .env and update the values:
    echo copy .env.example .env
)

REM Load environment variables if .env exists
if exist ".env" (
    echo Loading environment variables from .env file...
    for /f "tokens=*" %%i in (.env) do set %%i
)

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo Error: OPENAI_API_KEY environment variable is not set!
    echo Please set it in your .env file or set it manually:
    echo set OPENAI_API_KEY=your-api-key-here
    pause
    exit /b 1
)

REM Create plan_documents directory if it doesn't exist
if not exist "plan_documents" (
    echo Creating plan_documents directory...
    mkdir plan_documents
    echo Please place your PDF files in the plan_documents/ directory
)

REM Start the API server
echo Starting FastAPI server on port 8081...
python main.py

pause
