import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(name="get_toyota_offers_cleaned", description="Retrieves Toyota offers for various models")
def get_toyota_offers(
    slug: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves Toyota terms and conditions with filtering options.
    
    Args:
        slug (str, optional): Specific model to filter by (e.g., 'Prado', 'Land Cruiser')    
    Returns:
        dict: A dictionary containing:
            - status (str): 'success', 'not_found', or 'error'
            - count (int): Number of terms & conditions entries found
            - terms_conditions (list): List of terms and conditions with details
            - timestamp (str): When the request was processed

    
    Raises:
        Exception: For API errors or connection issues
    
    Examples:
        >>> get_toyota_offers(slug="Land Cruiser")
        {
            "status": "success",
            "count": 1,
            "terms_conditions": [...],
            "timestamp": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        # API endpoint configuration
        base_url = "https://csprod.toyotaqatar.com/graphql/execute.json/ToyotaWebsite/T4-MainSpecialOffers;language=en;brand=toyota;"
        
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
        terms_data = data['data']['t4MainspecialoffersList']['items'][0]['availableOffers']

        print(terms_data)

        filtered_terms = _apply_filters(
            terms_data, 
            slug
        )
        
        # Remove unwanted fields from each term
        cleaned_terms = [_remove_unwanted_fields(term) for term in filtered_terms]
        
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
    slug: Optional[str]
) -> List[Dict]:
    """Apply filters to the terms and conditions list."""
    filtered = terms_data

    if slug:
        filtered = [t for t in filtered if _matches_slug(t, slug)]
    
    return filtered

def _matches_slug(term: Dict, slug: str) -> bool:
    """Check if term matches slug."""
    print('slug', slug)
    slugData = term.get('slug', '').lower()
    # print('slug', term, slugData)
    return slug.replace(" ", "-").lower() in slugData

def _remove_unwanted_fields(term: Dict) -> Dict:
    """Remove unwanted fields from term data."""
    # Fields to remove
    fields_to_remove = ['_path', 'offersImage', 'mobileOffersImage', 'disclaimerImage', 'discoverButtonUrl']
    
    # Create a copy of the term without the unwanted fields
    cleaned_term = {key: value for key, value in term.items() if key not in fields_to_remove}
    
    return cleaned_term


if __name__ == "__main__":
    # Test the tool
    print("Toyota Offers (Urban Cruiser):")
    result = get_toyota_offers(slug="Urban Cruiser")
    print(f"Found {result['count']} terms & conditions entries")
    print("*"*100)
    print(result)