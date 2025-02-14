# Open firewall - only needed on first run
echo "** Opening port 8501 for incoming traffic..."
sudo firewall-cmd --zone=public --add-port=8501/tcp --permanent
sudo firewall-cmd --reload

# Activate virtual environment and navigate to app directory
cd /home/opc/src/genai_agent/genai_agent_env/bin
source activate
cd /home/opc/src/genai_playground-main

# Run the application in the background
echo "** Running application in the background..."
nohup streamlit run /home/opc/genai-agent-ussc/Home.py &
