# API Usage Examples

This document provides practical examples for using the OPD Token Allocation API.

## Table of Contents
- [Setup & Authentication](#setup--authentication)
- [Workflow Examples](#workflow-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Testing Concurrency](#testing-concurrency)

## Setup & Authentication

Currently, this MVP doesn't require authentication. For production, implement JWT or session-based auth.

### Base URL
```
http://localhost:8000/api/v1/
```

## Workflow Examples

### Complete Booking Flow

#### Step 1: Create a Doctor
```bash
curl -X POST http://localhost:8000/api/v1/doctors/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Sarah Johnson",
    "specialization": "Cardiology"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Dr. Sarah Johnson",
  "specialization": "Cardiology",
  "created_at": "2026-01-29T10:00:00Z"
}
```

#### Step 2: Create Multiple Slots for the Day
```bash
# Morning slot 9-10 AM
curl -X POST http://localhost:8000/api/v1/slots/ \
  -H "Content-Type: application/json" \
  -d '{
    "doctor": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "start_time": "2026-02-01T09:00:00Z",
    "end_time": "2026-02-01T10:00:00Z",
    "max_capacity": 15
  }'

# Morning slot 10-11 AM
curl -X POST http://localhost:8000/api/v1/slots/ \
  -H "Content-Type: application/json" \
  -d '{
    "doctor": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "start_time": "2026-02-01T10:00:00Z",
    "end_time": "2026-02-01T11:00:00Z",
    "max_capacity": 15
  }'
```

#### Step 3: Register Patients
```bash
# Patient 1 - Online booking
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john@example.com"
  }'

# Patient 2 - Walk-in
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "phone": "+1234567891",
    "email": "jane@example.com"
  }'
```

#### Step 4: Book Tokens
```bash
# Online booking (Priority 4)
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid-from-step-2",
    "patient_id": "patient-1-uuid",
    "category": "ONLINE"
  }'

# Walk-in (Priority 5)
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid-from-step-2",
    "patient_id": "patient-2-uuid",
    "category": "WALKIN"
  }'
```

**Response:**
```json
{
  "id": "token-uuid",
  "slot": "slot-uuid",
  "patient": "patient-uuid",
  "patient_name": "John Doe",
  "token_number": 1,
  "priority": 3.8,
  "category": "ONLINE",
  "status": "CONFIRMED",
  "estimated_time": "2026-02-01T09:00:00Z",
  "actual_time": null,
  "created_at": "2026-01-29T10:30:00Z"
}
```

### Priority-Based Allocation Example

```bash
# Book multiple patients with different priorities
# The system will automatically order them correctly

# 1. Walk-in patient (Priority 5)
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid",
    "patient_id": "patient-a-uuid",
    "category": "WALKIN"
  }'
# Gets token_number: 1

# 2. Online patient (Priority 4)
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid",
    "patient_id": "patient-b-uuid",
    "category": "ONLINE"
  }'
# Gets token_number: 1, Walk-in shifts to 2

# 3. Priority Paid (Priority 2)
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid",
    "patient_id": "patient-c-uuid",
    "category": "PRIORITY_PAID"
  }'
# Gets token_number: 1, others shift down
```

**Final Order:**
1. Priority Paid (priority 2)
2. Online (priority 4)
3. Walk-in (priority 5)

## Advanced Scenarios

### Emergency Patient Insertion

```bash
curl -X POST http://localhost:8000/api/v1/tokens/emergency/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "slot-uuid",
    "patient_id": "emergency-patient-uuid"
  }'
```

**Response:**
```json
{
  "token": {
    "id": "emergency-token-uuid",
    "token_number": 1,
    "priority": 1.0,
    "category": "EMERGENCY",
    "estimated_time": "2026-02-01T09:00:00Z"
  },
  "affected_tokens": [
    {
      "id": "token-1",
      "token_number": 2,
      "estimated_time": "2026-02-01T09:10:00Z"
    },
    {
      "id": "token-2",
      "token_number": 3,
      "estimated_time": "2026-02-01T09:20:00Z"
    }
  ],
  "message": "Emergency patient inserted at position 1"
}
```

### Doctor Delay Handling

```bash
# Doctor is delayed by 30 minutes
curl -X PUT http://localhost:8000/api/v1/slots/slot-uuid/delay/ \
  -H "Content-Type: application/json" \
  -d '{
    "delay_minutes": 30
  }'
```

**Response:**
```json
{
  "message": "Slot delayed by 30 minutes",
  "slot": {
    "id": "slot-uuid",
    "status": "DELAYED",
    "delay_minutes": 30,
    "current_capacity": 10,
    "max_capacity": 15
  }
}
```

All tokens in this slot will have their `estimated_time` pushed by 30 minutes.

### Token Cancellation

```bash
curl -X DELETE http://localhost:8000/api/v1/tokens/token-uuid/
```

**Response:**
```json
{
  "message": "Token cancelled successfully"
}
```

What happens:
1. Token status changed to CANCELLED
2. Slot capacity decremented
3. Waiting list checked for promotion
4. Remaining tokens compacted (gap removed)

### Marking No-Show

```bash
curl -X POST http://localhost:8000/api/v1/tokens/token-uuid/no_show/ \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "message": "Token cancelled successfully"
}
```

The system marks the token as NO_SHOW and processes it like a cancellation.

### Viewing Slot Status

```bash
# Get slot details with capacity info
curl http://localhost:8000/api/v1/slots/slot-uuid/

# Get all tokens for a slot
curl http://localhost:8000/api/v1/slots/slot-uuid/tokens/
```

**Response (tokens):**
```json
[
  {
    "id": "token-1-uuid",
    "token_number": 1,
    "patient_name": "Emergency Patient",
    "category": "EMERGENCY",
    "priority": 1.0,
    "status": "CONFIRMED",
    "estimated_time": "2026-02-01T09:00:00Z"
  },
  {
    "id": "token-2-uuid",
    "token_number": 2,
    "patient_name": "Priority Patient",
    "category": "PRIORITY_PAID",
    "priority": 2.0,
    "status": "CONFIRMED",
    "estimated_time": "2026-02-01T09:10:00Z"
  }
]
```

### Checking Waiting List

```bash
# Get waiting list for a specific slot
curl "http://localhost:8000/api/v1/waiting-list/by_slot/?slot_id=slot-uuid"
```

**Response:**
```json
[
  {
    "id": "waiting-1-uuid",
    "patient": "patient-uuid",
    "patient_name": "John Waiting",
    "category": "ONLINE",
    "priority": 4.0,
    "created_at": "2026-01-29T11:00:00Z"
  }
]
```

### Daily Reports

```bash
# Get today's report
curl http://localhost:8000/api/v1/reports/daily/

# Get report for specific date
curl "http://localhost:8000/api/v1/reports/daily/?date=2026-02-01"

# Filter by doctor
curl "http://localhost:8000/api/v1/reports/daily/?date=2026-02-01&doctor_id=doctor-uuid"
```

**Response:**
```json
{
  "date": "2026-02-01",
  "total_slots": 8,
  "total_tokens": 85,
  "confirmed_tokens": 70,
  "cancelled_tokens": 5,
  "no_show_tokens": 3,
  "completed_tokens": 7,
  "cancellation_rate": 5.88,
  "no_show_rate": 3.53,
  "capacity_utilization": 87.5,
  "category_breakdown": [
    {"category": "ONLINE", "count": 45},
    {"category": "WALKIN", "count": 25},
    {"category": "FOLLOWUP", "count": 10},
    {"category": "PRIORITY_PAID", "count": 3},
    {"category": "EMERGENCY", "count": 2}
  ],
  "status_breakdown": [
    {"status": "CONFIRMED", "count": 70},
    {"status": "COMPLETED", "count": 7},
    {"status": "CANCELLED", "count": 5},
    {"status": "NO_SHOW", "count": 3}
  ]
}
```

## Testing Concurrency

### Simulate Race Condition

Open two terminal windows and run simultaneously:

**Terminal 1:**
```bash
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "same-slot-uuid",
    "patient_id": "patient-1-uuid",
    "category": "ONLINE"
  }'
```

**Terminal 2 (run immediately):**
```bash
curl -X POST http://localhost:8000/api/v1/tokens/ \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "same-slot-uuid",
    "patient_id": "patient-2-uuid",
    "category": "ONLINE"
  }'
```

**Expected Behavior:**
- If slot has capacity: Both succeed with different token numbers
- If slot has only 1 space left: One succeeds, other goes to waiting list
- No race conditions or duplicate positions

### Load Testing Script

```bash
#!/bin/bash
# Create 50 concurrent requests

SLOT_ID="your-slot-uuid"

for i in {1..50}; do
  (
    curl -X POST http://localhost:8000/api/v1/tokens/ \
      -H "Content-Type: application/json" \
      -d "{
        \"slot_id\": \"$SLOT_ID\",
        \"patient_id\": \"patient-$i-uuid\",
        \"category\": \"ONLINE\"
      }" &
  )
done

wait
echo "All requests completed"
```

## Common Error Responses

### Slot Full
```json
{
  "error": "Slot is full. Added to waiting list."
}
```

### Duplicate Booking
```json
{
  "error": "Patient already has a booking for this day"
}
```

### Lock Timeout
```json
{
  "error": "Failed to acquire lock: timeout"
}
```

### Invalid Category
```json
{
  "category": [
    "\"INVALID\" is not a valid choice."
  ]
}
```

## Tips for Testing

1. **Use Swagger UI** at `http://localhost:8000/api/docs/` for interactive testing
2. **Check Admin Panel** at `http://localhost:8000/admin/` to verify database state
3. **Monitor Logs** for detailed error information
4. **Test Edge Cases** like full slots, concurrent bookings, emergency insertions
5. **Verify Priority Order** by booking patients with different categories

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create a doctor
doctor_response = requests.post(
    f"{BASE_URL}/doctors/",
    json={
        "name": "Dr. Smith",
        "specialization": "General Medicine"
    }
)
doctor_id = doctor_response.json()["id"]

# Create a slot
slot_response = requests.post(
    f"{BASE_URL}/slots/",
    json={
        "doctor": doctor_id,
        "start_time": "2026-02-01T09:00:00Z",
        "end_time": "2026-02-01T10:00:00Z",
        "max_capacity": 15
    }
)
slot_id = slot_response.json()["id"]

# Book a token
token_response = requests.post(
    f"{BASE_URL}/tokens/",
    json={
        "slot_id": slot_id,
        "patient_id": "patient-uuid",
        "category": "ONLINE"
    }
)

print(f"Token Number: {token_response.json()['token_number']}")
print(f"Priority: {token_response.json()['priority']}")
```

---

**Happy Testing! 🚀**
