"""
AWS Live Service Availability Checker
Template for checking real-time AWS service availability
"""
import json
from typing import Dict
import boto3

def check_aws_service_availability_live(region_code: str, service_name: str) -> bool:
    """
    Check AWS service availability using live AWS APIs
    
    Args:
        region_code: AWS region code (e.g., 'ap-southeast-1')
        service_name: AWS service name (e.g., 'ec2 g6.4xlarge', 'rds', 's3')
    
    Returns:
        bool: True if service is available, False otherwise
    """
    
    try:

        from botocore.exceptions import ClientError, NoCredentialsError
        
        service_name = service_name.lower().strip()
        print(f"DEBUG: Main function called with region='{region_code}', service='{service_name}'")
        
        # Check EC2 instance types
        if 'ec2' in service_name and any(x in service_name for x in ['g6', 'g5', 'p4', 'p3', 'c6', 'm6']):
            print(f"DEBUG: Taking EC2 instance path")
            return check_ec2_instance_availability(region_code, service_name)
        
        # Check basic services
        elif service_name in ['ec2', 's3', 'rds', 'lambda', 'ecs', 'eks', 'redshift']:
            print(f"DEBUG: Taking basic service path")
            return check_basic_service_availability(region_code, service_name)
        
        # Check RDS engines
        elif 'rds' in service_name and any(x in service_name for x in ['aurora', 'mysql', 'postgres']):
            print(f"DEBUG: Taking RDS engine path")
            return check_rds_engine_availability(region_code, service_name)
        
        print(f"DEBUG: Taking default path (unknown service)")
        return True  # Default to available for unknown services
        
    except ImportError as e:
        print(f"boto3 not installed. Install with: pip install boto3")
        return False
    except (NoCredentialsError, ClientError) as e:
        print(f"AWS credentials error: {e}")
        return False
    except Exception as e:
        print(f"AWS API error: {e}")
        return False

def check_ec2_instance_availability(region_code: str, service_request: str) -> bool:
    """
    Check if specific EC2 instance types are available in a region
    """
    try:
      
        print(f"DEBUG: Checking EC2 availability for '{service_request}' in {region_code}")
        ec2 = boto3.client('ec2', region_name=region_code)
        
        # Extract instance type from request
        instance_type = None
        for itype in ['g6.4xlarge', 'g6.2xlarge', 'g6.xlarge', 'g5.4xlarge', 'g5.2xlarge', 'g5.xlarge']:
            if itype in service_request:
                instance_type = itype
                break
        
        print(f"DEBUG: Extracted instance type: {instance_type}")
        
        if instance_type:
            # Check if instance type is available
            print(f"DEBUG: Calling describe_instance_type_offerings for {instance_type}")
            response = ec2.describe_instance_type_offerings(
                Filters=[
                    {
                        'Name': 'instance-type',
                        'Values': [instance_type]
                    }
                ],
                LocationType='region'
            )
            
            available = len(response['InstanceTypeOfferings']) > 0
            print(f"DEBUG: Instance type {instance_type} available: {available}")
            print(f"DEBUG: Response: {response['InstanceTypeOfferings']}")
            return available
        
        # For general EC2, check if any instances are available
        print(f"DEBUG: Checking general EC2 availability")
        response = ec2.describe_instance_type_offerings(
            MaxResults=1,
            LocationType='region'
        )
        
        available = len(response['InstanceTypeOfferings']) > 0
        print(f"DEBUG: General EC2 available: {available}")
        return available
        
    except Exception as e:
        print(f"DEBUG: EC2 check error: {e}")
        return True  # Default to available

def check_basic_service_availability(region_code: str, service_name: str) -> bool:
    """
    Check basic AWS service availability
    """
    try:        
        # Most basic services are available in all commercial regions
        if service_name in ['s3', 'lambda', 'ec2']:
            return True
        
        # Check RDS availability
        if service_name == 'rds':
            rds = boto3.client('rds', region_name=region_code)
            response = rds.describe_db_engine_versions(MaxRecords=20)
            return len(response['DBEngineVersions']) > 0
        
        # Check EKS availability
        if service_name == 'eks':
            eks = boto3.client('eks', region_name=region_code)
            try:
                eks.list_clusters(maxResults=1)
                return True
            except Exception as eks_e:
                print(f"EKS Check Exception: {eks_e}")
                return False
        
        # Check Redshift availability
        if service_name == 'redshift':
            redshift = boto3.client('redshift', region_name=region_code)
            try:
                redshift.describe_clusters(MaxRecords=20)
                return True
            except Exception as redshift_e:
                print(f"Redshift Check Exception: {redshift_e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Basic service check error: {e}")
        return True

def check_rds_engine_availability(region_code: str, service_request: str) -> bool:
    """
    Check RDS engine availability
    """
    try:
       
        rds = boto3.client('rds', region_name=region_code)
        
        engine_map = {
            'aurora': 'aurora-mysql',
            'mysql': 'mysql',
            'postgres': 'postgres',
            'oracle': 'oracle-ee',
            'sqlserver': 'sqlserver-ex'
        }
        
        for engine_name, engine_id in engine_map.items():
            if engine_name in service_request:
                response = rds.describe_db_engine_versions(
                    Engine=engine_id,
                    MaxRecords=1
                )
                return len(response['DBEngineVersions']) > 0
        
        return True
        
    except Exception as e:
        print(f"RDS engine check error: {e}")
        return True

def parse_aws_regional_data(json_data: str) -> Dict:
    """
    Parse AWS regional service data from JSON format
    
    Args:
        json_data: JSON string containing AWS regional service data
    
    Returns:
        Dict: Parsed service availability by region
    """
    try:
        data = json.loads(json_data)
        
        regional_services = {}
        
        for region in data.get('regions', []):
            region_code = region.get('code')
            services = [svc.lower() for svc in region.get('services', [])]
            regional_services[region_code] = services
            
        return regional_services
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {}

def manual_data_entry_helper():
    """
    Helper function to manually input AWS service data
    Call this function and paste the service data you copied from the AWS website
    """
    
    print("Manual AWS Service Data Entry Helper")
    print("=" * 50)
    print("1. Go to: https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/")
    print("2. Copy the service availability data")
    print("3. Paste it below (press Enter twice when done):")
    print()
    
    lines = []
    while True:
        try:
            line = input()
            if line == "" and len(lines) > 0 and lines[-1] == "":
                break
            lines.append(line)
        except EOFError:
            break
    
    # Process the manual input
    service_data = "\n".join(lines)
    
    # Parse common formats
    regional_services = {}
    current_region = None
    
    for line in lines:
        line = line.strip()
        
        # Detect region lines (usually contain region codes)
        if any(region in line.lower() for region in ['us-east', 'us-west', 'eu-', 'ap-', 'ca-', 'sa-', 'me-', 'af-']):
            # Extract region code
            for word in line.split():
                if any(region in word.lower() for region in ['us-east', 'us-west', 'eu-', 'ap-', 'ca-', 'sa-', 'me-', 'af-']):
                    current_region = word.lower()
                    regional_services[current_region] = []
                    break
        
        # Detect service lines
        elif current_region and any(service in line.lower() for service in ['ec2', 's3', 'rds', 'lambda', 'eks', 'ecs']):
            services = [svc.strip().lower() for svc in line.split(',') if svc.strip()]
            regional_services[current_region].extend(services)
    
    return regional_services

# Example usage with manual data
if __name__ == "__main__":
    print("AWS Service Availability Checker")
    print("Choose an option:")
    print("1. Manual data entry")
    print("2. Use sample data")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        service_data = manual_data_entry_helper()
        print("\nParsed service data:")
        for region, services in service_data.items():
            print(f"{region}: {services}")
    
    else:
        # Use existing static data as fallback
        from aws_service_checker import check_service_availability
        
        test_cases = [
            ("ap-southeast-1", "ec2 g6.4xlarge"),
            ("ap-south-1", "ec2"),
            ("us-east-1", "ec2 g6.4xlarge")
        ]
        
        for region, service in test_cases:
            available = check_service_availability(region, service)
            print(f"{service} in {region}: {'✅ Available' if available else '❌ Not Available'}")