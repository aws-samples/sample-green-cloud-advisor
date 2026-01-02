"""
Test for carbon intensity fetcher
"""

from carbon_intensity_fetcher import get_live_carbon_intensity

def test_get_live_carbon_intensity():
    """Test carbon intensity fetching"""
    try:
        # Test valid region
        location_based, market_based = get_live_carbon_intensity("eu-central-1")
        print(f"eu-central-1: location={location_based}, market={market_based}")
        
        # Test another region
        location_based, market_based = get_live_carbon_intensity("us-east-1")
        print(f"us-east-1: location={location_based}, market={market_based}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_live_carbon_intensity()