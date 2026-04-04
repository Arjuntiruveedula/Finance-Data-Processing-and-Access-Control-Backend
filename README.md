# Finance Dashboard Backend

A robust, scalable backend for a Finance Dashboard using **Django REST Framework** and **SQLite** (easy to migrate to PostgreSQL).

## Features
- **Role-Based Access Control**: Admins, Analysts, and Viewers via a Custom `User` model.
- **JWT Authentication**: Secure API endpoints via `SimpleJWT`.
- **Financial Records Management**: CRUD with soft deletes.
- **Dashboard Aggregations**: `/dashboard/summary/` for net balances & `/dashboard/trends/` for monthly rollups.
- **Swagger Documentation**: `/swagger/` interface.

## Design Decisions & Architecture

### 1. Choice of Framework
**Django & Django REST Framework (DRF)** were chosen for their rapid development capabilities, built-in admin panel, robust ORM, and excellent security features. DRF provides excellent out-of-the-box support for serialization, viewsets, and routing, which speeds up API development significantly.

### 2. Database Approach
For this assignment, **SQLite** is used as the default database for ease of setup and zero configuration overhead during development and testing. However, the schema and ORM models are fully compatible with **PostgreSQL**, which is the recommended choice for a production environment due to better concurrency handling and advanced data integrity features.

### 3. Authentication Approach
**JSON Web Tokens (JWT)** via `djangorestframework-simplejwt` was implemented.
- **Why JWT?** It's stateless, meaning the backend does not need to store session data in the database, reducing latency and making the backend easily scalable across multiple servers. 
- **Roles:** A custom User model leverages a `role` field (Admin, Analyst, Viewer) paired with custom DRF permission classes to enforce Role-Based Access Control (RBAC) securely at the endpoint level.

### 4. Project Architecture
The architecture follows a modular, "fat models, thin views" Django pattern to ensure separation of concerns:
- **`core/`**: Houses shared utilities, global exception handlers, and custom permission classes used across the project.
- **`users/`**: Manages custom authentication, user models, and role configurations.
- **`finance/`**: The core business logic app for handling `FinancialRecord` models and standard CRUD APIs.
- **`dashboard/`**: Contains reporting and aggregation logic. It separates read-heavy analytical queries from standard transactional endpoints.

### 5. Trade-offs Considered
- **Monolith vs. Microservices:** A monolithic Django app was chosen to reduce deployment complexity and overhead. Given the domain (Finance Dashboard) and scope, a monolith provides the fastest time-to-market without unnecessary network latency between services.
- **Soft Deletes vs. Hard Deletes:** Financial records are rarely hard-deleted for audit and compliance reasons. A soft-delete approach (using an `is_deleted` flag or similar filtering) ensures data continuity, though it adds slight complexity to querysets compared to standard hard deletes.
- **Real-time vs. Periodic Aggregation:** The dashboard currently does aggregations dynamically per request. While this is fine for smaller datasets, a trade-off is recognized: as data grows, rolling up data periodically via a background task (e.g., Celery) to a cached summary table would be needed to prevent slow dashboard load times.

## Prerequisites
- Python 3+ 
- Virtual Environment

## Setup Instructions

1. Activate your virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter drf-yasg
   ```

2. Run Migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Create Superuser:
   ```bash
   python manage.py createsuperuser
   # Assign 'Admin' role dynamically in Admin dashboard or through API.
   ```

4. Run the Server:
   ```bash
   python manage.py runserver
   ```

5. Access `http://127.0.0.1:8000/swagger/` for the complete API documentation.

## Testing
Run unit tests using:
```bash
python manage.py test
```
