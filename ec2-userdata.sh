#!/bin/bash
yum update -y
yum install -y python3 python3-pip git

# Clone your repository (replace with your repo URL)
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/GreenHouseAdvisor.git
cd GreenHouseAdvisor

# Install dependencies
pip3 install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/greencloud.service << EOF
[Unit]
Description=GreenCloud Advisor
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/GreenHouseAdvisor
ExecStart=/usr/bin/python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable greencloud
systemctl start greencloud