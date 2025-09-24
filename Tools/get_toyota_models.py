import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool

@tool(name="get_toyota_models", description="Retrieves Toyota car models and trims with filtering options")
def get_toyota_models(
    car_model: str = "RAV4",
    language: str = "en",
    brand: str = "toyota",
    category: Optional[str] = None,
    feature_filter: Optional[List[str]] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    drive_type: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota car models and trims with comprehensive filtering options.
    
    Args:
        car_model (str): Specific car model to search (e.g., 'RAV4', 'Camry', 'Corolla'). Default: 'RAV4'
        language (str): Language for results. Default: 'en'
        brand (str): Brand name. Default: 'toyota'
        category (str, optional): Vehicle category (e.g., 'SUV', 'Sedan', 'Hybrid')
        feature_filter (List[str], optional): List of features to filter by
        price_min (float, optional): Minimum price filter
        price_max (float, optional): Maximum price filter
        fuel_type (str, optional): Fuel type (e.g., 'Petrol', 'Hybrid', 'Electric')
        transmission (str, optional): Transmission type (e.g., 'Automatic', 'Manual')
        drive_type (str, optional): Drive type (e.g., '2WD', '4WD', 'AWD')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of models/trims found
            - models (list): List of vehicle models with details
            - filters_applied (dict): Summary of applied filters
    
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
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/TrimsEndpoint"
        
        # Prepare request parameters
        params = {
            'language': language,
            'brand': brand,
            'carModel': car_model
        }
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
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
        vehicles_data = data.get('data', {}).get('vehicles', [])
        if not vehicles_data:
            vehicles_data = data.get('data', {}).get('trims', [])
        
        if not vehicles_data:
            return {
                "status": "not_found",
                "error": "No vehicle models found for the specified criteria",
                "count": 0,
                "models": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Apply filters
        filtered_models = _apply_filters(
            vehicles_data, 
            category, 
            feature_filter, 
            price_min, 
            price_max, 
            fuel_type, 
            transmission, 
            drive_type
        )
        
        # Format the response
        formatted_models = _format_models(filtered_models)
        
        return {
            "status": "success",
            "count": len(formatted_models),
            "models": formatted_models,
            "filters_applied": {
                "car_model": car_model,
                "category": category,
                "feature_filter": feature_filter,
                "price_range": {
                    "min": price_min,
                    "max": price_max
                },
                "fuel_type": fuel_type,
                "transmission": transmission,
                "drive_type": drive_type
            },
            "timestamp": datetime.now().isoformat()
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
    feature_filter: Optional[List[str]],
    price_min: Optional[float],
    price_max: Optional[float],
    fuel_type: Optional[str],
    transmission: Optional[str],
    drive_type: Optional[str]
) -> List[Dict]:
    """Apply filters to the vehicle list."""
    filtered = vehicles
    
    # Category filter
    if category:
        filtered = [v for v in filtered if _matches_category(v, category)]
    
    # Feature filter
    if feature_filter:
        filtered = [v for v in filtered if _has_features(v, feature_filter)]
    
    # Price filter
    if price_min is not None or price_max is not None:
        filtered = [v for v in filtered if _in_price_range(v, price_min, price_max)]
    
    # Fuel type filter
    if fuel_type:
        filtered = [v for v in filtered if _matches_fuel_type(v, fuel_type)]
    
    # Transmission filter
    if transmission:
        filtered = [v for v in filtered if _matches_transmission(v, transmission)]
    
    # Drive type filter
    if drive_type:
        filtered = [v for v in filtered if _matches_drive_type(v, drive_type)]
    
    return filtered

def _matches_category(vehicle: Dict, category: str) -> bool:
    """Check if vehicle matches category."""
    vehicle_category = vehicle.get('category', '').lower()
    return category.lower() in vehicle_category

def _has_features(vehicle: Dict, features: List[str]) -> bool:
    """Check if vehicle has all specified features."""
    vehicle_features = vehicle.get('features', [])
    if isinstance(vehicle_features, str):
        vehicle_features = [vehicle_features]
    
    vehicle_features_lower = [f.lower() for f in vehicle_features]
    return all(feature.lower() in vehicle_features_lower for feature in features)

def _in_price_range(vehicle: Dict, min_price: Optional[float], max_price: Optional[float]) -> bool:
    """Check if vehicle price is within range."""
    price = vehicle.get('price', 0)
    if isinstance(price, str):
        # Remove currency symbols and commas
        price = float(price.replace('QR', '').replace(',', '').strip())
    
    if min_price is not None and price < min_price:
        return False
    if max_price is not None and price > max_price:
        return False
    
    return True

def _matches_fuel_type(vehicle: Dict, fuel_type: str) -> bool:
    """Check if vehicle matches fuel type."""
    vehicle_fuel = vehicle.get('fuel_type', '').lower()
    return fuel_type.lower() in vehicle_fuel

def _matches_transmission(vehicle: Dict, transmission: str) -> bool:
    """Check if vehicle matches transmission type."""
    vehicle_transmission = vehicle.get('transmission', '').lower()
    return transmission.lower() in vehicle_transmission

def _matches_drive_type(vehicle: Dict, drive_type: str) -> bool:
    """Check if vehicle matches drive type."""
    vehicle_drive = vehicle.get('drive_type', '').lower()
    return drive_type.lower() in vehicle_drive

def _format_models(vehicles: List[Dict]) -> List[Dict]:
    """Format vehicle data into standardized structure."""
    formatted = []
    
    for vehicle in vehicles:
        formatted_vehicle = {
            "model_name": vehicle.get('model_name', ''),
            "trim_level": vehicle.get('trim_name', ''),
            "category": vehicle.get('category', ''),
            "price": vehicle.get('price', 0),
            "fuel_type": vehicle.get('fuel_type', ''),
            "transmission": vehicle.get('transmission', ''),
            "drive_type": vehicle.get('drive_type', ''),
            "engine_capacity": vehicle.get('engine_capacity', ''),
            "horsepower": vehicle.get('horsepower', ''),
            "features": vehicle.get('features', []),
            "image_url": vehicle.get('image_url', ''),
            "description": vehicle.get('description', '')
        }
        
        # Clean price if it's a string
        if isinstance(formatted_vehicle["price"], str):
            formatted_vehicle["price"] = float(
                formatted_vehicle["price"].replace('QR', '').replace(',', '').strip()
            )
        
        formatted.append(formatted_vehicle)
    
    return formatted

# Additional helper tool for getting available models
@tool(name="get_available_toyota_models", description="Retrieves list of available Toyota models")
def get_available_toyota_models(language: str = "en", brand: str = "toyota") -> Dict[str, Any]:
    """Retrieves list of available Toyota models."""
    try:
        # This would typically call a different endpoint to get model list
        # For now, we'll return a static list or make a generic call
        
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/ModelsEndpoint"
        
        params = {
            'language': language,
            'brand': brand
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        models = data.get('data', {}).get('models', [])
        
        return {
            "status": "success",
            "available_models": [model.get('name', '') for model in models],
            "count": len(models),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback to known models if API fails
        known_models = [
            "RAV4", "Camry", "Corolla", "Land Cruiser", "Prado", 
            "Fortuner", "Hilux", "Yaris", "Hiace", "Coaster"
        ]
        
        return {
            "status": "success",
            "available_models": known_models,
            "count": len(known_models),
            "note": "Using fallback model list",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the tool
    print("Toyota Models (RAV4):")
    result = get_toyota_models(car_model="RAV4")
    print(f"Found {result['count']} models")
    
    print("\nToyota Models with SUV category:")
    result = get_toyota_models(car_model="RAV4", category="SUV")
    print(f"Found {result['count']} SUV models")
    
    print("\nAvailable Toyota Models:")
    models_result = get_available_toyota_models()
    print(f"Available models: {models_result['available_models']}")