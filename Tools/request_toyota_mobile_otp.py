import requests
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="request_toyota_mobile_otp", description="Request OTP verification code for Toyota mobile authentication")
def request_toyota_mobile_otp(
    mobile: str
) -> Dict[str, Any]:
    """Request OTP verification code for Toyota mobile authentication.
    
    Args:
        mobile (str): Mobile number in international format (e.g., '+97403012045')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'invalid_mobile', or 'error'
            - message (str): Descriptive message about the result
            - timestamp (str): When the OTP was requested
            - server_time (str): Server timestamp from the response
            - response_code (int): Response code from the API

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> request_toyota_mobile_otp(mobile="+97403012045")
        {
            "status": "success",
            "message": "OTP sent successfully",
            "timestamp": "2024-01-15T10:30:00",
            "server_time": "2025-10-23T05:49:42.001Z",
            "response_code": 1
        }
    """
    try:
        # Validate mobile number format
        validation_error = _validate_mobile_number(mobile)
        if validation_error:
            return validation_error
        
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/auth/otp/mobile/request"
        
        # Request payload
        payload = {
            "mobile": mobile
        }
        
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Toyota-OTP-Client/1.0"
        }
        
        # Make API request
        response = requests.post(
            base_url, 
            json=payload, 
            headers=headers,
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "message": "Failed to send OTP",
                "timestamp": datetime.now().isoformat(),
                "response_code": None
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data:
            return {
                "status": "error",
                "error": "No response data received from server",
                "message": "Failed to send OTP",
                "timestamp": datetime.now().isoformat(),
                "response_code": None
            }
        
        # Check response code (1 indicates success based on your example)
        response_code = data.get('responseCode')
        if response_code != 1:
            error_message = data.get('message', 'Unknown error occurred')
            return {
                "status": "error",
                "error": f"OTP request failed: {error_message}",
                "message": "Failed to send OTP",
                "timestamp": datetime.now().isoformat(),
                "response_code": response_code
            }
        
        # Extract response data
        server_time = data.get('data', {}).get('time') if data.get('data') else None
        
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "timestamp": datetime.now().isoformat(),
            "server_time": server_time,
            "response_code": response_code,
            "api_message": data.get('message', 'Success')
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "API request timed out",
            "message": "Network timeout while sending OTP",
            "timestamp": datetime.now().isoformat(),
            "response_code": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "message": "Network error while sending OTP",
            "timestamp": datetime.now().isoformat(),
            "response_code": None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"OTP request failed: {str(e)}",
            "message": "Unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
            "response_code": None
        }


def _validate_mobile_number(mobile: str) -> Optional[Dict]:
    """Validate the mobile number format."""
    if not mobile:
        return {
            "status": "invalid_mobile",
            "error": "Mobile number is required",
            "message": "Please provide a mobile number",
            "timestamp": datetime.now().isoformat(),
            "response_code": None
        }
    
    # Remove any spaces or special characters except +
    cleaned_mobile = re.sub(r'[^\d+]', '', mobile)
    
    # Basic validation for international format
    # Should start with + followed by country code and number
    if not re.match(r'^\+\d{8,15}$', cleaned_mobile):
        return {
            "status": "invalid_mobile",
            "error": "Invalid mobile number format",
            "message": "Please provide a valid mobile number in international format (e.g., +97403012045)",
            "timestamp": datetime.now().isoformat(),
            "response_code": None
        }
    
    # Simplified Qatar validation - only check if starts with +974 and has 8 digits after
    if cleaned_mobile.startswith('+974'):
        # Remove +974 and check if remaining are exactly 8 digits
        digits_after_country_code = cleaned_mobile[4:]  # Remove '+974'
        if len(digits_after_country_code) != 8:
            return {
                "status": "invalid_mobile",
                "error": "Invalid Qatar mobile number length",
                "message": "Qatar mobile numbers should have exactly 8 digits after +974",
                "timestamp": datetime.now().isoformat(),
                "response_code": None
            }
        # No additional validation - any 8 digits are acceptable including starting with 0
    
    return None


# Test function for the new OTP tool
def test_mobile_otp_api():
    """Test the mobile OTP API with various mobile numbers."""
    test_cases = [
        {
            "mobile": "+97403012045",
            "description": "Valid Qatar test number (from example)"
        },
        {
            "mobile": "+97413012045", 
            "description": "Valid Qatar number starting with 1"
        },
        {
            "mobile": "+97400123456",
            "description": "Valid Qatar number starting with 00"
        },
        {
            "mobile": "+97455123456",
            "description": "Valid Qatar number"
        },
        {
            "mobile": "+971501234567",
            "description": "Valid UAE number"
        },
        {
            "mobile": "123456789",
            "description": "Invalid format - missing country code"
        },
        {
            "mobile": "+974123",
            "description": "Invalid Qatar number - too short"
        },
        {
            "mobile": "+974123456789",
            "description": "Invalid Qatar number - too long"
        },
        {
            "mobile": "",
            "description": "Empty mobile number"
        }
    ]
    
    print("Testing Mobile OTP Request API:")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['description']}")
        print(f"Mobile: '{test_case['mobile']}'")
        
        result = request_toyota_mobile_otp(mobile=test_case['mobile'])
        
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"Server Time: {result.get('server_time', 'N/A')}")
            print(f"Response Code: {result.get('response_code', 'N/A')}")
        elif result.get('error'):
            print(f"Error: {result['error']}")


def debug_otp_api_details():
    """Debug function to show API details."""
    sample_payload = {
        "mobile": "+97403012045"
    }
    
    expected_response = {
        "message": "Success",
        "data": {
            "time": "2025-10-23T05:49:42.001Z"
        },
        "responseCode": 1
    }
    
    print("Mobile OTP Request API Details:")
    print("=" * 50)
    print(f"URL: POST https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/auth/otp/mobile/request")
    print(f"Payload: {sample_payload}")
    print(f"Expected Response: {expected_response}")
    print("=" * 50)


# if __name__ == "__main__":
#     # Show API details
#     debug_otp_api_details()
    
#     print("\n" + "=" * 60)
#     print("MOBILE OTP API FUNCTIONAL TEST")
#     print("=" * 60)
    
#     # Test the OTP API functionality
#     test_mobile_otp_api()
    
#     print("\n" + "=" * 60)
#     print("SPECIFIC TEST WITH EXAMPLE NUMBERS")
#     print("=" * 60)
    
#     # Test with the specific example numbers
#     test_numbers = ["+97403012045", "+97413012045", "+97400123456"]
    
#     for number in test_numbers:
#         print(f"\nTesting with mobile: {number}")
#         result = request_toyota_mobile_otp(number)
#         print(f"Result Status: {result['status']}")
#         if result['status'] == 'success':
#             print(f"✓ OTP sent successfully - Server Time: {result.get('server_time')}")
#         else:
#             print(f"✗ Failed: {result.get('error', 'Unknown error')}")