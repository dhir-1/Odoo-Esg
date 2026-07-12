# EcoSphere Backend

EcoSphere is an internal Environmental, Social, and Governance (ESG) management platform built for the Odoo hackathon. It tracks carbon emissions, CSR/social initiatives, governance compliance, and gamifies employee participation.

## Technology Stack
- **FastAPI** (async backend)
- **SQLAlchemy 2.0** (async) + **Alembic** for migrations
- **PostgreSQL** (local data storage)
- **Pydantic v2** for validation
- **python-jose** + **passlib** (JWT authentication & RBAC)

---

## Setup Instructions

### 1. Prerequisite: Local PostgreSQL
Make sure PostgreSQL is running locally and that you have a database named `ecosphere` created. If it doesn't exist yet, you can create it with:
```sql
CREATE DATABASE ecosphere;
```

### 2. Environment Configurations
Clone this repository, navigate to the `backend` directory, and create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Open `.env` and fill in your local Postgres credentials under `DATABASE_URL`. For example:
```text
DATABASE_URL="postgresql+asyncpg://<username>:<password>@localhost:5432/ecosphere"
```

### 3. Virtual Environment & Dependencies
Create and activate a python virtual environment, then install requirements:
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Running Database Migrations
Migrations are configured with Alembic to automatically read the connection string from your `.env` file:
```bash
# Check Alembic connection status
alembic current

# Run migrations (when available)
alembic upgrade head
```

### 5. Running the Application
Run the FastAPI development server:
```bash
uvicorn app.main:app --reload
```
You can access the interactive API docs at:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

To verify system health, query the `/health` endpoint:
```bash
curl http://127.0.0.1:8000/health
```
It should return:
```json
{
  "status": "healthy",
  "database": "connected"
}
```
