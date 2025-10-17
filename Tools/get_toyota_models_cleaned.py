import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import ast
import json


@tool(name="get_toyota_models_cleaned", description="Retrieves Toyota car models and trims with filtering options")
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
        print('Original car_model input:', car_model)
        print('Type of car_model input:', type(car_model))
        
        # Normalize car_model input to handle all formats
        car_model = _normalize_car_model_input(car_model)
        print('Normalized car_model:', car_model)

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


def _normalize_car_model_input(car_model: Optional[object]) -> Optional[List[str]]:
    """Normalize car_model input to handle all formats and return a list of strings."""
    if car_model is None:
        return None
        
    # If it's already a list, return as is (with string normalization)
    if isinstance(car_model, list):
        return [str(item).strip() for item in car_model if str(item).strip()]
    
    # Convert to string if it's not already
    car_model_str = str(car_model)
    
    # Case 1: JSON array format '["Prado","RAV4"]'
    if car_model_str.startswith('[') and car_model_str.endswith(']'):
        try:
            # Try to parse as JSON first
            parsed = json.loads(car_model_str)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            try:
                # Try ast.literal_eval as fallback
                parsed = ast.literal_eval(car_model_str)
                if isinstance(parsed, list):
                    # Handle case where we have a list with a single comma-separated string
                    if len(parsed) == 1 and isinstance(parsed[0], str) and ',' in parsed[0]:
                        return [item.strip() for item in parsed[0].split(',') if item.strip()]
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except:
                pass
    
    # Case 2 & 3: Comma-separated string format (with or without brackets)
    # Remove any surrounding brackets and quotes first
    cleaned_str = car_model_str.strip()
    if cleaned_str.startswith('["') and cleaned_str.endswith('"]'):
        cleaned_str = cleaned_str[2:-2]  # Remove the [" and "]
    elif cleaned_str.startswith('[') and cleaned_str.endswith(']'):
        cleaned_str = cleaned_str[1:-1]  # Remove the [ and ]
    
    # Split by comma and clean up each item
    models = [item.strip().strip('"\'') for item in cleaned_str.split(',')]
    
    # Remove any empty strings
    return [model for model in models if model]


def _apply_filters(
    vehicles: List[Dict], 
    category: Optional[str],
    car_model: Optional[List[str]],
) -> List[Dict]:
    """Apply filters to the vehicle list."""
    filtered = vehicles
    print('Applying filters - car_model:', car_model, 'category:', category)

    if car_model and len(car_model) > 0:
        filtered = [v for v in filtered if _matches_car_model(v, car_model)]

    # Category filter
    if category:
        filtered = [v for v in filtered if _matches_category(v, category)]
    
    return filtered


def _matches_car_model(vehicle: Dict, car_model: List[str]) -> bool:
    """Check if vehicle matches any of the car models in the list."""
    if not car_model:
        return True
        
    vehicle_name = vehicle.get('carName', '').lower()
    if not vehicle_name:
        return False
        
    # Check if any of the car_model strings is contained in the vehicle name
    return any(model.lower().strip() in vehicle_name for model in car_model if model.strip())


def _matches_category(vehicle: Dict, category: str) -> bool:
    """Check if vehicle matches category."""
    vehicle_category = vehicle.get('carTypes', '').lower() if vehicle.get('carTypes') is not None else ""
    return category.lower() in vehicle_category


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
#     # Test all cases
#     test_cases = [
#         '["Prado","RAV4"]',
#         '["Prado, RAV4,Land Cruiser"]',
#         "Prado, RAV4,Land Cruiser",
#         "Prado",  # Single model
#         "",  # Empty string
#         None,  # None input
#         "Prado, RAV4, Land Cruiser, Camry, Corolla",  # More than 3 models
#         ["Prado", "RAV4", "Land Cruiser"],  # List input
#         ["Prado", "RAV4", "Land Cruiser", "Camry", "Corolla"]  # Longer list
#     ]
    
#     for i, test_case in enumerate(test_cases, 1):
#         print(f"\n{'='*60}")
#         print(f"TEST CASE {i}: {test_case} (type: {type(test_case)})")
#         print(f"{'='*60}")
        
#         result = get_toyota_models_new(car_model=test_case)
#         print(f"Status: {result['status']}")
#         print(f"Count: {result['count']}")
#         print(f"Filters applied - car_model: {result.get('filters_applied', {}).get('car_model', 'None')}")
        
#         if result['status'] == 'success' and result['count'] > 0:
#             print(f"Found {result['count']} cars:")
#             for j, car in enumerate(result['cars'][:3], 1):  # Show first 3 cars
#                 print(f"  {j}. {car.get('carName', 'N/A')} - {car.get('carTypes', 'N/A')}")
#             if result['count'] > 3:
#                 print(f"  ... and {result['count'] - 3} more")
#         else:
#             print("No cars found or error occurred")