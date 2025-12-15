# The Accountant - Backend API

A RESTful API backend for The Accountant personal finance app. Built with FastAPI and PostgreSQL, featuring JWT authentication, Firebase integration, and comprehensive financial data management.

## Features

- **Authentication** - Email/password and Google Sign-In via Firebase
- **User Management** - Profile management with premium subscription support
- **Financial Data APIs** - Transactions, wallets, categories, budgets, and more
- **Multi-Currency Support** - Exchange rates with automatic updates
- **Data Synchronization** - Sync local app data with cloud storage
- **In-App Purchase Verification** - Google Play purchase validation

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT + Firebase Admin SDK
- **Migrations**: Alembic
- **Validation**: Pydantic v2

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with email/password |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/firebase` | Authenticate with Firebase/Google |
| GET | `/api/v1/auth/me` | Get current user |
| PUT | `/api/v1/auth/me` | Update user profile |
| POST | `/api/v1/auth/link-account` | Link Google to email account |

### Financial Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/transactions` | List/create transactions |
| GET/POST | `/api/v1/wallets` | List/create wallets |
| GET/POST | `/api/v1/categories` | List/create categories |
| GET/POST | `/api/v1/budgets` | List/create budgets |
| GET/POST | `/api/v1/objectives` | List/create savings goals |
| GET/POST | `/api/v1/recurring` | List/create recurring transactions |
| GET/POST | `/api/v1/payment-methods` | List/create payment methods |

### Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/exchange-rates` | Get currency exchange rates |
| POST | `/api/v1/sync` | Sync data from mobile app |
| POST | `/api/v1/iap/verify` | Verify in-app purchases |

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Firebase project with Admin SDK

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/the_accountant_backend.git
cd the_accountant_backend
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up Firebase Admin SDK
```bash
# Download your Firebase Admin SDK JSON from Firebase Console
# Save it as firebase-admin-sdk.json in the project root
```

6. Run database migrations
```bash
alembic upgrade head
```

7. Start the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

## Project Structure

```
app/
├── api/
│   └── v1/                 # API endpoints (versioned)
│       ├── auth.py         # Authentication endpoints
│       ├── transactions.py # Transaction CRUD
│       ├── wallets.py      # Wallet management
│       ├── categories.py   # Category management
│       ├── budgets.py      # Budget tracking
│       └── ...
├── core/
│   ├── dependencies.py     # FastAPI dependencies
│   └── security.py         # JWT and password hashing
├── models/                 # SQLAlchemy ORM models
├── schemas/                # Pydantic request/response schemas
├── services/               # Business logic services
├── config.py               # Configuration management
├── database.py             # Database connection
└── main.py                 # FastAPI app initialization
```

## Configuration

Required environment variables:

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=the_accountant_db
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_AUTH_ENABLED=True

# Server
HOST=0.0.0.0
PORT=8002
DEBUG=True
```

## Development

### Running Tests
```bash
pytest
```

### Creating Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### API Documentation
Once the server is running, access:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## Deployment

### Docker
```bash
docker build -t the-accountant-api .
docker run -p 8002:8002 --env-file .env the-accountant-api
```

### Production Considerations
- Use a production WSGI server (Gunicorn with Uvicorn workers)
- Set `DEBUG=False`
- Use strong `JWT_SECRET_KEY`
- Enable HTTPS
- Set appropriate `ALLOWED_ORIGINS` for CORS

## License

This project is proprietary software. All rights reserved.

## Support

For issues and feature requests, please use the GitHub issue tracker.
