# 🪟 Windows Setup Guide - Cash Flow App

## 🚨 Having Installation Issues?

If you're encountering pandas/numpy installation errors on Windows, you have several options:

### Option 1: Use Minimal Installation (Recommended for Quick Start)

```bash
cd backend
pip install -r requirements-minimal.txt
```

This installs only the core FastAPI dependencies and skips problematic data science packages. The app will still work with basic forecasting!

### Option 2: Use the Auto-Fallback Script

Simply run `start-backend.bat` - it will automatically try the full installation first, then fall back to minimal if it fails.

### Option 3: Install Pre-compiled Packages

If you want the full data science features:

1. **Upgrade pip first:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Install packages individually:**
   ```bash
   pip install numpy
   pip install pandas
   pip install scikit-learn
   pip install -r requirements.txt
   ```

3. **Or use conda (if you have it):**
   ```bash
   conda install pandas numpy scikit-learn
   pip install -r requirements.txt
   ```

## 🎯 What Works with Minimal Installation?

✅ **Full web application**
✅ **User authentication**
✅ **Transaction management**
✅ **Basic cash flow forecasting**
✅ **Scenario simulation**
✅ **Xero integration**
✅ **Dashboard with charts**

❌ **Advanced ML models (Prophet, complex statistics)**

## 🚀 Quick Start Commands

### Backend (Choose one):
```bash
# Option 1: Auto-fallback script
start-backend.bat

# Option 2: Manual minimal
cd backend
pip install -r requirements-minimal.txt
copy local.env .env
uvicorn main:app --reload
```

### Frontend:
```bash
# Always works the same
start-frontend.bat

# Or manually:
cd frontend
npm install
npm run dev
```

## 🔧 Troubleshooting Specific Errors

### "pandas metadata generation failed"
- **Solution**: Use `requirements-minimal.txt` instead
- **Why**: pandas requires C++ build tools on Windows

### "psycopg2 not found"
- **Solution**: This is expected, app uses SQLite instead
- **Why**: PostgreSQL development libraries not installed

### "Prophet installation failed"
- **Solution**: Prophet is optional and commented out
- **Why**: Requires additional system dependencies

## 📊 App Features Status

| Feature | Minimal Install | Full Install |
|---------|----------------|--------------|
| Dashboard | ✅ | ✅ |
| Transactions | ✅ | ✅ |
| Basic Forecasting | ✅ | ✅ |
| Advanced ML | ❌ | ✅ |
| Scenario Simulation | ✅ | ✅ |
| Xero Integration | ✅ | ✅ |

## 💡 Pro Tips

1. **Start with minimal** - Get the app running first, add features later
2. **Use the batch files** - They handle fallbacks automatically  
3. **Check Python version** - Use Python 3.8-3.11 for best compatibility
4. **Consider WSL** - Windows Subsystem for Linux often has fewer issues

## 🆘 Still Having Issues?

1. Make sure Python 3.8+ is installed
2. Try running as administrator
3. Check if antivirus is blocking installation
4. Use the minimal installation - it provides 90% of the functionality!

The app is designed to work great even without the advanced data science packages! 🎉
