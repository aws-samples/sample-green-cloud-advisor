"""
Sustainability Insights Generator
Provides AI-powered optimization recommendations for AWS workloads
"""

import boto3
import json
from typing import List, Dict, Any

class SustainabilityInsights:
    def __init__(self):
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception:
            self.bedrock = None
        
    def generate_insights(self, services: List[str], best_region: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate AI-powered sustainability optimization insights"""
        if not services:
            return []
            
        if not self.bedrock:
            return [{
                'type': 'Error',
                'title': '⚠️ AI Insights Unavailable',
                'description': 'Bedrock service not available. Please configure AWS credentials.',
                'impact': 'Info',
                'savings': 'N/A'
            }]
        
        try:
            workload_description = ' '.join(services)
            region_info = f"{best_region.get('region_name', 'Unknown')} with {best_region.get('market_based_intensity', 0)} kg CO2e/kWh"
            
            prompt = f"""Analyze this AWS workload and provide 3-4 specific sustainability optimization recommendations:

Workload: {workload_description}
Current Region: {region_info}
Services List: {services}

For each recommendation, suggest specific AWS services focusing on:
1. **Graviton processors**: Always recommend LATEST Graviton instances (c8g, r8g, m8g series) available in {region_info}. Compare current instances like c6i.8xlarge, r7i.8xlarge to c8g.8xlarge, r8g.8xlarge. Provide specific cost and performance savings.
2. **Trainium/Inferentia**: For ML workloads, recommend trn1, inf2 instances. Compare p4 GPU instances to Trainium alternatives.
3. **Serverless alternatives**: Lambda, Fargate, Aurora Serverless where applicable.


Provide recommendations in this exact format:
🚀 Compute Optimization
Migrate to latest Graviton-based instances for better price-performance and lower carbon footprint.
Impact: High | Savings: 15-25%

⚡ Serverless Migration
Replace always-on EC2 instances with Lambda functions for event-driven workloads.
Impact: Medium | Savings: 30-50%

Provide 3-4 similar recommendations with emojis, titles, descriptions, and impact/savings estimates."""
            
            response = self.bedrock.invoke_model(
                modelId="us.amazon.nova-pro-v1:0",
                body=json.dumps({
                    'messages': [{
                        'role': 'user',
                        'content': [{'text': prompt}]
                    }],
                    'inferenceConfig': {
                        'maxTokens': 1000
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['output']['message']['content'][0]['text']
            
            # Parse structured text response
            recommendations = self._parse_recommendations(ai_response)
            return recommendations if recommendations else [{
                'type': 'AI',
                'title': '🤖 AI Recommendations',
                'description': ai_response,
                'impact': 'High',
                'savings': 'Variable'
            }]
                
        except Exception as e:
            return [{
                'type': 'Error',
                'title': '⚠️ AI Analysis Failed',
                'description': f'Unable to generate AI insights: {str(e)}',
                'impact': 'Info',
                'savings': 'N/A'
            }]
    
    def _parse_recommendations(self, text: str) -> List[Dict[str, str]]:
        """Parse structured text recommendations into list format"""
        recommendations = []
        lines = text.strip().split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with emoji (likely a title)
            if any(ord(char) > 127 for char in line[:3]) and not line.startswith('Impact:'):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {
                    'type': 'Optimization',
                    'title': line,
                    'description': '',
                    'savings': 'Variable'
                }
            elif line.startswith('Impact:'):
                # Parse impact and savings from line like "Impact: High | Savings: 15-25%"
                parts = line.split('|')
                if len(parts) >= 1:
                    impact_part = parts[0].replace('Impact:', '').strip()
                    current_rec['impact'] = impact_part
                if len(parts) >= 2:
                    savings_part = parts[1].replace('Savings:', '').strip()
                    current_rec['savings'] = savings_part
            elif current_rec and not line.startswith('Impact:'):
                # Add to description
                if current_rec['description']:
                    current_rec['description'] += ' '
                current_rec['description'] += line
        
        # Add the last recommendation
        if current_rec:
            recommendations.append(current_rec)

        # Append programming language recommendation
        recommendations.append({
            'type': 'Programming',
            'title': '🚀 Programming Language recommendation',
            'description': 'Use energy efficient programming languages like C, Rust, C++, Ada, Java. Refer this blog https://aws.amazon.com/blogs/opensource/sustainability-with-rust/ for more detail',
            'impact': 'Medium',
            'savings': 'Variable'
        })  
        return recommendations