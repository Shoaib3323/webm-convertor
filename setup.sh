#!/bin/bash

echo "Setting up Telegram Video Converter Bot..."

# Update system packages
apt-get update

# Install FFmpeg
apt-get install -y ffmpeg

# Verify installations
echo "Python version:"
python3 --version

echo "FFmpeg version:"
ffmpeg -version

echo "Setup completed successfully!"
