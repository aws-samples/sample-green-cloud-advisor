#!/usr/bin/env python3
"""
GreenCloud Advisor - AWS Region Sustainability Recommender
Balances proximity and sustainability for optimal AWS region selection
"""

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

    
    def calculate_location_based_score(self, region_code: str) -> float:
        """Calculate location-based carbon intensity score (lower is better)"""
        location_based = get_live_carbon_intensity(region_code)
        return location_based
    

def main():
    advisor = GreenCloudAdvisor()

if __name__ == "__main__":
    main()