"""
Sustainability Insights Generator
Provides AI-powered optimization recommendations for AWS workloads
"""

import boto3
import json
import os
from typing import List, Dict, Any

def _load_insights_texts():
    filepath = os.path.join(os.path.dirname(__file__), '..', 'locales')
    texts = {}
    for lang_code in ['en', 'ja']:
        lp = os.path.join(filepath, f'{lang_code}.json')
        with open(lp, 'r', encoding='utf-8') as f:
            all_keys = json.load(f)
        # Extract keys prefixed with insights_
        texts[lang_code] = {k.replace('insights_', ''): v for k, v in all_keys.items() if k.startswith('insights_')}
    return texts

_TEXTS = _load_insights_texts()

class SustainabilityInsights:
    def __init__(self):
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception:
            self.bedrock = None
        
    def generate_insights(self, services: List[str], best_region: Dict[str, Any], lang: str = "en") -> List[Dict[str, str]]:
        """Generate AI-powered sustainability optimization insights"""
        t = _TEXTS.get(lang, _TEXTS["en"])

        if not services:
            return []
            
        if not self.bedrock:
            return [{
                'type': 'Error',
                'title': t['error_unavailable_title'],
                'description': t['error_unavailable_desc'],
                'impact': t['error_unavailable_impact'],
                'savings': 'N/A'
            }]
        
        try:
            workload_description = ' '.join(services)
            region_info = f"{best_region.get('region_name', 'Unknown')} with {best_region.get('market_based_intensity', 0)} kg CO2e/kWh"
            
            prompt = f"""Analyze this AWS workload and provide 3-4 specific sustainability optimization recommendations.
{t['lang_instruction']}

Workload: {workload_description}
Current Region: {region_info}
Services List: {services}

For each recommendation, suggest specific AWS services focusing on:
1. **Graviton processors**: Always recommend LATEST Graviton instances (c8g, r8g, m8g series) available in {region_info}. Compare current instances like c6i.8xlarge, r7i.8xlarge to c8g.8xlarge, r8g.8xlarge. Provide specific cost and performance savings.If unrelated, skip this part
2. **Trainium/Inferentia**: For ML workloads, recommend trn2, inf2 instances. Compare p4 GPU instances to Trainium alternatives if applicable. If unrelated, skip this part
3. **Serverless alternatives**: Lambda, Fargate, Aurora Serverless where applicable.If unrelated, skip this part.

Provide recommendations in this exact format (each title MUST start with an emoji, keep titles in English). For **savings** label, recommend a range that would suit, dont copy from the format:
🚀 Compute Optimization
Migrate to latest Graviton-based instances for better price-performance and lower carbon footprint.
{t['impact_label']}: High | {t['savings_label']}: 15-25%

⚡ Serverless Migration
Replace always-on EC2 instances with Lambda functions for event-driven workloads.
{t['impact_label']}: Medium | {t['savings_label']}: 30-50%

IMPORTANT: Each recommendation title MUST start with an emoji character. Keep titles in English. Descriptions can be in the requested language.
Provide 3-4 similar recommendations."""
            
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
            recommendations = self._parse_recommendations(ai_response, lang)
            return recommendations if recommendations else [{
                'type': 'AI',
                'title': t['fallback_title'],
                'description': ai_response,
                'impact': 'High',
                'savings': 'Variable'
            }]
                
        except Exception as e:
            return [{
                'type': 'Error',
                'title': t['error_failed_title'],
                'description': f'{t["error_failed_desc_prefix"]}{str(e)}',
                'impact': t['error_failed_impact'],
                'savings': 'N/A'
            }]
    
    def _parse_recommendations(self, text: str, lang: str = "en") -> List[Dict[str, str]]:
        """Parse structured text recommendations into list format"""
        t = _TEXTS.get(lang, _TEXTS["en"])
        recommendations = []
        lines = text.strip().split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect title: TITLE: prefix or short line starting with emoji
            is_title = False
            title_text = ''
            if line.startswith('TITLE:'):
                is_title = True
                title_text = line[6:].strip()
            elif len(line) < 60 and not line.startswith('Impact:') and not line.startswith('影響度:') and not line.startswith('DESCRIPTION:'):
                # Check if first char is actual emoji (not CJK/Japanese)
                first_char = ord(line[0]) if line else 0
                is_emoji = (0x1F300 <= first_char <= 0x1F9FF) or (0x2600 <= first_char <= 0x27BF) or (0x2B50 <= first_char <= 0x2B55)
                if is_emoji:
                    is_title = True
                    title_text = line
            
            if is_title:
                if current_rec.get('title'):
                    recommendations.append(current_rec)
                current_rec = {
                    'type': 'Optimization',
                    'title': title_text,
                    'description': '',
                    'impact': '',
                    'savings': 'Variable'
                }
            elif line.startswith('DESCRIPTION:'):
                if current_rec:
                    current_rec['description'] = line[12:].strip()
            elif line.startswith('Impact:') or line.startswith('影響度:'):
                prefix = '影響度:' if line.startswith('影響度:') else 'Impact:'
                rest = line[len(prefix):].strip()
                parts = rest.split('|')
                if parts:
                    current_rec['impact'] = parts[0].strip()
                if len(parts) >= 2:
                    savings_part = parts[1].strip()
                    for label in ['Savings:', '削減効果:']:
                        savings_part = savings_part.replace(label, '').strip()
                    current_rec['savings'] = savings_part
                # Store the raw Impact line to append at the end of description later
                if current_rec:
                    current_rec['_impact_line'] = line
            elif current_rec and current_rec.get('title') and not current_rec.get('description'):
                # Line after title is description (original format)
                current_rec['description'] = line
            elif current_rec and current_rec.get('description') and not line.startswith('Impact:') and not line.startswith('影響度:'):
                # Additional description lines
                current_rec['description'] += ' ' + line
        
        if current_rec.get('title'):
            recommendations.append(current_rec)

        # Append Impact/Savings line to end of description for each recommendation
        for rec in recommendations:
            impact_line = rec.pop('_impact_line', None)
            if impact_line:
                rec['description'] = rec['description'].rstrip() + ' **' + impact_line + '**'

        # Append programming language recommendation
        recommendations.append({
            'type': 'Programming',
            'title': t['prog_title'],
            'description': t['prog_desc'],
            'impact': 'Medium',
            'savings': 'Variable'
        })
        return recommendations
