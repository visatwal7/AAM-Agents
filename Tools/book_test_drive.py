import requests
from typing import Dict, Any, List
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="book_test_drive", description="Complete test drive booking flow - from car selection to slot booking")
def book_test_drive() -> Dict[str, Any]:
    """Complete test drive booking flow with user interaction.
    
    Returns:
        dict: A dictionary containing the booking status and details
    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> book_test_drive()
        {
            "status": "success",
            "message": "Test drive booking flow completed successfully",
            "selected_car": {...},
            "selected_location": {...},
            "available_slots": [...],
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        print("🚗 Welcome to Test Drive Booking System!")
        print("=" * 50)
        
        # Step 1: Get available cars
        print("\n📋 Step 1: Checking available cars...")
        cars_result = get_test_drive_cars()
        
        if cars_result.get('responseCode') != 1:
            return {
                "status": "error",
                "message": f"Failed to fetch cars: {cars_result.get('error', 'Unknown error')}",
                "timestamp": datetime.now().isoformat()
            }
        
        cars_data = cars_result['data']
        cars_list = cars_data.get('records', [])
        
        if not cars_list:
            return {
                "status": "error",
                "message": "No cars available for test drive",
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"✅ Found {len(cars_list)} cars available for test drive")
        
        # Display cars to user
        print("\nAvailable Cars:")
        print("-" * 30)
        for i, car in enumerate(cars_list, 1):
            print(f"{i}. {car['Name']} - {car['Model_Of_Interest__c']} ({car['Brand__c']})")
        
        # Step 2: User selects a car
        print("\n📝 Step 2: Please select a car")
        while True:
            try:
                car_choice = int(input(f"Enter car number (1-{len(cars_list)}): ").strip())
                if 1 <= car_choice <= len(cars_list):
                    selected_car = cars_list[car_choice - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(cars_list)}")
            except ValueError:
                print("Please enter a valid number")
        
        print(f"✅ Selected: {selected_car['Name']}")
        
        # Step 3: Get locations for selected car
        print(f"\n📍 Step 3: Finding test drive locations for {selected_car['Name']}...")
        locations_result = get_test_drive_locations(selected_car['Id'])
        
        if locations_result['status'] != 'success':
            return {
                "status": "error",
                "message": f"Failed to fetch locations: {locations_result.get('error', 'Unknown error')}",
                "selected_car": selected_car,
                "timestamp": datetime.now().isoformat()
            }
        
        locations_list = locations_result['locations']
        
        if not locations_list:
            return {
                "status": "error",
                "message": f"No test drive locations available for {selected_car['Name']}",
                "selected_car": selected_car,
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"✅ Found {len(locations_list)} locations")
        
        # Display locations to user
        print("\nAvailable Locations:")
        print("-" * 40)
        for i, location in enumerate(locations_list, 1):
            print(f"{i}. {location['Name']}")
            print(f"   📍 {location['Street']}, {location['City']}")
            if location.get('Longitude') and location.get('Latitude'):
                print(f"   🗺️  GPS: {location['Longitude']}, {location['Latitude']}")
            print()
        
        # Step 4: User selects a location
        print("\n📝 Step 4: Please select a location")
        while True:
            try:
                location_choice = int(input(f"Enter location number (1-{len(locations_list)}): ").strip())
                if 1 <= location_choice <= len(locations_list):
                    selected_location = locations_list[location_choice - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(locations_list)}")
            except ValueError:
                print("Please enter a valid number")
        
        print(f"✅ Selected: {selected_location['Name']}")
        
        # Step 5: Get date from user
        print("\n📅 Step 5: Please select a date for test drive")
        date = input("Enter date (YYYY-MM-DD format, e.g., 2025-10-07): ").strip()
        
        if not date:
            return {
                "status": "error",
                "message": "Date is required",
                "selected_car": selected_car,
                "selected_location": selected_location,
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 6: Get available time slots
        print(f"\n⏰ Step 6: Finding available time slots for {date}...")
        slots_result = _get_test_drive_slots_internal(date, selected_location['id'], selected_car['Id'])
        
        if slots_result.get('responseCode') != 1:
            return {
                "status": "error",
                "message": f"Failed to fetch time slots: {slots_result.get('error', 'Unknown error')}",
                "selected_car": selected_car,
                "selected_location": selected_location,
                "date": date,
                "timestamp": datetime.now().isoformat()
            }
        
        slots_data = slots_result.get('data', [])
        if not slots_data:
            return {
                "status": "error",
                "message": f"No time slots available for {date}",
                "selected_car": selected_car,
                "selected_location": selected_location,
                "date": date,
                "timestamp": datetime.now().isoformat()
            }
        
        territory_data = slots_data[0]
        available_slots = territory_data.get('slots', [])
        
        if not available_slots:
            return {
                "status": "error",
                "message": f"No time slots available for {date}",
                "selected_car": selected_car,
                "selected_location": selected_location,
                "date": date,
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"✅ Found {len(available_slots)} available time slots")
        
        # Display available slots
        print("\nAvailable Time Slots:")
        print("-" * 30)
        for i, slot in enumerate(available_slots, 1):
            start_time = slot['startTime']
            end_time = slot['endTime']
            
            # Convert UTC to readable time
            start_readable = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_readable = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            print(f"{i}. {start_readable.strftime('%I:%M %p')} - {end_readable.strftime('%I:%M %p')}")
        
        # Return successful booking flow result
        return {
            "status": "success",
            "message": "Test drive booking flow completed successfully",
            "selected_car": {
                "id": selected_car['Id'],
                "name": selected_car['Name'],
                "model": selected_car['Model_Of_Interest__c'],
                "brand": selected_car['Brand__c']
            },
            "selected_location": {
                "id": selected_location['id'],
                "name": selected_location['Name'],
                "street": selected_location['Street'],
                "city": selected_location['City'],
                "external_id": selected_location['External_Id__c']
            },
            "date": date,
            "available_slots": available_slots,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Booking flow failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def get_test_drive_cars() -> Dict[str, Any]:
    """Retrieves all available cars for test drive."""
    try:
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
        
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "message": "Error",
            "data": {},
            "responseCode": 0,
            "error": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "message": "Error",
            "data": {},
            "responseCode": 0,
            "error": f"Test drive cars lookup failed: {str(e)}"
        }


def get_test_drive_locations(resource_car_id: str) -> Dict[str, Any]:
    """Retrieves available test drive locations for a specific car model."""
    try:
        if not resource_car_id:
            return {
                "status": "error",
                "error": "Resource car ID is required",
                "count": 0,
                "locations": [],
                "car_id": "",
                "timestamp": datetime.now().isoformat()
            }
        
        base_url = f"https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/locations/{resource_car_id}"
        
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'data' not in data:
            return {
                "status": "not_found",
                "error": "No test drive locations data found in API response",
                "count": 0,
                "locations": [],
                "car_id": resource_car_id,
                "timestamp": datetime.now().isoformat()
            }
        
        locations_data = data['data']
        
        return {
            "status": "success",
            "count": len(locations_data),
            "locations": locations_data,
            "car_id": resource_car_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "locations": [],
            "car_id": resource_car_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Test drive locations lookup failed: {str(e)}",
            "count": 0,
            "locations": [],
            "car_id": resource_car_id,
            "timestamp": datetime.now().isoformat()
        }


def _get_test_drive_slots_internal(date: str, territory_id: str, vehicle_id: str) -> Dict[str, Any]:
    """Internal function to get test drive slots without user interaction."""
    try:
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/slots"
        
        payload = {
            "date": date,
            "territoryId": territory_id,
            "vehicleId": vehicle_id
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {
            "message": "Error",
            "data": [],
            "responseCode": 0,
            "error": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "message": "Error",
            "data": [],
            "responseCode": 0,
            "error": f"Test drive slots lookup failed: {str(e)}"
        }


# Individual tools for standalone use
@tool(name="get_test_drive_cars", description="Retrieves available cars for test drive")
def get_test_drive_cars_tool() -> Dict[str, Any]:
    """Standalone tool to get test drive cars."""
    return get_test_drive_cars()


@tool(name="get_test_drive_locations", description="Retrieves available test drive locations for a specific car model")
def get_test_drive_locations_tool(resource_car_id: str) -> Dict[str, Any]:
    """Standalone tool to get test drive locations."""
    return get_test_drive_locations(resource_car_id)


@tool(name="get_test_drive_slots", description="Retrieves available test drive time slots")
def get_test_drive_slots_tool(date: str, territory_id: str, vehicle_id: str) -> Dict[str, Any]:
    """Standalone tool to get test drive slots."""
    return _get_test_drive_slots_internal(date, territory_id, vehicle_id)


# # Test function
# if __name__ == "__main__":
#     # Test the complete booking flow
#     print("Testing Complete Test Drive Booking Flow:")
#     print("=" * 50)
    
#     result = book_test_drive()
    
#     print(f"\n🎯 Final Result:")
#     print(f"Status: {result['status']}")
#     print(f"Message: {result['message']}")
    
#     if result['status'] == 'success':
#         print(f"\n📋 Booking Summary:")
#         print(f"Car: {result['selected_car']['name']}")
#         print(f"Model: {result['selected_car']['model']}")
#         print(f"Location: {result['selected_location']['name']}")
#         print(f"Address: {result['selected_location']['street']}, {result['selected_location']['city']}")
#         print(f"Date: {result['date']}")
#         print(f"Available Slots: {len(result['available_slots'])}")
        
#         print(f"\n⏰ Available Time Slots:")
#         for i, slot in enumerate(result['available_slots'][:5], 1):  # Show first 5 slots
#             start_time = datetime.fromisoformat(slot['startTime'].replace('Z', '+00:00'))
#             end_time = datetime.fromisoformat(slot['endTime'].replace('Z', '+00:00'))
#             print(f"{i}. {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}")
        
#         if len(result['available_slots']) > 5:
#             print(f"... and {len(result['available_slots']) - 5} more slots")
    
#     print(f"\nTimestamp: {result['timestamp']}")
#     print("=" * 50)