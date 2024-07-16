import streamlit as st
import oci
import genai_agent_service_bmc_python_client
import random
from urllib.parse import urlparse, unquote

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.chains import ConversationChain 
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory

# OCI Configuration
CONFIG_PROFILE = "DEFAULT" #DEFAULT or PUBSEC06
config = oci.config.from_file()
endpoint = st.secrets["endpoint"]
#agent_endpoint_id = st.secrets["agent_endpoint_2"]
compartment_id = st.secrets["compartment_id"]


if st.session_state.get("page", "RAG") != st.session_state.current_page:
    # Clear all session state data
    st.session_state.clear()

    # Store the current page for the next comparison
    st.session_state.current_page = st.session_state.get("page", "RAG")

logo_image_path = st.secrets["logo"] 
st.logo(logo_image_path)  

AVATAR_MAPPING = {
    "user": ":material/record_voice_over:",
    "assistant": "o.png"
}

with st.sidebar:
   
    
    # Dynamically build agent options from secrets.toml
    agent_options = {}
    for key, value in st.secrets.items():
        if key.startswith("agent_endpoint_"):  # Filter for agent keys
            display_name = key.replace("agent_endpoint_", "").replace("_", " ").title() # Format display name
            agent_options[display_name] = value  # Add to the options dictionary

    # Randomly choose an index for the default agent
    agent_display_names = list(agent_options.keys())
    random_index = random.randrange(len(agent_display_names))

    selected_display_name = st.selectbox(
        "Choose your desired Agent Endpoint:",
        list(agent_options.keys()),  # Use keys as display names
        index=random_index
    )

    agent_endpoint_id = agent_options[selected_display_name]
    
    if st.button("Reset Chat", type="primary", use_container_width=True, help="Reset chat history and clear screen"):
            st.session_state.messages = []  
            agent_endpoint_id = agent_options[selected_display_name]
            st.session_state.session_id = None  
            st.toast("Chat reset!")  
            #st.rerun()

    st.info("This RAG agent is designed to answer questions related to the documents in its knowledge base of Oracle Cloud services and US Federal Government policies and guidance. If there is no reference it can pull from, it will tell you it can not answer the question.")
    st.info('Try asking "What is m-21-31?"')

st.header("Oracle GenAI Agent Chat")
st.subheader("Powered by Oracle Generative AI Agents (Beta)")
st.info('`This RAG agent answers questions about Oracle Cloud. Click on the home tab to learn more.`')

# Initialize chat history and session ID in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Create GenAI Agent Runtime Client (only if session_id is None)
if st.session_state.session_id is None:
    genai_agent_runtime_client = genai_agent_service_bmc_python_client.GenerativeAiAgentRuntimeClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )

    # Create session
    create_session_details = genai_agent_service_bmc_python_client.models.CreateSessionDetails(
        display_name="display_name", idle_timeout_in_seconds=10, description="description"
    )
    create_session_response = genai_agent_runtime_client.create_session(create_session_details, agent_endpoint_id)
    
    # Store session ID
    st.session_state.session_id = create_session_response.data.id

    # Check if welcome message exists and append to message history
    if hasattr(create_session_response.data, 'welcome_message'):
        st.session_state.messages.append({"role": "assistant", "content": create_session_response.data.welcome_message})

# Display chat messages
for message in st.session_state.messages:
    avatar = AVATAR_MAPPING.get(message["role"], "o.png")  # Default to "o.png" if not found
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Get user input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=":material/record_voice_over:"):
        st.markdown(user_input)

    # Execute session (re-use the existing session)
    genai_agent_runtime_client = genai_agent_service_bmc_python_client.GenerativeAiAgentRuntimeClient(
            config=config, 
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(), 
            timeout=(10, 240)
        )
    # Display a spinner while waiting for the response
    with st.spinner("Working..."):  # Spinner for visual feedback 
        execute_session_details = genai_agent_service_bmc_python_client.models.ExecuteSessionDetails(
        user_message=str(user_input), should_stream=False  # You can set this to True for streaming responses
     )
        execute_session_response = genai_agent_runtime_client.execute_session(agent_endpoint_id, st.session_state.session_id, execute_session_details)

       
    # Display agent response
    if execute_session_response.status == 200:
        response_content = execute_session_response.data.message.content
        st.session_state.messages.append({"role": "assistant", "content": response_content.text})
        with st.chat_message("assistant", avatar="o.png"):
            st.markdown(response_content.text)
     # Display citations
    if response_content.citations:
        with st.expander("Citations"):
            for i, citation in enumerate(response_content.citations, start=1):
                st.write(f"**Citation {i}:**")

                # # Extract the domain name for a friendlier display
                # parsed_url = urlparse(citation.source_location.url)
                # display_path = parsed_url.netloc

                # Extract the path after '/o/' and decode
                parsed_url = urlparse(citation.source_location.url)
                path_parts = parsed_url.path.split("/o/")  
                if len(path_parts) > 1:
                    display_path = unquote(path_parts[1])
                else:
                    display_path = parsed_url.netloc  # Fallback to domain if '/o/' not found

                # Use Markdown for a cleaner link presentation
                st.markdown(f"**Source:** [{display_path}]({citation.source_location.url})") 

                # Use st.text_area for better formatting of the citation text
                st.text_area("Citation Text", value=citation.source_text, height=200) 
    else:
        st.error(f"API request failed with status: {execute_session_response.status}")
