import requests
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="verify_toyota_otp_login", description="Verify OTP and login to Toyota test drive system")
def verify_toyota_otp_login(
    mobile: str,
    otp: str,
    otp_start_time: str
) -> Dict[str, Any]:
    """Verify OTP code and login to Toyota test drive booking system.
    
    Args:
        mobile (str): Mobile number in international format (e.g., '+97403012026')
        otp (str): OTP code received via SMS (e.g., '12345')
        otp_start_time (str): OTP request timestamp in ISO format (e.g., '2025-10-10T05:36:44.860Z')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'invalid_otp', 'invalid_mobile', or 'error'
            - message (str): Descriptive message about the result
            - access_token (str): JWT access token for authenticated requests
            - refresh_token (str): JWT refresh token for token renewal
            - must_update_user_data (bool): Whether user needs to update profile data
            - must_add_mobile (bool): Whether user needs to add mobile number
            - timestamp (str): When the login was attempted

    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> verify_toyota_otp_login(
        ...     mobile="+97403012026",
        ...     otp="12345",
        ...     otp_start_time="2025-10-10T05:36:44.860Z"
        ... )
        {
            "status": "success",
            "message": "Login successful",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "must_update_user_data": true,
            "must_add_mobile": false,
            "timestamp": "2024-01-15T10:30:00"
        }
    """
    try:
        # Validate input parameters
        validation_error = _validate_login_parameters(mobile, otp, otp_start_time)
        if validation_error:
            return validation_error
        
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/auth/login/mobile"
        
        # Request payload
        payload = {
            "mobile": mobile,
            "otp": otp,
            "otp_start_time": otp_start_time
        }
        
        # Make API request
        response = requests.post(base_url, json=payload)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API request failed with status code: {response.status_code}",
                "message": "Login failed due to server error",
                "timestamp": datetime.now().isoformat()
            }
        
        data = response.json()
   
        # Check if data is available and response is successful
        if not data:
            return {
                "status": "error",
                "error": "No response data received from server",
                "message": "Login failed - no server response",
                "timestamp": datetime.now().isoformat()
            }
        
        if data.get('responseCode') != 1:
            error_message = data.get('message', 'Unknown authentication error')
            status = 'invalid_otp' if 'otp' in error_message.lower() else 'error'
            return {
                "status": status,
                "error": f"Authentication failed: {error_message}",
                "message": "Login failed - invalid credentials",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract authentication data
        auth_data = data['data']
        
        return {
            "status": "success",
            "message": "Login successful",
            "access_token": auth_data.get('accessToken'),
            "refresh_token": auth_data.get('refreshToken'),
            "must_update_user_data": auth_data.get('mustUpdateUserData', False),
            "must_add_mobile": auth_data.get('mustAddMobile', False),
            "user_id": _extract_user_id_from_token(auth_data.get('accessToken')),
            "timestamp": datetime.now().isoformat(),
            "response_message": data.get('message', 'Success')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "message": "Network error during login",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Login failed: {str(e)}",
            "message": "Unexpected error during login",
            "timestamp": datetime.now().isoformat()
        }

def _validate_login_parameters(mobile: str, otp: str, otp_start_time: str) -> Optional[Dict]:
    """Validate the login parameters."""
    # Validate mobile number
    mobile_validation = _validate_mobile_number(mobile)
    if mobile_validation:
        return mobile_validation
    
    # Validate OTP
    if not otp or not otp.strip():
        return {
            "status": "invalid_otp",
            "error": "OTP code is required",
            "message": "Please enter the OTP code",
            "timestamp": datetime.now().isoformat()
        }
    
    if not re.match(r'^\d{4,8}$', otp.strip()):
        return {
            "status": "invalid_otp",
            "error": "Invalid OTP format",
            "message": "OTP should be 4-8 digits",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate OTP start time
    if not otp_start_time:
        return {
            "status": "error",
            "error": "OTP start time is required",
            "message": "OTP timestamp is missing",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Try to parse the ISO format timestamp
        datetime.fromisoformat(otp_start_time.replace('Z', '+00:00'))
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid OTP start time format",
            "message": "OTP timestamp should be in ISO format (e.g., 2025-10-10T05:36:44.860Z)",
            "timestamp": datetime.now().isoformat()
        }
    
    return None

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
    if not re.match(r'^\+\d{8,15}$', cleaned_mobile):
        return {
            "status": "invalid_mobile",
            "error": "Invalid mobile number format",
            "message": "Please provide a valid mobile number in international format (e.g., +97403012026)",
            "timestamp": datetime.now().isoformat()
        }
    
    return None

def _extract_user_id_from_token(token: Optional[str]) -> Optional[str]:
    """Extract user ID from JWT token (basic extraction without verification)."""
    if not token:
        return None
    
    try:
        # Basic JWT parsing (without verification)
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        import base64
        import json
        
        # Decode the payload
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded_payload = base64.b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        # Extract user ID from payload
        user_info = payload_data.get('user', {})
        return user_info.get('id')
        
    except Exception:
        # If extraction fails, return None
        return None

# Test function to debug the login API
def test_login_api():
    """Test the login API with various scenarios."""
    test_cases = [
        {
            "mobile": "+97403012026",
            "otp": "12345",
            "otp_start_time": "2025-10-10T05:36:44.860Z",
            "description": "Valid test credentials"
        },
        {
            "mobile": "+97403012026",
            "otp": "99999",
            "otp_start_time": "2025-10-10T05:36:44.860Z",
            "description": "Invalid OTP"
        },
        {
            "mobile": "+97412345678",
            "otp": "12345",
            "otp_start_time": "2025-10-10T05:36:44.860Z",
            "description": "Unregistered mobile"
        },
        {
            "mobile": "invalid",
            "otp": "12345",
            "otp_start_time": "2025-10-10T05:36:44.860Z",
            "description": "Invalid mobile format"
        },
        {
            "mobile": "+97403012026",
            "otp": "",
            "otp_start_time": "2025-10-10T05:36:44.860Z",
            "description": "Empty OTP"
        }
    ]
    
    print("Testing OTP Login API:")
    print("=" * 70)
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['description']}")
        print(f"Mobile: '{test_case['mobile']}'")
        print(f"OTP: '{test_case['otp']}'")
        print(f"OTP Time: '{test_case['otp_start_time']}'")
        
        result = verify_toyota_otp_login(
            mobile=test_case['mobile'],
            otp=test_case['otp'],
            otp_start_time=test_case['otp_start_time']
        )
        
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print("✓ Login successful!")
            print(f"  Access Token: {result['access_token'][:50]}...")
            print(f"  Refresh Token: {result['refresh_token'][:50]}...")
            print(f"  User ID: {result.get('user_id', 'N/A')}")
            print(f"  Update Data Required: {result['must_update_user_data']}")
            print(f"  Add Mobile Required: {result['must_add_mobile']}")
        else:
            print(f"✗ Login failed: {result.get('error', 'Unknown error')}")

def debug_login_api_payload():
    """Debug function to show what payload is being sent to the API."""
    sample_payload = {
        "mobile": "+97403012026",
        "otp": "12345",
        "otp_start_time": "2025-10-10T05:36:44.860Z"
    }
    
    print("OTP Login API Details:")
    print("=" * 50)
    print(f"URL: POST https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/auth/login/mobile")
    print(f"Payload: {sample_payload}")
    print("Expected Response: Access token, refresh token, and user flags")
    print("=" * 50)

def validate_otp_format(otp: str) -> Dict[str, Any]:
    """Helper function to validate OTP format separately."""
    if not otp or not otp.strip():
        return {
            "status": "invalid",
            "message": "OTP code is required",
            "timestamp": datetime.now().isoformat()
        }
    
    if not re.match(r'^\d{4,8}$', otp.strip()):
        return {
            "status": "invalid",
            "message": "OTP should be 4-8 digits",
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "status": "valid",
        "message": "OTP format is valid",
        "timestamp": datetime.now().isoformat()
    }

# # Complete authentication flow function
# def complete_authentication_flow(mobile: str, otp: str, otp_start_time: str) -> Dict[str, Any]:
#     """Complete authentication flow with validation and login."""
#     print(f"Starting authentication flow for: {mobile}")
#     print("-" * 40)
    
#     # Step 1: Validate mobile
#     mobile_validation = _validate_mobile_number(mobile)
#     if mobile_validation:
#         print("✗ Mobile validation failed")
#         return mobile_validation
    
#     # Step 2: Validate OTP
#     otp_validation = validate_otp_format(otp)
#     if otp_validation['status'] != 'valid':
#         print("✗ OTP validation failed")
#         return {
#             "status": "invalid_otp",
#             "error": otp_validation['message'],
#             "message": "OTP validation failed",
#             "timestamp": datetime.now().isoformat()
#         }
    
#     # Step 3: Attempt login
#     print("✓ Mobile and OTP format validated")
#     print("Attempting login...")
    
#     login_result = verify_toyota_otp_login(mobile, otp, otp_start_time)
    
#     if login_result['status'] == 'success':
#         print("✓ Authentication successful!")
#     else:
#         print(f"✗ Authentication failed: {login_result.get('error')}")
    
#     return login_result

# if __name__ == "__main__":
#     # Show API details
#     debug_login_api_payload()
    
#     print("\n" + "=" * 70)
#     print("OTP FORMAT VALIDATION TEST")
#     print("=" * 70)
    
#     # Test OTP validation
#     test_otps = ["12345", "1234", "12345678", "12", "abc", ""]
#     for otp in test_otps:
#         validation = validate_otp_format(otp)
#         print(f"OTP: '{otp}' -> {validation['status']}: {validation['message']}")
    
#     print("\n" + "=" * 70)
#     print("LOGIN API FUNCTIONAL TEST")
#     print("=" * 70)
    
#     # Test the login API functionality
#     test_login_api()
    
#     print("\n" + "=" * 70)
#     print("COMPLETE AUTHENTICATION FLOW TEST")
#     print("=" * 70)
    
#     # Test complete authentication flow
#     complete_authentication_flow(
#         mobile="+97403012026",
#         otp="12345",
#         otp_start_time="2025-10-10T05:36:44.860Z"
#     )
    
#     print("\n" + "=" * 70)
#     print("TOKEN INFORMATION")
#     print("=" * 70)
    
#     # Show token information from a successful login
#     sample_result = verify_toyota_otp_login(
#         mobile="+97403012026",
#         otp="12345", 
#         otp_start_time="2025-10-10T05:36:44.860Z"
#     )
    
#     if sample_result['status'] == 'success':
#         print("Token Details:")
#         print(f"Access Token Length: {len(sample_result['access_token'])} characters")
#         print(f"Refresh Token Length: {len(sample_result['refresh_token'])} characters")
#         print(f"User ID: {sample_result.get('user_id', 'Not extracted')}")
#         print(f"Update Required: {sample_result['must_update_user_data']}")
#         print(f"Add Mobile Required: {sample_result['must_add_mobile']}")