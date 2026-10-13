# MindleapV1 FastAPI Backend Flow Report

## 1. What this project is

MindleapV1 is a modular-monolith backend for a university mental-health platform. It uses:

- **FastAPI** for HTTP and WebSocket endpoints.
- **SQLAlchemy** for database access and ORM models.
- **Pydantic** for request validation and response serialization.
- **PostgreSQL/Supabase** as the intended database.
- **JWT + bcrypt** for stateless authentication.
- **Alembic** for database migrations.
- **Supabase Storage** for optional file/resource storage.

The backend is organized by responsibility rather than by one large file:

```text
Client
  |
  | HTTP request or WebSocket connection
  v
app/main.py
  |
  +--> Router: validates input, authenticates user, chooses operation
          |
          +--> Service: business rules and database queries
                  |
                  +--> SQLAlchemy model --> PostgreSQL/Supabase
                  |
                  +--> Pydantic response schema --> client
```

The best learning order is:

1. `app/main.py`
2. `app/core/config.py`
3. `app/db/database.py`
4. `app/models/` and `app/schemas/`
5. `app/api/deps.py` and `app/core/security.py`
6. `app/api/routers/`
7. `app/services/`
8. `alembic/`

That order follows the runtime dependency direction: application setup, configuration and database, data shapes, security, endpoints, business logic, and schema deployment.

## 2. Repository map

### Application package

| Path | Responsibility |
|---|---|
| `app/main.py` | Creates the FastAPI application, configures CORS, performs startup/shutdown work, and registers routers. |
| `app/core/config.py` | Defines the `Settings` object. Values come from `.env` and environment variables, with defaults in the class. |
| `app/core/security.py` | Hashes/verifies passwords and creates access/refresh JWTs. |
| `app/db/database.py` | Creates the SQLAlchemy engine, session factory, declarative base, and `get_db()` dependency. |
| `app/api/deps.py` | Shared authentication and authorization dependencies. |
| `app/api/routers/` | HTTP/WebSocket transport layer grouped by feature. |
| `app/services/` | Feature business logic and database operations. |
| `app/models/` | SQLAlchemy table mappings and relationships. |
| `app/schemas/` | Pydantic input/output models used by FastAPI. |
| `app/websockets/connection_manager.py` | In-memory registry of active WebSocket connections. |

### Database and documentation

| Path | Responsibility |
|---|---|
| `alembic/env.py` | Loads application settings and all models so Alembic can compare metadata and run migrations. |
| `alembic/versions/402c5b321ba2_initial_supabase_schema.py` | Initial schema migration. |
| `alembic.ini` | Alembic script location and logging configuration. The database URL is supplied dynamically by `env.py`. |
| `README.md` | High-level architecture and setup notes. |
| `architecture_design.md.resolved` | Design-level architecture material. |
| `database_schema.md.resolved` | Database design material. |
| `requirements.txt` | Root dependency lock/list. |
| `app/requirements.txt` | A second dependency snapshot; use the root file as the primary install source unless the project standard says otherwise. |
| `.env` | Local configuration. It contains sensitive values and should never be committed or copied into documentation. |

There is no `tests/` directory in the current repository inventory, so the report describes the implemented behavior rather than a tested contract.

## 3. Startup and application construction

### 3.1 Entry point

Run the application from the repository root with:

```powershell
uvicorn app.main:app --reload
```

`app.main:app` means:

- import the `app` package;
- import `main.py`;
- retrieve the module-level FastAPI object named `app`.

### 3.2 Import-time setup

`app/main.py` imports settings, routers, the SQLAlchemy engine, and `Base`. It then creates:

```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
```

With the current default `API_V1_STR`, the OpenAPI JSON endpoint is:

```text
/api/v1/openapi.json
```

FastAPI's interactive documentation remains at `/docs`, and ReDoc remains at `/redoc`.

### 3.3 Startup lifecycle

The `lifespan()` function runs before requests are accepted:

1. `engine.connect()` opens a database connection.
2. `SELECT 1` verifies connectivity.
3. `Base.metadata.create_all(bind=engine)` ensures tables exist.
4. `yield` hands control to the running application.
5. On shutdown, `engine.dispose()` releases pooled connections.

Alembic is described as the primary migration mechanism, while `create_all()` is also used as a fallback. In production, schema ownership should be made explicit so automatic table creation does not hide migration mistakes.

### 3.4 Router registration and final URL construction

The router path is the router decorator path joined with the prefix in `main.py`:

| Router | Prefix | Example endpoint |
|---|---|---|
| `auth.router` | `/api/v1/auth` | `POST /api/v1/auth/login` |
| `chat.router` | `/api/v1/chat` | `GET /api/v1/chat/sessions` |
| `appointment.router` | `/api/v1/appointment` | `POST /api/v1/appointment/book` |
| `assessment.router` | `/api/v1/assessment` | `POST /api/v1/assessment/submit` |
| `analytics.router` | `/api/v1/admin` | `GET /api/v1/admin/dashboard` |

The root health-style route is `GET /` and returns a welcome message. It does not itself verify the database; the lifespan startup does that.

## 4. Configuration and database flow

### 4.1 Configuration: `app/core/config.py`

The tagged file defines `Settings`, a Pydantic Settings object. Important groups are:

- application name and API prefix;
- `DATABASE_URL`;
- Supabase URL, keys, and storage bucket;
- JWT secret, algorithm, and access/refresh expiration;
- Redis URL reserved for future background-work infrastructure.

`settings = Settings()` is created at import time. Pydantic Settings reads `.env` and process environment values, with environment values taking precedence over defaults.

Important operational rule: use a strong, environment-provided `SECRET_KEY`; do not rely on the source default in a deployed system. Do not expose the contents of `.env`.

### 4.2 SQLAlchemy setup: `app/db/database.py`

The module creates:

1. `engine`: connection pool and PostgreSQL connection configuration.
2. `SessionLocal`: factory for request-scoped sessions.
3. `Base`: parent class for all ORM models.
4. `get_db()`: generator dependency.

For a normal endpoint, FastAPI calls `get_db()`, yields one `Session`, injects it into the endpoint/service, and closes it in the `finally` block after the response path finishes.

The database engine uses `pool_pre_ping`, a five-connection pool, overflow capacity, a timeout, connection recycling, and UTC timezone configuration.

### 4.3 Models versus schemas

These two layers have different purposes:

- `app/models/*.py` describes database tables, columns, foreign keys, indexes, and SQLAlchemy relationships.
- `app/schemas/*.py` describes the public API contract: accepted JSON/form data and returned JSON.

Schemas with `from_attributes = True` can serialize SQLAlchemy objects into response models. This is why a service can return an ORM object while FastAPI returns JSON with only the fields declared by the response schema.

## 5. Authentication and authorization flow

### 5.1 Signup and login

`app/api/routers/auth.py` owns the authentication endpoints:

#### Signup: `POST /api/v1/auth/signup`

1. FastAPI validates the JSON body as `UserCreate`.
2. The router checks whether the email already exists.
3. `security.get_password_hash()` hashes the plaintext password with bcrypt.
4. A `User` ORM object is inserted and committed.
5. The user is refreshed and returned through the `UserSchema` response model.

#### Login: `POST /api/v1/auth/login`

1. FastAPI parses OAuth2 form fields (`username` is used as the email and `password` is the password).
2. The router finds the user by email.
3. `security.verify_password()` checks the bcrypt hash.
4. `create_access_token()` creates a short-lived JWT.
5. `create_refresh_token()` creates a longer-lived JWT with `type: "refresh"`.
6. The response contains both tokens and `token_type: "bearer"`.

#### Refresh: `POST /api/v1/auth/refresh`

The refresh token is decoded, its `type` must be `"refresh"`, the user must exist and be active, and new access/refresh tokens are issued.

### 5.2 Protected request flow

Protected HTTP routes use `Depends(deps.get_current_user)`. The dependency chain is:

```text
Authorization: Bearer <access token>
  -> OAuth2PasswordBearer extracts token
  -> get_current_user decodes JWT
  -> TokenPayload validates payload fields
  -> refresh tokens are rejected for normal API access
  -> user ID is looked up in users
  -> user must exist and be active
  -> User ORM object is injected into the route
```

`get_current_active_admin()` builds on `get_current_user()` and additionally requires `UserRole.ADMIN`. The admin dashboard uses this stricter dependency.

### 5.3 Roles

`UserRole` has three values:

- `student`
- `counsellor`
- `admin`

Most role checks occur inside routers or the appointment service. Authentication answers “who is this?”; authorization answers “may this user perform this operation?”

## 6. Request lifecycle for ordinary HTTP endpoints

For a route such as `POST /api/v1/appointment/book`, the complete control flow is:

1. Uvicorn receives the HTTP request.
2. FastAPI matches the path and method to a router function.
3. FastAPI validates the request body using a Pydantic schema.
4. FastAPI resolves dependencies (`get_db`, `get_current_user`, and the feature service factory).
5. Authentication and role checks run.
6. The router delegates business work to a service.
7. The service queries or changes SQLAlchemy models.
8. The service commits or rolls back the session as needed.
9. The router returns an ORM object or list.
10. FastAPI validates/serializes the result using the declared response model.
11. The database session dependency closes the session.

This separation is the key navigation pattern: **router = transport and permissions; service = rules; model = persistence; schema = API shape**.

## 7. Feature-by-feature flow

### 7.1 Authentication: `app/api/routers/auth.py`

Start here when learning identity. It is the smallest complete vertical slice:

```text
auth route
  -> get_db
  -> User query
  -> app.core.security
  -> commit or JWT response
```

The user table is defined in `app/models/user.py`; public user output is defined in `app/schemas/user.py`; token output/payload are in `app/schemas/token.py`.

### 7.2 Assessments: `app/api/routers/assessment.py` -> `app/services/assessment.py`

Endpoints:

- `GET /api/v1/assessment/surveys`
- `GET /api/v1/assessment/surveys/{assessment_id}`
- `POST /api/v1/assessment/submit`
- `GET /api/v1/assessment/history`

Flow for submission:

1. Authenticate the caller.
2. Require the `student` role.
3. Load the selected assessment and its questions/options.
4. Build valid question and option-weight lookups.
5. Reject questions from another assessment.
6. Reject invalid options and duplicate answers.
7. Require every question to be answered.
8. Add option weights into `total_score`.
9. Map the score to `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`.
10. Commit `AssessmentResult`, then commit its `AssessmentResultDetail` rows.
11. Serialize the result with nested details.

Models are in `app/models/assessment.py`; API shapes are in `app/schemas/assessment.py`.

### 7.3 Appointments: `app/api/routers/appointment.py` -> `app/services/appointment.py`

Endpoints:

- `POST /api/v1/appointment/availability` — counsellor creates a slot.
- `GET /api/v1/appointment/availability/{counsellor_id}` — authenticated user views future open slots.
- `POST /api/v1/appointment/book` — student books a slot.
- `GET /api/v1/appointment/me` — student/counsellor views their appointments.
- `PATCH /api/v1/appointment/{appointment_id}/transition` — status/notes/link updates.
- `POST /api/v1/appointment/{appointment_id}/reschedule` — student changes a booking.

The important concurrency path is booking:

1. Check that the availability ID belongs to the requested counsellor.
2. Lock the availability row using `with_for_update()`.
3. Reject an already-booked slot.
4. Check for overlapping active appointments for the student.
5. Mark the availability row as booked.
6. Insert the appointment.
7. Commit both changes together.

Cancellation frees the old availability slot. Rescheduling locks the new slot, frees the old slot, changes the appointment times, and commits the transition.

The corresponding tables and indexes are defined in `app/models/appointment.py`; request/response shapes are in `app/schemas/appointment.py`.

### 7.4 AI chat: `app/api/routers/chat.py` -> `app/services/chatbot.py`

REST endpoints:

- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`

WebSocket endpoint:

```text
WS /api/v1/chat/ws/chatbot/{session_id}?token=<access_token>
```

REST session flow:

1. Authenticate the user.
2. Create or query only sessions belonging to that user.
3. Return session history through `ChatSession`/`ChatSessionWithMessages` schemas.

WebSocket flow:

1. The client supplies the JWT as a query-string token.
2. `get_ws_user()` decodes the token and loads the user.
3. The session ownership is checked.
4. `ConnectionManager.connect()` accepts and registers the socket.
5. The loop receives text.
6. The user message is persisted.
7. `ChatbotService.get_ai_response()` checks simple crisis keywords, simulates delay, and returns a demo response.
8. The AI message is persisted.
9. The response is sent to all active connections for that user.
10. On disconnect, the connection is removed.

`ConnectionManager` is process-local memory. It supports multiple sockets for one user, but it is not a cross-process message broker. Horizontal scaling would require a shared system such as Redis/Pub/Sub.

The current chatbot response is a demonstration implementation, not a production LLM integration. Its crisis matching is intentionally simple and should not be treated as a complete clinical safety system.

### 7.5 Admin analytics: `app/api/routers/analytics.py` -> `app/services/analytics.py`

Endpoint:

```text
GET /api/v1/admin/dashboard
```

Control flow:

1. Resolve `get_current_active_admin()`.
2. Count total, completed, and canceled appointments.
3. Count active AI chat sessions.
4. Count peer messages.
5. Build an `AdminDashboardAnalytics` response.

The engagement counts are database-backed. Department stress data and the overall stress score are currently mocked in `AnalyticsService`; the comments describe a future assessment aggregation query. This endpoint is therefore useful for understanding response composition, but its mental-health metrics are not yet live.

### 7.6 Storage helper: `app/services/storage.py`

This module is not currently mounted as a router. It is a reusable service for:

- `upload_file()`
- `get_public_url()`
- `delete_file()`

It creates a Supabase client using the service-role key and fails explicitly if the required settings are absent. Because a service-role key has broad privileges, this code should only run server-side and should never be exposed to a browser.

## 8. Database relationships to understand

The main relational structure is:

```text
users
  +--> counsellor_availability
  |       +--> appointments
  +--> appointments (as student)
  +--> appointments (as counsellor)
  +--> chat_sessions
  |       +--> chat_messages
  +--> peer_conversations
          +--> peer_messages

assessments
  +--> assessment_questions
          +--> assessment_options

users + assessments
  +--> assessment_results
          +--> assessment_result_details
```

Foreign keys and indexes are declared in the model files and reproduced by the initial Alembic migration. The migration imports every model in `alembic/env.py` so `Base.metadata` contains the complete schema during Alembic operations.

## 9. How to run and navigate while learning

### Step 1: Prepare configuration

Create or update `.env` in the repository root. At minimum, set a working `DATABASE_URL` and a private `SECRET_KEY`. For storage features, also set the Supabase URL and service-role key.

### Step 2: Install dependencies

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Apply the schema

The repository contains an initial Alembic revision. A migration-oriented workflow is:

```powershell
alembic upgrade head
```

The application also calls `Base.metadata.create_all()` during startup, so understand which mechanism your environment is relying on before changing models.

### Step 4: Start the API

```powershell
uvicorn app.main:app --reload
```

Then use:

- `http://127.0.0.1:8000/` for the root response;
- `http://127.0.0.1:8000/docs` for Swagger UI;
- `http://127.0.0.1:8000/redoc` for ReDoc.

### Step 5: Exercise a complete vertical path

Use this order in Swagger UI:

1. `POST /auth/signup` to create a user.
2. `POST /auth/login` with form data to receive tokens.
3. Authorize Swagger with the access token.
4. Explore assessments or chat sessions.
5. Create a counsellor separately if testing appointment permissions.
6. Test admin analytics with an admin user.

For the WebSocket route, use a WebSocket-capable client and pass the access token in the query string. The normal Swagger authorization mechanism does not automatically authenticate the WebSocket handshake.

## 10. Important implementation notes and caveats

These are observations for understanding and safe operation, not a change to behavior:

1. **Configuration defaults:** `app/core/config.py` contains fallback database and JWT values. Deployment should override them through environment configuration.
2. **CORS:** `app/main.py` allows every origin, method, and header while also enabling credentials. This is convenient for development but should be restricted in production.
3. **Secrets:** `.env` is local secret material. Keep it ignored and rotate any credential that may have been exposed.
4. **Authentication status codes:** invalid credentials and token errors use several different status codes (`400`, `401`, `403`, and `404`) across paths. Clients should follow the actual endpoint behavior rather than assume one universal code.
5. **WebSocket authentication:** the WebSocket helper validates the JWT and user existence, but the route has a separate authentication path from the HTTP dependency.
6. **Analytics:** department scores are mocked until assessment results are connected to departments.
7. **Peer messaging:** peer models and connection-manager support exist, but the current router exposes the AI chat WebSocket, not a complete peer-messaging API.
8. **Storage:** storage helpers exist without public upload/download endpoints.
9. **Tests:** no test directory was present in the repository inventory. Add endpoint/service tests before making concurrency, authentication, or crisis-guardrail changes.
10. **Documentation wording:** the README calls `/api/v1/openapi.json` “Swagger UI” in one place; it is the raw OpenAPI JSON document. Swagger UI is `/docs`.

## 11. A practical code-reading exercise

To understand one request completely, trace `POST /api/v1/appointment/book` in this order:

1. `app/main.py`: find the appointment router prefix.
2. `app/api/routers/appointment.py`: find `book_session()`.
3. Read its `AppointmentCreate` body, `get_current_user()` dependency, and student-role check.
4. Follow `get_appointment_service()` into `AppointmentService`.
5. Read `book_appointment()` line by line, especially the row lock and overlap query.
6. Open `app/models/appointment.py` to map each field to a database column.
7. Open `app/schemas/appointment.py` to see which fields are accepted and returned.
8. Compare the table definition in the Alembic revision.
9. Repeat the same method for assessment submission and chat WebSocket handling.

This method teaches the project's central FastAPI pattern without requiring you to read every file linearly.

