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

# Page config - MUST be first Streamlit command
st.set_page_config(page_title="GreenCloud Advisor", page_icon="🌱", layout="wide")

# load css
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Then call it
load_css('css/styles.css')

# Load locale texts from external JSON files
import json as _json
import os as _os

def _load_locales():
    locales_dir = _os.path.join(_os.path.dirname(__file__), 'locales')
    texts = {}
    for lang_code in ['en', 'ja']:
        filepath = _os.path.join(locales_dir, f'{lang_code}.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            texts[lang_code] = _json.load(f)
    return texts

TEXTS = _load_locales()

# Initialize language session state
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# CSS for language switcher button
st.markdown("""
<style>
.lang-switcher {
    position: fixed;
    top: 14px;
    right: 60px;
    z-index: 9999;
    background: white;
    border-radius: 20px;
    padding: 2px 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

# Language switcher button (right side of title)
title_col, lang_col = st.columns([8, 1])
with title_col:
    st.title("🌱 GreenCloud Advisor")
with lang_col:
    st.write("")
    current = st.session_state.lang
    label = "🇺🇸 EN" if current == "ja" else "🇯🇵 JA"
    if st.button(label, key="lang_btn"):
        st.session_state.lang = "en" if current == "ja" else "ja"
        st.rerun()

T = TEXTS[st.session_state.lang]
st.subheader(T["subtitle"])

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
    if st.button(T["tab_region"], 
                 type="primary" if st.session_state.active_tab == "Region Analysis" else "secondary",
                 key="tab1_btn"):
        st.session_state.active_tab = "Region Analysis"
        st.rerun()
        
with col2:
    if st.button(T["tab_ccft"], 
                 type="primary" if st.session_state.active_tab == "CCFT Report Analysis" else "secondary",
                 key="tab2_btn"):
        st.session_state.active_tab = "CCFT Report Analysis"
        st.rerun()

st.divider()

if st.session_state.active_tab == "Region Analysis":
    st.header(T["header_region"])
    
    # Configuration in columns
    config_col1, config_col2 = st.columns([1, 1])
    
    with config_col1:
        # AWS Services input
        services_input = st.text_area(
            T["label_services"],
            placeholder=T["placeholder_services"],
            help=T["help_services"],
            value=T["sample_workload"]
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
            T["label_regions"],
            region_options,
            default=default_regions if default_regions else region_options[:3]
        )

    # Main content for Region Analysis
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:       
        analyze_button = st.button(T["btn_analyze"], type="primary")
    
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
            st.warning(T["warn_no_services"])
        elif not selected_regions:
            st.warning(T["warn_no_regions"])
        else:
            try:          
                extractor = AWSServiceExtractor()
                required_services = extractor.extract_services(services_input)
                
                if required_services:
                    st.info(T["info_extracted"] + ', '.join(required_services))
                else:
                    st.warning(T["warn_no_extract"])
                    st.stop()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<div class="custom-info">{T["status_starting"]}</div>', unsafe_allow_html=True)
                
                    region_codes = [region.split(" ")[0] for region in selected_regions]
                    st.markdown(f'<div class="custom-info">{T["status_analyzing"]}{region_codes}</div>', unsafe_allow_html=True)
                
                    all_regions_data = []
                    for region_code in region_codes:
                        st.markdown(f'<div class="custom-info">{T["status_processing"]}{region_code}</div>', unsafe_allow_html=True)
                        for region in advisor.regions:
                            if region.code == region_code:
                                st.markdown(f'<div class="custom-info">{T["status_carbon"]}{region_code}</div>', unsafe_allow_html=True)
                                location_based = advisor.calculate_location_based_score(region.code)
                            
                                st.markdown(f'<div class="custom-info">{T["status_checking"]}{region_code}</div>', unsafe_allow_html=True)
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
                                    "supports_services": supports_all_services,
                                    "unavailable_services": unavailable_services
                                })
                                break
                
                    st.success(T["status_complete"] + str(len(all_regions_data)) + T["status_complete2"])
                
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
    results_container = st.container()
    
    # Display results from session state inside container
    with results_container:
        if st.session_state.get("show_results", False) and st.session_state.analysis_results:
            all_regions_data = st.session_state.analysis_results
            required_services = st.session_state.analysis_params["required_services"]
            
            # Sort by location_based_intensity (lower is better)
            all_regions_data.sort(key=lambda x: x["location_based_intensity"])
            
            # Filter for service compatibility
            filtered_options = [region for region in all_regions_data if region["supports_services"]]
            
            st.subheader(T["result_availability"])
            
            for region in all_regions_data:
                if region["unavailable_services"]:
                    st.error(f"❌ **{region['region_name']} ({region['region_code']})**: {T['result_missing']}{', '.join(region['unavailable_services'])}")
                else:
                    st.success(f"✅ **{region['region_name']} ({region['region_code']})**: {T['result_all_ok']}")
            
            # Show sustainability analysis for supported regions
            if filtered_options:
                # Display recommendation
                best = filtered_options[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        T["result_recommended"],
                        f"{best['region_name']}",
                        f"{best['region_code']}"
                    )
                
                with col2:
                    st.metric(
                        T["result_carbon"],
                        f"{round(best['location_based_intensity'], 3)} kg CO2e/kWh",
                        help=T["result_carbon_help"]
                    )
                
                # Comparison table and chart in single row with colored containers
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    with st.container(border=True):
                        st.subheader(T["result_comparison"])
                        df = pd.DataFrame(filtered_options)
                        df = df[['region_name', 'region_code', 'location_based_intensity']]
                        df.columns = [T["result_col_region"], T["result_col_code"], T["result_col_carbon"]]
                        st.dataframe(df, width='stretch')
                
                with col2:
                    with st.container(border=True):
                        st.markdown(f"<h4 style='font-size: 18px;'>{T['result_chart_title']}</h4>", unsafe_allow_html=True)
                        chart_data = pd.DataFrame({
                            T["result_col_region"]: [opt['region_name'] for opt in filtered_options],
                            T["result_chart_col"]: [opt['location_based_intensity'] for opt in filtered_options]
                        })
                        st.bar_chart(chart_data.set_index(T["result_col_region"]), height=300)
                
                st.subheader(T["result_insights"])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    {T["result_summary_title"]}
                    - {T["result_summary_evaluated"]}{len(st.session_state.analysis_params["selected_regions"])}{T["result_summary_regions"]}
                    - {len(filtered_options)}{T["result_summary_support"]}
                    """)
                
                with col2:
                    # Calculate emission reduction between highest and lowest location-based scores
                    highest_location = max(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                    lowest_location = min(filtered_options, key=lambda x: x['location_based_intensity'])['location_based_intensity']
                    emission_reduction = round(
                        (highest_location - lowest_location) / highest_location * 100, 1
                    )
                    
                    st.success(f"""
                    {T["result_benefits_title"]}
                    - {emission_reduction}{T["result_benefits_reduction"]}
                    - {T["result_benefits_best"]}{best['region_name']}
                    - {T["result_benefits_carbon"]}{best['location_based_intensity']} kg CO2e/kWh
                    """)
                
                st.subheader(T["result_opt_title"])
                
                with st.spinner(T["result_opt_spinner"]):
                    insights_generator = SustainabilityInsights()
                    insights = insights_generator.generate_insights(required_services, best, lang=st.session_state.lang)
                
                for insight in insights:
                    with st.expander(f"{insight['title']}"):
                        st.write(insight['description'])
                
                # Download PDF Report
                st.divider()
                col1, col2, col3 = st.columns([2, 1, 1])
                with col3:
                    def create_analysis_pdf():
                        # Remove emoji characters not supported by PDF fonts
                        import re
                        def _strip_emoji(text):
                            return re.sub(
                                r'[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0000200D\U00002600-\U000026FF]',
                                '', text).strip()

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
                        from reportlab.pdfbase import pdfmetrics
                        from reportlab.pdfbase.ttfonts import TTFont
                        import matplotlib.pyplot as plt
                        import matplotlib
                        import io
                        import os

                        # Japanese font setup
                        is_ja = st.session_state.lang == "ja"
                        font_name = 'Helvetica'
                        bold_font_name = 'Helvetica-Bold'

                        if is_ja:
                            # Try available fonts for macOS/Linux/Docker
                            jp_font_candidates = [
                                ('/Library/Fonts/Arial Unicode.ttf', None, 'Arial Unicode MS'),
                                ('/System/Library/Fonts/Arial Unicode.ttf', None, 'Arial Unicode MS'),
                                ('/usr/share/fonts/truetype/notosansjp/NotoSansJP-Regular.ttf', None, 'Noto Sans JP'),
                                ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 0, 'Noto Sans CJK JP'),
                                ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0, 'Noto Sans CJK JP'),
                            ]
                            for fp, subfont_idx, mpl_font_name in jp_font_candidates:
                                if os.path.exists(fp):
                                    try:
                                        if subfont_idx is not None:
                                            pdfmetrics.registerFont(TTFont('JpFont', fp, subfontIndex=subfont_idx))
                                        else:
                                            pdfmetrics.registerFont(TTFont('JpFont', fp))
                                        font_name = 'JpFont'
                                        bold_font_name = 'JpFont'
                                        matplotlib.rcParams['font.family'] = mpl_font_name
                                    except Exception:
                                        continue
                                    break
                        
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
                        styles = getSampleStyleSheet()
                        story = []
                        
                        # Custom styles with font applied
                        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=20, textColor=colors.darkgreen, fontName=font_name)
                        header_style = ParagraphStyle('CustomHeader', parent=styles['Heading1'], fontSize=16, textColor=colors.darkblue, spaceBefore=15, fontName=font_name)
                        metric_style = ParagraphStyle('MetricStyle', parent=styles['Normal'], fontSize=12, textColor=colors.darkgreen, leftIndent=20, fontName=font_name)
                        normal_style = ParagraphStyle('NormalJp', parent=styles['Normal'], fontName=font_name)
                        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1, fontName=font_name)

                        # Load PDF text definitions from locales
                        import json as _json
                        _locale_path = os.path.join(os.path.dirname(__file__), 'locales', f'{st.session_state.lang}.json')
                        with open(_locale_path, 'r', encoding='utf-8') as f:
                            _all = _json.load(f)
                        _pt = {k: v for k, v in _all.items() if k.startswith('pdf_')}

                        pdf_title       = _pt["pdf_title"]
                        pdf_generated   = _pt["pdf_generated_prefix"] + datetime.now().strftime(_pt["pdf_generated_fmt"])
                        pdf_workload    = _pt["pdf_workload"]
                        pdf_regions     = _pt["pdf_regions"]
                        pdf_rec_region  = _pt["pdf_rec_region"]
                        pdf_carbon      = _pt["pdf_carbon"]
                        pdf_chart_title = _pt["pdf_chart_title"]
                        pdf_chart_label_x = _pt["pdf_chart_label_x"]
                        pdf_chart_label_y = _pt["pdf_chart_label_y"]
                        pdf_chart_legend  = _pt["pdf_chart_legend"]
                        pdf_chart_comp    = _pt["pdf_chart_comp"]
                        pdf_services    = _pt["pdf_services"]
                        pdf_svc_name    = _pt["pdf_svc_name"]
                        pdf_svc_cat     = _pt["pdf_svc_cat"]
                        pdf_region_tbl  = _pt["pdf_region_tbl"]
                        pdf_col_region  = _pt["pdf_col_region"]
                        pdf_col_code    = _pt["pdf_col_code"]
                        pdf_col_carbon  = _pt["pdf_col_carbon"]
                        pdf_insights    = _pt["pdf_insights"]
                        pdf_emission    = _pt["pdf_emission"]
                        pdf_emission_v  = _pt["pdf_emission_v_fmt"].format(reduction=emission_reduction)
                        pdf_best        = _pt["pdf_best"]
                        pdf_lowest      = _pt["pdf_lowest"]
                        pdf_opt         = _pt["pdf_opt"]
                        pdf_rec_col1    = _pt["pdf_rec_col1"]
                        pdf_rec_col2    = _pt["pdf_rec_col2"]
                        pdf_rec_col3    = _pt["pdf_rec_col3"]
                        pdf_savings_title1 = _pt["pdf_savings_title1"]
                        pdf_savings_title2 = _pt["pdf_savings_title2"]
                        pdf_savings_body1 = _pt["pdf_savings_body1"]
                        pdf_savings_body2 = _pt["pdf_savings_body2"]
                        pdf_footer      = _pt["pdf_footer"]
                        
                        # Title
                        try:
                            title_table = Table([[
                                Paragraph(f"GreenCloud Advisor  {pdf_title}", title_style)
                            ]])
                            title_table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0)
                            ]))
                            story.append(title_table)
                        except:
                            story.append(Paragraph(f"GreenCloud Advisor - {pdf_title}", title_style))
                        
                        story.append(Paragraph(pdf_generated, normal_style))
                        story.append(Spacer(1, 30))

                        story.append(Paragraph(f"[Workload] {pdf_workload}", header_style))
                        story.append(Paragraph(services_input, normal_style))
                        story.append(Spacer(1, 20))

                        story.append(Paragraph(f"[Regions] {pdf_regions}", header_style))
                        regions_text = ", ".join(selected_regions)
                        story.append(Paragraph(regions_text, normal_style))
                        story.append(Spacer(1, 20))
                        
                        summary_data = [[
                            Paragraph(f"<b>★ {pdf_rec_region}</b>", metric_style),
                            Paragraph(f"<b>{best['region_name']} ({best['region_code']})</b>", normal_style)
                        ], [
                            Paragraph(f"<b>▼ {pdf_carbon}</b>", metric_style),
                            Paragraph(f"<b>{round(best['location_based_intensity'], 3)} kg CO2e/kWh</b>", normal_style)
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
                        
                        # Chart generation
                        def create_chart():
                            if not filtered_options:
                                return None
                            fig, ax = plt.subplots(figsize=(8, 5))
                            chart_regions = filtered_options[:min(6, len(filtered_options))]
                            regions = [opt['region_name'] for opt in chart_regions]
                            location_based = [opt['location_based_intensity'] for opt in chart_regions]
                            x = range(len(regions))
                            ax.bar(x, location_based, label=pdf_chart_legend, color="#583ecc", alpha=0.8)
                            ax.set_xlabel(pdf_chart_label_x, fontsize=12)
                            ax.set_ylabel(pdf_chart_label_y, fontsize=12)
                            ax.set_title(pdf_chart_comp, fontsize=14, fontweight='bold')
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
                        
                        story.append(Paragraph(f"▲ {pdf_chart_title}", header_style))
                        chart_buffer = create_chart()
                        if chart_buffer:
                            chart_img = Image(chart_buffer, width=6*inch, height=3.75*inch)
                            story.append(chart_img)
                        else:
                            story.append(Paragraph("No data available for chart generation", normal_style))
                        story.append(Spacer(1, 20))
                        
                        story.append(Paragraph(f"⚙ {pdf_services}", header_style))
                        
                        if required_services:
                            services_data = [[Paragraph(f'<b>⚙ {pdf_svc_name}</b>', normal_style),
                                            Paragraph(f'<b>● {pdf_svc_cat}</b>', normal_style)]]
                            
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
                                    Paragraph(service, normal_style),
                                    Paragraph(category, normal_style)
                                ])
                            
                            services_table = Table(services_data, colWidths=[3*inch, 2*inch])
                            services_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkorange),
                                ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
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
                            story.append(Paragraph("Services: N/A", normal_style))
                        
                        story.append(Spacer(1, 15))
                        
                        story.append(Paragraph(f"■ {pdf_region_tbl}", header_style))
                        table_data = [[
                            Paragraph(f'<b>● {pdf_col_region}</b>', normal_style),
                            Paragraph(f'<b>■ {pdf_col_code}</b>', normal_style),
                            Paragraph(f'<b>▲ {pdf_col_carbon}</b>', normal_style)
                        ]]
                        
                        for i, region in enumerate(filtered_options):
                            table_data.append([
                                Paragraph(region['region_name'], normal_style),
                                Paragraph(region['region_code'], normal_style),
                                Paragraph(f"{round(region['location_based_intensity'], 3)}", normal_style)
                            ])
                        
                        table = Table(table_data, colWidths=[2*inch, 1*inch, 2*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),  # Highlight best region
                            ('BACKGROUND', (0, 2), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                            ('FONTSIZE', (0, 1), (-1, -1), 8)
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 25))
                        
                        story.append(Paragraph(f"◆ {pdf_insights}", header_style))
                        insights_data = [[
                            Paragraph(f"<b>▼ {pdf_emission}</b>", normal_style),
                            Paragraph(pdf_emission_v, normal_style)
                        ], [
                            Paragraph(f"<b>★ {pdf_best}</b>", normal_style),
                            Paragraph(f"{best['region_name']}", normal_style)
                        ], [
                            Paragraph(f"<b>♦ {pdf_lowest}</b>", normal_style),
                            Paragraph(f"{round(best['location_based_intensity'], 3)} kg CO2e/kWh", normal_style)
                        ]]
                        
                        insights_table = Table(insights_data, colWidths=[2.5*inch, 3*inch])
                        insights_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
                            ('GRID', (0, 0), (-1, -1), 1, colors.gold),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('FONTNAME', (0, 0), (0, -1), bold_font_name)
                        ]))
                        story.append(insights_table)
                        story.append(Spacer(1, 20))
                        
                        story.append(Paragraph(f"◆ {pdf_opt}", header_style))
                        
                        rec_headers = [
                            Paragraph(f"<b>◆ {pdf_rec_col1}</b>", normal_style),
                            Paragraph(f"<b>$ {pdf_rec_col2}</b>", normal_style),
                            Paragraph(f"<b>⚙ {pdf_rec_col3}</b>", normal_style)
                        ]
                        
                        rec_table_data = [rec_headers]
                        
                        for insight in (insights if insights else []):
                            savings_text = "$ Cost & Carbon Savings"
                            if "cost" in insight["description"].lower() or "コスト" in insight["description"]:
                                savings_text = "$ Significant Cost Reduction"
                            elif "carbon" in insight["description"].lower() or "カーボン" in insight["description"]:
                                savings_text = "♦ Carbon Footprint Reduction"
                            elif "performance" in insight["description"].lower() or "パフォーマンス" in insight["description"]:
                                savings_text = "▲ Performance Optimization"
                            
                            rec_table_data.append([
                                Paragraph(f"<b>{_strip_emoji(insight['title'])}</b>", normal_style),
                                Paragraph(savings_text, normal_style),
                                Paragraph(_strip_emoji(insight["description"]), normal_style)
                            ])
                        
                        rec_table = Table(rec_table_data, colWidths=[2.2*inch, 1.8*inch, 3*inch])
                        rec_table.setStyle(TableStyle([
                            # Header styling
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkred),
                            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
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
                            *[('BACKGROUND', (0, i), (-1, i), colors.lightblue) for i in range(1, len(rec_table_data), 2)]
                        ]))
                        story.append(rec_table)
                        story.append(Spacer(1, 15))
                        
                        # Add savings summary box
                        savings_data = [[
                            Paragraph(f"$ <b>{pdf_savings_title1}</b>", metric_style),
                            Paragraph(f"♦ <b>{pdf_savings_title2}</b>", metric_style)
                        ], [
                            Paragraph(pdf_savings_body1, normal_style),
                            Paragraph(pdf_savings_body2, normal_style)
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
                        story.append(Paragraph(pdf_footer, footer_style))

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
                        label=T["result_download"],
                        data=create_analysis_pdf(),
                        file_name=f"GreenCloud_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}{'_ja' if st.session_state.lang == 'ja' else ''}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
            else:
                st.warning(T["result_no_regions"])
        else:
            st.info(T["info_placeholder"])

elif st.session_state.active_tab == "CCFT Report Analysis":
    st.header(T["header_ccft"])
    
    # CCFT Report upload
    uploaded_file = st.file_uploader(
        T["upload_ccft"],
        type=['csv', 'json'],
        help=T["upload_ccft_help"]
    )
    
    # Auto-switch to CCFT tab when file is uploaded
    if uploaded_file and st.session_state.active_tab != "CCFT Report Analysis":
        st.session_state.active_tab = "CCFT Report Analysis"
        st.rerun()
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Process carbon emission data if uploaded
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                ccft_data = pd.read_csv(uploaded_file)
                # Map new column names to legacy names for backward compatibility
                column_mapping = {
                    'total_mbm_emissions': 'total_mbm_emissions_value',
                    'total_lbm_emissions': 'total_lbm_emissions_value',
                    'service': 'product_code',
                    'region': 'location',
                    'usage_year': 'usage_month',
                }
                ccft_data.rename(columns={k: v for k, v in column_mapping.items() if k in ccft_data.columns}, inplace=True)
                # Add unit columns if missing
                if 'total_mbm_emissions_unit' not in ccft_data.columns:
                    ccft_data['total_mbm_emissions_unit'] = 'MTCO2e'
                if 'total_lbm_emissions_unit' not in ccft_data.columns:
                    ccft_data['total_lbm_emissions_unit'] = 'MTCO2e'
                st.success(T["ccft_csv_success"])
            else:
                ccft_data = json.load(uploaded_file)
                st.success(T["ccft_json_success"])
            
            # Load data into chatbot
            chatbot.load_ccft_data(ccft_data)
            
            # Create two columns for data overview and chatbot
            overview_col, chat_col = st.columns([1, 1])
            
            with overview_col:
                st.subheader(T["subheader_overview"])
                
                if isinstance(ccft_data, pd.DataFrame):
                    st.write(f"**Records:** {len(ccft_data)}")
                    st.write(f"**Columns:** {len(ccft_data.columns)}")
                    
                    carbon_cols = [col for col in ccft_data.columns if 'carbon' in col.lower() or 'co2' in col.lower() or 'emission' in col.lower()]
                    if carbon_cols:
                        total_emissions = ccft_data[carbon_cols[0]].sum()
                        st.metric(T["total_emissions"], f"{total_emissions:.2f} kg CO2e")
                    
                    if 'Region' in ccft_data.columns:
                        unique_regions = ccft_data['Region'].nunique()
                        st.metric(T["aws_regions"], unique_regions)
                    
                    with st.expander(T["data_preview"]):
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
                        insights_button = st.form_submit_button(T["btn_insights"], type="primary")
                        st.markdown('<style>div[data-testid="stForm"] button { width: 150px !important; }</style>', unsafe_allow_html=True)
                
                if insights_button:
                    with st.spinner("Analyzing your CCFT data..."):
                        st.session_state.insights_data = chatbot.get_data_insights(lang=st.session_state.lang)
                        st.session_state.show_insights_modal = True
                
                # Show modal if flag is set
                if st.session_state.show_insights_modal and st.session_state.insights_data:
                    @st.dialog(T["insights_modal_title"], width="large")
                    def show_insights():
                        insights_data = st.session_state.insights_data
                        if isinstance(insights_data, dict):
                            # Display charts if available
                            charts = insights_data.get("charts", [])
                            if charts:
                                st.write(T["insights_visualizations"])
                                
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
                                st.write(T["insights_ai_analysis"])
                                formatted_text = text_insights.replace('\n\n', '\n').strip()
                                st.markdown(formatted_text)
                            
                            # Download AI Insights Report button
                            st.divider()
                            col1, col2 = st.columns([3, 1])
                            with col2:
                                # Create AI insights PDF
                                from reportlab.lib.pagesizes import A4
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
                                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                                from reportlab.lib.units import inch
                                import io
                                import base64
                                
                                def create_insights_pdf():
                                    buffer = io.BytesIO()
                                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                                    styles = getSampleStyleSheet()
                                    story = []

                                    # Japanese font setup
                                    from reportlab.pdfbase import pdfmetrics
                                    from reportlab.pdfbase.ttfonts import TTFont
                                    import os as _os
                                    font_name = 'Helvetica'
                                    if st.session_state.lang == "ja":
                                        _jp_candidates = [
                                            ('/Library/Fonts/Arial Unicode.ttf', None),
                                            ('/System/Library/Fonts/Arial Unicode.ttf', None),
                                            ('/usr/share/fonts/truetype/notosansjp/NotoSansJP-Regular.ttf', None),
                                            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 0),
                                            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0),
                                        ]
                                        for fp, subfont_idx in _jp_candidates:
                                            if _os.path.exists(fp):
                                                try:
                                                    if subfont_idx is not None:
                                                        pdfmetrics.registerFont(TTFont('JpFont', fp, subfontIndex=subfont_idx))
                                                    else:
                                                        pdfmetrics.registerFont(TTFont('JpFont', fp))
                                                    font_name = 'JpFont'
                                                except Exception:
                                                    continue
                                                break

                                    title_style = ParagraphStyle('InsTitle', parent=styles['Title'], fontName=font_name)
                                    h1_style = ParagraphStyle('InsH1', parent=styles['Heading1'], fontName=font_name)
                                    h2_style = ParagraphStyle('InsH2', parent=styles['Heading2'], fontName=font_name)
                                    normal_style = ParagraphStyle('InsNormal', parent=styles['Normal'], fontName=font_name)
                                    
                                    # Title
                                    story.append(Paragraph(f"◆ {T['insights_pdf_title']}", title_style))
                                    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", normal_style))
                                    story.append(Spacer(1, 20))
                                    
                                    # Add charts
                                    if charts:
                                        story.append(Paragraph(T['insights_pdf_visualizations'], h1_style))
                                        for chart in charts:
                                            story.append(Paragraph(chart['title'], h2_style))
                                            img_buffer = io.BytesIO(base64.b64decode(chart['image']))
                                            img = Image(img_buffer, width=6*inch, height=3.6*inch)
                                            story.append(img)
                                            if 'description' in chart:
                                                story.append(Paragraph(chart['description'], normal_style))
                                            story.append(Spacer(1, 15))
                                    
                                    # Add AI analysis
                                    if text_insights:
                                        story.append(Paragraph(T['insights_pdf_analysis'], h1_style))
                                        paragraphs = text_insights.split('\n\n')
                                        for para in paragraphs:
                                            if para.strip():
                                                formatted_para = para.strip().replace('\n', '<br/>')
                                                story.append(Paragraph(formatted_para, normal_style))
                                                story.append(Spacer(1, 10))
                                    
                                    doc.build(story)
                                    buffer.seek(0)
                                    return buffer.getvalue()
                                
                                st.download_button(
                                    label=T["insights_download_btn"],
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
                st.subheader(T["subheader_chat"])
                
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
                        T["chat_input_label"],
                        placeholder=T["chat_placeholder"],
                        key="ccft_chat_input",
                        value="" if st.session_state.clear_ccft_input else st.session_state.get("ccft_chat_input", "")
                    )
                    send_button = st.form_submit_button(T["btn_send"], type="primary")
                
                if st.button(T["btn_clear"]):
                    st.session_state.chat_history = []
                    st.session_state.clear_ccft_input = True
                
                if send_button and user_question:
                        with st.spinner("🤖 GreenCloudAdvisor is analyzing your report..."):
                            response = chatbot.chat(user_question)
                            st.session_state.chat_history.append(("user", user_question))
                            st.session_state.chat_history.append(("assistant", response))
                            st.session_state.clear_ccft_input = True
                        st.rerun()
                
                # Reset clear flag
                if st.session_state.clear_ccft_input:
                    st.session_state.clear_ccft_input = False
                
                st.write(T["suggested_questions"])
                suggestions = T["suggestions"]
                
                for suggestion in suggestions:
                    if st.button(suggestion, key=f"suggest_{suggestion[:20]}"):
                        with st.spinner("🤖 GreenCloudAdvisor is analyzing your report..."):
                            response = chatbot.chat(suggestion)
                            st.session_state.chat_history.append(("user", suggestion))
                            st.session_state.chat_history.append(("assistant", response))
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error loading report: {e}")
    
    else:
        st.info(T["ce_upload_info"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(T["expected_format"])
            example_data = pd.DataFrame({
                'Region': ['us-east-1', 'eu-west-1', 'ap-southeast-1'],
                'Service': ['EC2', 'S3', 'RDS'],
                'Usage': [100, 50, 25],
                'Carbon_Emissions_kg': [45.2, 12.3, 8.7]
            })
            st.dataframe(example_data, width='stretch')
        
        with col2:
            st.subheader(T["generic_assistant"])
            st.write(T["generic_assistant_desc"])
            
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
                    T["generic_input_label"],
                    placeholder=T["generic_placeholder"],
                    key="generic_chat_input",
                    value="" if st.session_state.clear_generic_input else st.session_state.get("generic_chat_input", "")
                )
                generic_send_button = st.form_submit_button(T["btn_send"], type="primary")
            
            if st.button(T["btn_clear"], key="generic_clear"):
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
            
            st.write(T["suggested_questions"])
            generic_suggestions = T["generic_suggestions"]
            
            for suggestion in generic_suggestions:
                if st.button(suggestion, key=f"generic_{suggestion[:20]}"):
                    with st.spinner("Thinking..."):
                        response = chatbot.chat(suggestion)
                        st.session_state.generic_chat_history.append(("user", suggestion))
                        st.session_state.generic_chat_history.append(("assistant", response))

# Footer
st.markdown("---")
st.markdown(T["footer"])