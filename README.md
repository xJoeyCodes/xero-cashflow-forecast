# Cash Flow Forecasting Web App

A fintech solution for SMEs that integrates with Xero's API to provide cash flow forecasting and scenario planning.

## 🏗️ Architecture

- **Backend**: FastAPI + PostgreSQL (Supabase)
- **Frontend**: React (Vite) + TailwindCSS
- **ML/Forecasting**: Prophet, scikit-learn, pandas
- **Integration**: Xero API with OAuth2.0
- **Deployment**: Backend (Render), Frontend (Vercel), DB (Supabase)

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API calls
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔑 Environment Variables

Create `.env` files in both backend and frontend directories with the required environment variables (see `.env.example` files).

## 📊 Features

- **Cash Flow Forecasting**: ML-powered predictions using historical data
- **Xero Integration**: Automatic transaction sync via OAuth2.0
- **Scenario Planning**: Interactive sliders to simulate different business scenarios
- **Dashboard**: Visual charts and KPI cards for financial insights
- **Real-time Sync**: Keep data updated with Xero automatically

## 🔧 Development

This project is built as a demonstration for fintech internship applications, showcasing:
- API integration skills
- Machine learning implementation
- Full-stack development
- Financial data handling
- Modern web technologies
