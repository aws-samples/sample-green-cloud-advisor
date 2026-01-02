#!/usr/bin/env python3
"""
Test script for dynamic AWS regions fetching
"""

from aws_regions_fetcher import AWSRegionsFetcher
from greencloud_advisor import GreenCloudAdvisor

def test_dynamic_regions():
    print("🧪 Testing Dynamic AWS Regions Fetching\n")
    
    # Test regions fetcher directly
    fetcher = AWSRegionsFetcher()
    regions = fetcher.get_aws_regions()
    
    print(f"📍 Found {len(regions)} AWS regions:")
    for region in sorted(regions, key=lambda x: x.code):
        print(f"  • {region.code}: {region.name} at {region.location}")
    
    # Test with GreenCloudAdvisor
    print(f"\n🌱 Testing with GreenCloudAdvisor:")
    advisor = GreenCloudAdvisor()
    print(f"  • Advisor loaded {len(advisor.regions)} regions")
    
    # Show some examples
    print(f"\n🔍 Sample regions:")
    for region in advisor.regions[:5]:
        print(f"  • {region.code}: {region.name}")

if __name__ == "__main__":
    test_dynamic_regions()