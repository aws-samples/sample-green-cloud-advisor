#!/usr/bin/env python3
"""
AWS Regions Dynamic Fetcher
Fetches AWS regions and their coordinates dynamically
"""

import boto3
from typing import List, Tuple, Dict
from dataclasses import dataclass

@dataclass(frozen=True)
class RegionData:
    code: str
    name: str
    location: Tuple[float, float]  # (lat, lon)

# Global cache for regions
_cached_regions = []

class AWSRegionsFetcher:
    def __init__(self):
        self.region_names = {
            "us-east-1": "N. Virginia", "us-east-2": "Ohio", "us-west-1": "N. California", "us-west-2": "Oregon",
            "eu-west-1": "Ireland", "eu-west-2": "London", "eu-west-3": "Paris", "eu-central-1": "Frankfurt",
            "eu-north-1": "Stockholm", "eu-south-1": "Milan", "ap-south-1": "Mumbai", "ap-southeast-1": "Singapore",
            "ap-southeast-2": "Sydney", "ap-northeast-1": "Tokyo", "ap-northeast-2": "Seoul", "ap-northeast-3": "Osaka",
            "ap-east-1": "Hong Kong", "ca-central-1": "Canada Central", "sa-east-1": "São Paulo",
            "me-south-1": "Bahrain", "af-south-1": "Cape Town", "ap-south-2": "Hyderabad"
        }
    
    def get_aws_regions(self) -> List[RegionData]:
        """Fetch AWS regions dynamically using boto3"""
        global _cached_regions
        if not _cached_regions:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            response = ec2.describe_regions()
            _cached_regions = [RegionData(
                region['RegionName'], 
                self.region_names.get(region['RegionName'], region['RegionName']), 
                (0.0, 0.0)
            ) for region in response['Regions']]
        return _cached_regions