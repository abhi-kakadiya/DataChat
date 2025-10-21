# DataChat - AI-Powered Data Analysis Platform

**Tagline:** "Chat with your data - AI-powered analytics for everyone"

A graduate-level project demonstrating **Prompt Engineering for Numerical Datasets using DSPy**. This full-stack application enables users to upload CSV/Excel files and interact with their data using natural language queries, powered by DSPy's advanced prompt optimization framework.

## 🎯 Project Overview

DataChat combines backend engineering, AI/ML, data processing, and modern web development to create a production-ready data analysis platform. The system uses DSPy (Declarative Self-improving Language Programs) to optimize prompts for:

- **Natural Language to SQL/Pandas conversion** with high accuracy
- **Automated insight generation** from numerical datasets
- **Interactive chat interface** for querying data
- **Real-time feedback loop** for continuous model improvement

## 🌟 Key Features

### Backend (FastAPI + DSPy)
- ✅ **DSPy-powered NL-to-SQL Engine**: Converts natural language questions to executable Pandas queries
- ✅ **AI Insight Generation**: Automatically discovers correlations, trends, anomalies, and distributions
- ✅ **Prompt Optimization**: Uses BootstrapFewShot and user feedback to improve query accuracy
- ✅ **Async Task Queue**: Background processing with Celery for dataset analysis
- ✅ **JWT Authentication**: Secure user management and authorization
- ✅ **Object Storage**: MinIO for scalable file storage
- ✅ **RESTful API**: Comprehensive endpoints for all operations

### Frontend (React + TypeScript + shadcn/ui)
- ✅ **Modern UI**: Beautiful, responsive design with Tailwind CSS and shadcn/ui components
- ✅ **Chat Interface**: Real-time natural language query interface
- ✅ **Data Visualization**: Tables and charts for query results
- ✅ **Dataset Management**: Upload, preview, and manage multiple datasets
- ✅ **Insight Dashboard**: View AI-generated insights with confidence scores
- ✅ **Feedback System**: Thumbs up/down for query quality improvement

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and Setup Environment

\`\`\`bash
git clone <repository-url>
cd DataChat

# Backend setup
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other configuration

# Frontend setup
cd frontend
cp .env.example .env
# Update VITE_API_URL if needed (default: http://localhost:8000)
\`\`\`

### 2. Start Infrastructure Services

\`\`\`bash
# Start PostgreSQL, Redis, and MinIO
docker-compose up -d postgres redis minio
\`\`\`

### 3. Run Backend

\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start Celery worker (in one terminal)
celery -A src.core.celery:celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A src.core.celery:celery_app beat --loglevel=info

# Start FastAPI server (in another terminal)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

Backend will be available at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

### 4. Run Frontend

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

Frontend will be available at: **http://localhost:3000**

## 📊 Usage Guide

### 1. Register/Login
- Navigate to http://localhost:3000
- Create an account or login

### 2. Upload Dataset
- Click "Upload Dataset" on the dashboard
- Select a CSV or Excel file (max 100MB)
- Provide name and description
- Wait for processing to complete

### 3. Query Your Data
- Click on a dataset (status must be "ready")
- Enter natural language questions like:
  - "Show me the average sales by category"
  - "Which products have the highest revenue?"
  - "Find all records where price > 100"
  - "Show me the top 10 customers by total purchases"

### 4. View Insights
- Click "Generate Insights" to get AI-powered analysis
- View correlations, trends, anomalies, and distributions
- Each insight includes confidence scores and recommendations

### 5. Provide Feedback
- Use 👍 or 👎 buttons on query results
- Your feedback helps improve the DSPy models over time

## 🔬 DSPy Prompt Engineering

This project demonstrates advanced prompt engineering techniques using DSPy's Chain of Thought and signature optimization.

### Key Components:
- **NL-to-SQL Module**: Converts natural language to executable Pandas queries
- **Insight Generator**: Automatically discovers patterns and generates insights
- **Optimization Loop**: Uses user feedback to improve prompts over time

## 🛠️ Technology Stack

### Backend
- FastAPI, DSPy, OpenAI
- PostgreSQL, Redis, Celery
- MinIO, Pandas, NumPy, SciPy

### Frontend
- React 18, TypeScript, Vite
- shadcn/ui, Tailwind CSS
- React Query, React Router
- Recharts, Axios

## 📁 API Endpoints

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/datasets/upload` - Upload dataset
- `GET /api/v1/datasets/` - List datasets
- `POST /api/v1/queries/` - Create and execute query
- `POST /api/v1/insights/generate/dataset/{id}` - Generate insights

See full API documentation at http://localhost:8000/docs

## 📄 License

MIT License - Graduate project for educational purposes.

---

**Built with ❤️ for graduate-level demonstration of Prompt Engineering with DSPy**
