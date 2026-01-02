"""
AWS Service Extractor using Bedrock Nova Pro
Extracts AWS services from workload descriptions
"""

import boto3
import json
from typing import List, Dict
import re

class AWSServiceExtractor:
    def __init__(self):
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock client: {e}")
            self.bedrock = None
    
    def extract_services(self, workload_description: str) -> List[str]:
        """Extract AWS services from workload description using Nova Pro"""
        if not self.bedrock:
            raise Exception("Bedrock client not initialized. Please check AWS credentials and permissions.")
        
        prompt = f"""
        Extract all AWS services mentioned in this workload description. Return only the service names in lowercase, separated by commas.
        
        For specific instance types like "g6.4xlarge", return as "ec2 g6.4xlarge".
        For RDS engines like "MySQL", return as "rds mysql".
        
        Workload description: {workload_description}
        
        Return format: service1, service2, service3
        """
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 200
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId="us.amazon.nova-pro-v1:0",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        extracted_text = response_body['output']['message']['content'][0]['text'].strip()
        
        # Parse the response and clean up
        services = [s.strip().lower() for s in extracted_text.split(',') if s.strip()]
        return services