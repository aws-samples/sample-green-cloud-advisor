#!/usr/bin/env python3
"""
GreenCloud Advisor - AWS Region Sustainability Recommender
Balances proximity and sustainability for optimal AWS region selection
"""
from typing import Tuple
from src.aws_regions_fetcher import AWSRegionsFetcher
from src.aws_live_checker import check_aws_service_availability_live
from src.carbon_intensity_fetcher import get_live_carbon_intensity

class GreenCloudAdvisor:
    def __init__(self):
        self.regions_fetcher = AWSRegionsFetcher()
        self.regions = self.regions_fetcher.get_aws_regions()
    
    def check_service_availability(self, region_code: str, service: str) -> bool:
        """Check if service/instance type is available in region using live API"""
        try:
            return check_aws_service_availability_live(region_code, service)
        except Exception:
            return False

    
    def calculate_sustainability_score(self, region_code: str, 
                                     weight_market: float = 0.7) -> Tuple[float, float, float]:
        """Calculate sustainability score using live data (lower is better)"""
        location_based, market_based = get_live_carbon_intensity(region_code)
        score = (market_based * weight_market + location_based * (1 - weight_market))
        return location_based, market_based, score
    

def main():
    advisor = GreenCloudAdvisor()

if __name__ == "__main__":
    main()