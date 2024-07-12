# About

Demo App for Oracle Cloud Generative AI Services 

- The `RAG Agent` leverages the power of [Oracle's Cloud Data Platform](https://www.oracle.com/data-platform/) to provide you with a seamless and informative retrieval-augmented generation (RAG) chat experience through [Oracle Generative AI Agents](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/overview.htm), which is currently in beta. 
- The `LLM Playground` gives you an opportunity to see [Oracle Cloud Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/overview.htm) in action. 
- The UI is Streamlit, an open-source Python framework.
![llm_screenshot](llm.png)
## Live Demo App
[https://genai.pavlakos.cloud](https://genai.pavlakos.cloud/)

- Use **RAG Agent** to chat with an AI that has specialized knowledge of Oracle Cloud for US Government. 
  - Ask it things like `How can Oracle Cloud support my agency's zero trust journey?`
- Use **LLM Playground** to chat with foundational models on Oracle Cloud Generative AI Service.
  - You can play with the hyperparamters and change models with the sidebar.
  - Try them out by clicking the links on the sidebar to the left!

## Generative AI Agent (Beta) Features
- **Secure & Private:** All data remains confidential within your Oracle Cloud tenancy, benefiting from all of the built-in security features.
- **Chat with the GenAI Agent:** Have a conversation - ask questions and get insightful answers.
- **View Citations:** Explore the sources behind the agent's responses to validate the responses are grounded. 
- **Reset Chat:** A button to clear the session history and start fresh. 

## Underlying Architecture
![diagram](RAG%20Demo%20Diagram.png)
- **Object Storage:** Stores private data files for the knowledge base with AES256 encryption.
- **Generative AI Agents (Beta):** Provides the RAG pipeline as a PaaS service. 
- **Open Search:** Knowledge base holding the private data files, automatically indexed for fast search. 
- **Generative AI Service:** Can be either shared or dedicated hosting, with your choice of Cohere and Meta for Large Language Model (LLM).
- **Compute:** A virtual machine hosts the Streamlit app to provide the UI. 

## Known Issues

- LLM Playground does not display chat history properly
  - This is to do with how I am handling memory
  - Code will be updated once I fix it

## Try it Out in Your Oracle Cloud Tenancy

### Before you start

- You must have an Oracle Cloud Account subscribed to the Chicago, Frankfurt, or London region
- You must already have an Generative AI Agents (beta) endpoint available
  - this app only provides a front end
  - currently only available with whitelisting in Chicago region
- You must set up oci config in order to authenticate to the agent endpoint.
- You must update `.streamlit/secrets.toml`
  - agent_endpoint_id
  - compartment_id
  - other items as noted in comments

### Oracle Cloud Free Tier
- Did you know you can [sign up for an Oracle Cloud Free Tier Account](https://www.oracle.com/cloud/free/)?
   - You get $300 in credits for 30 days to use on all available services
   - You get `Always Free Resources` for as long as you want them including but not limited to: 
      - Oracle Autonmous Database with APEX
      - NoSQL Database
      - 2 AMD Compute Instances with 1/8 OCPU and 1 GB RAM each
      - Up to 4 ARM Compute Instances with a combined total of 4 OCPU and 24 GB of RAM  
      - 200 GB Block Storage
      - 20 GB Object and Archive Storage
      - Security Services including Certificates, Valut and Bastion (managed SSH jumpbox)
      - Observability Services including Logging, Monitoring, Notifications
      - Networking Services including VCN, Load Balancer, Site-to-Site VPN, and 10 TB of outbound data transfer per month
- If you are one of my customers I can get you up to 60 days and $500 in credits. Reach out to me directly and I will get you set up. 

### Get started

0. Set up Generative AI Agents service and note the agent_endpoint_id
2. Make sure you have port 8501 open on security list
3. Launch a VM with ubuntu base image and attach setup.sh as cloud-init script
4. SSH into your VM (ubuntu@ipaddress) and check the log at /home/ubuntu/genai_agent_setup.log
5. Run setup.sh if you did not add it as cloud-init script
6. Set up OCI config
7. Update `.streamlit/secrets.toml` with your agent_endpoint_id and compartment_id
8. Use run.sh to run the demo
9. Your application will be running on http://server-ip-address:8501

## Screenshots
![agent_screenshot](agent.png) ![llm_screenshot](llm.png)


