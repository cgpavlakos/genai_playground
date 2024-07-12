import streamlit as st

st.set_page_config(page_title="GenAI Agent", 
                   page_icon="🤖", layout="centered", 
                   initial_sidebar_state="expanded", menu_items=None)

logo_image_path = st.secrets["logo"] 
st.logo(logo_image_path)  

# Get the current page from query parameters
st.session_state.current_page ="Home"
st.query_params.page = "Home"
current_page = st.query_params.page

# Compare with previous page and clear session state if it changed
if current_page != st.session_state.current_page:
    st.session_state.clear() 
    st.session_state.current_page = current_page
with st.sidebar:
   st.info("Check out the [architecure diagram](https://raw.githubusercontent.com/cgpavlakos/genai_agent/main/RAG%20Demo%20Diagram.png), [product page](https://www.oracle.com/artificial-intelligence/generative-ai/agents/), and [source code](https://github.com/cgpavlakos/genai_agent/tree/main) to see how the Oracle Data Platform and Generative AI come together for this demo of a fully secure and private RAG chatbot.")
st.markdown(
    """
    ## What can I do here?
    - Use **RAG Agent** to chat with an AI that has specialized knowledge of Oracle Cloud for US Government. 
        - Ask it things like `How can Oracle Cloud support my agency's zero trust journey?`
    - Use **LLM Playground** to chat with foundational models on Oracle Cloud Generative AI Service.
        - You can play with the hyperparamters and change models with the sidebar.
    - Try them out by clicking the links on the sidebar to the left!
    
    ## About
    - The RAG Agent demo leverages the power of **Oracle's Cloud Data Platform** to provide you with a seamless and informative retrieval-augmented generation (RAG) chat experience 
    through **Generative AI Agents**, which is currently in beta. 
    - The LLM Playground gives you an opportunity to see **Oracle Cloud Generative AI** in action. 
    - The UI is Streamlit, an open-source Python framework.

    ## Generative AI Agent Features
    - **Secure & Private:** All data remains confidential within your Oracle Cloud tenancy, benefiting from all of the built-in security features.
    - **Chat with the GenAI Agent:** Have a conversation - ask questions and get insightful answers.
    - **View Citations:** Explore the sources behind the agent's responses to validate the responses are grounded. 
    - **Reset Chat:** A button to clear the session history and start fresh. 

    ## Underlying Oracle Cloud Data Platform Services
    - **Object Storage:** Stores private data files for the knowledge base with AES256 encryption.
    - **Generative AI Agents (Beta):** Provides the RAG pipeline as a PaaS service. 
    - **Open Search:** Knowledge base holding the private data files, automatically indexed for fast search. 
    - **Generative AI Service:** Can be either shared or dedicated hosting, with your choice of Cohere and Meta for Large Language Model (LLM).
    - **Compute:** A virtual machine hosts the Streamlit app to provide the UI. 

    ## Data Sources for the RAG Agent
    - **Executive Orders:** Including Executive Order 14028 - Improving the Nation's Cybersecurity
    - **Government Memos and Guidance:** Documents such as M-21-31 and guidance from CISA and NIST
    - **Oracle Product Documentation:** Technical documentation about Oracle Cloud Services 
    - **Oracle Whitepapers:** Created by Federal Civilian the field team regarding topics such as TIC 3.0
    
    ## Why did the RAG Agent not answer my question?
    - The RAG agent is designed to answer questions related to the documents in its knowledge base of Oracle Cloud services and US Federal Government policies and guidance. 
    - If there is no reference it can pull from, it will tell you it can not answer the question instead of making up an answer that is not grounded.
    - Try asking it things like `What is an Identity Domain?` or `How do I meet FedRAMP requirements on Oracle Cloud?`

    ## What LLM models are available in the LLM Playground?
    - **Command R** or `cohere.command-r-16k` is the default and is a smaller-scale language model than Command R+. While Command R offers high-quality responses, it might not possess the same level of sophistication and depth.
        - Command R is suited for a wide range of applications requiring text generation, summarization, translation, or text-based classification. It’s an excellent choice for building conversational AI agents, chat based conversational applications and more. 
    - **Command R+** or `cohere.command-r-plus` employs a larger model, resulting in enhanced performance and more sophisticated understandings.
        - Command R+ is tailored for demanding language tasks requiring deeper understanding, complexity, and nuance. It excels in applications like text generation, question-answering, sentiment analysis, and information retrieval.
    - **Llama 3** or `meta.llama-3-70b-instruct` is an open source model from Meta. 
        - This 70 billion-parameter generation model is highly performant and has a broad general knowledge, making it suitable for various tasks, from generating ideas to refining text analysis and drafting written content, such as emails, blog posts, and descriptions.

    ## How can I see the difference between RAG and using a LLM without my data for context?
    - You can chat with a **RAG Agent** that has domain-specific knowledge on Oracle Cloud and then check out the **LLM Playground** to evaluate Cohere and Meta foundational models.
        - Try asking both of them `What is m-21-31?` to see the difference between a grounded response from domain specific knowledge and a hallucination.  
    
    *Created by chris.pavlakos@oracle.com*
    """
)
