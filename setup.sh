#!/bin/bash

# This can be executed on an opc base image, or you can do steps manually with necessary changes on other OS. 
# Make sure your oci setup is correct

# Define a log file
LOG_FILE=/home/opc/genai_agent_setup.log

# Redirect standard output (stdout) and standard error (stderr) to the log file
exec &>> "$LOG_FILE"

# Update and upgrade system packages
echo "** Starting system update and upgrade (check log for details)..."
sudo dnf config-manager --set-enabled ol8_appstream
sudo dnf update
sudo dnf clean all

#sudo yum update -y && sudo yum upgrade -y

# Install required python libraries
echo "** Installing python libraries (check log for details)..."
sudo dnf install python3.12 -y

# Create directories
echo "** Creating directories..."
mkdir /home/opc/src
mkdir /home/opc/src/genai_agent

# Navigate to gen_ai directory
cd /home/opc/src/genai_agent

# Create virtual environment and activate it
echo "** Creating and activating virtual environment..."
sudo python3.12 -m venv genai_agent_env
sudo chown -R opc:opc /home/opc/src/genai_agent/genai_agent_env
source genai_agent_env/bin/activate

# Download sample application and SDK
cd /home/opc/
echo "** Downloading sample application..."
wget https://github.com/cgpavlakos/genai_playground/archive/refs/heads/main.zip
unzip main.zip -d src

# Install python libraries using pip
cd /home/opc/src/genai_playground-main
echo "** Installing python libraries with pip (check log for details)..."
pip install -r requirements.txt

# Allow traffic on port 8501 (replace with your desired port if needed)
# sudo firewall-cmd --zone=public --add-port=8501/tcp --permanent
# sudo firewall-cmd --reload

# OCI CLI setup (commented out, replace with your own setup)
# bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
# oci setup config

echo "** Application installed. Make sure to edit your secrets.toml. Check the log file (~/genai_agent_setup.log) for details."

# Deactivate virtual environment (optional)
# deactivate
# /home/opc/src/genai_agent
# /home/opc/src/genai_playground-main
