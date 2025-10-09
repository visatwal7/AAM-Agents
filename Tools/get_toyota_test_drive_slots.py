import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_test_drive_slots", description="Retrieves available test drive time slots for a specific car, location, and date")
def get_toyota_test_drive_slots(
    date: str,
    territory_id: str,
    vehicle_id: str
) -> Dict[str, Any]:
    """Retrieves available test drive time slots for a specific car, location, and date.
    
    Args:
        date (str): Date for test drive in YYYY-MM-DD format (e.g., '2025-10-09')
        territory_id (str): Location ID from the locations endpoint (e.g., '0HhHp000000yAcaKAE')
        vehicle_id (str): Car ID from the cars endpoint (e.g., '0HnHp000000u3dYKAQ')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of available slots found
            - slots (list): List of available time slots
            - territory_id (str): The territory ID that was queried
            - timestamp (str): When the request was made

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_test_drive_slots(
        ...     date="2025-10-09",
        ...     territory_id="0HhHp000000yAcaKAE",
        ...     vehicle_id="0HnHp000000u3dYKAQ"
        ... )
        {
            "status": "success",
            "count": 5,
            "slots": [...],
            "territory_id": "0HhHp000000yAcaKAE",
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Validate required parameters
        validation_error = _validate_slots_parameters(date, territory_id, vehicle_id)
        if validation_error:
            return validation_error
        
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/slots"
        
        # Request payload
        payload = {
            "date": date,
            "territoryId": territory_id,
            "vehicleId": vehicle_id
        }
        
        # Make API request
        response = requests.post(base_url, json=payload)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "count": 0,
                "slots": [],
                "territory_id": territory_id,
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            return {
                "status": "not_found",
                "error": "No slot data found in API response or invalid response code",
                "count": 0,
                "slots": [],
                "territory_id": territory_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract slot data from the response structure
        slot_data = data['data']
        
        # Find slots for the specific territory
        available_slots = _extract_slots_for_territory(slot_data, territory_id)
        
        return {
            "status": "success",
            "count": len(available_slots),
            "slots": available_slots,
            "territory_id": territory_id,
            "date": date,
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "slots": [],
            "territory_id": territory_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Slot lookup failed: {str(e)}",
            "count": 0,
            "slots": [],
            "territory_id": territory_id,
            "timestamp": datetime.now().isoformat()
        }

def _validate_slots_parameters(date: str, territory_id: str, vehicle_id: str) -> Optional[Dict]:
    """Validate the input parameters for the slots API."""
    if not date:
        return {
            "status": "error",
            "error": "Date is required (YYYY-MM-DD format)",
            "count": 0,
            "slots": [],
            "timestamp": datetime.now().isoformat()
        }
    
    if not territory_id:
        return {
            "status": "error",
            "error": "Territory ID is required",
            "count": 0,
            "slots": [],
            "timestamp": datetime.now().isoformat()
        }
    
    if not vehicle_id:
        return {
            "status": "error",
            "error": "Vehicle ID is required",
            "count": 0,
            "slots": [],
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid date format. Please use YYYY-MM-DD format",
            "count": 0,
            "slots": [],
            "timestamp": datetime.now().isoformat()
        }
    
    return None

def _extract_slots_for_territory(slot_data: List[Dict], territory_id: str) -> List[Any]:
    """Extract slots for a specific territory from the API response."""
    for territory_data in slot_data:
        if territory_data.get('territoryId') == territory_id:
            return territory_data.get('slots', [])
    return []

# # Test function to debug the slots API
# def test_slots_api():
#     """Test the slots API with sample data."""
#     # Sample test data
#     test_cases = [
#         {
#             "date": "2025-10-09",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "vehicle_id": "0HnHp000000u3dYKAQ",
#             "description": "Main Showroom - Corolla Cross"
#         },
#         {
#             "date": "2025-10-10",
#             "territory_id": "0HhHp000000yAcMKAU", 
#             "vehicle_id": "0HnHp000000u3daKAA",
#             "description": "City Center - Corolla"
#         }
#     ]
    
#     print("Testing Slots API:")
#     print("=" * 60)
    
#     for test_case in test_cases:
#         print(f"\nTest Case: {test_case['description']}")
#         print(f"Date: {test_case['date']}")
#         print(f"Territory: {test_case['territory_id']}")
#         print(f"Vehicle: {test_case['vehicle_id']}")
        
#         result = get_toyota_test_drive_slots(
#             date=test_case['date'],
#             territory_id=test_case['territory_id'],
#             vehicle_id=test_case['vehicle_id']
#         )
        
#         print(f"Status: {result['status']}")
#         print(f"Slots Available: {result['count']}")
        
#         if result['count'] > 0:
#             print("Available Slots:")
#             for slot in result['slots']:
#                 print(f"  - {slot}")
#         else:
#             print("No slots available or error occurred")
#             if result.get('error'):
#                 print(f"Error: {result['error']}")

# def debug_slots_api_payload():
#     """Debug function to show what payload is being sent to the API."""
#     sample_payload = {
#         "date": "2025-10-09",
#         "territoryId": "0HhHp000000yAcaKAE",
#         "vehicleId": "0HnHp000000u3dYKAQ"
#     }
    
#     print("Slots API Request Details:")
#     print("=" * 40)
#     print(f"URL: POST https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/slots")
#     print(f"Payload: {sample_payload}")
#     print("=" * 40)

# def get_sample_data_for_testing():
#     """Get sample car and location IDs for testing the slots API."""
#     try:
#         # Get cars
#         cars_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
#         cars_response = requests.get(cars_url)
#         cars_data = cars_response.json()
        
#         sample_car = None
#         if cars_data.get('responseCode') == 1 and cars_data['data']['records']:
#             sample_car = cars_data['data']['records'][0]  # Get first car
        
#         # Get locations for the sample car
#         sample_location = None
#         if sample_car:
#             locations_url = f"https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/locations/{sample_car['Id']}"
#             headers = {"resourceCarId": sample_car['Id']}
#             locations_response = requests.get(locations_url, headers=headers)
#             locations_data = locations_response.json()
            
#             if locations_data.get('responseCode') == 1 and locations_data['data']:
#                 sample_location = locations_data['data'][0]  # Get first location
        
#         return sample_car, sample_location
        
#     except Exception as e:
#         print(f"Error getting sample data: {e}")
#         return None, None

# # if __name__ == "__main__":
# #     # Show API details
# #     debug_slots_api_payload()
    
# #     print("\n" + "=" * 60)
# #     print("GETTING SAMPLE DATA FOR TESTING")
# #     print("=" * 60)
    
# #     # Get sample data for testing
# #     sample_car, sample_location = get_sample_data_for_testing()
    
# #     if sample_car and sample_location:
# #         print(f"Sample Car: {sample_car['Name']} (ID: {sample_car['Id']})")
# #         print(f"Sample Location: {sample_location['Name']} (ID: {sample_location['id']})")
        
# #         # Test with sample data
# #         test_date = (datetime.now().replace(year=2025)).strftime('%Y-%m-%d')
        
# #         print(f"\nTesting with sample data for date: {test_date}")
# #         result = get_toyota_test_drive_slots(
# #             date=test_date,
# #             territory_id=sample_location['id'],
# #             vehicle_id=sample_car['Id']
# #         )
        
# #         print(f"Status: {result['status']}")
# #         print(f"Slots Found: {result['count']}")
# #         if result['count'] > 0:
# #             print("Available Slots:")
# #             for slot in result['slots']:
# #                 print(f"  - {slot}")
# #     else:
# #         print("Could not get sample data. Using hardcoded values for testing.")
        
# #         # Test with hardcoded values
# #         print("\n" + "=" * 60)
# #         print("TESTING WITH SAMPLE VALUES")
# #         print("=" * 60)
# #         test_slots_api()