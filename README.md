# 🌿 EcoSphere — Enterprise ESG Management Platform

A full-stack **ESG (Environmental, Social & Governance)** management system built with **FastAPI** (Python) and **React + Vite** (TypeScript). EcoSphere helps organizations track carbon emissions, manage CSR activities, enforce governance policies, gamify sustainability, and generate executive-level ESG reports — all from a single unified dashboard.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Alembic · APScheduler · JWT Auth |
| **Frontend** | React 19 · Vite · TypeScript · Recharts · Framer Motion · Sonner · Lucide Icons |
| **Real-time** | WebSockets (native) for live dashboard updates & notifications |
| **Design System** | Piazzolla headings · Onest body · Warm cream/terracotta/sage/lime/gold palette |

---

## 🏗️ Project Structure

```
ESG/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # Route handlers
│   │   ├── core/                # Security, permissions, config
│   │   ├── db/                  # Database engine, session, base
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── services/            # Business logic (reports, notifications, gamification, scores)
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── smoke_test.py            # End-to-end API smoke test
│
├── frontend/
│   ├── src/
│   │   ├── components/ecosphere/  # Design system components
│   │   ├── components/ui/         # shadcn/ui primitives
│   │   ├── contexts/              # AuthContext provider
│   │   ├── lib/                   # API client, utilities
│   │   └── routes/                # Page components
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
└── planning/                    # Design wireframes & prompt docs
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (with npm)
- **PostgreSQL 14+** (running locally or via Docker)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment — create a .env file with:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ecosphere_db
# SECRET_KEY=your-secret-key-here

# Run database migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**  
Swagger docs at **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at **http://localhost:5173**

### 3. Default Admin Credentials

After running migrations, the seed data creates a default admin account:

| Field | Value |
|-------|-------|
| Email | `admin@ecosphere.com` |
| Password | `adminpassword` |

You can also create a new account via the **Sign Up** page on the login screen.

---

## 📦 API Modules

### 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/signup` | Public self-registration (Employee role) |
| POST | `/auth/register` | Admin-only user creation (any role) |
| GET | `/auth/me` | Get current user profile |

### 🏢 Departments (`/api/v1/departments`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/departments/public` | Public list for signup dropdowns |
| GET | `/departments/` | List all departments (auth required) |
| POST | `/departments/` | Create department (Admin) |
| PATCH | `/departments/{id}` | Update department (Admin) |
| DELETE | `/departments/{id}` | Delete department (Admin) |

### 👥 Employees (`/api/v1/employees`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/employees/` | Search/list employees with filters (Admin/Manager) |

### 🌱 Environmental (`/api/v1/carbon-transactions`, `/api/v1/emission-factors`, etc.)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/carbon-transactions/` | Carbon transaction CRUD |
| POST | `/carbon-transactions/simulate` | Auto-calculate CO₂e from emission factor |
| GET/POST | `/emission-factors/` | Emission factor management |
| GET/POST | `/product-esg-profiles/` | Product ESG profile management |
| GET/POST | `/environmental-goals/` | Environmental goal tracking |

### 🤝 Social (`/api/v1/csr`, `/api/v1/participation`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/csr/activities/` | CSR activity CRUD |
| POST | `/csr/activities/{id}/join` | Employee self-enrollment |
| PATCH | `/participation/{id}/approve` | Manager/Admin approval |
| GET | `/csr/diversity-metrics/` | Diversity breakdown data |
| GET | `/csr/training-records/` | Training completion records |

### ⚖️ Governance (`/api/v1/governance`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/governance/policies/` | ESG policy management |
| POST | `/governance/policies/{id}/acknowledge` | Employee acknowledgement |
| GET | `/governance/policies/{id}/unacknowledged-employees` | Unacknowledged list |
| GET/POST | `/governance/audits/` | Audit management |
| GET/POST | `/governance/compliance-issues/` | Compliance issue tracking |

### 🏆 Gamification (`/api/v1/challenges`, `/api/v1/badges`, `/api/v1/rewards`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/challenges/` | Challenge CRUD |
| POST | `/challenges/{id}/enroll` | Employee challenge enrollment |
| GET | `/badges/` | Badge gallery (earned vs locked) |
| GET/POST | `/rewards/` | Reward store & redemption |
| GET | `/leaderboard` | Points-based leaderboard |

### 📊 Dashboard (`/api/v1/dashboard`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Four KPI tiles (E, S, G, Overall scores) |
| GET | `/dashboard/emissions-trend` | Monthly CO₂e time series |
| GET | `/dashboard/department-ranking` | Department score ranking |
| GET | `/dashboard/recent-activity` | Activity feed |
| GET | `/dashboard/quick-stats` | Quick action stats |

### 📈 Reports (`/api/v1/reports`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/environmental` | Environmental pillar report |
| GET | `/reports/social` | Social pillar report |
| GET | `/reports/governance` | Governance pillar report |
| GET | `/reports/esg-summary` | Executive ESG overview |

### ⚙️ Settings (`/api/v1/settings`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/PATCH | `/settings/esg-configuration` | ESG weights & toggles (Admin) |
| GET/PATCH | `/settings/notification-preferences` | Notification toggles (Admin) |

### 🔔 Notifications & WebSocket
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | User notification list |
| PATCH | `/notifications/{id}/read` | Mark notification as read |
| WS | `/ws/live?token=...` | Real-time event stream |

---

## 🎨 Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Login / Signup** | `/login` | Authentication with register toggle |
| **Dashboard** | `/` | Executive KPI overview with live charts |
| **Environmental** | `/environmental` | Emissions, factors, goals, product profiles |
| **Social** | `/social` | CSR activities, diversity metrics, approvals |
| **Governance** | `/governance` | Policies, audits, compliance issues |
| **Gamification** | `/gamification` | Challenges, badges, rewards, leaderboard |
| **Reports** | `/reports` | Pillar reports with CSV/XLSX/PDF export |
| **Settings** | `/settings` | ESG weights, departments, categories (Admin) |

---

## 🔑 Role-Based Access Control (RBAC)

| Feature | Employee | Manager | Admin |
|---------|----------|---------|-------|
| View Dashboard | ✅ (own dept) | ✅ (own dept) | ✅ (org-wide) |
| Join CSR / Challenges | ✅ | ✅ | ✅ |
| Approve Participation | ❌ | ✅ (own dept) | ✅ (all) |
| Create Policies / Audits | ❌ | ❌ | ✅ |
| Manage Departments | ❌ | ❌ | ✅ |
| ESG Configuration | ❌ | ❌ | ✅ |
| View Reports | ❌ | ✅ (own dept) | ✅ (org-wide) |
| Search Employees | ❌ (403) | ✅ (own dept) | ✅ (all) |

---

## 🧮 ESG Scoring System

EcoSphere calculates three sub-scores (0–100 each) and a weighted overall score:

```
Overall ESG Score = (Environmental × Eweight) + (Social × Sweight) + (Governance × Gweight)
```

Default weights: **Environmental 0.40** · **Social 0.30** · **Governance 0.30**  
Weights are configurable via the Admin Settings page (must sum to 1.0).

Scores are recalculated automatically via APScheduler and can also be triggered manually via `POST /api/v1/scores/calculate`.

---

## 🔄 Real-Time Updates

EcoSphere uses **WebSockets** for live updates:

1. Frontend connects to `ws://localhost:8000/api/v1/ws/live?token=<JWT>`
2. Backend broadcasts events on key actions (score changes, approvals, badge unlocks)
3. Dashboard auto-refreshes KPI tiles and activity feed without polling

---

## 🧪 Testing

```bash
cd backend

# Run the full smoke test (requires server running on port 8000)
python smoke_test.py

# Run individual module tests
python test_employees.py
python test_reports.py
python test_settings.py
python test_dashboard.py
```

---

## 📄 License

This project is for educational and demonstration purposes.

---

Built with 🌿 by the EcoSphere Team
