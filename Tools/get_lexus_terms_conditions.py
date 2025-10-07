import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_lexus_terms_conditions", description="Retrieves Lexus terms and conditions for various models and offers")
def get_lexus_terms_conditions(
    model_of_interest: Optional[str] = None,
    slug: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Lexus terms and conditions with filtering options.
    
    Args:
        model_of_interest (str, optional): Specific model to filter by (e.g., 'LX', 'RX', 'ES')
        slug (str, optional): Slug identifier to filter by (e.g., 'lx', 'rx', 'es')
    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of terms & conditions entries found
            - terms_conditions (list): List of terms and conditions with details
            - timestamp (str): When the request was processed

    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_lexus_terms_conditions(model_of_interest="LX")
        {
            "status": "success",
            "count": 1,
            "terms_conditions": [...],
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        # API endpoint configuration for Lexus
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/T26-Terms-Conditions;language=en;brand=lexus"
        
        # Make API request
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
   
        # Check if data is available
        if not data or 'data' not in data:
            return {
                "status": "not_found",
                "error": "No terms and conditions data found in API response",
                "count": 0,
                "terms_conditions": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract terms and conditions data from the response structure
        terms_data = data['data']['t26Terms_conditionsList']['items']

        filtered_terms = _apply_filters(
            terms_data, 
            model_of_interest,
            slug
        )
        
        return {
            "status": "success",
            "count": len(filtered_terms),
            "terms_conditions": filtered_terms,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "count": 0,
            "terms_conditions": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Terms and conditions lookup failed: {str(e)}",
            "count": 0,
            "terms_conditions": [],
            "timestamp": datetime.now().isoformat()
        }

def _apply_filters(
    terms_data: List[Dict], 
    model_of_interest: Optional[str],
    slug: Optional[str],
) -> List[Dict]:
    """Apply filters to the terms and conditions list."""
    filtered = terms_data

    if model_of_interest:
        filtered = [t for t in filtered if _matches_model_of_interest(t, model_of_interest)]

    if slug:
        filtered = [t for t in filtered if _matches_slug(t, slug)]
    
    return filtered

def _matches_model_of_interest(term: Dict, model_of_interest: str) -> bool:
    """Check if term matches modelOfInterest."""
    model = term.get('modelOfInterest', '').lower()
    return model_of_interest.lower() in model

def _matches_slug(term: Dict, slug: str) -> bool:
    """Check if term matches slug."""
    term_slug = term.get('slug', '').lower()
    return slug.lower() in term_slug

# if __name__ == "__main__":
#     # Test the tool
#     print("Lexus Terms & Conditions:")
#     result = get_lexus_terms_conditions(model_of_interest="LX")
#     print(f"Found {result['count']} terms & conditions entries")
#     print(result)