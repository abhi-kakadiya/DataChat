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

## 🏗️ Project Architecture

```
DataChat/
├── backend/                          # FastAPI backend
│   ├── src/
│   │   ├── api/v1/                  # REST API endpoints
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── dataset.py          # Dataset management
│   │   │   ├── query.py            # NL query processing
│   │   │   └── insight.py          # AI insight generation
│   │   ├── core/                    # Core configuration
│   │   │   ├── config.py           # Settings
│   │   │   ├── database.py         # Database setup
│   │   │   ├── security.py         # JWT & auth
│   │   │   └── celery.py           # Task queue
│   │   ├── dspy_modules/            # DSPy prompt engineering
│   │   │   ├── config.py           # DSPy configuration
│   │   │   ├── nl_to_sql.py        # NL to SQL conversion
│   │   │   └── insight_generator.py # AI insight generation
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/                # Business logic layer
│   │   └── tasks/                   # Celery background tasks
│   ├── alembic/                     # Database migrations
│   ├── requirements.txt
│   └── docker-compose.yaml
│
└── frontend/                         # React TypeScript frontend
    ├── src/
    │   ├── components/ui/           # shadcn/ui components
    │   ├── pages/                   # Application pages
    │   │   ├── LoginPage.tsx
    │   │   ├── DashboardPage.tsx
    │   │   └── ChatPage.tsx
    │   ├── services/                # API client
    │   ├── hooks/                   # React hooks
    │   ├── types/                   # TypeScript types
    │   └── lib/                     # Utilities
    ├── package.json
    └── vite.config.ts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd DataChat

# Backend setup
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other configuration

# Frontend setup
cd frontend
cp .env.example .env
# Update VITE_API_URL if needed (default: http://localhost:8000)
```

### 2. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and MinIO
docker-compose up -d postgres redis minio
```

### 3. Run Backend

```bash
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
```

**Backend URLs:**
- API Server: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

**Frontend URL:** http://localhost:3000

## 📊 Usage Guide

### 1. Register/Login
- Navigate to http://localhost:3000
- Create an account or login

### 2. Upload Dataset
- Click **"Upload Dataset"** on the dashboard
- Select a CSV or Excel file (max 100MB)
- Provide name and description
- Wait for processing to complete (status will change to "ready")

### 3. Query Your Data
Click on a dataset (status must be "ready") and enter natural language questions:

**Example Queries:**
```
Show me the average sales by category
Which products have the highest revenue?
Find all records where price > 100
Show me the top 10 customers by total purchases
What is the correlation between price and quantity?
Display records grouped by region with total sales
```

### 4. View Insights
- Click **"Generate Insights"** to get AI-powered analysis
- View correlations, trends, anomalies, and distributions
- Each insight includes:
  - Confidence score (0.0 to 1.0)
  - Detailed description
  - Supporting data
  - Actionable recommendations

### 5. Provide Feedback
- Use 👍 or 👎 buttons on query results
- Your feedback helps improve the DSPy models over time
- Positive feedback creates training examples for prompt optimization

## 🔬 DSPy Prompt Engineering

This project demonstrates advanced prompt engineering techniques using DSPy's Chain of Thought and signature optimization.

### NL-to-SQL Module

```python
class NLToSQLSignature(dspy.Signature):
    """Signature for converting natural language queries to SQL."""
    schema_info: str = dspy.InputField(
        desc="Database schema information including table name, column names, types, and sample values"
    )
    natural_language_query: str = dspy.InputField(
        desc="User's question in natural language about the data"
    )
    query_type: str = dspy.OutputField(
        desc="Type of query: aggregation, filtering, sorting, grouping, statistical, or visualization"
    )
    sql_query: str = dspy.OutputField(
        desc="Valid Pandas query or SQL-like expression to answer the question"
    )
    explanation: str = dspy.OutputField(
        desc="Brief explanation of what the query does and how it answers the question"
    )

class NLToSQL(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_query = dspy.ChainOfThought(NLToSQLSignature)
```

### Insight Generator

```python
class InsightGenerationSignature(dspy.Signature):
    """Signature for generating insights from data analysis."""
    dataset_info: str = dspy.InputField(
        desc="Dataset overview including shape, columns, types, and basic statistics"
    )
    statistical_analysis: str = dspy.InputField(
        desc="Statistical analysis results including correlations, distributions, and anomalies"
    )
    insight_type: str = dspy.OutputField(
        desc="Type of insight: trend, correlation, anomaly, distribution, statistical, or summary"
    )
    title: str = dspy.OutputField(desc="Clear, concise title for the insight")
    description: str = dspy.OutputField(desc="Detailed description explaining the insight")
    confidence_score: float = dspy.OutputField(desc="Confidence score from 0.0 to 1.0")
```

### Key Components:
- **NL-to-SQL Module**: Converts natural language to executable Pandas queries using Chain of Thought
- **Insight Generator**: Automatically discovers patterns and generates insights
- **Optimization Loop**: Uses user feedback (👍👎) to improve prompts over time
- **Statistical Analysis**: Correlation detection, anomaly detection (IQR), trend analysis (linear regression)

## 🛠️ Technology Stack

### Backend
| Category | Technologies |
|----------|-------------|
| Framework | FastAPI 0.115.0 |
| AI/ML | DSPy 2.4.13, OpenAI, LiteLLM |
| Database | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| Cache/Queue | Redis 7, Celery 5.4 |
| Storage | MinIO 7.2 |
| Data Processing | Pandas 2.2, NumPy 1.26, SciPy |
| Authentication | JWT, Bcrypt |
| Monitoring | Structlog, Prometheus, OpenTelemetry |

### Frontend
| Category | Technologies |
|----------|-------------|
| Framework | React 18, TypeScript |
| Build Tool | Vite |
| UI Library | shadcn/ui components |
| Styling | Tailwind CSS |
| State Management | React Query (TanStack Query) |
| Routing | React Router DOM |
| Charts | Recharts |
| HTTP Client | Axios |

## 📁 API Endpoints

### Authentication
```http
POST /api/v1/auth/login          # User login
POST /api/v1/auth/register       # User registration
```

### Users
```http
GET /api/v1/users/me             # Get current user profile
GET /api/v1/users/               # List all users (superuser only)
```

### Datasets
```http
POST   /api/v1/datasets/upload         # Upload CSV/XLSX file
GET    /api/v1/datasets/               # List user's datasets
GET    /api/v1/datasets/{id}           # Get dataset details
GET    /api/v1/datasets/{id}/preview   # Preview first N rows
DELETE /api/v1/datasets/{id}           # Delete dataset
```

### Queries
```http
POST  /api/v1/queries/                    # Create and execute query
GET   /api/v1/queries/                    # List user's queries
GET   /api/v1/queries/{id}                # Get query details
GET   /api/v1/queries/dataset/{id}        # List dataset queries
PATCH /api/v1/queries/{id}                # Update query feedback
```

### Insights
```http
POST   /api/v1/insights/generate/dataset/{id}  # Generate dataset insights
POST   /api/v1/insights/generate/query/{id}    # Generate query insights
GET    /api/v1/insights/dataset/{id}           # List dataset insights
GET    /api/v1/insights/query/{id}             # List query insights
GET    /api/v1/insights/{id}                   # Get specific insight
DELETE /api/v1/insights/{id}                   # Delete insight
```

### Health
```http
GET /                            # Root endpoint
GET /health                      # Health check
GET /api/v1/docs                 # Swagger UI documentation
```

**Full API Documentation:** http://localhost:8000/docs

## ⚙️ Configuration

### Backend Environment Variables

Create `.env` file from `.env.example`:

```bash
# Application
PROJECT_NAME="DSPy Prompt Engineer"
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://datachat_user:datachat_password@localhost:5432/datachat
DATABASE_URL_SYNC=postgresql://datachat_user:datachat_password@localhost:5432/datachat

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=dspy-datasets

# OpenAI (for DSPy)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# JWT
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# DSPy Settings
DSPY_MAX_TRAIN_SIZE=1000
DSPY_MAX_DEV_SIZE=200
DSPY_OPTIMIZATION_ROUNDS=10

# Limits
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_TASKS=5
```

### Frontend Environment Variables

Create `frontend/.env` file:

```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Database Schema

### Users
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Datasets
```sql
CREATE TABLE datasets (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    row_count INTEGER,
    column_count INTEGER,
    column_info JSON,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    owner_id VARCHAR REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Queries
```sql
CREATE TABLE queries (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id) NOT NULL,
    dataset_id VARCHAR REFERENCES datasets(id) NOT NULL,
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT,
    query_type VARCHAR,
    result_data JSON,
    result_summary TEXT,
    execution_time FLOAT,
    row_count INTEGER,
    status VARCHAR DEFAULT 'pending',
    error_message TEXT,
    user_feedback VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Insights
```sql
CREATE TABLE insights (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR REFERENCES datasets(id) NOT NULL,
    query_id VARCHAR REFERENCES queries(id),
    insight_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    confidence_score FLOAT,
    supporting_data JSON,
    visualization_config JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔒 Security Features

- **JWT Authentication**: Token-based auth with expiration
- **Password Hashing**: Bcrypt for secure password storage
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Prevention**: Parameterized queries
- **CORS Configuration**: Controlled cross-origin requests
- **File Upload Validation**: Type and size limits
- **Rate Limiting**: Configurable request limits
- **Environment Variables**: Sensitive data in .env files

## 📈 Performance & Monitoring

### Metrics Tracked
- Query success rate
- Average execution time per query
- User feedback ratio (👍/👎)
- Insight confidence scores
- Dataset processing times

### Background Tasks
```bash
# Scheduled Tasks (Celery Beat)
cleanup-old-files          # Daily - Clean up old datasets and files
generate-dataset-insights  # Hourly - Auto-generate insights
update-dspy-models         # Every 6 hours - Optimize DSPy prompts
```

### Monitoring Commands
```bash
# View Celery worker status
celery -A src.core.celery:celery_app inspect active

# View scheduled tasks
celery -A src.core.celery:celery_app inspect scheduled

# Monitor task queue
celery -A src.core.celery:celery_app events
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_queries.py

# Type checking
mypy src/
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🐳 Docker Deployment

### Full Stack with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Individual Services
```bash
# Start only database services
docker-compose up -d postgres redis minio

# Scale Celery workers
docker-compose up -d --scale celery-worker=3
```

## 🎓 Academic Context

**Graduate Project Topic:** Prompt Engineering for Numerical Datasets using DSPy

This project demonstrates:

1. **Advanced Prompt Engineering**
   - DSPy signature design for structured outputs
   - Chain of Thought reasoning for complex queries
   - Prompt optimization using user feedback

2. **Machine Learning Integration**
   - Statistical analysis (correlations, distributions)
   - Anomaly detection algorithms
   - Trend analysis with linear regression

3. **Full-Stack Development**
   - Modern backend architecture with FastAPI
   - Production-ready frontend with React
   - Microservices with async task processing

4. **Software Engineering Best Practices**
   - Clean architecture with separation of concerns
   - Type safety (TypeScript + Python type hints)
   - Database migrations and version control
   - Comprehensive error handling and logging

## 🤝 Contributing

This is a graduate project, but improvements are welcome!

```bash
# Fork the repository
git clone <your-fork>

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: Add your feature"

# Push and create PR
git push origin feature/your-feature-name
```

## 📄 License

MIT License - Graduate project for educational purposes.

## 🔗 Resources

- [DSPy Documentation](https://dspy-docs.vercel.app/)
- [DSPy GitHub](https://github.com/stanfordnlp/dspy)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Celery Documentation](https://docs.celeryq.dev/)
- [React Query](https://tanstack.com/query/latest)

## 👨‍💻 Author

**Graduate Student Project**
**Topic:** Prompt Engineering for Numerical Datasets using DSPy
**Institution:** McMaster University
**Year:** 2025

---

**Built with ❤️ for graduate-level demonstration of Prompt Engineering with DSPy**

*Showcasing the intersection of AI, data science, and modern web development*
