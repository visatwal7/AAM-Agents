import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_test_drive_locations", description="Retrieves Toyota test drive locations for a specific car model")
def get_toyota_test_drive_locations(
    resource_car_id: str,
    city: Optional[str] = None,
    location_name: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota test drive locations for a specific car model with filtering options.
    
    Args:
        resource_car_id (str): The car resource ID to get locations for (required)
        city (str, optional): Filter locations by city (e.g., 'Doha', 'Lusail')
        location_name (str, optional): Filter locations by name (e.g., 'Main Showroom', 'City Center')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of locations found
            - locations (list): List of test drive locations with details
            - timestamp (str): When the request was made

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_test_drive_locations(resource_car_id="0HnHp000000u3dYKAQ", city="Doha")
        {
            "status": "success",
            "count": 2,
            "locations": [...],
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Validate required parameter
        if not resource_car_id:
            return {
                "status": "error",
                "error": "resource_car_id is required",
                "count": 0,
                "locations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # API endpoint configuration
        base_url = f"https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/locations/{resource_car_id}"
        
        # Make API request with headers
        headers = {
            "resourceCarId": resource_car_id
        }
        
        response = requests.get(base_url, headers=headers)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "count": 0,
                "locations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            return {
                "status": "not_found",
                "error": "No location data found in API response or invalid response code",
                "count": 0,
                "locations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract location data from the response structure
        location_records = data['data']

        filtered_locations = _apply_location_filters(
            location_records, 
            city,
            location_name
        )
        
        return {
            "status": "success",
            "count": len(filtered_locations),
            "locations": filtered_locations,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "locations": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Location lookup failed: {str(e)}",
            "count": 0,
            "locations": [],
            "timestamp": datetime.now().isoformat()
        }

def _apply_location_filters(
    locations: List[Dict], 
    city: Optional[str],
    location_name: Optional[str]
) -> List[Dict]:
    """Apply filters to the location list."""
    filtered = locations

    # City filter
    if city:
        filtered = [loc for loc in filtered if _matches_city(loc, city)]

    # Location name filter
    if location_name:
        filtered = [loc for loc in filtered if _matches_location_name(loc, location_name)]
    
    return filtered

def _matches_city(location: Dict, city: str) -> bool:
    """Check if location matches the city filter."""
    location_city = _safe_lower(location.get('City'))
    return city.lower() in location_city

def _matches_location_name(location: Dict, location_name: str) -> bool:
    """Check if location matches the name filter."""
    name = _safe_lower(location.get('Name'))
    external_id = _safe_lower(location.get('External_Id__c'))
    search_term = location_name.lower().strip()
    
    return (search_term in name or 
            search_term in external_id or
            _partial_match(name, search_term))

def _safe_lower(value: Any) -> str:
    """Safely convert value to lowercase, handling None values."""
    if value is None:
        return ""
    return str(value).lower()

def _partial_match(field_value: str, search_term: str) -> bool:
    """Check for partial matches by splitting words."""
    if not field_value or not search_term:
        return False
    
    # Split both field value and search term into words
    field_words = field_value.split()
    search_words = search_term.split()
    
    # Check if any search word appears in any field word
    for search_word in search_words:
        for field_word in field_words:
            if search_word in field_word:
                return True
    return False

# Test function to debug the filtering
def test_location_filtering():
    """Test the location filtering logic with sample data."""
    # Sample data from the API response
    sample_locations = [
        {
            "Name": "Main Showroom Toyota",
            "External_Id__c": "TD001",
            "Longitude": 51.5482684434861,
            "Latitude": 25.269168627363623,
            "City": "Doha",
            "Street": "Street 310",
            "id": "0HhHp000000yAcaKAE"
        },
        {
            "Name": "City Center Showroom Toyota",
            "External_Id__c": "TD003",
            "Longitude": 51.48608,
            "Latitude": 25.346795,
            "City": "Doha",
            "Street": "Street 850",
            "id": "0HhHp000000yAcMKAU"
        },
        {
            "Name": "Lusail Showroom Toyota",
            "External_Id__c": "TD002",
            "Longitude": None,
            "Latitude": None,
            "City": "Lusail",
            "Street": "Street 335",
            "id": "0HhHp000000yAcVKAU"
        }
    ]
    
#     print("Testing location filtering logic:")
    
#     # Test city filtering
#     test_cities = ["Doha", "Lusail", "doha"]
#     for city in test_cities:
#         print(f"\nFilter by city: '{city}'")
#         filtered = _apply_location_filters(sample_locations, city=city, location_name=None)
#         print(f"Found {len(filtered)} locations:")
#         for loc in filtered:
#             print(f"  - {loc['Name']} in {loc['City']}")
    
#     # Test name filtering
#     test_names = ["Main", "City Center", "Showroom", "Toyota"]
#     for name in test_names:
#         print(f"\nFilter by name: '{name}'")
#         filtered = _apply_location_filters(sample_locations, city=None, location_name=name)
#         print(f"Found {len(filtered)} locations:")
#         for loc in filtered:
#             print(f"  - {loc['Name']}")

# def debug_location_api_data(resource_car_id: str):
#     """Debug function to see actual API data structure."""
#     try:
#         base_url = f"https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/locations/{resource_car_id}"
#         headers = {
#             "resourceCarId": resource_car_id
#         }
        
#         response = requests.get(base_url, headers=headers)
#         data = response.json()
        
#         if data.get('responseCode') == 1:
#             locations = data['data']
#             print(f"\nTotal locations in API for car {resource_car_id}: {len(locations)}")
#             print("\nFirst 5 locations:")
#             for i, location in enumerate(locations[:5]):
#                 print(f"{i+1}. Name: '{location.get('Name')}'")
#                 print(f"   City: '{location.get('City')}'")
#                 print(f"   Street: '{location.get('Street')}'")
#                 print(f"   External_ID: '{location.get('External_Id__c')}'")
#                 print(f"   Coordinates: {location.get('Latitude')}, {location.get('Longitude')}")
#                 print()
#         else:
#             print(f"API response not successful for car {resource_car_id}")
            
#     except Exception as e:
#         print(f"Debug error: {e}")

# # Helper function to get car IDs first for testing
# def get_available_car_ids():
#     """Get available car IDs for testing the locations API."""
#     try:
#         cars_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
#         response = requests.get(cars_url)
#         data = response.json()
        
#         if data.get('responseCode') == 1:
#             cars = data['data']['records']
#             print("Available car IDs for testing:")
#             for i, car in enumerate(cars[:5]):  # Show first 5 cars
#                 print(f"{i+1}. ID: {car.get('Id')}, Name: {car.get('Name')}")
#             return [car.get('Id') for car in cars[:3]]  # Return first 3 IDs for testing
#         return []
#     except Exception as e:
#         print(f"Error getting car IDs: {e}")
#         return []

# if __name__ == "__main__":
#     # First test the filtering logic with sample data
#     test_location_filtering()
    
#     print("\n" + "="*60)
#     print("GETTING AVAILABLE CAR IDs FOR TESTING")
#     print("="*60)
    
#     # Get some car IDs to test with
#     test_car_ids = get_available_car_ids()
    
#     if test_car_ids:
#         print("\n" + "="*60)
#         print("TESTING LOCATIONS API WITH REAL CAR IDs")
#         print("="*60)
        
#         for car_id in test_car_ids[:2]:  # Test with first 2 car IDs
#             print(f"\nTesting with car ID: {car_id}")
            
#             # Debug - show actual API data
#             debug_location_api_data(car_id)
            
#             # Test different filters
#             print(f"\nLocations for car {car_id} (all):")
#             result_all = get_toyota_test_drive_locations(resource_car_id=car_id)
#             print(f"Found {result_all['count']} locations")
            
#             if result_all['count'] > 0:
#                 # Test city filter if we have locations
#                 sample_city = result_all['locations'][0].get('City') if result_all['locations'] else "Doha"
#                 print(f"\nLocations in {sample_city}:")
#                 result_city = get_toyota_test_drive_locations(resource_car_id=car_id, city=sample_city)
#                 print(f"Found {result_city['count']} locations in {sample_city}")
                
#                 # Test name filter
#                 print(f"\nLocations with 'Showroom' in name:")
#                 result_name = get_toyota_test_drive_locations(resource_car_id=car_id, location_name="Showroom")
#                 print(f"Found {result_name['count']} locations with 'Showroom'")
#     else:
#         print("\nNo car IDs available for testing. Using sample car ID.")
#         # Use a sample car ID for testing
#         sample_car_id = "0HnHp000000u3dYKAQ"
#         debug_location_api_data(sample_car_id)
#         result = get_toyota_test_drive_locations(resource_car_id=sample_car_id)
#         print(f"Found {result['count']} locations for sample car")