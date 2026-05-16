# AutoFyx Backend API

This repository contains the backend service for the AutoFyx Vehicle Analyzer System. It is built using [FastAPI](https://fastapi.tiangolo.com/) and provides robust endpoints for user management, vehicle data analysis, machine learning-based recommendations, and comprehensive financial calculations (such as maintenance costs and loan amortization).

## Key Features

- **Vehicle Recommendation Engine:** Machine learning pipeline using Scikit-Learn, Pandas, and NumPy to provide tailored vehicle suggestions based on user preferences.
- **Financial Calculations:** Endpoints to compute 5-year total cost of ownership, loan amortization, and predicted maintenance expenses.
- **Authentication & Authorization:** Secure user authentication using JWT and bcrypt, with distinct roles for Admins, Researchers, and standard Users.
- **Comprehensive Data Models:** Integration with MongoDB for flexible data storage and SQLAlchemy for structured relational data.
- **Analytics Dashboard:** API endpoints supplying real-time statistics and historical data trends for researcher and admin portals.

## Technology Stack

- **Framework:** FastAPI (Python 3.x)
- **Database:** MongoDB (Motor/PyMongo), PostgreSQL (SQLAlchemy + Asyncpg)
- **Machine Learning:** Scikit-Learn, Pandas, NumPy, Joblib
- **Authentication:** PyJWT, Passlib, Argon2
- **External Integrations:** AWS S3 / Appwrite for media storage

## Getting Started

### Prerequisites
- Python 3.9+
- MongoDB instance (local or Atlas)
- PostgreSQL database

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd backend/api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   Copy `.env.example` to `.env` and configure your database URIs, secret keys, and storage credentials.

### Running the Application

Start the FastAPI development server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. 
You can view the interactive API documentation (Swagger UI) at `http://localhost:8000/docs` or `http://localhost:8000/redoc`.

## Project Structure

- `routes/` - API endpoint definitions grouped by feature.
- `models/` & `schemas/` - Database models and Pydantic validation schemas.
- `controllers/` & `services/` - Core business logic and data processing modules.
- `ml/` - Machine learning models and prediction pipelines.
- `config/` - Configuration for database connections and environment variables.
