# OPD Token Allocation System - MVP

A Django REST API backend for managing patient token allocation in hospital Outpatient Department (OPD). This MVP version implements priority-based allocation, concurrency handling, and dynamic reallocation.

## 🚀 QUICK START (Choose One)

### Option 1: Deploy to Railway (Recommended for Submission)
**Takes 5 minutes - Get a live URL!**

1. Push to GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "Deploy from GitHub"
4. Add PostgreSQL and Redis
5. Done! See [EASY_DEPLOYMENT.md](EASY_DEPLOYMENT.md) for details

### Option 2: Run with Docker (Local Testing)
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
# Visit http://localhost:8000/api/docs/
```

### Option 3: Manual Setup (Development)
```bash
chmod +x setup.sh
./setup.sh
python manage.py runserver
```

## 🔧 TROUBLESHOOTING

### All Issues? Run the Fix Script
```bash
chmod +x fix.sh
./fix.sh
# Choose option 1 to fix everything
```

### Common Issues Fixed:
- ✅ Admin login failed → Run `docker-compose exec web python manage.py createsuperuser`
- ✅ Demo.py errors → Already fixed in updated version
- ✅ Missing dependencies → Added `requests` to requirements.txt
- ✅ API endpoint errors → Corrected all endpoint URLs

## Features

✅ **Priority-based Token Allocation**
- 5-tier priority system (Emergency, Priority Paid, Follow-up, Online, Walk-in)
- Time-bonus for fair ordering within same priority
- Automatic position calculation

✅ **Capacity Management**
- Hard capacity limits per slot
- Waiting list when slot is full
- Automatic promotion from waiting list

✅ **Dynamic Reallocation**
- Token cancellation handling
- No-show management
- Emergency patient insertion
- Doctor delay propagation

✅ **Concurrency Control**
- Redis-based distributed locks
- Database transaction management
- Race condition prevention

✅ **REST API**
- Complete CRUD operations
- OpenAPI/Swagger documentation
- Daily reports and analytics

## Tech Stack

- **Django 5.0.1** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and distributed locks
- **drf-spectacular** - API documentation

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Clone and setup**
```bash
cd opd_token_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and Redis credentials
```

3. **Setup database**
```bash
# Create PostgreSQL database
createdb opd_tokens

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

4. **Create admin user**
```bash
python manage.py createsuperuser
```

5. **Run server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

### Access Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## API Endpoints

### Doctors
- `GET /api/v1/doctors/` - List all doctors
- `POST /api/v1/doctors/` - Create a doctor
- `GET /api/v1/doctors/{id}/` - Get doctor details
- `PUT /api/v1/doctors/{id}/` - Update doctor
- `DELETE /api/v1/doctors/{id}/` - Delete doctor

### Patients
- `GET /api/v1/patients/` - List all patients
- `POST /api/v1/patients/` - Create a patient
- `GET /api/v1/patients/{id}/` - Get patient details
- `PUT /api/v1/patients/{id}/` - Update patient
- `DELETE /api/v1/patients/{id}/` - Delete patient

### Slots
- `GET /api/v1/slots/` - List all slots
- `POST /api/v1/slots/` - Create a slot
- `GET /api/v1/slots/{id}/` - Get slot details
- `PUT /api/v1/slots/{id}/delay/` - Mark slot as delayed
- `GET /api/v1/slots/{id}/tokens/` - Get all tokens for a slot

### Tokens
- `GET /api/v1/tokens/` - List all tokens
- `POST /api/v1/tokens/` - Request a new token
- `GET /api/v1/tokens/{id}/` - Get token details
- `DELETE /api/v1/tokens/{id}/` - Cancel a token
- `POST /api/v1/tokens/emergency/` - Insert emergency patient
- `POST /api/v1/tokens/{id}/no_show/` - Mark as no-show

### Reports
- `GET /api/v1/reports/daily/` - Daily allocation report
  - Query params: `date` (YYYY-MM-DD), `doctor_id` (UUID)

### Waiting List
- `GET /api/v1/waiting-list/` - List all waiting entries
- `GET /api/v1/waiting-list/by_slot/?slot_id={id}` - Get waiting list for slot

## Usage Examples

### 1. Create a Doctor
```bash
curl -X POST http://localhost:8000/api/v1/doctors/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. John Smith",
    "specialization": "Cardiology"
  }'
```

### 2. Create a Slot
```bash
curl -X POST http://localhost:8000/api/v1/slots/ \
  -H "Content-Type: application/json" \
  -d '{
    "doctor": "doctor-uuid-here",
    "start_time": "2026-02-01T09:00:00Z",
    "end_time": "2026-02-01T10:00:00Z",
    "max_capacity": 15
  }'
```

### 3. Create a Patient
```bash
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "phone": "+1234567890",
    "email": "jane@example.com"
  }'
```

### 4. Request a Token
```bash
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid-here",
    "patient_id": "patient-uuid-here",
    "category": "ONLINE"
  }'
```

**Category options**: `EMERGENCY`, `PRIORITY_PAID`, `FOLLOWUP`, `ONLINE`, `WALKIN`

### 5. Insert Emergency Patient
```bash
curl -X POST http://localhost:8000/api/v1/tokens/emergency/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid-here",
    "patient_id": "patient-uuid-here"
  }'
```

### 6. Cancel a Token
```bash
curl -X DELETE http://localhost:8000/api/v1/tokens/{token-id}/
```

### 7. Delay a Slot
```bash
curl -X PUT http://localhost:8000/api/v1/slots/{slot-id}/delay/ \
  -H "Content-Type: application/json" \
  -d '{
    "delay_minutes": 30
  }'
```

### 8. Get Daily Report
```bash
curl "http://localhost:8000/api/v1/reports/daily/?date=2026-02-01"
```

## Priority System

The system uses a 5-tier priority system where **lower values = higher priority**:

| Category | Base Priority | Description |
|----------|--------------|-------------|
| EMERGENCY | 1 | Emergency patients (highest priority) |
| PRIORITY_PAID | 2 | Premium/paid patients |
| FOLLOWUP | 3 | Follow-up appointments |
| ONLINE | 4 | Online bookings |
| WALKIN | 5 | Walk-in patients (lowest priority) |

### Priority Calculation

```
Final Priority = Base Priority - Time Bonus
Time Bonus = min((hours_since_booking × 0.1), 1.0)
```

**Example:**
- Patient A: Online booking (priority 4), booked 2 hours ago
  - Time bonus = 2 × 0.1 = 0.2
  - Final priority = 4 - 0.2 = **3.8**
  
- Patient B: Online booking (priority 4), booked 30 minutes ago
  - Time bonus = 0.5 × 0.1 = 0.05
  - Final priority = 4 - 0.05 = **3.95**

Patient A gets the token before Patient B due to earlier booking.

## How It Works

### Token Allocation Flow

1. **Request arrives** → Acquire distributed lock on slot
2. **Check capacity** → Verify slot has space available
3. **Calculate priority** → Compute final priority score
4. **Find position** → Determine insertion point based on priority
5. **Resequence** → Shift existing tokens if needed
6. **Create token** → Persist token in database
7. **Update capacity** → Increment slot counter
8. **Release lock** → Free the slot for other requests

### Concurrency Handling

- **Redis Locks**: Distributed locks prevent race conditions
- **Database Locks**: Row-level locking with `SELECT FOR UPDATE`
- **Transactions**: ACID guarantees for all operations
- **Check Constraints**: Database-level capacity enforcement

### Edge Cases Handled

✅ Double booking prevention (same patient, same day)  
✅ Capacity overflow protection  
✅ Concurrent request handling  
✅ Emergency insertion with capacity override  
✅ Cascading delays across slots  
✅ Waiting list management  
✅ Token compaction after cancellations  

## Database Schema

```
doctors
├── id (UUID, PK)
├── name
├── specialization
└── created_at

slots
├── id (UUID, PK)
├── doctor_id (FK → doctors)
├── start_time
├── end_time
├── max_capacity
├── current_capacity
├── status (ACTIVE/DELAYED/CANCELLED)
├── delay_minutes
└── created_at

patients
├── id (UUID, PK)
├── name
├── phone
├── email
└── created_at

tokens
├── id (UUID, PK)
├── slot_id (FK → slots)
├── patient_id (FK → patients)
├── token_number
├── priority
├── category
├── status (CONFIRMED/CANCELLED/NO_SHOW/COMPLETED)
├── estimated_time
├── actual_time
├── created_at
└── updated_at

waiting_list
├── id (UUID, PK)
├── slot_id (FK → slots)
├── patient_id (FK → patients)
├── category
├── priority
└── created_at
```

## Testing

### Manual Testing with Admin Panel

1. Go to http://localhost:8000/admin/
2. Create doctors, patients, and slots
3. Test token allocation through the API
4. View real-time updates in admin panel

### Testing Concurrency

Use multiple terminal windows to send simultaneous requests:

```bash
# Terminal 1
curl -X POST http://localhost:8000/api/v1/tokens/ -H "Content-Type: application/json" -d '{"slot_id":"...","patient_id":"...","category":"ONLINE"}'

# Terminal 2 (at the same time)
curl -X POST http://localhost:8000/api/v1/tokens/ -H "Content-Type: application/json" -d '{"slot_id":"...","patient_id":"...","category":"WALKIN"}'
```

Only one request should succeed if the slot is at capacity.

## Production Considerations

This is an MVP version. For production deployment, consider:

### Required Enhancements
- [ ] Authentication & Authorization (JWT/OAuth)
- [ ] Rate limiting
- [ ] Celery for background tasks (no-show grace period)
- [ ] Email/SMS notifications
- [ ] Logging and monitoring (Sentry)
- [ ] API versioning
- [ ] Data backup strategy
- [ ] Load balancing
- [ ] HTTPS/SSL configuration

### Scaling
- [ ] Redis Cluster for distributed locks
- [ ] PostgreSQL read replicas
- [ ] Caching strategy for read-heavy endpoints
- [ ] Horizontal scaling with multiple app servers

### Monitoring
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Health check endpoints
- [ ] Performance profiling

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Debug mode | True |
| SECRET_KEY | Django secret key | (required) |
| DATABASE_NAME | PostgreSQL database name | opd_tokens |
| DATABASE_USER | PostgreSQL username | postgres |
| DATABASE_PASSWORD | PostgreSQL password | postgres |
| DATABASE_HOST | PostgreSQL host | localhost |
| DATABASE_PORT | PostgreSQL port | 5432 |
| REDIS_HOST | Redis host | localhost |
| REDIS_PORT | Redis port | 6379 |
| REDIS_DB | Redis database number | 0 |

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Test connection
psql -U postgres -d opd_tokens
```

### Redis Connection Issues
```bash
# Check if Redis is running
sudo service redis status

# Test connection
redis-cli ping
```

### Migration Issues
```bash
# Reset migrations (development only!)
python manage.py migrate tokens zero
python manage.py migrate
```

## License

This is a demonstration project. Modify as needed for your use case.

## Support

For issues and questions:
1. Check the API documentation at `/api/docs/`
2. Review the logs
3. Test with Swagger UI for detailed error messages

---

**Built with ❤️ for efficient hospital operations**
