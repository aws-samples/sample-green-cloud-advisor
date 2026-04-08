import boto3
import json
import os
import pandas as pd
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io
import base64

class CCFTChatbot:
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize CCFT Chatbot with Bedrock Nova Pro"""
        self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
        self.model_id = "us.amazon.nova-pro-v1:0"
        self.ccft_data = None
        self.data_summary = ""
    
    def load_ccft_data(self, data: Any) -> None:
        """Load CCFT data for analysis"""
        self.ccft_data = data
        self.data_summary = self._generate_data_summary()
    
    def _generate_data_summary(self) -> str:
        """Generate a summary of the CCFT data"""
        if self.ccft_data is None:
            return "No CCFT data loaded."
        
        if isinstance(self.ccft_data, pd.DataFrame):
            # Use actual CCFT column names
            date_range = "N/A"
            if 'usage_month' in self.ccft_data.columns:
                date_range = f"{self.ccft_data['usage_month'].min()} to {self.ccft_data['usage_month'].max()}"
            
            summary = f"""
CCFT Data Summary:
- Total records: {len(self.ccft_data)}
- Columns: {', '.join(self.ccft_data.columns)}
- Date range: {date_range}
"""
            
            # Add regional breakdown using 'location' column
            if 'location' in self.ccft_data.columns:
                regions = self.ccft_data['location'].value_counts()
                summary += f"\nTop Regions: {', '.join(regions.index[:5])}"
            
            if 'product_code' in self.ccft_data.columns:
                services = self.ccft_data['product_code'].value_counts()
                summary += f"\nTop Services: {', '.join(services.index[:5])}"
            
            if 'total_mbm_emissions_value' in self.ccft_data.columns:
                mbm_total = self.ccft_data['total_mbm_emissions_value'].sum()
                summary += f"\nTotal MBM emissions: {mbm_total:.2f} MTCO2e"
            
            if 'total_lbm_emissions_value' in self.ccft_data.columns:
                lbm_total = self.ccft_data['total_lbm_emissions_value'].sum()
                summary += f"\nTotal LBM emissions: {lbm_total:.2f} MTCO2e"
            
            return summary
        
        elif isinstance(self.ccft_data, dict):
            return f"CCFT JSON data with keys: {', '.join(self.ccft_data.keys())}"
        
        return "CCFT data format not recognized."
    
    def chat(self, user_message: str) -> str:
        """Chat with Claude about CCFT data"""
        try:
            data_context = ""
            if self.ccft_data is not None and isinstance(self.ccft_data, pd.DataFrame):
                data_context = f"\n\nActual CCFT Data Sample:\n{self.ccft_data.head(5).to_string()}\n\nData Summary:\n{self.data_summary}"
            
            system_prompt = f"""You are an AWS sustainability expert analyzing Customer Carbon Footprint Tool (CCFT) data. 

Your role:
- Answer questions about AWS carbon emissions and sustainability
- Analyze the provided CCFT data
- Provide insights on carbon footprint optimization
- Suggest AWS regions and services for better sustainability
- Explain carbon accounting methodologies (location-based vs market-based)
- Use Amazon Sustainability pillar to understand customer workload and offer suggestions

Keep responses concise and actionable. Focus on sustainability insights and recommendations.{data_context}"""

            full_message = user_message
            if self.ccft_data is not None and isinstance(self.ccft_data, pd.DataFrame):
                # Include the complete dataset for Nova to analyze
                full_message += f"\n\nComplete CCFT Dataset:\n{self.ccft_data.to_string()}"
            
            messages = [
                {
                    "role": "user",
                    "content": [{"text": full_message}]
                }
            ]
            
            body = {
                "system": [{"text": system_prompt}],
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": 2000,
                    "temperature": 0.1
                }
            }
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}. Please check your AWS credentials and Bedrock access."
    
    def get_data_insights(self, lang: str = "en") -> Dict[str, Any]:
        """Get automated insights about the CCFT data with visualizations"""
        if self.ccft_data is None:
            return {"text": "No CCFT data loaded for analysis.", "charts": []}
        
        # i18n: Load chart texts and setup font
        _locale_path = os.path.join(os.path.dirname(__file__), '..', 'locales', f'{lang}.json')
        with open(_locale_path, 'r', encoding='utf-8') as f:
            _all_texts = json.load(f)
        # Map chart keys (prefixed with chart_) to short keys for convenience
        t = {k[6:]: v for k, v in _all_texts.items() if k.startswith('chart_')}

        font_prop = None
        if lang == "ja":
            for fp in ['/Library/Fonts/Arial Unicode.ttf', '/System/Library/Fonts/Arial Unicode.ttf',
                       '/usr/share/fonts/truetype/notosansjp/NotoSansJP-Regular.ttf',
                       '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                       '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
                if os.path.exists(fp):
                    try:
                        fm.fontManager.addfont(fp)
                        prop = fm.FontProperties(fname=fp)
                        plt.rcParams['font.family'] = 'sans-serif'
                        plt.rcParams['font.sans-serif'] = [prop.get_name()] + plt.rcParams.get('font.sans-serif', [])
                        plt.rcParams['axes.unicode_minus'] = False
                        font_prop = prop
                        break
                    except Exception:
                        continue
        fp_kw = {"fontproperties": font_prop} if font_prop else {}
        
        charts = []
        
        if isinstance(self.ccft_data, pd.DataFrame):
            plt.style.use('default')
            print(f"Available columns: {list(self.ccft_data.columns)}")
            
            # Chart 1: Service emissions
            if 'product_code' in self.ccft_data.columns and 'total_mbm_emissions_value' in self.ccft_data.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                service_data = self.ccft_data.groupby('product_code')['total_mbm_emissions_value'].sum().sort_values(ascending=False)
                # Filter out services with zero or very small emissions
                service_data = service_data[service_data > 0.001]
                print(f"Service data for chart: {service_data}")
                
                if len(service_data) > 0:
                    service_data.plot(kind='bar', ax=ax, color='skyblue')
                    ax.set_title(t["svc_title"], fontsize=14, fontweight='bold', **fp_kw)
                    ax.set_xlabel(t["svc_xlabel"], **fp_kw)
                    ax.set_ylabel(t["svc_ylabel"], **fp_kw)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    img_str = base64.b64encode(img_buffer.getvalue()).decode()
                    charts.append({"title": "Carbon Emissions by Service", "image": img_str, "description": "This chart shows AWS services ranked by their market-based carbon emissions, helping identify the highest impact services."})
                plt.close()
            
            # Chart 2: Regional emissions using total_mbm_emissions_value
            if 'location' in self.ccft_data.columns and 'total_mbm_emissions_value' in self.ccft_data.columns:
                fig, ax = plt.subplots(figsize=(12, 6))
                region_data = self.ccft_data.groupby('location')['total_mbm_emissions_value'].sum().sort_values(ascending=True)
                # Filter out regions with zero emissions
                region_data = region_data[region_data > 0]
                region_data.plot(kind='barh', ax=ax, color='lightgreen')
                ax.set_title('AWS Regions by Carbon Emissions (MBM)', fontsize=14, fontweight='bold')
                ax.set_xlabel('CO2 Emissions (MTCO2e)')
                ax.set_ylabel('AWS Regions')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                img_buffer.seek(0)
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                charts.append({"title": "Carbon Emissions by Region", "image": img_str, "description": "This horizontal bar chart displays AWS regions with carbon emissions, ordered from lowest to highest (regions with zero emissions are excluded)."})
                plt.close()
            

            
            # Chart 3: LBM vs MBM comparison
            if 'total_lbm_emissions_value' in self.ccft_data.columns and 'total_mbm_emissions_value' in self.ccft_data.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                lbm_total = self.ccft_data['total_lbm_emissions_value'].sum()
                mbm_total = self.ccft_data['total_mbm_emissions_value'].sum()
                
                methods = ['Location-Based Method', 'Market-Based Method']
                values = [lbm_total, mbm_total]
                colors = ['#ff7f0e', '#2ca02c']
                
                bars = ax.bar(methods, values, color=colors)
                ax.set_title('Total Emissions: LBM vs MBM Comparison', fontsize=14, fontweight='bold')
                ax.set_ylabel('CO2 Emissions (MTCO2e)')
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                           f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                img_buffer.seek(0)
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                charts.append({"title": t["compare_chart_title"], "image": img_str, "description": t["compare_desc"]})
                plt.close()
            
            # Chart 4: Monthly emissions trend
            if 'usage_month' in self.ccft_data.columns and 'total_mbm_emissions_value' in self.ccft_data.columns:
                fig, ax = plt.subplots(figsize=(12, 6))
                monthly_data = self.ccft_data.groupby('usage_month')['total_mbm_emissions_value'].sum().sort_index()
                
                ax.plot(monthly_data.index, monthly_data.values, marker='o', linewidth=2, markersize=6, color='#1f77b4')
                ax.fill_between(monthly_data.index, monthly_data.values, alpha=0.3, color='#1f77b4')
                ax.set_title(t["trend_title"], fontsize=14, fontweight='bold', **fp_kw)
                ax.set_xlabel(t["trend_xlabel"], **fp_kw)
                ax.set_ylabel(t["trend_ylabel"], **fp_kw)
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                img_buffer.seek(0)
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                charts.append({"title": t["trend_chart_title"], "image": img_str, "description": t["trend_desc"]})
                plt.close()
        
        # Ask Claude to generate a professional summary
        if isinstance(self.ccft_data, pd.DataFrame):
            region_analysis = self.ccft_data.groupby('location')['total_mbm_emissions_value'].sum().sort_values(ascending=False)
            service_analysis = self.ccft_data.groupby('product_code')['total_mbm_emissions_value'].sum().sort_values(ascending=False)
            lbm_total = self.ccft_data['total_lbm_emissions_value'].sum()
            mbm_total = self.ccft_data['total_mbm_emissions_value'].sum()
            
            summary_prompt = f"""Generate a professional executive summary of this AWS CCFT report using the actual data provided:

Actual Data Analysis:
- Total LBM Emissions: {lbm_total:.2f} MTCO2e
- Total MBM Emissions: {mbm_total:.2f} MTCO2e
- Top 5 Regions by Emissions: {region_analysis.head().to_string()}
- Top 5 Services by Emissions: {service_analysis.head().to_string()}
- Date Range: {self.ccft_data['usage_month'].min()} to {self.ccft_data['usage_month'].max()}

Include:
1. Executive Overview 
2. Top 3 AWS Services by actual emission values
3. Regional Analysis with specific numbers
4. LBM vs MBM Analysis with percentage difference
5. Key Findings from the actual data
6. Give real-world comparison like two way air trips between Bagalore to Deli in India, two way car trips between Bagalore to Deli in India and electricity consumption per house in Bangalore with respective flight, car and house icons as bullet points. 

Use professional business language with specific numbers from the data. {t['summary_lang_instruction']}"""
        else:
            summary_prompt = "Generate a professional executive summary noting that CCFT data format is not recognized for detailed analysis."
        
        text_insights = self.chat(summary_prompt)
        
        print(f"Total charts generated: {len(charts)}")
        if len(charts) == 0:
            print("No charts were generated. Check data columns and values.")
        return {"text": text_insights, "charts": charts}
