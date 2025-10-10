import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_test_drive_cars", description="Retrieves Toyota cars available for test drive with filtering options")
def get_toyota_test_drive_cars(
    car_model: Optional[str] = None,
    brand: Optional[str] = None,
    is_active: Optional[bool] = True
) -> Dict[str, Any]:
    """Retrieves Toyota cars available for test drive with comprehensive filtering options.
    
    Args:
        car_model (str, optional): Specific car model to search (e.g., 'Corolla Cross', 'Corolla'). 
        brand (str, optional): Vehicle brand filter (e.g., 'TOY')
        is_active (bool, optional): Filter by active status. Default: True
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of cars found
            - total_size (int): Total number of cars available
            - cars (list): List of car records with details
            - timestamp (str): When the request was made

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_test_drive_cars(car_model="Corolla Cross", brand="TOY")
        {
            "status": "success",
            "count": 5,
            "total_size": 102,
            "cars": [...],
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
        
        # Make API request
        response = requests.get(base_url)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "count": 0,
                "total_size": 0,
                "cars": [],
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            return {
                "status": "not_found",
                "error": "No car data found in API response or invalid response code",
                "count": 0,
                "total_size": 0,
                "cars": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract car records from the response structure
        car_records = data['data']['records']

        filtered_cars = _apply_filters(
            car_records, 
            car_model,
            brand,
            is_active
        )
        
        return {
            "status": "success",
            "count": len(filtered_cars),
            "total_size": data['data']['totalSize'],
            "done": data['data']['done'],
            "cars": filtered_cars,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "total_size": 0,
            "cars": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Car lookup failed: {str(e)}",
            "count": 0,
            "total_size": 0,
            "cars": [],
            "timestamp": datetime.now().isoformat()
        }

def _apply_filters(
    cars: List[Dict], 
    car_model: Optional[str],
    brand: Optional[str],
    is_active: Optional[bool]
) -> List[Dict]:
    """Apply filters to the car list."""
    filtered = cars

    # Car model filter - improved matching
    if car_model:
        filtered = [car for car in filtered if _matches_car_model(car, car_model)]

    # Brand filter
    if brand:
        filtered = [car for car in filtered if _matches_brand(car, brand)]

    # Active status filter
    if is_active is not None:
        filtered = [car for car in filtered if car.get('IsActive') == is_active]
    
    return filtered

def _matches_car_model(car: Dict, car_model: str) -> bool:
    """Check if car matches the model filter with flexible matching."""
    # Get all possible fields that might contain model information
    car_name = _safe_lower(car.get('Name'))
    model_of_interest = _safe_lower(car.get('Model_Of_Interest__c'))
    product_code = _safe_lower(car.get('ProductCode'))
    
    search_model = car_model.lower().strip()
    
    # Check if search term appears in any of the fields
    return (search_model in car_name or 
            search_model in model_of_interest or
            search_model in product_code or
            _partial_match(car_name, search_model) or
            _partial_match(model_of_interest, search_model))

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

def _matches_brand(car: Dict, brand: str) -> bool:
    """Check if car matches the brand filter."""
    car_brand = _safe_lower(car.get('Brand__c'))
    return brand.lower() in car_brand

#Test function to debug the filtering
def test_filtering():
    """Test the filtering logic with sample data."""
    # Sample data from the API response
    sample_cars = [
        {
            "Id": "0HnHp000000u3dYKAQ",
            "Name": "COROLLA CROSS 1.8L",
            "Brand__c": "TOY",
            "IsActive": True,
            "Model_Of_Interest__c": "Corolla Cross",
            "External_Id__c": "",
            "Material": None,
            "ProductCode": None,
            "ModelYear": None
        },
        {
            "Id": "0HnHp000000u3daKAA",
            "Name": "COROLLA XLI 1.6",
            "Brand__c": "TOY",
            "IsActive": True,
            "Model_Of_Interest__c": "Corolla",
            "External_Id__c": "",
            "Material": None,
            "ProductCode": None,
            "ModelYear": None
        }
    ]
    
    print("Testing filtering logic:")
    
    test_cases = [
        "COROLLA CROSS 1.8L",
        "Corolla Cross", 
        "Corolla",
        "Cross",
        "XLI"
    ]
    
    for search_term in test_cases:
        print(f"\nSearch for '{search_term}':")
        for car in sample_cars:
            matches = _matches_car_model(car, search_term)
            print(f"  {car['Name']}: {matches}")

def debug_api_data():
    """Debug function to see actual API data structure."""
    try:
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
        response = requests.get(base_url)
        data = response.json()
        
        if data.get('responseCode') == 1:
            cars = data['data']['records']
            print(f"\nTotal cars in API: {len(cars)}")
            print("\nFirst 5 cars:")
            for i, car in enumerate(cars[:5]):
                print(f"{i+1}. Name: '{car.get('Name')}'")
                print(f"   Model_Of_Interest: '{car.get('Model_Of_Interest__c')}'")
                print(f"   Brand: '{car.get('Brand__c')}'")
                print(f"   ProductCode: '{car.get('ProductCode')}'")
                print()
        else:
            print("API response not successful")
            
    except Exception as e:
        print(f"Debug error: {e}")

if __name__ == "__main__":
    # First test the filtering logic
    test_filtering()
    
    print("\n" + "="*50)
    print("DEBUG API DATA STRUCTURE")
    print("="*50)
    debug_api_data()
    
    print("\n" + "="*50)
    print("API TEST RESULTS")
    print("="*50)
    
    # Then test the actual API calls
    test_searches = ["Corolla Cross", "Corolla", "Cross", "XLI", "CAMRY"]
    
    for search_term in test_searches:
        print(f"\nSearching for: '{search_term}'")
        result = get_toyota_test_drive_cars(car_model=search_term)
        print(f"Found {result['count']} models")
        if result['count'] > 0:
            for car in result['cars'][:3]:  # Show first 3 matches
                print(f"  - {car.get('Name')}")
    
    print("\nAll active Toyota cars:")
    result_all = get_toyota_test_drive_cars()
    print(f"Found {result_all['count']} active Toyota cars")