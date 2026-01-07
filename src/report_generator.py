import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import io
import base64

class CCFTReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
    def generate_charts(self, data: pd.DataFrame):
        """Generate charts for the report"""
        charts = {}
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. LBM vs MBM by Service
        if 'Service' in data.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            service_data = data.groupby('Service')[['Location_Based_Emissions_kg', 'Market_Based_Emissions_kg']].sum()
            service_data.plot(kind='bar', ax=ax, color=['#ff7f0e', '#2ca02c'])
            ax.set_title('Location-Based vs Market-Based Emissions by Service', fontsize=14, fontweight='bold')
            ax.set_ylabel('Emissions (kg CO2e)')
            ax.legend(['Location-Based Method (LBM)', 'Market-Based Method (MBM)'])
            plt.xticks(rotation=45)
            plt.tight_layout()
            charts['service_comparison'] = self._fig_to_base64(fig)
            plt.close()
        
        # 2. Regional Emissions
        if 'Region' in data.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            region_data = data.groupby('Region')['Market_Based_Emissions_kg'].sum().sort_values(ascending=False)
            region_data.plot(kind='bar', ax=ax, color='#1f77b4')
            ax.set_title('Market-Based Emissions by AWS Region', fontsize=14, fontweight='bold')
            ax.set_ylabel('Emissions (kg CO2e)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            charts['regional_emissions'] = self._fig_to_base64(fig)
            plt.close()
        
        # 3. Monthly Trend (if Date column exists)
        if 'Date' in data.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            data['Date'] = pd.to_datetime(data['Date'])
            monthly_data = data.groupby(data['Date'].dt.to_period('M'))[['Location_Based_Emissions_kg', 'Market_Based_Emissions_kg']].sum()
            monthly_data.plot(ax=ax, marker='o', linewidth=2)
            ax.set_title('Monthly Emissions Trend', fontsize=14, fontweight='bold')
            ax.set_ylabel('Emissions (kg CO2e)')
            ax.legend(['Location-Based Method', 'Market-Based Method'])
            plt.tight_layout()
            charts['monthly_trend'] = self._fig_to_base64(fig)
            plt.close()
        
        return charts
    
    def _fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string"""
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        return img_str
    
    def generate_summary_stats(self, data: pd.DataFrame):
        """Generate summary statistics"""
        stats = {}
        
        # Total emissions
        if 'Location_Based_Emissions_kg' in data.columns:
            stats['total_lbm'] = data['Location_Based_Emissions_kg'].sum()
        if 'Market_Based_Emissions_kg' in data.columns:
            stats['total_mbm'] = data['Market_Based_Emissions_kg'].sum()
        
        # Reduction percentage
        if 'total_lbm' in stats and 'total_mbm' in stats:
            stats['reduction_pct'] = ((stats['total_lbm'] - stats['total_mbm']) / stats['total_lbm'] * 100)
        
        # Top emitting service
        if 'Service' in data.columns and 'Market_Based_Emissions_kg' in data.columns:
            top_service = data.groupby('Service')['Market_Based_Emissions_kg'].sum().idxmax()
            stats['top_service'] = top_service
        
        # Top emitting region
        if 'Region' in data.columns and 'Market_Based_Emissions_kg' in data.columns:
            top_region = data.groupby('Region')['Market_Based_Emissions_kg'].sum().idxmax()
            stats['top_region'] = top_region
        
        return stats
    
    def create_html_report(self, data: pd.DataFrame, charts: dict, stats: dict):
        """Create HTML report for preview"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AWS Carbon Footprint Executive Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; color: #232F3E; }}
                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #FF9900; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                .chart {{ text-align: center; margin: 30px 0; }}
                .chart img {{ max-width: 100%; height: auto; }}
                .ghg-section {{ background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 AWS Carbon Footprint Executive Report</h1>
                <p>Generated on {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <div class="metric-value">{stats.get('total_mbm', 0):.1f}</div>
                    <div class="metric-label">Total MBM Emissions (kg CO2e)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{stats.get('reduction_pct', 0):.1f}%</div>
                    <div class="metric-label">Reduction vs LBM</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{stats.get('top_service', 'N/A')}</div>
                    <div class="metric-label">Highest Emitting Service</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{stats.get('top_region', 'N/A')}</div>
                    <div class="metric-label">Highest Emitting Region</div>
                </div>
            </div>
            
            <div class="ghg-section">
                <h2>🏛️ GHG Protocol Compliance</h2>
                <p><strong>Scope 2 Emissions Reporting:</strong></p>
                <ul>
                    <li><strong>Location-Based Method (LBM):</strong> {stats.get('total_lbm', 0):.1f} kg CO2e - Uses average emission factors for electricity grids</li>
                    <li><strong>Market-Based Method (MBM):</strong> {stats.get('total_mbm', 0):.1f} kg CO2e - Reflects contractual arrangements and renewable energy purchases</li>
                </ul>
                <p><strong>Recommendation:</strong> Report both methods as per GHG Protocol requirements. AWS renewable energy investments result in {stats.get('reduction_pct', 0):.1f}% lower emissions using MBM.</p>
            </div>
        """
        
        # Add charts
        for chart_name, chart_data in charts.items():
            html += f"""
            <div class="chart">
                <img src="data:image/png;base64,{chart_data}" alt="{chart_name}">
            </div>
            """
        
        html += """
            <div style="margin-top: 40px; padding: 20px; background: #f0f0f0; border-radius: 8px;">
                <h3>Key Recommendations</h3>
                <ul>
                    <li>Focus optimization efforts on highest emitting services and regions</li>
                    <li>Consider migrating workloads to regions with lower carbon intensity</li>
                    <li>Implement AWS sustainability best practices and right-sizing</li>
                    <li>Continue monitoring both LBM and MBM metrics for comprehensive reporting</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_pdf_report(self, data: pd.DataFrame, charts: dict, stats: dict):
        """Create PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=self.styles['Heading1'], 
                                   fontSize=18, spaceAfter=30, alignment=1)
        story.append(Paragraph("🌱 AWS Carbon Footprint Executive Report", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['Heading2']))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total MBM Emissions', f"{stats.get('total_mbm', 0):.1f} kg CO2e"],
            ['Total LBM Emissions', f"{stats.get('total_lbm', 0):.1f} kg CO2e"],
            ['Reduction vs LBM', f"{stats.get('reduction_pct', 0):.1f}%"],
            ['Top Emitting Service', stats.get('top_service', 'N/A')],
            ['Top Emitting Region', stats.get('top_region', 'N/A')]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # GHG Protocol Section
        story.append(Paragraph("GHG Protocol Compliance", self.styles['Heading2']))
        ghg_text = f"""
        <b>Scope 2 Emissions Reporting:</b><br/>
        • <b>Location-Based Method (LBM):</b> {stats.get('total_lbm', 0):.1f} kg CO2e - Uses average emission factors for electricity grids<br/>
        • <b>Market-Based Method (MBM):</b> {stats.get('total_mbm', 0):.1f} kg CO2e - Reflects contractual arrangements and renewable energy purchases<br/><br/>
        <b>Recommendation:</b> Report both methods as per GHG Protocol requirements. AWS renewable energy investments result in {stats.get('reduction_pct', 0):.1f}% lower emissions using MBM.
        """
        story.append(Paragraph(ghg_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add charts as images
        for chart_name, chart_data in charts.items():
            img_buffer = io.BytesIO(base64.b64decode(chart_data))
            img = Image(img_buffer, width=6*inch, height=3.6*inch)
            story.append(img)
            story.append(Spacer(1, 10))
        
        # Recommendations
        story.append(Paragraph("Key Recommendations", self.styles['Heading2']))
        recommendations = """
        • Focus optimization efforts on highest emitting services and regions<br/>
        • Consider migrating workloads to regions with lower carbon intensity<br/>
        • Implement AWS sustainability best practices and right-sizing<br/>
        • Continue monitoring both LBM and MBM metrics for comprehensive reporting
        """
        story.append(Paragraph(recommendations, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_report(self, data: pd.DataFrame):
        """Generate complete report with charts and statistics"""
        charts = self.generate_charts(data)
        stats = self.generate_summary_stats(data)
        html_report = self.create_html_report(data, charts, stats)
        pdf_report = self.create_pdf_report(data, charts, stats)
        
        return {
            'html': html_report,
            'pdf': pdf_report,
            'charts': charts,
            'stats': stats
        }