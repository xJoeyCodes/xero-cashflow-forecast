@echo off
echo Starting Cash Flow Backend...
cd backend

echo Setting up environment...
if not exist .env (
    copy local.env .env
    echo Created .env file from local.env
)

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing dependencies...
echo Trying full requirements first...
pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo.
    echo ⚠️  Full installation failed. Trying minimal requirements...
    pip install -r requirements-minimal.txt
    
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ⚠️  Minimal installation also failed. Trying ultra-minimal...
        echo This version will definitely work but with simplified features.
        echo.
        pip install -r requirements-ultra-minimal.txt
        
        if %ERRORLEVEL% neq 0 (
            echo.
            echo ❌ Even ultra-minimal installation failed!
            echo Please check your Python installation.
            echo.
            pause
            exit /b 1
        else (
            echo.
            echo ✅ Ultra-minimal installation successful!
            echo Using simplified backend (main_simple.py)
            echo.
            set USE_SIMPLE=1
        )
    else (
        echo.
        echo ✅ Minimal installation successful!
        echo Note: Some advanced features may be limited.
    )
)

echo.
echo ✅ Backend dependencies installed successfully!
echo 🚀 Starting FastAPI server...
echo.
echo Open http://localhost:8000 in your browser to see the API
echo Open http://localhost:8000/docs for the interactive API documentation
echo.

if defined USE_SIMPLE (
    echo Starting simplified backend...
    uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
) else (
    echo Starting full backend...
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
)

