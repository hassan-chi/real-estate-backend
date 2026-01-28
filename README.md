# Real Estate Backend API

A comprehensive backend API for a Real Estate application, built with **Django** and **Django Ninja**.

## 🚀 Features

*   **Authentication**: Custom user model with role-based access (User, Seller, Agent, Admin) and SMS-based OTP verification (Twilio).
*   **Property Management**:
    *   Create, Read, Update, Delete (CRUD) properties.
    *   Image management: Multiple images, cover image selection, drag-and-drop reordering.
    *   Location support (Latitude/Longitude).
    *   Advanced filtering (Search, Type, Status, Price range).
*   **Lead Management (Property Requests)**:
    *   Track leads: Purchase, Rent, Call, Details.
    *   In-app messaging for inquiries.
    *   Status tracking: New, Contacted, In Progress, Closed.
    *   **Admin Dashboard**: Agents see only their assigned leads; Admins see all.
*   **Location Services**: Integrated with `cities_light` for Country/Region/City data.
*   **Documentation**: Automatic interactive API docs via Swagger/Redoc.

## 🛠️ Tech Stack

*   **Framework**: Django 6.0+
*   **API**: Django Ninja (FastAPI-like schema validation)
*   **Database**: SQLite (default) / PostgreSQL (production ready)
*   **Auth**: JWT (via Ninja) + Twilio OTP

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd real_estate
```

### 2. Create a Virtual Environment
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
> **Note**: This project no longer requires GDAL/GEOS binary libraries as it uses standard fields for location.

### 4. Environment Configuration
Create a `.env` file in the root directory (or copy `.env.example`):
```bash
cp .env.example .env
```
Update the `.env` file with your credentials:
```ini
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database (Optional for SQLite, required for Postgres)
# POSTGRES_DB=...
# POSTGRES_USER=...

# Twilio (For OTP)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_VERIFY_SERVICE_SID=your_service_sid

# OTP Testing (Optional)
OTP_TEST_MODE=true
OTP_WHITELIST=+1234567890
OTP_TEST_CODE=12345
```

### 5. Database Setup
Initialize the database (SQLite by default):
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py cities_light
```

### 6. Create a Superuser
Access the admin panel by creating a superuser:
```bash
python manage.py createsuperuser
```

## 🏃‍♂️ Running the Server

Start the development server:
```bash
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000`.

## 📚 API Documentation

Interactive API documentation is automatically generated. Once the server is running, visit:

*   **Swagger UI**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

### Key Endpoints

#### Properties
*   `GET /api/property/` - List all properties (Pagination + Filtering)
*   `POST /api/property/` - Create a new property
*   `PATCH /api/property/{id}/images/reorder` - Reorder images
*   `POST /api/property/{id}/images` - Add images

#### Leads (Property Requests)
*   `POST /api/leads/` - Create a new inquiry/lead
*   `GET /api/leads/` - List incoming leads (for Agents/Owners)
*   `GET /api/leads/my-requests` - List my sent requests (for Buyers)
*   `PATCH /api/leads/{id}` - Update status or assign agent

#### Auth
*   `POST /api/auth/login` - Login with Phone/Password
*   `POST /api/auth/register` - New user registration
*   `POST /api/auth/verify-otp` - Verify phone number

## 🛡️ Admin Panel

Access the Django Admin panel at:
*   [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

**Features:**
*   **Property Management**: Approve/Reject properties on the fly.
*   **Lead Management**: Agents can view/manage only their assigned leads.
