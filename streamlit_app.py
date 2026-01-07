import streamlit as st
import pandas as pd
import json
from datetime import datetime
from src.greencloud_advisor import GreenCloudAdvisor
from src.aws_service_extractor import AWSServiceExtractor
from src.aws_live_checker import check_aws_service_availability_live
from src.ccft_chatbot import CCFTChatbot
from src.report_generator import CCFTReportGenerator
from src.aws_regions_fetcher import AWSRegionsFetcher
from src.sustainability_insights import SustainabilityInsights

# load css
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Then call it
load_css('css/styles.css')


# Page config
st.set_page_config(page_title="GreenCloud Advisor", page_icon="🌱", layout="wide")

st.title("🌱 GreenCloud Advisor")
st.subheader("AWS Region Sustainability Recommender")

# Initialize advisor and chatbot
@st.cache_resource
def load_advisor():
    return GreenCloudAdvisor()

@st.cache_resource
def load_chatbot():
    return CCFTChatbot()

@st.cache_resource
def load_report_generator():
    return CCFTReportGenerator()

advisor = load_advisor()
chatbot = load_chatbot()
report_gen = load_report_generator()


# Initialize session state for active tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Region Analysis"

# Custom tab buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🌍 Region Analysis", 
                 type="primary" if st.session_state.active_tab == "Region Analysis" else "secondary",
                 key="tab1_btn"):
        st.session_state.active_tab = "Region Analysis"
        st.rerun()
        
with col2:
    if st.button("📊 CCFT Report Analysis", 
                 type="primary" if st.session_state.active_tab == "CCFT Report Analysis" else "secondary",
                 key="tab2_btn"):
        st.session_state.active_tab = "CCFT Report Analysis"
        st.rerun()

st.divider()

if st.session_state.active_tab == "Region Analysis":
    st.header("🌍 Region Analysis Configuration")
    
    # Configuration in columns
    config_col1, config_col2 = st.columns([1, 1])
    
    with config_col1:
        # AWS Services input
        services_input = st.text_area(
            "AWS Services or Workload Description",
            placeholder="e.g., We need a web application with GPU instances for ML training, object storage for data, and a MySQL database",
            help="Describe your workload or list AWS services. AI will extract the services automatically.",
            value="I have an app with below details on AWS Creating a Web App —> Need EKS cluster with 5000 c6i.8xlarge RDS instance with Master and two replicas with size of each RDS node as r7i.8xlarge. It will also have 5 nodes if Redis Elaticache on top of RDS with size cache.m4.10xlarge. We will also be usng some p4 GPU isntances as well."
        )
        
        # Services will be extracted when analyze button is clicked
        required_services = []
    
    with config_col2:
        # Get regions dynamically from aws_regions_fetcher
        fetcher = AWSRegionsFetcher()
        regions = fetcher.get_aws_regions()
        region_options = [f"{region.code} ({region.name})" for region in regions]
        
        # Set specific default regions
        default_regions = []
        for region_option in region_options:
            if any(code in region_option for code in ['us-east-1', 'us-east-2', 'eu-south-1', 'eu-north-1']):
                default_regions.append(region_option)
        
        selected_regions = st.multiselect(
            "Potential AWS Regions",
            region_options,
            default=default_regions if default_regions else region_options[:3]
        )

    # Main content for Region Analysis
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:       
        analyze_button = st.button("🔍 Analyze Regions", type="primary")
    
    # Initialize session state for analysis results
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "analysis_params" not in st.session_state:
        st.session_state.analysis_params = None
    
    if analyze_button:
        # Clear previous results and set processing flag
        st.session_state.analysis_results = None
        st.session_state.analysis_params = None
        st.session_state.show_results = False
        
        if not services_input:
            st.warning("Please specify AWS services or workload description")
        elif not selected_regions:
            st.warning("Please select at least one potential region")
        else:
            try:          
                # Extract services from input using AI
                extractor = AWSServiceExtractor()
                required_services = extractor.extract_services(services_input)
                
                if required_services:
                    st.info(f"🤖 AI extracted services: {', '.join(required_services)}")
                else:
                    st.warning("No AWS services could be extracted from the description. Please be more specific.")
                    st.stop()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="custom-info">🔄 Starting analysis...</div>', unsafe_allow_html=True)
                
                    # Filter results to only selected regions
                    region_codes = [region.split(" ")[0] for region in selected_regions]
                    st.markdown(f'<div class="custom-info">🔍 Analyzing regions: {region_codes}</div>', unsafe_allow_html=True)
                
                    # Get all regions data for selected regions
                    all_regions_data = []
                    for region_code in region_codes:
                        st.markdown(f'<div class="custom-info">⚙️ Processing region: {region_code}</div>', unsafe_allow_html=True)
                        for region in advisor.regions:
                            if region.code == region_code:
                                st.markdown(f'<div class="custom-info">📊 Getting carbon intensity for {region_code}</div>', unsafe_allow_html=True)
                                location_based, market_based, sustainability_score = advisor.calculate_sustainability_score(region.code)
                            
                                st.markdown(f'<div class="custom-info">✅ Checking service availability for {region_code}</div>', unsafe_allow_html=True)
                                # Check service availability using live API
                                unavailable_services = []
                                for service in required_services:
                                    try:
                                        if not check_aws_service_availability_live(region.code, service):
                                            unavailable_services.append(service)
                                    except Exception as e:
                                        unavailable_services.append(f"{service} (API Error)")
                            
                                supports_all_services = len(unavailable_services) == 0
                            
                                all_regions_data.append({
                                    "region_code": region.code,
                                    "region_name": region.name,
                                    "location_based_intensity": location_based,
                                    "market_based_intensity": market_based,
                                    "sustainability_score": round(sustainability_score, 3),
                                    "supports_services": supports_all_services,
                                    "unavailable_services": unavailable_services
                                })
                                break
                
                    st.success(f"Analysis complete! Found {len(all_regions_data)} regions.")
                
                    # Store results in session state
                    st.session_state.analysis_results = all_regions_data
                    st.session_state.analysis_params = {
                        "required_services": required_services,
                        "selected_regions": selected_regions
                    }
                    st.session_state.show_results = True
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.stop()
    
    # Results container box - placed after debug statements
    results_container = st.container(border=False)
    
    # Display results from session state inside container
    with results_container:
        if st.session_state.get("show_results", False) and st.session_state.analysis_results:
            all_regions_data = st.session_state.analysis_results
            required_services = st.session_state.analysis_params["required_services"]
            
            # Sort by sustainability score
            all_regions_data.sort(key=lambda x: x["sustainability_score"])
            
            # Filter for service compatibility
            filtered_options = [region for region in all_regions_data if region["supports_services"]]
            
            # Always show service availability status for all selected regions
            st.subheader("🔍 Service Availability Check")
            
            for region in all_regions_data:
                if region["unavailable_services"]:
                    st.error(f"❌ **{region['region_name']} ({region['region_code']})**: Missing {', '.join(region['unavailable_services'])}")
                else:
                    st.success(f"✅ **{region['region_name']} ({region['region_code']})**: All services available")
            
            # Show sustainability analysis for supported regions
            if filtered_options:
                # Display recommendation
                best = filtered_options[0]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "🏆 Recommended Region",
                        f"{best['region_name']}",
                        f"{best['region_code']}"
                    )
                
                with col2:
                    st.metric(
                        "🌱 Market-based Intensity",
                        f"{round(best['market_based_intensity'], 2)} kg CO2e/kWh",
                        help=f"Market-based intensity: {round(best['market_based_intensity'], 2)} kg CO2e/kWh\n\nThis value represents the carbon intensity of electricity that AWS actually purchases, accounting for:\n• Renewable Energy Certificates (RECs)\n• Power Purchase Agreements (PPAs)\n• Direct renewable energy investments\n\nCalculated using WattTime API data and AWS sustainability commitments. Lower values indicate cleaner energy procurement."
                    )
                
                with col3:
                    # Find the region with lowest score for comparison
                    lowest_region = min(filtered_options, key=lambda x: x['sustainability_score'])
                    
                    st.metric(
                        "📊 Sustainability Score",
                        f"{best['sustainability_score']}",
                        help=f"Calculated as: (Market-based × 0.7) + (Location-based × 0.3)\n\nFormula: ({best['market_based_intensity']} × 0.7) + ({best['location_based_intensity']} × 0.3) = {best['sustainability_score']}\n\nLowest score region: {lowest_region['region_name']} ({lowest_region['sustainability_score']})"
                    )
                
                # Comparison table and chart in single row with colored containers
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    with st.container(border=True):
                        st.subheader("📊 Region Comparison")
                        df = pd.DataFrame(filtered_options)
                        df = df[['region_name', 'region_code', 
                                'location_based_intensity', 'market_based_intensity', 
                                'sustainability_score']]
                        df.columns = ['Region', 'Code',
                                     'Location-based (kg CO2e/kWh)', 'Market-based (kg CO2e/kWh)', 
                                     'Sustainability Score']
                        st.dataframe(df, width='stretch')
                
                with col2:
                    with st.container(border=True):
                        st.markdown("<h4 style='font-size: 18px;'>📈 Carbon Intensity Comparison</h4>", unsafe_allow_html=True)
                        chart_data = pd.DataFrame({
                            'Region': [opt['region_name'] for opt in filtered_options],
                            'Location-based': [opt['location_based_intensity'] for opt in filtered_options],
                            'Market-based': [opt['market_based_intensity'] for opt in filtered_options]
                        })
                        st.bar_chart(chart_data.set_index('Region'), height=300)
                
                # Analysis summary
                st.subheader("🎯 Key Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **Analysis Summary:**
                    - Evaluated {len(st.session_state.analysis_params["selected_regions"])} selected regions
                    - {len(filtered_options)} regions support your services
                    """)
                
                with col2:
                    # Calculate emission reduction between highest and lowest location-based scores
                    highest_location = max(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                    lowest_location = min(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                    emission_reduction = round(
                        (highest_location - lowest_location) / highest_location * 100, 1
                    )
                    
                    st.success(f"""
                    **Sustainability Benefits:**
                    - {emission_reduction}% emission reduction between highest and lowest regions
                    - Best region: {best['region_name']}
                    - Lowest carbon intensity: {best['market_based_intensity']} kg CO2e/kWh
                    """)
                
                # Sustainability Insights Widget
                st.subheader("💡 Optimization Recommendations")
                
                with st.spinner("Generating AI-powered recommendations..."):
                    insights_generator = SustainabilityInsights()
                    insights = insights_generator.generate_insights(required_services, best)
                
                for insight in insights:
                    with st.expander(f"{insight['title']}"):
                        st.write(insight['description'])
                
                # Download PDF Report
                st.divider()
                col1, col2, col3 = st.columns([2, 1, 1])
                with col3:
                    def create_analysis_pdf():
                        # Safety checks
                        if not filtered_options:
                            st.error("No data available for PDF generation")
                            return b""  # Return empty bytes
                        
                        from reportlab.lib.pagesizes import A4
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.lib.units import inch
                        from reportlab.lib import colors
                        from reportlab.graphics.shapes import Drawing, Rect
                        from reportlab.graphics.charts.barcharts import VerticalBarChart
                        from reportlab.graphics.charts.legends import Legend
                        import matplotlib.pyplot as plt
                        import io
                        
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
                        styles = getSampleStyleSheet()
                        story = []
                        
                        # Custom styles
                        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=20, textColor=colors.darkgreen)
                        header_style = ParagraphStyle('CustomHeader', parent=styles['Heading1'], fontSize=16, textColor=colors.darkblue, spaceBefore=15)
                        metric_style = ParagraphStyle('MetricStyle', parent=styles['Normal'], fontSize=12, textColor=colors.darkgreen, leftIndent=20)
                        
                        # Title with avatar
                        try:
                            avatar_img = Image("image/GreenCloudAdvisor_avatar.png", width=1*inch, height=1*inch)
                            title_table = Table([[
                                avatar_img,
                                Paragraph("<font color='green'></font> GreenCloud Advisor\n<font size=14>Region Analysis Report</font>", title_style)
                            ]], colWidths=[1.2*inch, 5*inch])
                            title_table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0)
                            ]))
                            story.append(title_table)
                        except:
                            story.append(Paragraph("<font color='green'></font> GreenCloud Advisor - Region Analysis Report", title_style))
                        
                        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
                        story.append(Spacer(1, 30))

                        # Add the workload description
                        story.append(Paragraph("<font color='blue'>📋</font> Workload Description", header_style))
                        story.append(Paragraph(services_input, styles['Normal']))
                        story.append(Spacer(1, 20))

                        # Add the selected AWS regions
                        story.append(Paragraph("<font color='blue'>🌍</font> Potential AWS Regions", header_style))
                        regions_text = ", ".join(selected_regions)
                        story.append(Paragraph(regions_text, styles['Normal']))
                        story.append(Spacer(1, 20))
                        
                        # Executive Summary Box
                        summary_data = [[
                            Paragraph("<font color='gold'>★</font> <b>Recommended Region</b>", metric_style),
                            Paragraph(f"<b>{best['region_name']} ({best['region_code']})</b>", styles['Normal'])
                        ], [
                            Paragraph("<font color='green'>♦</font> <b>Sustainability Score</b>", metric_style),
                            Paragraph(f"<b>{best['sustainability_score']}</b>", styles['Normal'])
                        ], [
                            Paragraph("<font color='blue'>▼</font> <b>Carbon Intensity</b>", metric_style),
                            Paragraph(f"<b>{round(best['market_based_intensity'], 3)} kg CO2e/kWh</b>", styles['Normal'])
                        ]]
                        
                        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                        summary_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
                        ]))
                        story.append(summary_table)
                        story.append(Spacer(1, 25))
                        
                        # Create Carbon Intensity Chart
                        def create_chart():
                            if not filtered_options:
                                return None
                            
                            fig, ax = plt.subplots(figsize=(8, 5))
                            chart_regions = filtered_options[:min(6, len(filtered_options))]
                            regions = [opt['region_name'] for opt in chart_regions]
                            location_based = [opt['location_based_intensity'] for opt in chart_regions]
                            market_based = [opt['market_based_intensity'] for opt in chart_regions]
                            
                            x = range(len(regions))
                            width = 0.35
                            
                            ax.bar([i - width/2 for i in x], location_based, width, label='Location-based', color="#583ecc", alpha=0.8)
                            ax.bar([i + width/2 for i in x], market_based, width, label='Market-based', color="#76769a", alpha=0.8)
                            
                            ax.set_xlabel('AWS Regions', fontsize=12)
                            ax.set_ylabel('Carbon Intensity (kg CO2e/kWh)', fontsize=12)
                            ax.set_title('Carbon Intensity Comparison', fontsize=14, fontweight='bold')
                            ax.set_xticks(x)
                            ax.set_xticklabels(regions, rotation=45, ha='right')
                            ax.legend()
                            ax.grid(True, alpha=0.3)
                            
                            plt.tight_layout()
                            chart_buffer = io.BytesIO()
                            plt.savefig(chart_buffer, format='png', dpi=150, bbox_inches='tight')
                            chart_buffer.seek(0)
                            plt.close()
                            return chart_buffer
                        
                        # Add chart to PDF
                        story.append(Paragraph("<font color='blue'>▲</font> Carbon Intensity Analysis", header_style))
                        chart_buffer = create_chart()
                        if chart_buffer:
                            chart_img = Image(chart_buffer, width=6*inch, height=3.75*inch)
                            story.append(chart_img)
                        else:
                            story.append(Paragraph("No data available for chart generation", styles['Normal']))
                        story.append(Spacer(1, 20))
                        
                        # Services Analysis with table structure
                        story.append(Paragraph("<font color='orange'>⚙</font> Required Services", header_style))
                        
                        if required_services:
                            # Create services table
                            services_data = [[Paragraph('<b><font color="orange">⚙</font> Service Name</b>', styles['Normal']),
                                            Paragraph('<b><font color="blue">●</font> Category</b>', styles['Normal'])]]
                            
                            # Map services to categories
                            service_categories = {
                                'EC2': 'Compute', 'ECS': 'Compute', 'EKS': 'Compute', 'Lambda': 'Compute',
                                'S3': 'Storage', 'EBS': 'Storage', 'EFS': 'Storage',
                                'RDS': 'Database', 'DynamoDB': 'Database', 'ElastiCache': 'Database',
                                'VPC': 'Networking', 'CloudFront': 'Networking', 'Route53': 'Networking',
                                'IAM': 'Security', 'KMS': 'Security', 'Secrets Manager': 'Security'
                            }
                            
                            for service in required_services:
                                category = service_categories.get(service, 'Other')
                                services_data.append([
                                    Paragraph(service, styles['Normal']),
                                    Paragraph(category, styles['Normal'])
                                ])
                            
                            services_table = Table(services_data, colWidths=[3*inch, 2*inch])
                            services_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkorange),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 9),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                            ]))
                            story.append(services_table)
                        else:
                            story.append(Paragraph("<b>Services:</b> No services specified", styles['Normal']))
                        
                        story.append(Spacer(1, 15))
                        
                        # Enhanced Region Comparison Table
                        story.append(Paragraph("<font color='purple'>■</font> Region Comparison Table", header_style))
                        table_data = [[
                            Paragraph('<b><font color="blue">●</font> Region</b>', styles['Normal']),
                            Paragraph('<b><font color="red">■</font> Code</b>', styles['Normal']),
                            Paragraph('<b><font color="orange">▲</font> Location-based</b>', styles['Normal']),
                            Paragraph('<b><font color="green">▼</font> Market-based</b>', styles['Normal']),
                            Paragraph('<b><font color="gold">★</font> Score</b>', styles['Normal'])
                        ]]
                        
                        for i, region in enumerate(filtered_options):
                            row_color = colors.lightgreen if i == 0 else colors.white
                            table_data.append([
                                region['region_name'],
                                region['region_code'],
                                f"{round(region['location_based_intensity'], 3)}",
                                f"{round(region['market_based_intensity'], 3)}",
                                f"{region['sustainability_score']}"
                            ])
                        
                        table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.8*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),  # Highlight best region
                            ('BACKGROUND', (0, 2), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                            ('FONTSIZE', (0, 1), (-1, -1), 8)
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 25))
                        
                        # Key Insights with icons
                        story.append(Paragraph("<font color='red'>◆</font> Key Insights", header_style))
                        # Calculate emission reduction between highest and lowest location-based scores
                        highest_location = max(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                        lowest_location = min(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                        emission_reduction = round((highest_location - lowest_location) / highest_location * 100, 1)
                        
                        insights_data = [[
                            Paragraph("<font color='blue'>▼</font> Emission Reduction:", styles['Normal']),
                            Paragraph(f"{emission_reduction}% with market-based accounting", styles['Normal'])
                        ], [
                            Paragraph("<font color='gold'>★</font> Best Region:", styles['Normal']),
                            Paragraph(f"{best['region_name']}", styles['Normal'])
                        ], [
                            Paragraph("<font color='green'>♦</font> Lowest Carbon Intensity:", styles['Normal']),
                            Paragraph(f"{best['market_based_intensity']} kg CO2e/kWh", styles['Normal'])
                        ]]
                        
                        insights_table = Table(insights_data, colWidths=[2.5*inch, 3*inch])
                        insights_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
                            ('GRID', (0, 0), (-1, -1), 1, colors.gold),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold')
                        ]))
                        story.append(insights_table)
                        story.append(Spacer(1, 20))
                        
                        # Optimization Recommendations with enhanced styling
                        story.append(Paragraph("<font color='yellow'>◆</font> Optimization Recommendations", header_style))
                        
                        # Create comprehensive recommendations table
                        rec_headers = [
                            Paragraph('<b><font color="red">◆</font> Recommendation</b>', styles['Normal']),
                            Paragraph('<b><font color="green">$</font> Potential Savings</b>', styles['Normal']),
                            Paragraph('<b><font color="orange">⚙</font> Implementation</b>', styles['Normal'])
                        ]
                        
                        rec_table_data = [rec_headers]
                        
                        for insight in (insights if insights else []):
                            # Extract potential savings from description
                            savings_text = "<font color='green'>$</font> Cost & Carbon Savings"
                            if 'cost' in insight['description'].lower():
                                savings_text = "<font color='green'>$$</font> Significant Cost Reduction"
                            elif 'carbon' in insight['description'].lower():
                                savings_text = "<font color='green'>♦</font> Carbon Footprint Reduction"
                            elif 'performance' in insight['description'].lower():
                                savings_text = "<font color='blue'>▲</font> Performance Optimization"
                            
                            rec_table_data.append([
                                Paragraph(f"<b>{insight['title']}</b>", styles['Normal']),
                                Paragraph(savings_text, styles['Normal']),
                                Paragraph(insight['description'], styles['Normal'])
                            ])
                        
                        rec_table = Table(rec_table_data, colWidths=[2.2*inch, 1.8*inch, 3*inch])
                        rec_table.setStyle(TableStyle([
                            # Header styling
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkred),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            
                            # Data rows styling
                            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.lightsteelblue),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                            
                            # Alternate row colors
                            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
                            ('BACKGROUND', (0, 3), (-1, 3), colors.lightblue),
                            ('BACKGROUND', (0, 5), (-1, 5), colors.lightblue)
                        ]))
                        story.append(rec_table)
                        story.append(Spacer(1, 15))
                        
                        # Add savings summary box
                        savings_data = [[
                            Paragraph("<font color='green'>$</font> <b>Estimated Annual Savings</b>", metric_style),
                            Paragraph("<font color='green'>♦</font> <b>Environmental Impact</b>", metric_style)
                        ], [
                            Paragraph("• Cost optimization: 15-30%\n• Resource efficiency: 20-40%\n• Operational savings: 10-25%", styles['Normal']),
                            Paragraph("• Carbon reduction: 25-50%\n• Energy efficiency: 30-60%\n• Sustainable operations", styles['Normal'])
                        ]]
                        
                        savings_table = Table(savings_data, colWidths=[3*inch, 3*inch])
                        savings_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.gold),
                            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
                            ('GRID', (0, 0), (-1, -1), 2, colors.orange),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
                        ]))
                        story.append(savings_table)
                        story.append(Spacer(1, 10))
                        
                        # Footer
                        story.append(Spacer(1, 30))
                        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1)
                        story.append(Paragraph("Generated by GreenCloud Advisor - AWS Region Sustainability Recommender", footer_style))
                        
                        try:
                            doc.build(story)
                            buffer.seek(0)
                            return buffer.getvalue()
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
                            # Return a minimal PDF
                            buffer = io.BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=A4)
                            simple_story = [Paragraph("Error generating detailed report", styles['Normal'])]
                            doc.build(simple_story)
                            buffer.seek(0)
                            return buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=create_analysis_pdf(),
                        file_name=f"GreenCloud_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
            else:
                st.warning("⚠️ No regions support all your required services. Consider modifying your requirements.")
        else:
            st.info("📊 Click 'Analyze Regions' to see sustainability analysis results here.")

elif st.session_state.active_tab == "CCFT Report Analysis":
    st.header("📊 CCFT Report Analysis & AI Assistant")
    
    # CCFT Report upload
    uploaded_file = st.file_uploader(
        "Upload CCFT Report",
        type=['csv', 'json'],
        help="Upload your AWS Customer Carbon Footprint Tool report for AI-powered analysis"
    )
    
    # Auto-switch to CCFT tab when file is uploaded
    if uploaded_file and st.session_state.active_tab != "CCFT Report Analysis":
        st.session_state.active_tab = "CCFT Report Analysis"
        st.rerun()
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Process CCFT data if uploaded
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                ccft_data = pd.read_csv(uploaded_file)
                st.success("✅ CCFT CSV report loaded successfully!")
            else:
                ccft_data = json.load(uploaded_file)
                st.success("✅ CCFT JSON report loaded successfully!")
            
            # Load data into chatbot
            chatbot.load_ccft_data(ccft_data)
            
            # Create two columns for data overview and chatbot
            overview_col, chat_col = st.columns([1, 1])
            
            with overview_col:
                st.subheader("📋 Report Overview")
                
                if isinstance(ccft_data, pd.DataFrame):
                    st.write(f"**Records:** {len(ccft_data)}")
                    st.write(f"**Columns:** {len(ccft_data.columns)}")
                    
                    # Show key metrics
                    carbon_cols = [col for col in ccft_data.columns if 'carbon' in col.lower() or 'co2' in col.lower() or 'emission' in col.lower()]
                    if carbon_cols:
                        total_emissions = ccft_data[carbon_cols[0]].sum()
                        st.metric("Total Emissions", f"{total_emissions:.2f} kg CO2e")
                    
                    if 'Region' in ccft_data.columns:
                        unique_regions = ccft_data['Region'].nunique()
                        st.metric("AWS Regions", unique_regions)
                    
                    # Data preview
                    with st.expander("📄 Data Preview"):
                        st.dataframe(ccft_data.head(5), width='stretch')
                
                # Initialize session state for insights
                if "show_insights_modal" not in st.session_state:
                    st.session_state.show_insights_modal = False
                if "insights_data" not in st.session_state:
                    st.session_state.insights_data = None
                
                # Get AI insights button
                btn_col1, btn_col2 = st.columns([2, 1])
                with btn_col2:
                    with st.form("ai_insights_form"):
                        insights_button = st.form_submit_button("🤖 Get AI Insights", type="primary")
                        st.markdown('<style>div[data-testid="stForm"] button { width: 150px !important; }</style>', unsafe_allow_html=True)
                
                if insights_button:
                    with st.spinner("Analyzing your CCFT data..."):
                        st.session_state.insights_data = chatbot.get_data_insights()
                        st.session_state.show_insights_modal = True
                
                # Show modal if flag is set
                if st.session_state.show_insights_modal and st.session_state.insights_data:
                    @st.dialog("🤖 AI Insights - Carbon Footprint Analysis", width="large")
                    def show_insights():
                        insights_data = st.session_state.insights_data
                        if isinstance(insights_data, dict):
                            # Display charts if available
                            charts = insights_data.get("charts", [])
                            if charts:
                                st.write("**📊 Generated Visualizations:**")
                                
                                # Display charts in 2x2 grid
                                for i in range(0, len(charts), 2):
                                    col1, col2 = st.columns(2)
                                    
                                    # First chart in row
                                    with col1:
                                        if i < len(charts):
                                            chart = charts[i]
                                            st.subheader(chart["title"])
                                            st.image(f"data:image/png;base64,{chart['image']}", width='stretch')
                                            if "description" in chart:
                                                st.caption(chart["description"])
                                    
                                    # Second chart in row
                                    with col2:
                                        if i + 1 < len(charts):
                                            chart = charts[i + 1]
                                            st.subheader(chart["title"])
                                            st.image(f"data:image/png;base64,{chart['image']}", width='stretch')
                                            if "description" in chart:
                                                st.caption(chart["description"])
                                    
                                    st.divider()
                            
                            # Display text insights if available
                            text_insights = insights_data.get("text", "")
                            if text_insights:
                                st.write("**🤖 AI Analysis:**")
                                formatted_text = text_insights.replace('\n\n', '\n').strip()
                                st.markdown(formatted_text)
                            
                            # Download AI Insights Report button
                            st.divider()
                            col1, col2 = st.columns([3, 1])
                            with col2:
                                # Create AI insights PDF
                                from reportlab.lib.pagesizes import A4
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
                                from reportlab.lib.styles import getSampleStyleSheet
                                from reportlab.lib.units import inch
                                import io
                                import base64
                                
                                def create_insights_pdf():
                                    buffer = io.BytesIO()
                                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                                    styles = getSampleStyleSheet()
                                    story = []
                                    
                                    # Title
                                    story.append(Paragraph("<font color='blue'>◆</font> AI Carbon Footprint Insights Report", styles['Title']))
                                    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
                                    story.append(Spacer(1, 20))
                                    
                                    # Add charts
                                    if charts:
                                        story.append(Paragraph("Generated Visualizations", styles['Heading1']))
                                        for chart in charts:
                                            story.append(Paragraph(chart['title'], styles['Heading2']))
                                            img_buffer = io.BytesIO(base64.b64decode(chart['image']))
                                            img = Image(img_buffer, width=6*inch, height=3.6*inch)
                                            story.append(img)
                                            if 'description' in chart:
                                                story.append(Paragraph(chart['description'], styles['Normal']))
                                            story.append(Spacer(1, 15))
                                    
                                    # Add AI analysis
                                    if text_insights:
                                        story.append(Paragraph("AI Analysis", styles['Heading1']))
                                        # Split text into paragraphs and format properly
                                        paragraphs = text_insights.split('\n\n')
                                        for para in paragraphs:
                                            if para.strip():
                                                # Handle bullet points and formatting
                                                formatted_para = para.strip().replace('\n', '<br/>')
                                                story.append(Paragraph(formatted_para, styles['Normal']))
                                                story.append(Spacer(1, 10))
                                    
                                    doc.build(story)
                                    buffer.seek(0)
                                    return buffer.getvalue()
                                
                                st.download_button(
                                    label="📥 Download report",
                                    data=create_insights_pdf(),
                                    file_name=f"AI_Insights_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    type="primary"
                                )
                        else:
                            st.write(insights_data)
                    
                    show_insights()
                    # Reset the flag after showing modal
                    st.session_state.show_insights_modal = False
            
            with chat_col:
                st.subheader("💬 Ask me about your carbon footprint")
                
                # Chat interface
                chat_container = st.container()
                
                # Display chat history
                with chat_container:
                    for i, (role, message) in enumerate(st.session_state.chat_history):
                        if role == "user":
                            st.write(f"**You:** {message}")
                        else:
                            st.write(f"**GreenCloudAdvisor:** {message}")
                        st.write("---")
                
                # Initialize text clearing flag
                if "clear_ccft_input" not in st.session_state:
                    st.session_state.clear_ccft_input = False
                
                # Chat input with form for Enter key support
                with st.form("chat_form"):
                    user_question = st.text_input(
                        "Ask about your CCFT data:",
                        placeholder="e.g., Which region has the highest emissions?",
                        key="ccft_chat_input",
                        value="" if st.session_state.clear_ccft_input else st.session_state.get("ccft_chat_input", "")
                    )
                    
                    send_button = st.form_submit_button("Send", type="primary")
                
                # Clear button outside form
                if st.button("Clear Chat"):
                    st.session_state.chat_history = []
                    st.session_state.clear_ccft_input = True
                
                if send_button and user_question:
                        with st.spinner("🤖 GreenCloudAdvisor is analyzing your CCFT data..."):
                            response = chatbot.chat(user_question)
                            st.session_state.chat_history.append(("user", user_question))
                            st.session_state.chat_history.append(("assistant", response))
                            st.session_state.clear_ccft_input = True
                        st.rerun()
                
                # Reset clear flag
                if st.session_state.clear_ccft_input:
                    st.session_state.clear_ccft_input = False
                
                # Suggested questions
                st.write("**💡 Suggested Questions:**")
                suggestions = [
                    "Which AWS region has the lowest carbon footprint?",
                    "What are my top 3 carbon emission sources?",
                    "How can I reduce my AWS carbon footprint?",
                    "Compare location-based vs market-based emissions",
                    "Which services should I optimize first?"
                ]
                
                for suggestion in suggestions:
                    if st.button(suggestion, key=f"suggest_{suggestion[:20]}"):
                        with st.spinner("🤖 GreenCloudAdvisor is analyzing your CCFT data..."):
                            response = chatbot.chat(suggestion)
                            st.session_state.chat_history.append(("user", suggestion))
                            st.session_state.chat_history.append(("assistant", response))
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error loading CCFT report: {e}")
    
    else:
        st.info("📤 Please upload your CCFT report (CSV or JSON format) to begin AI-powered analysis")
        
        # Show example and setup instructions
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Expected File Format")
            example_data = pd.DataFrame({
                'Region': ['us-east-1', 'eu-west-1', 'ap-southeast-1'],
                'Service': ['EC2', 'S3', 'RDS'],
                'Usage': [100, 50, 25],
                'Carbon_Emissions_kg': [45.2, 12.3, 8.7]
            })
            st.dataframe(example_data, width='stretch')
        
        with col2:
            st.subheader("💬 Generic Sustainability Assistant")
            st.write("**Don't have CCFT report? No problem! Ask general sustainability questions:**")
            
            # Initialize session state for generic chat history
            if "generic_chat_history" not in st.session_state:
                st.session_state.generic_chat_history = []
            
            # Generic chat interface
            generic_chat_container = st.container()
            
            # Display generic chat history
            with generic_chat_container:
                for i, (role, message) in enumerate(st.session_state.generic_chat_history):
                    if role == "user":
                        st.write(f"**You:** {message}")
                    else:
                        st.write(f"**GreenCloud Advisor:** {message}")
                    st.write("---")
            
            # Initialize text clearing flag for generic chat
            if "clear_generic_input" not in st.session_state:
                st.session_state.clear_generic_input = False
            
            # Generic chat input with form for Enter key support
            with st.form("generic_chat_form"):
                generic_question = st.text_input(
                    "Ask about AWS sustainability:",
                    placeholder="e.g., What are AWS sustainability best practices?",
                    key="generic_chat_input",
                    value="" if st.session_state.clear_generic_input else st.session_state.get("generic_chat_input", "")
                )
                
                generic_send_button = st.form_submit_button("Send", type="primary")
            
            # Clear button outside form
            if st.button("Clear Chat", key="generic_clear"):
                st.session_state.generic_chat_history = []
                st.session_state.clear_generic_input = True
            
            if generic_send_button and generic_question:
                with st.spinner("Thinking..."):
                    response = chatbot.chat(generic_question)
                    st.session_state.generic_chat_history.append(("user", generic_question))
                    st.session_state.generic_chat_history.append(("assistant", response))
                    st.session_state.clear_generic_input = True
            
            # Reset clear flag for generic chat
            if st.session_state.clear_generic_input:
                st.session_state.clear_generic_input = False
            
            # Generic suggested questions
            st.write("**💡 Suggested Questions:**")
            generic_suggestions = [
                "What are AWS sustainability best practices?",
                "How can I reduce my cloud carbon footprint?",
                "Which AWS regions are most sustainable?",
                "What is the AWS Well-Architected Sustainability Pillar?",
                "How does renewable energy affect cloud emissions?"
            ]
            
            for suggestion in generic_suggestions:
                if st.button(suggestion, key=f"generic_{suggestion[:20]}"):
                    with st.spinner("Thinking..."):
                        response = chatbot.chat(suggestion)
                        st.session_state.generic_chat_history.append(("user", suggestion))
                        st.session_state.generic_chat_history.append(("assistant", response))

# Footer
st.markdown("---")
st.markdown("*GreenCloud Advisor helps you balance proximity and sustainability in AWS region selection*")