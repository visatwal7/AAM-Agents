import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import ast


@tool(name="get_toyota_models_new", description="Retrieves Toyota car models and trims with filtering options")
def get_toyota_models_new(
    car_model: Optional[object] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota car models and trims with comprehensive filtering options.
    
    Args:
        car_model (object): Specific car model to search (e.g., ['RAV4'], ['Camry', 'Corolla']).
        category (str, optional): Vehicle category (e.g., 'SUV', 'Sedan', 'Hybrid')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of models/trims found
            - cars (list): List of vehicle models with details
    """
    try:
        # API endpoint configuration
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/TrimsEndpoint;language=en;brand=toyota"
        print('car_model', car_model)
        if car_model:
            car_model = ast.literal_eval(car_model)

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
        vehicles_data = data['data']['carFragmentsList']['items']

        print('car_model', car_model)

        filtered_models = _apply_filters(
            vehicles_data, 
            category,
            car_model
        )
        
        # Create the result dictionary first
        result = {
            "status": "success",
            "count": len(filtered_models),
            "cars": filtered_models,
            "filters_applied": {
                "car_model": car_model,
                "category": category
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Then transform it
        return transform_api_response(result)
        
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
    car_model: Optional[object],
) -> List[Dict]:
    """Apply filters to the vehicle list."""
    filtered = vehicles
    print('carModel', car_model, category)

    if car_model and len(car_model) > 0:
        filtered = [v for v in filtered if _matches_car_model(v, car_model)]

    # Category filter
    if category:
        filtered = [v for v in filtered if _matches_category(v, category)]
    
    return filtered

def _matches_car_model(vehicle: Dict, car_model: object) -> bool:
    """Check if vehicle matches carModel."""
    vehicle_name = vehicle.get('carName').lower()
    return any(vehicle_name in item.lower() for item in car_model)

def _matches_category(vehicle: Dict, category: str) -> bool:
    """Check if vehicle matches category."""
    vehicle_category = vehicle.get('carTypes').lower() if vehicle.get('carTypes') != None else ""
    return category.lower() in vehicle_category


import json

def transform_api_response(api_response):
    """
    Transform API response by:
    1. Removing all '_path' and 'icon' keys
    2. Converting sectionFeatures from list of dict to list of str
    3. Converting carImage objects to just the _dmS7Url string
    4. Returning a simplified Python dictionary
    """
    
    def process_item(item):
        """Recursively process dictionary items"""
        if isinstance(item, dict):
            # Create a new dict without '_path' and 'icon' keys
            new_dict = {}
            for key, value in item.items():
                if key in ['_path', 'icon']:
                    continue
                elif key == 'carImage' and isinstance(value, dict):
                    # Extract just the _dmS7Url from carImage objects
                    new_dict[key] = value.get('_dmS7Url')
                elif key == 'sectionFeatures' and isinstance(value, list):
                    # Convert sectionFeatures to list of strings
                    new_dict[key] = [process_feature(feature) for feature in value]
                else:
                    new_dict[key] = process_item(value)
            return new_dict
        elif isinstance(item, list):
            # Process each item in the list
            return [process_item(element) for element in item]
        else:
            # Return primitive values as-is
            return item
    
    def process_feature(feature):
        """Extract featureValue from feature items"""
        if isinstance(feature, dict) and 'featureValue' in feature:
            return feature['featureValue']
        elif isinstance(feature, str):
            return feature
        else:
            return str(feature)
    
    # Process the entire API response
    transformed_data = process_item(api_response)
    return transformed_data

# if __name__ == "__main__":
#     # Test the tool
#     print("Toyota Models (Prada):")
#     result = get_toyota_models_new(car_model='["Prado"]')
#     print(f"Found {result['count']} Prado models")
#     print('*'*50)
#     #print(result)
#     cleaned_data = transform_api_response(result)
#     print(cleaned_data)