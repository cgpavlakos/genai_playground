sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8501 -j ACCEPT
cd ~/genai_agent/genai_agent_env/bin
source activate
cd ~/genai_agent
nohup streamlit run Home.py &
