# Order Management System

## Tech Stack
- Backend: Django + DRF + PostgreSQL
- Frontend: React
- Auth: JWT (SimpleJWT)

## Setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Configure .env with DB credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## API Endpoints
| Method | Endpoint | Role |
|--------|----------|------|
| POST | /api/register/ | Public |
| POST | /api/login/ | Public |
| GET/POST | /api/products/ | Auth/Admin |
| GET/POST | /api/orders/ | Auth |
| POST | /api/orders/{id}/assign/ | Admin |
| PATCH | /api/orders/{id}/status/ | Delivery |
