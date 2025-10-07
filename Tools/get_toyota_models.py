import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_models", description="Retrieves Toyota car models and trims with filtering options")
def get_toyota_models(
    car_model: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota car models and trims with comprehensive filtering options.
    
    Args:
        car_model (str): Specific car model to search (e.g., 'RAV4', 'Camry', 'Corolla'). Default: 'RAV4'
        category (str, optional): Vehicle category (e.g., 'SUV', 'Sedan', 'Hybrid')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of models/trims found
            - cars (list): List of vehicle models with details

    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_models(car_model="RAV4", category="SUV", fuel_type="Hybrid")
        {
            "status": "success",
            "count": 3,
            "models": [...],
            "filters_applied": {...}
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/TrimsEndpoint;language=en;brand=toyota"
        
        # Make API request
        response = requests.get(base_url)
        data = response.json()
   
        # Check if data is available
        if not data or 'data' not in data:
            return {
                "status": "not_found",
                "error": "No vehicle data found in API response",
                "count": 0,
                "models": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract vehicle data from the response structure
        # Adjust this path based on actual API response structure
        vehicles_data = data['data']['carFragmentsList']['items']

        filtered_models = _apply_filters(
            vehicles_data, 
            category,
            car_model
        )
        
        return {
            "status": "success",
            "count": len(filtered_models),
            "cars": filtered_models
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "models": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Vehicle lookup failed: {str(e)}",
            "count": 0,
            "models": [],
            "timestamp": datetime.now().isoformat()
        }

def _apply_filters(
    vehicles: List[Dict], 
    category: Optional[str],
    car_model: Optional[str],
) -> List[Dict]:
    """Apply filters to the vehicle list."""
    filtered = vehicles

    if car_model:
        filtered = [v for v in filtered if _matches_car_model(v, car_model)]

    # Category filter
    if category:
        filtered = [v for v in filtered if _matches_category(v, category)]
    
    return filtered

def _matches_car_model(vehicle: Dict, car_model: str) -> bool:
    """Check if vehicle matches carModel."""
    vehicle_name = vehicle.get('carName').lower()
    return car_model.lower() in vehicle_name

def _matches_category(vehicle: Dict, category: str) -> bool:
    """Check if vehicle matches category."""
    vehicle_category = vehicle.get('carTypes').lower() if vehicle.get('carTypes') != None else ""
    return category.lower() in vehicle_category

# if __name__ == "__main__":
#     # Test the tool
#     print("Toyota Models (RAV4):")
#     result = get_toyota_models(category="SUV")
#     print(f"Found {result['count']} SUV models", result)
