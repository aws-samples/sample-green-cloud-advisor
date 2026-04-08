#!/bin/bash
set -e

echo "=== GreenCloud Advisor - Local Setup ==="

# OS判定
OS="$(uname -s)"

# 日本語フォントのインストール
echo ""
echo ">>> Installing Japanese fonts..."

if [ "$OS" = "Darwin" ]; then
    # macOS: Arial Unicodeは標準搭載のため不要
    echo "macOS detected. Arial Unicode.ttf is pre-installed. No action needed."

elif [ "$OS" = "Linux" ]; then
    # Linux: ディストリビューション判定
    if command -v apt-get &> /dev/null; then
        echo "Debian/Ubuntu detected. Installing fonts-noto-cjk..."
        sudo apt-get update -q
        sudo apt-get install -y fonts-noto-cjk
    elif command -v yum &> /dev/null; then
        echo "RHEL/CentOS detected. Installing google-noto-cjk-fonts..."
        sudo yum install -y google-noto-cjk-fonts
    elif command -v dnf &> /dev/null; then
        echo "Fedora detected. Installing google-noto-cjk-fonts..."
        sudo dnf install -y google-noto-cjk-fonts
    else
        echo "WARNING: Unknown Linux distro. Please install a CJK font manually."
    fi
else
    echo "WARNING: Unsupported OS: $OS"
fi

# Pythonパッケージのインストール
echo ""
echo ">>> Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the app locally, run:"
echo "  python3 -m streamlit run streamlit_app.py --server.port 8501"
