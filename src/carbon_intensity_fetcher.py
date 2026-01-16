"""
Carbon Intensity Data Fetcher
Fetches real-time carbon intensity data for AWS regions using ElectricityMaps API
"""

import json
import requests
from typing import Tuple, Dict
from src.aws_regions_fetcher import _cached_regions, AWSRegionsFetcher

def _create_region_mapping() -> Dict[str, str]:
    """Create region to country zone mapping from cached regions"""
    fetcher = AWSRegionsFetcher()
    regions = fetcher.get_aws_regions()
    
    # Base mapping for known regions
    base_mapping = {
        "us-east-1": "US", "us-east-2": "US-CAL-LDWP", "us-west-1": "US-CAL-CISO", "us-west-2": "US-CAL-IID",
        "mx-central-1": "MX",
        "eu-west-1": "IE", "eu-west-2": "GB", "eu-west-3": "FR", "eu-central-1": "DE",
        "cn-north-1" : "CN", "cn-northwest-1" : "CN", "ap-east-1" : "HK",
        "eu-north-1": "SE", "eu-south-1": "IT", "ap-south-1": "IN-WE", "ap-south-2": "IN-SO","ap-southeast-1": "SG",
        "ap-southeast-2": "AU-NSW", "ap-southeast-3" : "ID", "ap-southeast-4": "AU-QLD", "ap-southeast-5" : "ML", "ap-southeast-6": "NZ",
        "ap-northeast-1": "JP", "ap-northeast-2": "KR",
        "ap-northeast-3": "JP-KN", "ap-east-1": "HK", "ca-central-1": "CA",
        "sa-east-1": "BR-SE", "me-south-1": "BH", "af-south-1": "ZA"
    }
    
    # Add all cached regions, use base mapping or default to 'DE'
    region_mapping = {}
    for region in regions:
        region_mapping[region.code] = base_mapping.get(region.code, "DE")
    
    return region_mapping

def get_live_carbon_intensity(region_code: str) -> Tuple[float, float]:
    """Get live carbon intensity data for AWS region using ElectricityMaps API"""
    region_mapping = _create_region_mapping()
    
    zone = region_mapping.get(region_code)
    if not zone:
        zone ='DE'

    #Read the config file and use the API_TOKEN variable to create api_token variable
    with open('config', 'r') as f:
        for line in f:
            if line.startswith('API_TOKEN='):
                api_token = line.split('=')[1].strip().strip("'\"")
                break
   
    try:        
        headers = {
            'auth-token': api_token,
            'Content-Type': 'application/json'
        }
        url = f'https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={zone}'
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("API response:", data)
        carbon_intensity = data.get("carbonIntensity", 400) / 1000  # Convert g/kWh to kg/kWh
        
        # Return both location-based and market-based (assuming 30% reduction for market-based)
        location_based = carbon_intensity
        market_based = carbon_intensity * 0.7
        
        return location_based, market_based
            
    except Exception as e:
        raise Exception(f"Failed to fetch carbon intensity for {region_code}: {str(e)}")