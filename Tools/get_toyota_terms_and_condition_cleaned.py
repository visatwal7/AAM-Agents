import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_terms_conditions_cleaned", description="Retrieves Toyota terms and conditions for various models and offers")
def get_toyota_terms_conditions(
    slug: Optional[str] = None,
    offer_type: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota terms and conditions with filtering options.
    
    Args:
        slug (str, optional): Specific model to filter by (e.g., 'Prado', 'Land Cruiser')  
        offer_type(str, optional): Specific type for offer (e.g., 'ramadan')
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of terms & conditions entries found
            - terms_conditions (list): List of terms and conditions with details
            - timestamp (str): When the request was processed

    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_terms_conditions(slug="Land Cruiser")
        {
            "status": "success",
            "count": 1,
            "terms_conditions": [...],
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/T26-Terms-Conditions;language=en;brand=toyota"
        
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
            slug,
            offer_type
        )
        
        # Remove _path from each term entry
        cleaned_terms = _remove_path_keys(filtered_terms)
        
        return {
            "status": "success",
            "count": len(cleaned_terms),
            "terms_conditions": cleaned_terms,
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
    slug: Optional[str],
    offer_type: Optional[str]
) -> List[Dict]:
    """Apply filters to the terms and conditions list."""
    filtered = terms_data
    print('offer_type', offer_type)
    if offer_type and offer_type.lower() == 'ramadan':
        print('In If')
        filtered = [t for t in filtered if _matches_ramadan_data(t)]
    else:
        print('In Else')
        filtered = [t for t in filtered if _matches_main_page_data(t)]
    #print(filtered)
    if slug:
        filtered = [t for t in filtered if _matches_slug(t, slug)]
    
    return filtered

def _remove_path_keys(terms_data: List[Dict]) -> List[Dict]:
    """Remove _path key from each term dictionary."""
    cleaned_terms = []
    for term in terms_data:
        # Create a copy of the term without the _path key
        cleaned_term = {key: value for key, value in term.items() if key != '_path'}
        cleaned_terms.append(cleaned_term)
    return cleaned_terms

def _matches_slug(term: Dict, slug: str) -> bool:
    """Check if term matches slug."""

    slugData = term.get('slug', '').lower()
    print('slug', slug.lower(), slugData)
    return slug.replace(" ", "-").lower() in slugData

def _matches_main_page_data(term: Dict) -> bool:
    path = term.get('_path', '').lower()
    return 'main-page' in path

def _matches_ramadan_data(term: Dict) -> bool:
    path = term.get('_path', '').lower()
    return 'ramadan-campaign' in path

# if __name__ == "__main__":
#     # Test the tool
#     print("Toyota Terms & Conditions (Urban Cruiser):")
#     result = get_toyota_terms_conditions(slug="land-cruiser")
#     print(f"Found {result['count']} terms & conditions entries")
#     print(result)