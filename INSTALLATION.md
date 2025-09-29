# 🚀 Cash Flow Forecasting App - Installation Guide

## Quick Start (Windows)

### Option 1: Use Batch Files (Easiest)
1. **Start Backend**: Double-click `start-backend.bat`
2. **Start Frontend**: Double-click `start-frontend.bat`
3. **Open App**: Navigate to http://localhost:3000

### Option 2: Manual Setup

#### Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- Git (optional)

#### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
copy local.env .env     # Copy environment file
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

### Database
- **Development**: Uses SQLite (no setup required)
- **Production**: Configure PostgreSQL in `.env` file

### Xero Integration (Optional)
1. Create a Xero app at https://developer.xero.com
2. Add credentials to `.env` file:
   ```
   XERO_CLIENT_ID=your_client_id
   XERO_CLIENT_SECRET=your_client_secret
   ```

## 🎯 Demo Access

### Login Credentials
- **Email**: demo@example.com
- **Password**: demo123

### Sample Data
The app includes sample transaction data for demonstration purposes.

## 📊 Features Available

- ✅ **Cash Flow Dashboard** with KPI cards and charts
- ✅ **Transaction Management** (add, view, delete)
- ✅ **ML Forecasting** using multiple algorithms
- ✅ **Scenario Simulation** with interactive sliders
- ✅ **Xero Integration** (OAuth2.0 authentication)
- ✅ **Responsive Design** (mobile-friendly)

## 🛠️ Troubleshooting

### Common Issues

**1. psycopg2 Installation Error**
- This is expected on Windows without PostgreSQL
- The app will use SQLite instead (works perfectly for demo)

**2. Prophet Installation Issues**
- Prophet is optional and commented out in requirements.txt
- Uncomment if you want advanced forecasting (requires additional setup)

**3. Port Already in Use**
- Backend: Change port in `uvicorn main:app --port 8001`
- Frontend: Change port in `vite.config.js`

**4. Node.js/Python Not Found**
- Install Node.js from https://nodejs.org
- Install Python from https://python.org

## 🚀 Deployment

### Backend (Render)
1. Push code to GitHub
2. Connect to Render
3. Use `render.yaml` configuration

### Frontend (Vercel)
1. Push code to GitHub  
2. Connect to Vercel
3. Uses `vercel.json` configuration

## 📝 API Documentation

Once the backend is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎨 Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: React, Vite, TailwindCSS, Recharts
- **ML**: scikit-learn, pandas, numpy, (Prophet optional)
- **Auth**: JWT tokens, OAuth2.0 (Xero)

## 📞 Support

If you encounter any issues:
1. Check this guide first
2. Ensure all prerequisites are installed
3. Try the batch files for automated setup
4. Check the terminal output for specific error messages

**Happy Forecasting! 📈**
