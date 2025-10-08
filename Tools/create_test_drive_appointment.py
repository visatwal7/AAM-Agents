import requests
from typing import Dict, Any, List
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="create_test_drive_appointment", description="Creates a test drive appointment with user details and selected slot")
def create_test_drive_appointment(
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
) -> Dict[str, Any]:
    """Creates a test drive appointment with the provided details.
    
    Args:
        access_token (str): Bearer token for authentication
        first_name (str): User's first name
        last_name (str): User's last name
        mobile (str): User's mobile number
        start_time (str): Start time of the test drive slot (ISO format)
        brand (str): Car brand - "Toyota" or "Lexus"
        model_of_interest (str): Car model name
        territory_id (str): Service center/location ID
        resources (List[str]): List of resource IDs for the appointment
        vehicle_id (str): Vehicle ID for the test drive
    
    Returns:
        dict: A dictionary containing the appointment creation response:
            - status (str): 'success' or 'error'
            - message (str): Descriptive message
            - service_appointment_id (str, optional): Created appointment ID
            - assigned_resource_ids (List[str], optional): Assigned resource IDs
            - timestamp (str): When the request was processed
    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> create_test_drive_appointment(
        ...     access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     first_name="John",
        ...     last_name="Doe",
        ...     mobile="+97460417026",
        ...     start_time="2025-10-07T06:00:00.000Z",
        ...     brand="Toyota",
        ...     model_of_interest="Corolla Cross",
        ...     territory_id="0HhHp000000yAcaKAE",
        ...     resources=["0HnHp000000u3cpKAA", "0HnHp000000u3cqKAA"],
        ...     vehicle_id="0HnHp000000u3dYKAQ"
        ... )
        {
            "status": "success",
            "message": "Appointment created successfully",
            "service_appointment_id": "08pWr000003O1E9IAK",
            "assigned_resource_ids": ["03rWr000000PHVVIA4", "03rWr000000PHVWIA4"],
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://web-backenddev-cont-001-ajath8a5beh9eycz.westeurope-01.azurewebsites.net/api/v1/orders/test_drive/appointment"
        
        # Prepare request payload
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "mobile": mobile,
            "startTime": start_time,
            "brand": brand,
            "modelOfInterest": model_of_interest,
            "territoryId": territory_id,
            "resources": resources,
            "vehicleId": vehicle_id
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Make API request
        print("Creating test drive appointment...")
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if appointment was created successfully
        if data.get("responseCode") == 1:
            appointment_data = data.get("data", {})
            return {
                "status": "success",
                "message": "Appointment created successfully",
                "service_appointment_id": appointment_data.get("serviceAppointmentId"),
                "assigned_resource_ids": appointment_data.get("assignedResourceIds", []),
                "appointment_data": appointment_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Appointment creation failed: {data.get('message', 'Unknown error')}",
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
            "message": f"Appointment creation failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@tool(name="create_test_drive_appointment_interactive", description="Interactive tool to create test drive appointment with user input")
def create_test_drive_appointment_interactive(access_token: str) -> Dict[str, Any]:
    """Interactive tool that asks user for all required details to create a test drive appointment.
    
    Args:
        access_token (str): Bearer token for authentication
    
    Returns:
        dict: A dictionary containing the appointment creation response
    """
    try:
        print("📅 Test Drive Appointment Booking")
        print("=" * 50)
        
        # Collect user information
        print("\n👤 Please enter your personal details:")
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        mobile = input("Mobile Number (e.g., +97460417026): ").strip()
        
        # Collect appointment details
        print("\nPlease enter car details:")
        brand = input("Brand (Toyota/Lexus): ").strip()
        model_of_interest = input("Model of Interest: ").strip()
        vehicle_id = input("Vehicle ID: ").strip()
        
        # Collect location details
        print("\n📍 Please enter location details:")
        territory_id = input("Territory ID (Service Center ID): ").strip()
        
        # Collect slot details
        print("\n⏰ Please enter appointment details:")
        start_time = input("Start Time (ISO format, e.g., 2025-10-07T06:00:00.000Z): ").strip()
        
        # Collect resources
        print("\n🔧 Please enter resource IDs (comma-separated):")
        resources_input = input("Resource IDs: ").strip()
        resources = [res.strip() for res in resources_input.split(',') if res.strip()]
        
        # Validate required fields
        if not all([first_name, last_name, mobile, start_time, brand, model_of_interest, territory_id, resources, vehicle_id]):
            return {
                "status": "error",
                "message": "All fields are required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Create appointment
        return create_test_drive_appointment(
            access_token=access_token,
            first_name=first_name,
            last_name=last_name,
            mobile=mobile,
            start_time=start_time,
            brand=brand,
            model_of_interest=model_of_interest,
            territory_id=territory_id,
            resources=resources,
            vehicle_id=vehicle_id
        )
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Appointment creation failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Helper function to integrate with the booking flow
def create_appointment_from_booking_flow(
    access_token: str,
    user_details: Dict[str, str],
    booking_details: Dict[str, Any],
    selected_slot: Dict[str, Any]
) -> Dict[str, Any]:
    """Helper function to create appointment from booking flow data.
    
    Args:
        access_token (str): Bearer token for authentication
        user_details (Dict): User personal details
        booking_details (Dict): Booking details from the flow
        selected_slot (Dict): Selected time slot details
    
    Returns:
        dict: Appointment creation response
    """
    # Extract required information from booking flow
    first_name = user_details.get('first_name')
    last_name = user_details.get('last_name')
    mobile = user_details.get('mobile')
    
    # Convert brand code to full name
    brand_code = booking_details['selected_car']['brand']
    brand = "Toyota" if brand_code == "TOY" else "Lexus"
    
    # Use resources from the selected slot
    resources = selected_slot.get('resources', [])
    
    return create_test_drive_appointment(
        access_token=access_token,
        first_name=first_name,
        last_name=last_name,
        mobile=mobile,
        start_time=selected_slot['startTime'],
        brand=brand,
        model_of_interest=booking_details['selected_car']['model'],
        territory_id=booking_details['selected_location']['id'],
        resources=resources,
        vehicle_id=booking_details['selected_car']['id']
    )


# # Test function
# if __name__ == "__main__":
#     # Test the tool with sample data
#     print("Test Drive Appointment Tool:")
#     print("=" * 50)
    
#     # You would need to get an actual access token from authentication
#     sample_access_token = "your_access_token_here"
    
#     # Test with interactive mode
#     result = create_test_drive_appointment_interactive(sample_access_token)
    
#     print(f"\n📋 Appointment Result:")
#     print(f"Status: {result['status']}")
#     print(f"Message: {result['message']}")
    
#     if result['status'] == 'success':
#         print(f"Service Appointment ID: {result['service_appointment_id']}")
#         print(f"Assigned Resource IDs: {result['assigned_resource_ids']}")
#         print(f"Number of Resources: {len(result['assigned_resource_ids'])}")
    
#     print(f"Timestamp: {result['timestamp']}")
#     print("=" * 50)