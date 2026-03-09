# MindleapV1 API - University Mental Health Platform

## 1. Project Overview
MindleapV1 is a comprehensive backend platform written in Python and FastAPI designed to support university mental health initiatives. It provides features for Role-Based User Access (Students, Counselors, Administrators), an AI-driven Chatbot with Crisis guardrails, real-time WebSocket Peer-to-Peer messaging, and a robust Appointment Scheduling Engine to track and manage counselor availability without double bookings. The Administrator Dashboard aggregates platform telemetry for high-level departmental stress monitoring.

---

## 2. Architecture
The system is built as a Modular Monolith with an eye toward microservice extraction later.

*   **API Framework:** FastAPI
*   **Database ORM:** SQLAlchemy
*   **Realtime Communication:** WebSockets (managed via an in-memory `ConnectionManager`, easily adaptable to Redis Pub/Sub for horizontal scaling).
*   **Security:** JWT-based stateless authentication and bcrypt password hashing.

### Modules:
1.  **Auth & Identity:** Handles Login, JWTs, and RBAC (`app/api/routers/auth.py`).
2.  **Communication Services:** Manages the AI Chatbot and Peer Messaging channels (`app/api/routers/chat.py`).
3.  **Scheduling Engine:** Preempts double-booking using Database-level locks (`app/services/appointment.py`).
4.  **Admin Analytics:** Aggregates health metrics across departments for dashboard consumption (`app/services/analytics.py`).

---

## 3. Database Schema & Table Relationships

The platform heavily relies on a Relational Database structure. Core tables include:
*   **`users`**: Base identity (Email, hashed_pass, Role).
*   **`counsellor_availability`**: Discrete time slots defined by a user with the `COUNSELLOR` role. Uniquely indexed by time to prevent overlap.
*   **`appointments`**: A relationship between a `STUDENT`, a `COUNSELLOR`, and an `AVAILABILITY` slot.
*   **`chat_sessions` & `chat_messages`**: One-to-many relationship holding the history of a student's conversation with the AI.
*   **`peer_conversations` & `peer_messages`**: Self-referencing tables connecting two students or a student and a counselor for live chat.

---

## 4. Environment Variables
To run securely in production, configure the following variables (or utilize the `pydantic-settings` overrides):

```env
PROJECT_NAME="MindleapV1 API"
API_V1_STR="/api/v1"
SECRET_KEY="<YOUR_SECURE_RANDOM_256BIT_STRING_HERE>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"
DATABASE_URL="mysql+pymysql://root:password@localhost:3306/mindleap" # Update with local MySQL credentials
```

---

## 5. Setup Instructions (Local Development)

### 1. Create & Activate Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\Activate.ps1
# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
> Note: If the backend was just generated, dependencies include: `fastapi`, `uvicorn`, `passlib[bcrypt]`, `python-jose[cryptography]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, and `psycopg2-binary`.

### 3. Start the Application
The `app/main.py` entry point handles automatic database generation via SQLAlchemy `Base.metadata.create_all` for rapid local testing using SQLite.

```bash
uvicorn app.main:app --reload
```

---

## 6. API Documentation
Because the project uses FastAPI, interactive OpenAPI documentation is automatically generated.
Once the server is running on `http://127.0.0.1:8000`, open your browser to:

*   **Swagger UI (Interactive API Explorer):** `http://127.0.0.1:8000/api/v1/openapi.json` (raw API definition) or `http://127.0.0.1:8000/docs`.
*   **ReDoc (Reading format):** `http://127.0.0.1:8000/redoc`.

---

## 7. Docker Usage (Coming Soon / Productionizing)
For production deployments, you will want to isolate the application behind NGINX alongside a managed PostgreSQL database. Create a `Dockerfile` utilizing a lightweight Base (e.g., `python:3.11-slim`) and execute via optimized Gunicorn workers wrapping Uvicorn.
