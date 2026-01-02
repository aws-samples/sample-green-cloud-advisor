# 🌱 GreenCloud Advisor

AWS Region Sustainability Recommender that balances proximity and environmental impact.

## Features

- **Smart Region Selection**: Analyzes proximity, service availability, and carbon footprint
- **Dual Carbon Accounting**: Uses both location-based and market-based methods
- **CCFT Integration**: Upload and analyze your AWS Customer Carbon Footprint Tool reports
- **Interactive Web UI**: Streamlit-based interface for easy use

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Or use the CLI version:**
   ```bash
   python greencloud_advisor.py
   ```

## Usage

### Web Interface
1. Enter your AWS services or workload description
2. Select potential AWS regions to evaluate
3. Set your location (latitude/longitude)
4. Optionally upload your CCFT report
5. Click "Analyze Regions" for recommendations

### Inputs
- **AWS Services**: EC2, S3, RDS, Lambda, etc.
- **Regions**: Select from available AWS regions
- **Location**: Your geographic coordinates
- **CCFT Report**: CSV or JSON format (optional)

### Outputs
- **Recommended Region**: Best sustainability score
- **Comparison Table**: All evaluated regions
- **Carbon Intensity Chart**: Visual comparison
- **Key Insights**: Analysis summary and benefits

## How It Works

1. **Proximity Analysis**: Finds regions within your distance preference
2. **Service Filtering**: Ensures regions support your required services
3. **Sustainability Scoring**: Combines location-based (30%) and market-based (70%) carbon intensities
4. **Ranking**: Recommends the most sustainable option

## Example

For a London-based company needing EC2, S3, and RDS:
- **Input**: London coordinates (51.5074, -0.1278)
- **Output**: Stockholm (eu-north-1) recommended with 0.003 sustainability score
- **Benefit**: 99.7% emission reduction vs location-based accounting