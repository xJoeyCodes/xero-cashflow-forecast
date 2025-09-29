@echo off
echo Starting Cash Flow Frontend...
cd frontend

echo Installing dependencies...
npm install

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ NPM installation failed!
    echo Please make sure Node.js is installed.
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Frontend dependencies installed successfully!
echo 🚀 Starting development server...
echo.
echo The app will open at http://localhost:3000
echo Make sure the backend is running at http://localhost:8000
echo.

npm run dev
