#!/usr/bin/env python3
"""
Test script for Menu and Feedback functionality
"""
import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_menu_operations():
    """Test menu CRUD operations"""
    print("Testing Menu Operations...")

    # Test data
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    # Create menu
    menu_data = {
        "date": today.isoformat(),
        "meal_type": "lunch",
        "items": "Rice, Dal, Chicken Curry, Salad"
    }

    print(f"Creating menu: {menu_data}")
    response = requests.post(f"{BASE_URL}/menu/", json=menu_data)
    print(f"Create response: {response.status_code}")
    if response.status_code == 201:
        menu = response.json()
        print(f"Created menu: {menu}")
        menu_id = menu['id']
    else:
        print(f"Error: {response.text}")
        return None

    # Get menu by ID
    print(f"\nGetting menu {menu_id}...")
    response = requests.get(f"{BASE_URL}/menu/{menu_id}")
    print(f"Get response: {response.status_code}")
    if response.status_code == 200:
        menu = response.json()
        print(f"Retrieved menu: {menu}")

    # Update menu
    update_data = {
        "items": "Rice, Dal, Chicken Curry, Salad, Yogurt"
    }
    print(f"\nUpdating menu {menu_id}: {update_data}")
    response = requests.put(f"{BASE_URL}/menu/{menu_id}", json=update_data)
    print(f"Update response: {response.status_code}")
    if response.status_code == 200:
        menu = response.json()
        print(f"Updated menu: {menu}")

    # Get all menus
    print("\nGetting all menus...")
    response = requests.get(f"{BASE_URL}/menu/")
    print(f"List response: {response.status_code}")
    if response.status_code == 200:
        menus = response.json()
        print(f"Found {len(menus)} menus")

    return menu_id

def test_feedback_operations(menu_id, student_id=1):
    """Test feedback CRUD operations"""
    print("\nTesting Feedback Operations...")

    # Create feedback
    feedback_data = {
        "student_id": student_id,
        "menu_id": menu_id,
        "date": datetime.now().isoformat(),
        "meal_type": "lunch",
        "rating": 4,
        "comment": "Tasty food, but could use more vegetables"
    }

    print(f"Creating feedback: {feedback_data}")
    response = requests.post(f"{BASE_URL}/menu/feedback", json=feedback_data)
    print(f"Create response: {response.status_code}")
    if response.status_code == 201:
        feedback = response.json()
        print(f"Created feedback: {feedback}")
        feedback_id = feedback['id']
    else:
        print(f"Error: {response.text}")
        return None

    # Get feedback
    print(f"\nGetting feedback {feedback_id}...")
    response = requests.get(f"{BASE_URL}/menu/feedback/?menu_id={menu_id}")
    print(f"Get response: {response.status_code}")
    if response.status_code == 200:
        feedbacks = response.json()
        print(f"Found {len(feedbacks)} feedbacks for menu {menu_id}")

    # Update feedback
    update_data = {
        "rating": 5,
        "comment": "Excellent food! Very satisfied."
    }
    print(f"\nUpdating feedback {feedback_id}: {update_data}")
    response = requests.put(f"{BASE_URL}/menu/feedback/{feedback_id}", json=update_data)
    print(f"Update response: {response.status_code}")
    if response.status_code == 200:
        feedback = response.json()
        print(f"Updated feedback: {feedback}")

    return feedback_id

def test_menu_stats(menu_id):
    """Test menu statistics"""
    print(f"\nTesting Menu Statistics for menu {menu_id}...")
    response = requests.get(f"{BASE_URL}/menu/{menu_id}/stats")
    print(f"Stats response: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Menu stats: {stats}")
    else:
        print(f"Error: {response.text}")

def main():
    """Main test function"""
    print("Starting Menu and Feedback API Tests...")
    print("=" * 50)

    try:
        # Test menu operations
        menu_id = test_menu_operations()
        if not menu_id:
            print("Menu creation failed, skipping feedback tests")
            return

        # Test feedback operations
        feedback_id = test_feedback_operations(menu_id)
        if feedback_id:
            # Test menu stats
            test_menu_stats(menu_id)

        print("\n" + "=" * 50)
        print("Tests completed successfully!")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()
