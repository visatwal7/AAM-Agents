import requests
from typing import Dict, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="mobile_authentication", description="Handles mobile OTP authentication flow for user login")
def mobile_authentication() -> Dict[str, Any]:
    """Handles complete mobile OTP authentication flow by asking user for mobile number and OTP.
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - message (str): Descriptive message about the operation
            - access_token (str, optional): JWT access token for authenticated requests
            - refresh_token (str, optional): JWT refresh token
            - must_update_user_data (bool, optional): Flag indicating if user data needs update
            - must_add_mobile (bool, optional): Flag indicating if mobile needs to be added
            - timestamp (str): When the request was processed
    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> mobile_authentication()
        {
            "status": "success",
            "message": "Authentication successful",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "must_update_user_data": false,
            "must_add_mobile": false,
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1"
        
        # Step 1: Ask user for mobile number
        mobile_number = input("Please enter your mobile number (e.g., +97403012025): ").strip()
        
        if not mobile_number:
            return {
                "status": "error",
                "message": "Mobile number is required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 2: Request OTP
        otp_result = _request_otp(base_url, mobile_number)
        
        if not otp_result["success"]:
            return {
                "status": "error",
                "message": f"OTP request failed: {otp_result['error']}",
                "timestamp": datetime.now().isoformat()
            }
        
        otp_start_time = otp_result["otp_start_time"]
        
        # Step 3: Ask user for OTP
        print("OTP has been sent to your mobile number.")
        otp_code = input("Please enter the OTP you received: ").strip()
        
        if not otp_code:
            return {
                "status": "error",
                "message": "OTP code is required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 4: Login with OTP
        login_result = _login_with_otp(base_url, mobile_number, otp_code, otp_start_time)
        
        if not login_result["success"]:
            return {
                "status": "error",
                "message": f"Login failed: {login_result['error']}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Return successful authentication result
        return {
            "status": "success",
            "message": "Authentication successful",
            "access_token": login_result["access_token"],
            "refresh_token": login_result["refresh_token"],
            "must_update_user_data": login_result["must_update_user_data"],
            "must_add_mobile": login_result["must_add_mobile"],
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"API request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Authentication failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def _request_otp(base_url: str, mobile_number: str) -> Dict[str, Any]:
    """Request OTP for the mobile number.
    
    Args:
        base_url (str): Base API URL
        mobile_number (str): Mobile number to send OTP to
    
    Returns:
        dict: Result containing success status and OTP start time
    """
    url = f"{base_url}/auth/otp/mobile/request"
    
    payload = {
        "mobile": mobile_number
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("responseCode") == 1:
        return {
            "success": True,
            "otp_start_time": result["data"]["time"],
            "message": result.get("message", "OTP sent successfully")
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "Unknown error during OTP request")
        }


def _login_with_otp(base_url: str, mobile_number: str, otp: str, otp_start_time: str) -> Dict[str, Any]:
    """Login with OTP code.
    
    Args:
        base_url (str): Base API URL
        mobile_number (str): Mobile number used for OTP request
        otp (str): OTP code received via SMS
        otp_start_time (str): OTP start time from the request response
    
    Returns:
        dict: Login result containing tokens and user flags
    """
    url = f"{base_url}/auth/login/mobile"
    
    payload = {
        "mobile": mobile_number,
        "otp": otp,
        "otp_start_time": otp_start_time
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("responseCode") == 1:
        data = result["data"]
        return {
            "success": True,
            "access_token": data["accessToken"],
            "refresh_token": data["refreshToken"],
            "must_update_user_data": data["mustUpdateUserData"],
            "must_add_mobile": data["mustAddMobile"],
            "message": result.get("message", "Login successful")
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "Unknown error during login")
        }


# Test function
if __name__ == "__main__":
    # Test the authentication tool
    print("Mobile Authentication Tool:")
    print("=" * 50)
    
    result = mobile_authentication()
    
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        print(f"Access Token: {result['access_token'][:50]}...")
        print(f"Refresh Token: {result['refresh_token'][:50]}...")
        print(f"Must Update User Data: {result['must_update_user_data']}")
        print(f"Must Add Mobile: {result['must_add_mobile']}")
    
    print(f"Timestamp: {result['timestamp']}")
    print("=" * 50)