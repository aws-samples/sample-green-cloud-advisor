#!/usr/bin/env python3
"""
Test script to verify AWS live API functionality
"""

from aws_live_checker import check_aws_service_availability_live

def test_service_availability():
    """Test specific service availability cases"""
    
    test_cases = [
        ("ap-southeast-1", "ec2 g6.4xlarge", "Singapore G6.4xlarge (should be False)"),
        ("ap-southeast-1", "ec2 g5.2xlarge", "Singapore G5.2xlarge (should be True)"),
        ("ap-south-1", "ec2 g6.4xlarge", "Mumbai g6.4xlarge (should be True)"),
        ("us-east-1", "ec2 g6.4xlarge", "US-East-1 G6.4xlarge (should be True)"),
        ("ap-south-1", "ec2", "Mumbai EC2 (should be True)"),
        ("ap-southeast-1", "s3", "Singapore S3 (should be True)")
    ]
    
    print("Testing AWS Live API Service Availability")
    print("=" * 50)
    
    for region, service, description in test_cases:
        try:
            result = check_aws_service_availability_live(region, service)
            status = "✅ Available" if result else "❌ Not Available"
            print(f"{description}: {status}")
        except Exception as e:
            print(f"{description}: ⚠️ Error - {e}")
    
    print("\nNote: Ensure AWS credentials are configured with 'aws configure'")

if __name__ == "__main__":
    test_service_availability()