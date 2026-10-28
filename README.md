# Transaction Ledger API

A high-integrity, production-grade REST API and minimal management dashboard for managing accounts, financial transactions, and bilateral money transfers. Built with **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL** with strict ACID compliance, row-level locking, and deadlock-free settlement.

---

## Key Features

- **Strict Atomicity (ACID):** Transaction insertion and account balance mutations are executed within atomic database transaction blocks.
- **Double-Spending Prevention:** Pessimistic write locks (`SELECT ... FOR UPDATE`) prevent balance check race conditions under concurrent workloads.
- **Deadlock Protection:** Bilateral transfers enforce deterministic lock ordering by sorting target account IDs prior to acquiring row locks.
- **Schema Validation & Integrity:** Strict runtime validation via Pydantic v2 schemas and composite PostgreSQL constraints (`UNIQUE(account_id, reference_id)`).
- **Immutability:** Financial ledger entries are append-only; no modification or deletion endpoints exist.
- **Interactive UI:** Built-in Swiss-style minimalist dashboard served directly alongside the API.

---

## Tech Stack

- **Runtime & Language:** Python 3.10+
- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **ORM & Migrations:** SQLAlchemy 2.0
- **Database:** PostgreSQL 15
- **Driver:** Psycopg 3
- **Validation:** Pydantic v2
- **Testing:** Pytest, pytest-asyncio, HTTPX

---

## Project Structure

```text
ledger-api/
├── app/
│   ├── __init__.py
│   ├── config.py             # Environment configuration
│   ├── database.py           # Database engine & session dependency
│   ├── models.py             # SQLAlchemy models & DB constraints
│   ├── schemas.py            # Pydantic validation schemas
│   ├── crud.py               # Atomic database operations with row locking
│   ├── main.py               # FastAPI entry point & static file routing
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── accounts.py       # Account & transaction endpoints
│   │   └── transfers.py      # Bilateral money transfer endpoint
│   └── static/
│       └── index.html        # Minimalist dashboard UI
├── tests/
│   ├── __init__.py
│   └── test_ledger.py        # Integration & concurrency race-condition tests
├── docker-compose.yml        # PostgreSQL container setup
├── requirements.txt
├── .env
├── ASSUMPTIONS.md
└── README.md

Getting Started

1. Prerequisites
Python 3.10 or higherDocker & Docker Compose (or an external PostgreSQL instance)

2. Setup Virtual Environment & DependenciesBash# Clone the repository
git clone <repository_url>
cd ledger-api

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

3. Start PostgreSQL DatabaseStart the PostgreSQL service using Docker Compose:Bashdocker compose up -d
Ensure your .env file in the root directory matches your database credentials:Code snippetDATABASE_URL=postgresql+psycopg://ledger_user:ledger_password@localhost:5432/ledger_db

4. Run the Application
Start the development server with hot-reload enabled:Bash

uvicorn app.main:app --reload --port 3000

Once running, access the following in your browser:
Web Dashboard: http://localhost:3000/dashboardInteractive OpenAPI Documentation (Swagger UI): http://localhost:3000/docsAlternative API Documentation (ReDoc): http://localhost:3000/redocHealth 
Check: http://localhost:3000/healthRunning 

Automated Tests

The test suite validates basic business rules, schema boundaries, and includes a parallel concurrency stress test simulating simultaneous withdrawals to guarantee double-spending is impossible.
With the virtual environment active, run:Bash
pytest -v
