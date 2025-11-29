import requests
import time

BASE_URL = "http://localhost:8000"

def test_workflow():
    # 1. Create a user
    user_data = {"name": "Test User", "email": "test@example.com", "card_status": "ACTIVE"}
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    if response.status_code != 200:
        print(f"Failed to create user: {response.text}")
        return
    user = response.json()
    user_id = user["id"]
    print(f"Created user {user_id} with status {user['card_status']}")

    # 2. Simulate a safe transaction
    safe_tx = {
        "user_id": user_id,
        "merchant": "Safe Mart",
        "amount": 100.0,
        "category": "Groceries",
        "timestamp": "2023-10-27T10:00:00"
    }
    response = requests.post(f"{BASE_URL}/simulate_transaction", json=safe_tx)
    print(f"Safe transaction response: {response.status_code}")
    
    # Check user status (should still be ACTIVE)
    response = requests.get(f"{BASE_URL}/users")
    users = response.json()
    my_user = next((u for u in users if u["id"] == user_id), None)
    print(f"User status after safe tx: {my_user['card_status']}")

    # 3. Simulate a violation transaction (Gambling)
    violation_tx = {
        "user_id": user_id,
        "merchant": "Casino Royale",
        "amount": 200.0,
        "category": "Gambling",
        "timestamp": "2023-10-27T12:00:00"
    }
    response = requests.post(f"{BASE_URL}/simulate_transaction", json=violation_tx)
    print(f"Violation transaction response: {response.status_code}")

    # Check user status (should be FROZEN)
    response = requests.get(f"{BASE_URL}/users")
    users = response.json()
    my_user = next((u for u in users if u["id"] == user_id), None)
    print(f"User status after violation tx: {my_user['card_status']}")
    
    if my_user['card_status'] == "FROZEN":
        print("SUCCESS: User card was frozen!")
    else:
        print("FAILURE: User card was NOT frozen.")

if __name__ == "__main__":
    try:
        test_workflow()
    except Exception as e:
        print(f"Test failed: {e}")
