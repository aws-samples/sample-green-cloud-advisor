"""
AWS Service Availability Checker
Maps specific AWS services and instance types to regional availability
Based on AWS Regional Product Services data
"""

# Comprehensive service availability by region
# Default services available in all regions
DEFAULT_SERVICES = {
    "ec2": ["standard-instances"],
    "s3": ["standard"],
    "rds": ["mysql", "postgres"],
    "lambda": ["standard"],
    "ecs": ["ec2"],
    "eks": ["standard"]
}

AWS_REGIONAL_SERVICES = {
    "us-east-1": {
        "ec2": ["all-instances"],
        "ec2-g6": ["g6.xlarge", "g6.2xlarge", "g6.4xlarge", "g6.8xlarge", "g6.12xlarge", "g6.16xlarge"],
        "ec2-g5": ["g5.xlarge", "g5.2xlarge", "g5.4xlarge", "g5.8xlarge", "g5.12xlarge", "g5.16xlarge"],
        "s3": ["standard", "glacier", "deep-archive"],
        "rds": ["mysql", "postgres", "aurora", "oracle", "sqlserver"],
        "lambda": ["standard", "provisioned"],
        "redshift": ["dc2", "ra3", "serverless"],
        "eks": ["standard", "fargate"],
        "ecs": ["ec2", "fargate"]
    },
    "ap-south-1": {  # Mumbai
        "ec2": ["standard-instances"],
        "ec2-g5": ["g5.xlarge", "g5.2xlarge"],  # Limited G5
        "s3": ["standard", "glacier"],
        "rds": ["mysql", "postgres", "aurora"],
        "lambda": ["standard"],
        "eks": ["standard"],
        "ecs": ["ec2", "fargate"]
    },
    "ap-southeast-1": {  # Singapore - Limited G6 availability
        "ec2": ["standard-instances"],
        "ec2-g5": ["g5.xlarge", "g5.2xlarge", "g5.4xlarge"],  # Limited G5
        "s3": ["standard", "glacier"],
        "rds": ["mysql", "postgres", "aurora"],
        "lambda": ["standard"],
        "redshift": ["dc2", "ra3"],
        "eks": ["standard"],
        "ecs": ["ec2", "fargate"]
    },
    "eu-west-1": {
        "ec2": ["all-instances"],
        "ec2-g6": ["g6.xlarge", "g6.2xlarge", "g6.4xlarge"],
        "ec2-g5": ["g5.xlarge", "g5.2xlarge", "g5.4xlarge", "g5.8xlarge"],
        "s3": ["standard", "glacier", "deep-archive"],
        "rds": ["mysql", "postgres", "aurora", "oracle"],
        "lambda": ["standard", "provisioned"],
        "redshift": ["dc2", "ra3", "serverless"],
        "eks": ["standard", "fargate"],
        "ecs": ["ec2", "fargate"]
    }
}

def check_service_availability(region_code: str, service_request: str) -> bool:
    """
    Check if a specific service/instance type is available in a region
    
    Args:
        region_code: AWS region code (e.g., 'ap-southeast-1')
        service_request: Service request (e.g., 'ec2 g6.4xlarge', 'rds aurora', 's3')
    
    Returns:
        bool: True if service is available, False otherwise
    """
    # Use region-specific services or fall back to defaults
    region_services = AWS_REGIONAL_SERVICES.get(region_code, DEFAULT_SERVICES)
    service_request = service_request.lower().strip()
    
    # Parse service request
    if "g6" in service_request:
        if "ec2-g6" not in region_services:
            return False
        if any(instance in service_request for instance in ["xlarge", "2xlarge", "4xlarge"]):
            requested_instance = next((inst for inst in ["g6.xlarge", "g6.2xlarge", "g6.4xlarge", "g6.8xlarge"] 
                                     if inst.split('.')[1] in service_request), None)
            return requested_instance in region_services.get("ec2-g6", [])
        return True
    
    elif "g5" in service_request:
        if "ec2-g5" not in region_services:
            return False
        if any(instance in service_request for instance in ["xlarge", "2xlarge", "4xlarge"]):
            requested_instance = next((inst for inst in ["g5.xlarge", "g5.2xlarge", "g5.4xlarge", "g5.8xlarge"] 
                                     if inst.split('.')[1] in service_request), None)
            return requested_instance in region_services.get("ec2-g5", [])
        return True
    
    elif "ec2" in service_request:
        return "ec2" in region_services
    
    elif "rds" in service_request:
        if "aurora" in service_request:
            return "aurora" in region_services.get("rds", [])
        return "rds" in region_services
    
    elif "redshift" in service_request:
        if "serverless" in service_request:
            return "serverless" in region_services.get("redshift", [])
        return "redshift" in region_services
    
    # Default service check
    service_name = service_request.split()[0]
    return service_name in region_services

def get_unavailable_services(region_code: str, service_requests: list) -> list:
    """
    Get list of services that are NOT available in the specified region
    
    Args:
        region_code: AWS region code
        service_requests: List of service requests
    
    Returns:
        list: Services not available in the region
    """
    unavailable = []
    for service in service_requests:
        if not check_service_availability(region_code, service):
            unavailable.append(service)
    return unavailable

# Example usage
if __name__ == "__main__":
    # Test cases
    print("Testing service availability:")
    print(f"G6.4xlarge in Singapore: {check_service_availability('ap-southeast-1', 'ec2 g6.4xlarge')}")  # Should be False
    print(f"G5.2xlarge in Singapore: {check_service_availability('ap-southeast-1', 'ec2 g5.2xlarge')}")  # Should be True
    print(f"G6.4xlarge in US-East-1: {check_service_availability('us-east-1', 'ec2 g6.4xlarge')}")     # Should be True