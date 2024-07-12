from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.chains import ConversationChain 
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

import streamlit as st
import oci 
import time
import yaml

AVATAR_MAPPING = {
"user": st.secrets["user_avatar"],
"assistant": st.secrets["assisstant_avatar"],
}

logo_image_path = st.secrets["logo"] 
st.logo(logo_image_path)  

# OCI Configuration
CONFIG_PROFILE = "DEFAULT" #DEFAULT or PUBSEC06
config = oci.config.from_file()
endpoint = st.secrets["endpoint"]
compartment_id = st.secrets["compartment_id"]
llm_endpoint = st.secrets["llm_endpoint"]

#this ensures that chat history does not "leak" from one page to the other
st.session_state.current_page = "not null"
# Get the current page from query parameters"
st.query_params.page = "LLM_Playground"
current_page = st.query_params.page

# Compare with previous page and clear session state if it changed
if current_page != st.session_state.current_page:
    st.session_state.clear() 
    st.session_state.current_page = current_page

# Streamlit UI
st.header("Oracle LLM Playground")
st.subheader("Powered by Oracle Generative AI Service")
st.info("`This chat does not have access to the RAG Agent's knowledge base. Notice how different the answers are. Use the sidebar to change the LLM model, update parameters, and reset the chat.`")

# Now set up the langchain 
DEFAULT_CLAUDE_TEMPLATE = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.

Current conversation:
{history}
Human: {input}
Assistant:"""

CLAUDE_PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=DEFAULT_CLAUDE_TEMPLATE)

INIT_MESSAGE = {"role": "assistant", "content": "Hi! I am Oracle Generative AI! How may I help you?"}

# Re-initialize the chat after
def new_chat():
    st.session_state["messages"] = [INIT_MESSAGE]
    st.toast("Chat reset!")
    

def update_params():
    st.session_state["conv_chain"] = init_conversationchain()
    st.toast("Parameters saved!")
    

# Sidebar info
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.button("Save Changes", on_click=update_params, type='primary', use_container_width=True) 
    with col2:
        st.button("Reset Chat", on_click=new_chat, type='primary', use_container_width=True)
    options = ["cohere.command-r-16k", 
            "cohere.command-r-plus", 
            "meta.llama-3-70b-instruct"]
    st.markdown("## LLM Model Selection")
    LLM_MODEL = st.selectbox("Choose your desired LLM model:", options, index=0, 
                            help="Defaults to cohere.command-r-16k")
    st.markdown("## Inference Parameters")
    TEMPERATURE = st.slider("Temperature", min_value=0.0,
                            max_value=1.0, value=0.3, step=0.1,
                            help="A number that sets the randomness of the generated output. A lower temperature means less random generations. Use lower numbers for tasks such as question answering or summarizing. High temperatures can generate hallucinations or factually incorrect information.")
    TOP_P = st.slider("Top-P", min_value=0.0,
                    max_value=1.0, value=0.75, step=0.01,
                    help="To eliminate tokens with low likelihood, assign p a minimum percentage for the next token's likelihood. For example, when p is set to 0.75, the model eliminates the bottom 25 percent for the next token. Set to 1.0 to consider all tokens and set to 0 to disable. If both k and p are enabled, p acts after k.")
    TOP_K = st.slider("Top-K", min_value=1,
                    max_value=500, value=0, step=5,
                    help="A sampling method in which the model chooses the next token randomly from the top k most likely tokens. A higher value for k generates more random output, which makes the output text sound more natural.")
    MAX_TOKENS = st.slider("Max Tokens", min_value=0,
                        max_value=4000, value=500, step=8,
                        help="The maximum number of output tokens that the model will generate for the response. A token is generally a few letters.")
    FREQUENCY_PENALTY = st.slider("Frequency Penalty", min_value=0.0,
                            max_value=1.0, value=0.0, step=0.1,
                            help="To reduce repetitiveness of generated tokens, this number penalizes new tokens based on their frequency in the generated text so far. Greater numbers encourage the model to use new tokens, while lower numbers encourage the model to repeat the tokens.")
    PRESENCE_PENALTY = st.slider("Presence Penalty", min_value=0.0,
                            max_value=1.0, value=0.0, step=0.1,
                            help="To reduce repetitiveness of generated tokens, this number penalizes new tokens based on whether they've appeared in the generated text so far. Greater numbers encourage the model to use new tokens, while lower numbers encourage the model to repeat the tokens.")
    MEMORY_WINDOW = st.slider("Memory Window", min_value=0,
                            max_value=10, value=3, step=1,
                            help="How many interactions to keep in memory.")

# Initialize the ConversationChain
def init_conversationchain():
    model_kwargs = {'temperature': TEMPERATURE,
                    'top_p': TOP_P,
                    'top_k': TOP_K,
                    'max_tokens': MAX_TOKENS,
                    'is_stream': "True"}

    llm = ChatOCIGenAI(
    model_id=LLM_MODEL,
    service_endpoint=llm_endpoint,
    compartment_id=compartment_id,
    model_kwargs=model_kwargs
)


    conversation = ConversationChain(
        llm=llm,
        verbose=True,
        memory=ConversationBufferWindowMemory(k=MEMORY_WINDOW, ai_prefix="Assistant"),
        prompt=CLAUDE_PROMPT,
    )

    return conversation

#initialize conversation chain
if "conv_chain" not in st.session_state:  # Check if conv_chain exists in session state
    st.session_state["conv_chain"] = init_conversationchain()
conv_chain = st.session_state["conv_chain"]


def generate_response(conversation, input_text):
    human_message = HumanMessage(content=input_text)
    ai_response = conversation.run(input_text) # Get the full response directly
    return ai_response


if "messages" not in st.session_state:
    st.session_state.messages = [INIT_MESSAGE]
    conv_chain = init_conversationchain()

# User input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": AVATAR_MAPPING.get("user")})

    # Get and append assistant's response to the messages state
    with st.chat_message("assistant", avatar="o.png"):
        with st.spinner("Thinking..."):
            full_response = generate_response(conv_chain, prompt)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "avatar": "o.png"})

# Display all chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=AVATAR_MAPPING.get(message["role"], "o.png")):
        st.markdown(message["content"])
