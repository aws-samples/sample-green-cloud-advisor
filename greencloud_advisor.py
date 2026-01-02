#!/usr/bin/env python3
"""
GreenCloud Advisor - AWS Region Sustainability Recommender
Balances proximity and sustainability for optimal AWS region selection
"""

import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
import math
from aws_regions_fetcher import AWSRegionsFetcher, RegionData

class GreenCloudAdvisor:
    def __init__(self):
        self.regions_fetcher = AWSRegionsFetcher()
        self.regions = self.regions_fetcher.get_aws_regions()
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371 * c  # Earth's radius in km
    
    def find_nearby_regions(self, user_location: Tuple[float, float], 
                          max_distance_km: int = 5000) -> List[RegionData]:
        """Find regions within specified distance from user location"""
        nearby = []
        for region in self.regions:
            distance = self._calculate_distance(user_location, region.location)
            if distance <= max_distance_km:
                nearby.append((region, distance))
        
        return [region for region, _ in sorted(nearby, key=lambda x: x[1])]
    
    def check_service_availability(self, region_code: str, service: str) -> bool:
        """Check if service/instance type is available in region using live API"""
        from aws_live_checker import check_aws_service_availability_live
        try:
            return check_aws_service_availability_live(region_code, service)
        except Exception:
            return False
    
    def filter_by_services(self, regions: List[RegionData], 
                          required_services: List[str]) -> List[RegionData]:
        """Filter regions that support all required services using live API"""
        compatible_regions = []
        for region in regions:
            if all(self.check_service_availability(region.code, service) 
                  for service in required_services):
                compatible_regions.append(region)
        return compatible_regions
    
    def calculate_sustainability_score(self, region_code: str, 
                                     weight_market: float = 0.7) -> Tuple[float, float, float]:
        """Calculate sustainability score using live data (lower is better)"""
        from carbon_intensity_fetcher import get_live_carbon_intensity
        location_based, market_based = get_live_carbon_intensity(region_code)
        score = (market_based * weight_market + location_based * (1 - weight_market))
        return location_based, market_based, score
    
    def recommend_region(self, user_location: Tuple[float, float], 
                        required_services: List[str], 
                        max_distance_km: int = 5000) -> Dict:
        """Main recommendation function"""
        
        nearby_regions = self.find_nearby_regions(user_location, max_distance_km)
        
        if not nearby_regions:
            return {"error": "No regions found within specified distance"}
        
        compatible_regions = self.filter_by_services(nearby_regions, required_services)
        
        if not compatible_regions:
            return {"error": "No regions support all required services"}
        
        scored_regions = []
        for region in compatible_regions:
            location_based, market_based, sustainability_score = self.calculate_sustainability_score(region.code)
            
            scored_regions.append({
                "region_code": region.code,
                "region_name": region.name,
                "location_based_intensity": location_based,
                "market_based_intensity": market_based,
                "sustainability_score": round(sustainability_score, 3)
            })
        
        scored_regions.sort(key=lambda x: x["sustainability_score"])
        
        return {
            "recommended_region": scored_regions[0],
            "all_options": scored_regions,
            "analysis": {
                "total_regions_evaluated": len(self.regions),
                "nearby_regions_found": len(nearby_regions),
                "service_compatible_regions": len(compatible_regions)
            }
        }

def main():
    advisor = GreenCloudAdvisor()
    
    print("🌱 GreenCloud Advisor - AWS Sustainability Recommender\n")
    
    # Example: Company in London needs EC2, S3, RDS
    london_location = (51.5074, -0.1278)
    required_services = ["ec2", "s3", "rds"]
    
    recommendation = advisor.recommend_region(
        user_location=london_location,
        required_services=required_services,
        max_distance_km=6000
    )
    
    if "error" in recommendation:
        print(f"❌ {recommendation['error']}")
        return
    
    best = recommendation["recommended_region"]
    print(f"🏆 RECOMMENDED REGION: {best['region_name']} ({best['region_code']})")
    print(f"📍 Distance: {best['distance_km']} km")
    print(f"🌍 Location-based: {best['location_based_intensity']} kg CO2e/kWh")
    print(f"🌱 Market-based: {best['market_based_intensity']} kg CO2e/kWh")
    print(f"⭐ Sustainability Score: {best['sustainability_score']}")
    
    print(f"\n📊 ANALYSIS:")
    analysis = recommendation["analysis"]
    print(f"• Evaluated {analysis['total_regions_evaluated']} total regions")
    print(f"• Found {analysis['nearby_regions_found']} nearby regions")
    print(f"• {analysis['service_compatible_regions']} regions support your services")
    
    print(f"\n🔍 ALL OPTIONS:")
    for i, option in enumerate(recommendation["all_options"], 1):
        print(f"{i}. {option['region_name']} - Score: {option['sustainability_score']} "
              f"({option['distance_km']} km)")

if __name__ == "__main__":
    main()