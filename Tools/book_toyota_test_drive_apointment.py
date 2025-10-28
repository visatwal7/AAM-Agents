import requests
import re
import json
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="book_toyota_test_drive_appointment", description="Book a test drive appointment for Toyota vehicles")
def book_toyota_test_drive_appointment(
    bearer_token: str,
    first_name: str,
    last_name: str,
    mobile: str,
    start_time: str,
    brand: str,
    model_of_interest: str,
    territory_id: str,
    resources: Union[List[str], str],
    vehicle_id: str
) -> Dict[str, Any]:
    """Book a test drive appointment for Toyota vehicles.
    
    Args:
        bearer_token (str): Bearer token for authentication (without 'Bearer' prefix)
        first_name (str): Customer's first name
        last_name (str): Customer's last name
        mobile (str): Customer's mobile number in international format
        start_time (str): Test drive slot start time in ISO format
        brand (str): Vehicle brand ('Toyota' or 'Lexus')
        model_of_interest (str): Car model interested in
        territory_id (str): Service center/location ID
        resources (Union[List[str], str]): List of resource IDs or string representation
        vehicle_id (str): Vehicle ID from the cars endpoint
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'validation_error', or 'error'
            - message (str): Descriptive message about the result
            - service_appointment_id (str): ID of the created service appointment
            - assigned_resource_ids (list): List of assigned resource IDs
            - timestamp (str): When the booking was attempted

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> book_toyota_test_drive_appointment(
        ...     bearer_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     first_name="Vivek",
        ...     last_name="Satwal",
        ...     mobile="+97460417045",
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
            "service_appointment_id": "08pWr000003T2ZNIA0",
            "assigned_resource_ids": ["03rWr000000PYWLIA4", "03rWr000000PYWMIA4"],
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Convert resources to list if it's a string
        resources_list = _convert_resources_to_list(resources)
        
        # Validate all input parameters
        validation_error = _validate_booking_parameters(
            bearer_token, first_name, last_name, mobile, start_time,
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
        
        # Headers with bearer token authentication
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "User-Agent": "Toyota-Booking-Client/1.0"
        }
        
        # Make API request
        response = requests.post(
            base_url, 
            json=payload, 
            headers=headers,
            timeout=30
        )
        
        # Handle different HTTP status codes
        if response.status_code == 401:
            return {
                "status": "error",
                "error": "Authentication failed - invalid or expired bearer token",
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
        elif response.status_code == 403:
            return {
                "status": "error",
                "error": "Access forbidden - insufficient permissions",
                "message": "You don't have permission to book test drives",
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
        if not data:
            return {
                "status": "error",
                "error": "No response data received from server",
                "message": "Test drive booking failed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check response code (1 indicates success based on your example)
        response_code = data.get('responseCode')
        if response_code != 1:
            error_message = data.get('message', 'Unknown error occurred')
            return {
                "status": "error",
                "error": f"Booking failed: {error_message}",
                "message": "Test drive booking failed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract appointment data from response
        appointment_data = data.get('data', {})
        service_appointment_id = appointment_data.get('serviceAppointmentId')
        assigned_resource_ids = appointment_data.get('assignedResourceIds', [])
        
        return {
            "status": "success",
            "message": "Test drive booked successfully",
            "service_appointment_id": service_appointment_id,
            "assigned_resource_ids": assigned_resource_ids,
            "response_message": data.get('message', 'Success'),
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "API request timed out",
            "message": "Network timeout while booking test drive",
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
    bearer_token: str,
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
    # Validate bearer token
    if not bearer_token or not bearer_token.strip():
        return {
            "status": "validation_error",
            "error": "Bearer token is required",
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
            "message": "Please provide a valid mobile number in international format (e.g., +97460417045)",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


# Test function for the booking API
# def test_booking_api():
#     """Test the booking API with sample data."""
#     test_cases = [
#         {
#             "bearer_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNThCM0I0QzYtN0IwNy00NzE0LUFDQjQtQjdEQUUzMERGNEVCIiwic2ZBY2NvdW50SWQiOiIwMDFXcjAwMDAwbm8xQ3RJQUkiLCJjcmVhdGVkQXQiOiIyMDI1LTEwLTIzVDA5OjAwOjUzLjYzMCIsInVwZGF0ZWRBdCI6IjIwMjUtMTAtMjNUMDk6MDE6NDAuNTM3IiwicGhvbmVzIjpbeyJpZCI6IkMwNTg1RjMzLTIzRDItNDAxMi1BREMxLTAwRERCOUY2Mjc0QSIsInBob25lTnVtYmVyIjoiKzk3NDAzMDEyMDQ1In1dfSwiaWF0IjoxNzYxMjc3ODg2LCJleHAiOjE3NjEzNjQyODZ9.UmVlDFUin0IcpozhBjmuUXn7_XmANfoN1sAtcWPwWi4",
#             "first_name": "Vivek",
#             "last_name": "Satwal",
#             "mobile": "+97460417045",
#             "start_time": "2025-10-10T10:00:00",
#             "brand": "Toyota",
#             "model_of_interest": "RAV4",
#             "territory_id": "0HhHp000000yAcaKAE",
#             "resources": ["0HnHp000000u3cpKAA", "0HnWR0000001Z5N0AU"],
#             "vehicle_id": "0HnHp000000u3dYKAQ",
#             "description": "Valid booking with list resources"
#         }
#     ]
    
#     print("Testing Test Drive Booking API:")
#     print("=" * 70)
    
#     for test_case in test_cases:
#         print(f"\nTest Case: {test_case['description']}")
        
#         result = book_toyota_test_drive_appointment(
#             bearer_token=test_case['bearer_token'],
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
#             print(f"Service Appointment ID: {result.get('service_appointment_id')}")
#             print(f"Assigned Resources: {result.get('assigned_resource_ids')}")
#         else:
#             print(f"✗ Booking failed: {result.get('error', 'Unknown error')}")


# def debug_booking_payload():
#     """Debug function to show booking API details."""
#     sample_payload = {
#         "firstName": "Vivek",
#         "lastName": "Satwal",
#         "mobile": "+97460417045",
#         "startTime": "2025-10-10T10:00:00",
#         "brand": "Toyota",
#         "modelOfInterest": "RAV4",
#         "territoryId": "0HhHp000000yAcaKAE",
#         "resources": ["RES001", "RES002"],
#         "vehicleId": "0HnHp000000u3dYKAQ"
#     }
    
#     expected_response = {
#         "message": "Success",
#         "data": {
#             "assignedResourceIds": ["03rWr000000PYWLIA4", "03rWr000000PYWMIA4"],
#             "serviceAppointmentId": "08pWr000003T2ZNIA0"
#         },
#         "responseCode": 1
#     }
    
#     print("Test Drive Booking API Details:")
#     print("=" * 50)
#     print(f"URL: POST https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/appointment")
#     print(f"Headers: Authorization: Bearer <token>")
#     print(f"Payload: {json.dumps(sample_payload, indent=2)}")
#     print(f"Expected Response: {json.dumps(expected_response, indent=2)}")
#     print("=" * 50)


# if __name__ == "__main__":
#     # Show API details
#     debug_booking_payload()
    
#     print("\n" + "=" * 70)  # Fixed this line - use string multiplication
#     print("BOOKING API TEST")
#     print("=" * 70)  # Fixed this line - use string multiplication
    
#     # Test the booking API
#     test_booking_api()