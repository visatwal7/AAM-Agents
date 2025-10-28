import requests
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="request_toyota_otp", description="Request OTP verification code for Toyota test drive booking")
def request_toyota_otp(
    mobile: str
) -> Dict[str, Any]:
    """Request OTP verification code for Toyota test drive booking.
    
    Args:
        mobile (str): Mobile number in international format (e.g., '+97403012026')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'invalid_mobile', or 'error'
            - message (str): Descriptive message about the result
            - timestamp (str): When the OTP was requested
            - server_time (str): Server timestamp from the response

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> request_toyota_otp(mobile="+97403012026")
        {
            "status": "success",
            "message": "OTP sent successfully",
            "timestamp": "2024-01-15T10:30:00",
            "server_time": "2025-10-10T05:36:44.860Z"
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
        
        # Make API request
        response = requests.post(base_url, json=payload)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "message": "Failed to send OTP",
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data or data.get('responseCode') != 1:
            error_message = data.get('message', 'Unknown error occurred') if data else 'No response from server'
            return {
                "status": "error",
                "error": f"OTP request failed: {error_message}",
                "message": "Failed to send OTP",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract response data
        server_time = data['data']['time'] if data.get('data') and data['data'].get('time') else None
        
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "timestamp": datetime.now().isoformat(),
            "server_time": server_time,
            "response_message": data.get('message', 'Success')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "message": "Network error while sending OTP",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"OTP request failed: {str(e)}",
            "message": "Unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }

def _validate_mobile_number(mobile: str) -> Optional[Dict]:
    """Validate the mobile number format."""
    if not mobile:
        return {
            "status": "invalid_mobile",
            "error": "Mobile number is required",
            "message": "Please provide a mobile number",
            "timestamp": datetime.now().isoformat()
        }
    
    # Remove any spaces or special characters except +
    cleaned_mobile = re.sub(r'[^\d+]', '', mobile)
    
    # Basic validation for international format
    # Should start with + followed by country code and number
    if not re.match(r'^\+\d{8,15}$', cleaned_mobile):
        return {
            "status": "invalid_mobile",
            "error": "Invalid mobile number format",
            "message": "Please provide a valid mobile number in international format (e.g., +97403012026)",
            "timestamp": datetime.now().isoformat()
        }
    
    # Specific validation for Qatar numbers (+974) if needed
    if cleaned_mobile.startswith('+974'):
        if len(cleaned_mobile) != 11:  # +974 + 8 digits
            return {
                "status": "invalid_mobile",
                "error": "Invalid Qatar mobile number",
                "message": "Qatar mobile numbers should be 8 digits after +974",
                "timestamp": datetime.now().isoformat()
            }
    
    return None

# Test function to debug the OTP API
def test_otp_api():
    """Test the OTP API with various mobile numbers."""
    test_cases = [
        {
            "mobile": "+97403012026",
            "description": "Valid Qatar test number"
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
            "mobile": "",
            "description": "Empty mobile number"
        },
        {
            "mobile": "+974 1234 5678",
            "description": "Valid number with spaces"
        }
    ]
    
    print("Testing OTP Request API:")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['description']}")
        print(f"Mobile: '{test_case['mobile']}'")
        
        result = request_toyota_otp(mobile=test_case['mobile'])
        
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"Server Time: {result.get('server_time', 'N/A')}")
        elif result.get('error'):
            print(f"Error: {result['error']}")

def debug_otp_api_payload():
    """Debug function to show what payload is being sent to the API."""
    sample_payload = {
        "mobile": "+97403012026"
    }
    
    print("OTP Request API Details:")
    print("=" * 40)
    print(f"URL: POST https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/auth/otp/mobile/request")
    print(f"Payload: {sample_payload}")
    print("Expected Response: {'message': 'Success', 'data': {'time': '...'}, 'responseCode': 1}")
    print("=" * 40)

def validate_mobile_format(mobile: str) -> Dict[str, Any]:
    """Helper function to validate mobile number format separately."""
    validation_result = _validate_mobile_number(mobile)
    if validation_result:
        return validation_result
    else:
        return {
            "status": "valid",
            "message": "Mobile number format is valid",
            "mobile": mobile,
            "timestamp": datetime.now().isoformat()
        }

#Batch OTP request function for testing multiple numbers
def batch_otp_test(mobile_numbers: List[str]) -> List[Dict[str, Any]]:
    """Test OTP requests for multiple mobile numbers."""
    results = []
    print(f"Batch testing {len(mobile_numbers)} mobile numbers:")
    print("=" * 50)
    
    for mobile in mobile_numbers:
        print(f"\nTesting: {mobile}")
        result = request_toyota_otp(mobile)
        results.append({"mobile": mobile, **result})
        
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"  ✓ OTP sent successfully")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    # Show API details
    debug_otp_api_payload()
    
    print("\n" + "=" * 60)
    print("MOBILE NUMBER VALIDATION TEST")
    print("=" * 60)
    
    # Test mobile number validation
    test_numbers = ["+97403012026", "+97412345678", "123456", "+971501234567", ""]
    for number in test_numbers:
        validation = validate_mobile_format(number)
        print(f"Mobile: '{number}' -> {validation['status']}: {validation['message']}")
    
    print("\n" + "=" * 60)
    print("OTP API FUNCTIONAL TEST")
    print("=" * 60)
    
    # Test the OTP API functionality
    test_otp_api()
    
    print("\n" + "=" * 60)
    print("BATCH TEST WITH SAMPLE NUMBERS")
    print("=" * 60)
    
    # Batch test with sample numbers
    sample_numbers = [
        "+97403012026",  # Valid test number
        "+97455123456",  # Another Qatar number
        "123456",        # Invalid
        "+971501234567"  # UAE number
    ]
    
    batch_otp_test(sample_numbers)
    
    print("\n" + "=" * 60)
    print("USAGE EXAMPLE")
    print("=" * 60)
    
    # Example usage
    print("\nExample: Request OTP for test number")
    result = request_toyota_otp("+97413012026")
    print(f"Result: {result}")