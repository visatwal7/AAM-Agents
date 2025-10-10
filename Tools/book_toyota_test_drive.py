import requests
import re
import json
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="book_toyota_test_drive", description="Book a test drive appointment for Toyota vehicles")
def book_toyota_test_drive(
    access_token: str,
    first_name: str,
    last_name: str,
    mobile: str,
    start_time: str,
    brand: str,
    model_of_interest: str,
    territory_id: str,
    resources: Union[List[str], str],  # Accept both list and string
    vehicle_id: str
) -> Dict[str, Any]:
    """Book a test drive appointment for Toyota vehicles.
    
    Args:
        access_token (str): Bearer token for authentication
        first_name (str): Customer's first name
        last_name (str): Customer's last name
        mobile (str): Customer's mobile number in international format
        start_time (str): Test drive slot start time
        brand (str): Vehicle brand ('Toyota' or 'Lexus')
        model_of_interest (str): Car model interested in
        territory_id (str): Service center/location ID
        resources (Union[List[str], str]): List of resource IDs or string representation
        vehicle_id (str): Vehicle ID from the cars endpoint
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'validation_error', or 'error'
            - message (str): Descriptive message about the result
            - appointment_id (str): ID of the created appointment if successful
            - timestamp (str): When the booking was attempted

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> book_toyota_test_drive(
        ...     access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     first_name="John",
        ...     last_name="Doe",
        ...     mobile="+97460417026",
        ...     start_time="2025-10-10T10:00:00",
        ...     brand="Toyota",
        ...     model_of_interest="RAV4",
        ...     territory_id="0HhHp000000yAcaKAE",
        ...     resources=["RES001", "RES002"],
        ...     vehicle_id="0HnHp000000u3dYKAQ"
        ... )
        {
            "status": "success",
            "message": "Test drive booked successfully",
            "appointment_id": "APP123456",
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Convert resources to list if it's a string
        resources_list = _convert_resources_to_list(resources)
        
        # Validate all input parameters
        validation_error = _validate_booking_parameters(
            access_token, first_name, last_name, mobile, start_time,
            brand, model_of_interest, territory_id, resources_list, vehicle_id
        )
        if validation_error:
            return validation_error
        
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/appointment"
        
        # Request payload
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "mobile": mobile,
            "startTime": start_time,
            "brand": brand,
            "modelOfInterest": model_of_interest,
            "territoryId": territory_id,
            "resources": resources_list,
            "vehicleId": vehicle_id
        }
        
        # Headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make API request
        response = requests.post(base_url, json=payload, headers=headers)
        
        # Check if request was successful
        if response.status_code == 401:
            return {
                "status": "error",
                "error": "Authentication failed - invalid or expired token",
                "message": "Please login again to book test drive",
                "timestamp": datetime.now().isoformat()
            }
        elif response.status_code == 400:
            error_data = response.json()
            return {
                "status": "validation_error",
                "error": f"Bad request: {error_data.get('message', 'Invalid input data')}",
                "message": "Please check your booking details",
                "timestamp": datetime.now().isoformat()
            }
        elif response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "message": "Failed to book test drive - server error",
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            error_message = data.get('message', 'Unknown error occurred') if data else 'No response from server'
            return {
                "status": "error",
                "error": f"Booking failed: {error_message}",
                "message": "Test drive booking failed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract appointment ID from response if available
        appointment_id = data.get('data', {}).get('appointmentId') if data.get('data') else None
        
        return {
            "status": "success",
            "message": "Test drive booked successfully",
            "appointment_id": appointment_id,
            "response_message": data.get('message', 'Success'),
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "message": "Network error while booking test drive",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Booking failed: {str(e)}",
            "message": "Unexpected error during test drive booking",
            "timestamp": datetime.now().isoformat()
        }

def _convert_resources_to_list(resources: Union[List[str], str]) -> List[str]:
    """Convert resources parameter to list if it's a string."""
    if isinstance(resources, list):
        return resources
    elif isinstance(resources, str):
        try:
            # Try to parse as JSON string
            if resources.startswith('[') and resources.endswith(']'):
                return json.loads(resources)
            # If it's a comma-separated string
            elif ',' in resources:
                return [resource.strip() for resource in resources.split(',')]
            # If it's a single resource as string
            else:
                return [resources.strip()]
        except (json.JSONDecodeError, AttributeError):
            # If parsing fails, return as single item list
            return [resources]
    else:
        # If it's any other type, try to convert to list
        return list(resources) if hasattr(resources, '__iter__') and not isinstance(resources, str) else [str(resources)]

def _validate_booking_parameters(
    access_token: str,
    first_name: str,
    last_name: str,
    mobile: str,
    start_time: str,
    brand: str,
    model_of_interest: str,
    territory_id: str,
    resources: List[str],
    vehicle_id: str
) -> Optional[Dict]:
    """Validate all booking parameters."""
    # Validate access token
    if not access_token or not access_token.strip():
        return {
            "status": "validation_error",
            "error": "Access token is required",
            "message": "Please provide authentication token",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate names
    if not first_name or not first_name.strip():
        return {
            "status": "validation_error",
            "error": "First name is required",
            "message": "Please provide your first name",
            "timestamp": datetime.now().isoformat()
        }
    
    if not last_name or not last_name.strip():
        return {
            "status": "validation_error",
            "error": "Last name is required",
            "message": "Please provide your last name",
            "timestamp": datetime.now().isoformat()
        }
    
    if len(first_name.strip()) < 2 or len(last_name.strip()) < 2:
        return {
            "status": "validation_error",
            "error": "Name should be at least 2 characters",
            "message": "Please provide valid first and last names",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate mobile number
    mobile_validation = _validate_mobile_number(mobile)
    if mobile_validation:
        return mobile_validation
    
    # Validate start time
    if not start_time:
        return {
            "status": "validation_error",
            "error": "Start time is required",
            "message": "Please select a test drive time slot",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Try to parse the datetime
        datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    except ValueError:
        return {
            "status": "validation_error",
            "error": "Invalid start time format",
            "message": "Start time should be in ISO format (e.g., 2025-10-10T10:00:00)",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate brand
    valid_brands = ['toyota', 'lexus']
    if not brand or brand.lower() not in valid_brands:
        return {
            "status": "validation_error",
            "error": f"Invalid brand. Must be one of: {', '.join(valid_brands)}",
            "message": "Please select a valid vehicle brand",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate model
    if not model_of_interest or not model_of_interest.strip():
        return {
            "status": "validation_error",
            "error": "Model of interest is required",
            "message": "Please select a car model",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate territory ID
    if not territory_id or not territory_id.strip():
        return {
            "status": "validation_error",
            "error": "Territory ID is required",
            "message": "Please select a service location",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate resources
    if not resources or len(resources) == 0:
        return {
            "status": "validation_error",
            "error": "Resources are required",
            "message": "Please provide booking resources",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate that all resources are strings
    for resource in resources:
        if not isinstance(resource, str) or not resource.strip():
            return {
                "status": "validation_error",
                "error": "All resources must be non-empty strings",
                "message": "Please provide valid resource IDs",
                "timestamp": datetime.now().isoformat()
            }
    
    # Validate vehicle ID
    if not vehicle_id or not vehicle_id.strip():
        return {
            "status": "validation_error",
            "error": "Vehicle ID is required",
            "message": "Please select a vehicle",
            "timestamp": datetime.now().isoformat()
        }
    
    return None

def _validate_mobile_number(mobile: str) -> Optional[Dict]:
    """Validate the mobile number format."""
    if not mobile:
        return {
            "status": "validation_error",
            "error": "Mobile number is required",
            "message": "Please provide a mobile number",
            "timestamp": datetime.now().isoformat()
        }
    
    # Remove any spaces or special characters except +
    cleaned_mobile = re.sub(r'[^\d+]', '', mobile)
    
    # Basic validation for international format
    if not re.match(r'^\+\d{8,15}$', cleaned_mobile):
        return {
            "status": "validation_error",
            "error": "Invalid mobile number format",
            "message": "Please provide a valid mobile number in international format (e.g., +97460417026)",
            "timestamp": datetime.now().isoformat()
        }
    
    return None

# # Test function to debug the booking API with different resource formats
# def test_booking_api_with_different_resource_formats():
#     """Test the booking API with various resource formats."""
#     test_cases = [
#         {
#             "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#             "first_name": "John",
#             "last_name": "Doe",
#             "mobile": "+97460417026",
#             "start_time": "2025-10-10T10:00:00",
#             "brand": "Toyota",
#             "model_of_interest": "RAV4",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "resources": ["0HnHp000000u3cpKAA", "0HnWR0000001Z5N0AU"],  # List format
#             "vehicle_id": "0HnHp000000u3dYKAQ",
#             "description": "List resources format"
#         },
#         {
#             "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#             "first_name": "Jane",
#             "last_name": "Smith",
#             "mobile": "+97460417026",
#             "start_time": "2025-10-10T11:00:00",
#             "brand": "Toyota",
#             "model_of_interest": "Corolla",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "resources": '["0HnHp000000u3cpKAA", "0HnWR0000001Z5N0AU"]',  # JSON string format
#             "vehicle_id": "0HnHp000000u3daKAA",
#             "description": "JSON string resources format"
#         },
#         {
#             "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#             "first_name": "Bob",
#             "last_name": "Wilson",
#             "mobile": "+97460417026",
#             "start_time": "2025-10-10T12:00:00",
#             "brand": "Toyota",
#             "model_of_interest": "Camry",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "resources": "0HnHp000000u3cpKAA,0HnWR0000001Z5N0AU",  # Comma-separated string
#             "vehicle_id": "0HnHp000000u3dYKAQ",
#             "description": "Comma-separated resources format"
#         },
#         {
#             "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#             "first_name": "Alice",
#             "last_name": "Brown",
#             "mobile": "+97460417026",
#             "start_time": "2025-10-10T13:00:00",
#             "brand": "Toyota",
#             "model_of_interest": "RAV4",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "resources": "0HnHp000000u3cpKAA",  # Single resource as string
#             "vehicle_id": "0HnHp000000u3dYKAQ",
#             "description": "Single resource string format"
#         }
#     ]
    
#     print("Testing Test Drive Booking API with Different Resource Formats:")
#     print("=" * 90)
    
#     for test_case in test_cases:
#         print(f"\nTest Case: {test_case['description']}")
#         print(f"Resources input type: {type(test_case['resources'])}")
#         print(f"Resources input value: {test_case['resources']}")
        
#         # Test conversion first
#         converted_resources = _convert_resources_to_list(test_case['resources'])
#         print(f"Converted resources: {converted_resources}")
#         print(f"Converted type: {type(converted_resources)}")
        
#         # Then test the full booking
#         result = book_toyota_test_drive(
#             access_token=test_case['access_token'],
#             first_name=test_case['first_name'],
#             last_name=test_case['last_name'],
#             mobile=test_case['mobile'],
#             start_time=test_case['start_time'],
#             brand=test_case['brand'],
#             model_of_interest=test_case['model_of_interest'],
#             territory_id=test_case['territory_id'],
#             resources=test_case['resources'],
#             vehicle_id=test_case['vehicle_id']
#         )
        
#         print(f"Status: {result['status']}")
#         print(f"Message: {result['message']}")
        
#         if result['status'] == 'success':
#             print("✓ Test drive booked successfully!")
#             if result.get('appointment_id'):
#                 print(f"Appointment ID: {result['appointment_id']}")
#         else:
#             print(f"✗ Booking failed: {result.get('error', 'Unknown error')}")

# def debug_resource_conversion():
#     """Debug function to test resource conversion."""
#     test_inputs = [
#         '["0HnHp000000u3cpKAA", "0HnWR0000001Z5N0AU"]',  # JSON string
#         "0HnHp000000u3cpKAA,0HnWR0000001Z5N0AU",        # Comma-separated
#         "0HnHp000000u3cpKAA",                           # Single string
#         ["0HnHp000000u3cpKAA", "0HnWR0000001Z5N0AU"],   # Actual list
#         "invalid format",                               # Invalid format
#     ]
    
#     print("Resource Conversion Debug:")
#     print("=" * 50)
    
#     for test_input in test_inputs:
#         result = _convert_resources_to_list(test_input)
#         print(f"Input: {test_input} (type: {type(test_input).__name__})")
#         print(f"Output: {result} (type: {type(result).__name__})")
#         print("-" * 30)

# if __name__ == "__main__":
#     # Show resource conversion debugging
#     debug_resource_conversion()
    
#     print("\n" + "=" * 90)
#     print("BOOKING API WITH DIFFERENT RESOURCE FORMATS")
#     print("=" * 90)
    
#     # Test the booking API with different resource formats
#     test_booking_api_with_different_resource_formats()