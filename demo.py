"""
Demo script to test the OPD Token Allocation System
Run this after setting up the database and starting the server

For Docker: docker-compose exec web python demo.py
For Local: python demo.py
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Detect if running inside Docker
try:
    import socket
    hostname = socket.gethostname()
    if 'web' in hostname or hostname.startswith('opd'):
        BASE_URL = "http://localhost:8000/api/v1"
    else:
        BASE_URL = "http://localhost:8000/api/v1"
except:
    BASE_URL = "http://localhost:8000/api/v1"


def print_response(title, response):
    """Pretty print API responses"""
    print(f"\n{'='*60}")
    print(f"🔹 {title}")
    print(f"{'='*60}")
    if response.status_code in [200, 201]:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text[:500])
    else:
        print(f"❌ Error {response.status_code}")
        print(f"URL: {response.url}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text[:500])


def test_full_workflow():
    """Test complete booking workflow"""
    
    print("\n" + "="*60)
    print("🏥 OPD TOKEN ALLOCATION SYSTEM - DEMO")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    # 1. Create Doctors
    print("\n📋 STEP 1: Creating Doctors")
    print("-" * 60)
    
    doctors = [
        {"name": "Dr. Sarah Johnson", "specialization": "Cardiology"},
        {"name": "Dr. Michael Chen", "specialization": "Orthopedics"},
        {"name": "Dr. Emily Brown", "specialization": "General Medicine"}
    ]
    
    doctor_ids = []
    for doctor in doctors:
        response = requests.post(f"{BASE_URL}/doctors/", json=doctor)
        print_response(f"Created: {doctor['name']}", response)
        if response.status_code == 201:
            doctor_ids.append(response.json()["id"])
    
    if not doctor_ids:
        print("\n❌ No doctors created. Check if server is running.")
        return
    
    # 2. Create Slots
    print("\n📋 STEP 2: Creating Time Slots")
    print("-" * 60)
    
    tomorrow = datetime.now() + timedelta(days=1)
    slot_times = [
        (9, 10), (10, 11), (11, 12)  # Morning slots
    ]
    
    slot_ids = []
    for doctor_id in doctor_ids[:1]:  # Use first doctor for demo
        for start_hour, end_hour in slot_times:
            start_time = tomorrow.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = tomorrow.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
            slot_data = {
                "doctor": doctor_id,  # Changed from doctor_id to doctor
                "start_time": start_time.isoformat(),  # Removed Z
                "end_time": end_time.isoformat(),  # Removed Z
                "max_capacity": 6  # Increased for demo
            }
            
            response = requests.post(f"{BASE_URL}/slots/", json=slot_data)
            print_response(f"Slot {start_hour}:00-{end_hour}:00", response)
            if response.status_code == 201:
                slot_ids.append(response.json()["id"])
    
    if not slot_ids:
        print("\n❌ No slots created. Stopping demo.")
        return
    
    # 3. Create Patients
    print("\n📋 STEP 3: Creating Patients")
    print("-" * 60)
    
    patients = [
        {"name": "John Doe", "phone": "+1234567890", "email": "john@example.com"},
        {"name": "Jane Smith", "phone": "+1234567891", "email": "jane@example.com"},
        {"name": "Bob Wilson", "phone": "+1234567892", "email": "bob@example.com"},
        {"name": "Alice Davis", "phone": "+1234567893", "email": "alice@example.com"},
        {"name": "Charlie Brown", "phone": "+1234567894", "email": "charlie@example.com"},
        {"name": "Emergency Patient", "phone": "+1234567895", "email": "emergency@example.com"}
    ]
    
    patient_ids = []
    for patient in patients:
        response = requests.post(f"{BASE_URL}/patients/", json=patient)
        print_response(f"Created: {patient['name']}", response)
        if response.status_code == 201:
            patient_ids.append(response.json()["id"])
    
    # 4. Book Tokens with Different Priorities
    print("\n📋 STEP 4: Booking Tokens (Priority-based)")
    print("-" * 60)
    
    test_slot_id = slot_ids[0]
    
    bookings = [
        {"patient_idx": 0, "category": "WALKIN", "name": "John (Walk-in)"},
        {"patient_idx": 1, "category": "ONLINE", "name": "Jane (Online)"},
        {"patient_idx": 2, "category": "PRIORITY_PAID", "name": "Bob (Priority Paid)"},
        {"patient_idx": 3, "category": "FOLLOWUP", "name": "Alice (Follow-up)"},
        {"patient_idx": 4, "category": "ONLINE", "name": "Charlie (Online)"},
    ]
    
    token_ids = []
    for booking in bookings:
        token_data = {
            "slot_id": test_slot_id,
            "patient_id": patient_ids[booking["patient_idx"]],
            "category": booking["category"]
        }
        
        response = requests.post(f"{BASE_URL}/tokens/", json=token_data)
        print_response(f"Booking: {booking['name']}", response)
        if response.status_code == 201:
            token_ids.append(response.json()["id"])
    
    # 5. View Slot Status
    print("\n📋 STEP 5: Viewing Slot Status & Token Order")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/slots/{test_slot_id}/")
    print_response("Slot Details", response)
    
    response = requests.get(f"{BASE_URL}/slots/{test_slot_id}/tokens/")
    print_response("All Tokens (Priority Order)", response)
    
    # 6. Insert Emergency Patient
    print("\n📋 STEP 6: Inserting Emergency Patient")
    print("-" * 60)
    
    emergency_data = {
        "slot_id": test_slot_id,
        "patient_id": patient_ids[5]  # Emergency patient
    }
    
    response = requests.post(f"{BASE_URL}/tokens/emergency/", json=emergency_data)
    print_response("Emergency Insertion", response)
    
    # 7. View Updated Token Order
    print("\n📋 STEP 7: Updated Token Order After Emergency")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/slots/{test_slot_id}/tokens/")
    print_response("All Tokens (After Emergency)", response)
    
    # 8. Test Slot Delay
    print("\n📋 STEP 8: Simulating Doctor Delay")
    print("-" * 60)
    
    delay_data = {"delay_minutes": 15}
    response = requests.put(f"{BASE_URL}/slots/{test_slot_id}/delay/", json=delay_data)
    print_response("Slot Delayed by 15 minutes", response)
    
    # 9. View tokens after delay
    response = requests.get(f"{BASE_URL}/slots/{test_slot_id}/tokens/")
    print_response("Tokens After Delay", response)
    
    # 10. Cancel a Token
    print("\n📋 STEP 9: Cancelling a Token")
    print("-" * 60)
    
    if token_ids:
        token_to_cancel = token_ids[0]
        response = requests.delete(f"{BASE_URL}/tokens/{token_to_cancel}/")
        print_response("Token Cancelled", response)
    
    # 11. View final token order
    print("\n📋 STEP 10: Final Token Order")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/slots/{test_slot_id}/tokens/")
    print_response("Final Token Order", response)
    
    # 12. Generate Daily Report
    print("\n📋 STEP 11: Daily Report")
    print("-" * 60)
    
    report_date = tomorrow.strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/reports/daily/?date={report_date}")
    print_response("Daily Allocation Report", response)
    
    # 13. Test Capacity Overflow (Waiting List)
    print("\n📋 STEP 12: Testing Capacity Overflow")
    print("-" * 60)
    
    overflow_data = {
        "slot_id": test_slot_id,
        "patient_id": patient_ids[0],  # Try to book again
        "category": "WALKIN"
    }
    
    response = requests.post(f"{BASE_URL}/tokens/", json=overflow_data)
    print_response("Overflow Booking Attempt", response)
    
    # Check waiting list
    response = requests.get(f"{BASE_URL}/waiting-list/by_slot/?slot_id={test_slot_id}")
    print_response("Waiting List", response)
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📊 Summary:")
    print("   - Created 3 doctors and 3 time slots")
    print("   - Registered 6 patients")
    print("   - Tested priority-based allocation")
    print("   - Inserted emergency patient at position 1")
    print("   - Applied 15-minute delay to slot")
    print("   - Cancelled a token and tested reallocation")
    print("   - Generated daily report")
    print("   - Tested capacity overflow")
    print("\n🌐 View full results in:")
    print("   Admin Panel: http://localhost:8000/admin/")
    print("   API Docs: http://localhost:8000/api/docs/")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running!")
    print("   Docker: docker-compose up -d")
    print("   Local: python manage.py runserver\n")
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL}/doctors/", timeout=5)
        print(f"✅ Server is reachable at {BASE_URL}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: Could not connect to server at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print("\n   Make sure:")
        print("   1. Django server is running")
        print("   2. Database migrations are complete")
        print("   3. You're using the correct URL")
        sys.exit(1)
    
    input("\nPress Enter to start the demo...")
    
    try:
        test_full_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
