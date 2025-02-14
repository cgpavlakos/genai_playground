# UI imports
import streamlit as st
from urllib.parse import urlparse, unquote 
import datetime
import pytz
from datetime import timedelta
import random
import time

# OCI-related imports
import oci
from oci.config import from_file
from oci.object_storage import ObjectStorageClient
from oci.object_storage.models import CreatePreauthenticatedRequestDetails
import genai_agent_service_bmc_python_client 

# LangChain-related imports
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI


# OCI Configuration
CONFIG_PROFILE = "DEFAULT" #DEFAULT or PUBSEC06
config = oci.config.from_file()
endpoint = st.secrets["endpoint"]
#agent_endpoint_id = st.secrets["agent_endpoint_2"]
compartment_id = st.secrets["compartment_id"]
object_storage_client = ObjectStorageClient(config)

st.set_page_config(page_title="HelpLine Agent", 
                   page_icon="ussc.png", layout="centered", 
                   initial_sidebar_state="expanded", menu_items=None)

def reset_session_state():
    st.session_state.messages = []
    st.session_state.session_id = None

if st.session_state.get("page", "RAG") != st.session_state.current_page:
    # Clear all session state data
    st.session_state.clear()

    # Store the current page for the next comparison
    st.session_state.current_page = st.session_state.get("page", "RAG")

logo_image_path = st.secrets["customer_logo"] 
st.logo(logo_image_path, size="large") 

AVATAR_MAPPING = {
    "user": st.secrets["user_avatar"],
    "assistant": st.secrets["assistant_avatar"]
}

with st.sidebar:
    
    if st.button("Reset Chat", type="primary", use_container_width=True, help="Reset chat history and clear screen"):
            st.session_state.messages = []  
           # agent_endpoint_id = agent_options[selected_display_name]
            st.session_state.session_id = None  
            st.toast("Chat reset!")  
            #st.rerun()

    st.info("This RAG agent is designed to answer questions related to the documents in its knowledge base USSC Primers and Backgrounders. If there is no reference it can pull from, it will tell you it can not answer the question.")
    st.info('Try asking "What is VICAR?"')

    on = st.toggle("Show Agent Endpoint", value=True)
    #allow for changing between multiple endpoints
    if on:
        agent_options = {}
        for key, value in st.secrets.items():
            if key.startswith("agent_endpoint_"): 
                display_name = key.replace("agent_endpoint_", "").replace("_", " ").title()
                agent_options[display_name] = value 
                
        agent_display_names = list(agent_options.keys())
        if "selected_display_name" not in st.session_state:
            st.session_state.selected_display_name = random.choice(agent_display_names) #set to 0 for static
         
        selected_display_name = st.selectbox(
            "Choose Agent Endpoint:",
            agent_display_names,
            index=agent_display_names.index(st.session_state.selected_display_name), # Find index of selected agent
            on_change=reset_session_state
        )
    
        # Update selected_display_name in session state
        st.session_state.selected_display_name = selected_display_name

        agent_endpoint_id = agent_options[selected_display_name]

st.header("USSC HelpLine GenAI Chat")
st.subheader("Powered by Oracle Generative AI Agents")
st.info('`This RAG agent answers questions about the sentencing guidelines using USSC documents and provides citations.`')

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
    avatar = AVATAR_MAPPING.get(message["role"], "ussc.png")  # Default to "o.png" if not found
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
    
    # Display agent response in chunks to simulate streaming
    # Thanks to saileshan.x.subhakaran@oracle.com for this 
    if execute_session_response.status == 200:
        response_content = execute_session_response.data.message.content
        response_parts = response_content.text.split(' ')  # Split response into words for simulation
        displayed_response = ""
        response_placeholder = st.empty()
        for part in response_parts:
            displayed_response += part + ' '
            response_placeholder.markdown(displayed_response)
            time.sleep(0.025)  # Adjust delay as needed
        st.session_state.messages.append({"role": "assistant", "content": response_content.text, avatar: avatar})

    #  # Display citations with direct URLs - not recommended but OK if your bucket is public 
    # if response_content.citations:
    #     with st.expander("Citations"):
    #         for i, citation in enumerate(response_content.citations, start=1):
    #             st.write(f"**Citation {i}:**")

    #             # Extract the path after '/o/' and decode
    #             parsed_url = urlparse(citation.source_location.url)
    #             path_parts = parsed_url.path.split("/o/")  
    #             if len(path_parts) > 1:
    #                 display_path = unquote(path_parts[1])
    #             else:
    #                 display_path = parsed_url.netloc  # Fallback to domain if '/o/' not found

    #             # Use Markdown for a cleaner link presentation
    #             st.markdown(f"**Source:** [{display_path}]({citation.source_location.url})") 

    # Display citations with PAR URLs
    if response_content.citations or execute_session_response.status == 200:
        with st.expander("Citations"):
            for i, citation in enumerate(response_content.citations, start=1):
                st.write(f"**Citation {i}:**")

                parsed_url = urlparse(citation.source_location.url)
                path_parts = parsed_url.path.split("/")
                if len(path_parts) >= 5 and path_parts[1] == "n" and path_parts[3] == "b":
                    namespace_name = path_parts[2]
                    bucket_name = path_parts[4]
                    encoded_object_name = citation.source_location.url.split("o/")[-1]
                    object_name = unquote(encoded_object_name)  # Decode the URL
                    display_path = object_name

                    # Generate PAR URL
                    try:
                        par_details = CreatePreauthenticatedRequestDetails(
                            name=f"Download_{object_name}",
                            access_type="ObjectRead",
                            time_expires=datetime.datetime.now(pytz.timezone('UTC')) + timedelta(minutes=5), # 5 minute expiry, adjust as necessary for your security needs
                            object_name=object_name
                        )
                        par = object_storage_client.create_preauthenticated_request(
                            namespace_name,
                            bucket_name,
                            par_details
                        )

                        object_storage_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        
                        par_url = object_storage_endpoint + par.data.access_uri

                        st.markdown(f"**Source:** [{display_path}]({par_url})")  
                    except Exception as e:
                        st.error(f"Failed to generate PAR URL for {display_path}: {e}")
                else:  
                    st.markdown(f"**Source:** [{citation.source_location.url}]({citation.source_location.url})")
                    st.error(f"Citation {i} does not reference a valid object storage URL.")


                st.text_area("Citation Text", value=citation.source_text, height=200)
    else:
        st.error(f"API request failed with status: {execute_session_response.status}")

