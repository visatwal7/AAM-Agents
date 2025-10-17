import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import re


@tool(name="book_test_drive", description="Check car availability and get details for test drive booking")
def book_test_drive(
    car_request: str
) -> Dict[str, Any]:
    """Check if a car is available for test drive and get booking details.
    
    Args:
        car_request (str): Natural language request for test drive (e.g., "I want to book test drive for Prado")
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'available', 'not_found', or 'error'
            - message (str): Human readable response
            - available_cars (list): List of available cars with details
            - count (int): Number of available cars found
            - timestamp (str): When the request was made

    Examples:
        >>> book_test_drive("I want to book test drive for Prado")
        {
            "status": "available",
            "message": "Great! I found 3 Prado models available for test drive.",
            "available_cars": [...],
            "count": 3,
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Extract car model from natural language request
        car_model = _extract_car_model(car_request)
        
        if not car_model:
            return {
                "status": "not_found",
                "message": "I couldn't identify which car model you're looking for. Please specify the car model (e.g., 'Prado', 'Corolla', 'RAV4').",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }

        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
        
        # Make API request
        response = requests.get(base_url, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "message": "Sorry, I'm having trouble accessing the car database right now. Please try again later.",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            return {
                "status": "error",
                "message": "The car database is currently unavailable. Please try again later.",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract car records from the response structure
        car_records = data['data']['records']

        # Filter for active cars matching the requested model
        available_cars = _find_available_cars(car_records, car_model)
        
        # Transform the response to show only essential booking details
        transformed_cars = _transform_for_booking(available_cars)
        
        # Generate appropriate message based on results
        if transformed_cars:
            if len(transformed_cars) == 1:
                message = f"Perfect! I found 1 {car_model} model available for test drive."
            else:
                message = f"Great! I found {len(transformed_cars)} {car_model} models available for test drive."
            
            return {
                "status": "available",
                "message": message,
                "available_cars": transformed_cars,
                "count": len(transformed_cars),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_found",
                "message": f"I'm sorry, but I couldn't find any available {car_model} models for test drive at the moment. Please check back later or consider other models.",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Network error occurred while checking car availability. Please check your connection and try again.",
            "available_cars": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "An unexpected error occurred while processing your request. Please try again.",
            "available_cars": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }


def _extract_car_model(user_input: str) -> str:
    """Extract car model from natural language input."""
    if not user_input:
        return ""
    
    # Convert to lowercase for easier matching
    input_lower = user_input.lower()
    
    # Common car models to look for
    car_models = [
        'prado', 'corolla', 'camry', 'rav4', 'fortuner', 'hilux', 'innova', 
        'hiace', 'crown', 'supra', 'gr86', 'raize', 'veloz', 'urban cruiser',
        'highlander', 'land cruiser', 'lx600', 'ls500', 'es350', 'ux300', 'nx350'
    ]
    
    # Look for car models in the input
    for model in car_models:
        if model in input_lower:
            return model.title()
    
    # Try to extract using patterns
    patterns = [
        r'(?:book|test drive|drive|want|looking for)\s+(?:a|the)?\s*([a-zA-Z0-9\s]+?)(?:\s+test drive|\s+car|\.|$)',
        r'test drive\s+for\s+([a-zA-Z0-9\s]+)',
        r'book\s+(?:a|the)?\s*([a-zA-Z0-9\s]+)(?:\s+for test drive)?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, input_lower)
        if match:
            potential_model = match.group(1).strip()
            # Check if it matches known models or looks like a car model
            if any(word in potential_model.lower() for word in ['prado', 'corolla', 'camry', 'rav4', 'fortuner']):
                return potential_model.title()
            elif len(potential_model.split()) <= 3:  # Likely a car model name
                return potential_model.title()
    
    return ""


def _find_available_cars(cars: List[Dict], car_model: str) -> List[Dict]:
    """Find active cars that match the requested model."""
    available_cars = []
    search_term = car_model.lower()
    
    for car in cars:
        # Check if car is active
        if not car.get('IsActive', False):
            continue
            
        car_name = car.get('Name', '').lower()
        model_interest = car.get('Model_Of_Interest__c', '').lower()
        
        # Check for matches in car name or model of interest
        if (search_term in car_name or 
            search_term in model_interest or
            any(word in car_name for word in search_term.split()) or
            any(word in model_interest for word in search_term.split())):
            available_cars.append(car)
    
    return available_cars


def _transform_for_booking(cars: List[Dict]) -> List[Dict]:
    """Transform car data to show only essential booking details."""
    transformed = []
    
    for car in cars:
        # Create a clean car object with only booking-relevant information
        transformed_car = {
            "Id": car.get("Id"),
            "Name": car.get("Name"),
            "Brand__c": car.get("Brand__c"),
            "IsActive": car.get("IsActive"),
            "Model_Of_Interest__c": car.get("Model_Of_Interest__c")
        }
        transformed.append(transformed_car)
    
    return transformed


# Additional helper functions for specific use cases
@tool(name="check_car_availability", description="Check if specific car models are available for test drive")
def check_car_availability(
    car_models: str
) -> Dict[str, Any]:
    """Check availability of specific car models for test drive.
    
    Args:
        car_models (str): Comma-separated list of car models (e.g., "Prado, Corolla, RAV4")
    
    Returns:
        dict: Availability status for each requested model
    """
    models = [model.strip() for model in car_models.split(',')]
    results = {}
    
    for model in models:
        result = book_test_drive(f"I want to book test drive for {model}")
        results[model] = {
            "available": result["status"] == "available",
            "count": result["count"],
            "cars": result["available_cars"]
        }
    
    return {
        "status": "success",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@tool(name="get_all_available_cars", description="Get all cars currently available for test drive")
def get_all_available_cars() -> Dict[str, Any]:
    """Get all active cars available for test drive."""
    try:
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/cars"
        
        response = requests.get(base_url, timeout=10)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": "Unable to fetch car data",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
        
        if not data or data.get('responseCode') != 1:
            return {
                "status": "error",
                "message": "Invalid response from car database",
                "available_cars": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Filter only active cars
        active_cars = [car for car in data['data']['records'] if car.get('IsActive', False)]
        transformed_cars = _transform_for_booking(active_cars)
        
        return {
            "status": "success",
            "message": f"Found {len(transformed_cars)} cars available for test drive",
            "available_cars": transformed_cars,
            "count": len(transformed_cars),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching car data: {str(e)}",
            "available_cars": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the tool with various natural language requests
    test_requests = [
        "I want to book test drive for Prado",
        "Can I test drive a Corolla?",
        "Book test drive for Toyota RAV4",
        "I'm interested in Fortuner test drive",
        "Show me available Camry models for test drive",
        "Test drive booking for Honda Civic"  # Should return not found
    ]
    
    print("🚗 Test Drive Booking System")
    print("=" * 50)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📝 Request {i}: '{request}'")
        print("-" * 40)
        
        result = book_test_drive(request)
        
        print(f"📊 Status: {result['status']}")
        print(f"💬 Message: {result['message']}")
        print(f"🔢 Count: {result['count']}")
        
        if result['status'] == 'available' and result['count'] > 0:
            print("\n🚘 Available Cars:")
            for car in result['available_cars']:
                print(f"   • {car['Name']}")
                print(f"     Brand: {car['Brand__c']}")
                print(f"     Model: {car['Model_Of_Interest__c']}")
                print(f"     Available: {'Yes' if car['IsActive'] else 'No'}")
                print(f"     ID: {car['Id']}")
                print()