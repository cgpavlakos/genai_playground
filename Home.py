import streamlit as st

st.session_state.current_page = st.session_state.get("page", "Home")
if st.session_state.get("page", "Home") != st.session_state.current_page:
    # Clear all session state data
    st.session_state.clear()

    # Store the current page for the next comparison
    st.session_state.current_page = st.session_state.get("page", "Home")

st.set_page_config(page_title="Home", layout="centered", 
                   initial_sidebar_state="expanded", menu_items=None)

logo_image_path = st.secrets["logo"]
st.logo(logo_image_path, size="large")  

with st.sidebar:
   st.info("Check out the [architecure diagram](https://raw.githubusercontent.com/cgpavlakos/genai_agent/main/RAG%20Demo%20Diagram.png), [product page](https://www.oracle.com/artificial-intelligence/generative-ai/agents/), and [source code](https://github.com/cgpavlakos/genai_agent/tree/main) to see how the Oracle Data Platform and Generative AI come together a fully secure and private RAG chatbot.")
st.markdown(
    """
    ## About
    This 4-in-1 demo showcases the power of **Oracle's Cloud Platform** and **AI Services** with real-world utility:
    - The **LLM Playground** shows [**Oracle Cloud Generative AI**](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) in action. 
        - You can play with the hyperparameters and change models with the sidebar.
    - **USSC Helpline Agent** uses [**Generative AI Agents**](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/home.htm) for a retrieval-augmented generation (RAG) chat.
        - The documents used are all publicly available on [ussc.gov](https://www.ussc.gov/product-type/primers).
        - This was created originally as a tailored demo for the customer. 
    - The **Speech to Text** page uses [**OCI Speech**](https://docs.oracle.com/en-us/iaas/Content/speech/home.htm) to transcribe, and [**Generative AI**]((https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)) to provide a summary. 
    - The **Summarize Document** page uses [**Generative AI**](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) to provide a summary of any text or PDF file.
    - The UI is Streamlit, an open-source Python framework running on [**OCI Compute**](https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm).

    ##### More about the USSC Helpline Agent:
    - What Data Sources are in the the Knowledge Base?
        - **Primers** on topics including Criminal History, RICO, and Firearms 
        - **Additional USSC Public Documents** such as _Federal Sentencing: The Basics — 2020 and Selected Supreme Court Cases on Sentencing Issues - August 2024_
    - Why did the RAG Agent not answer my question?
        - The RAG agent is designed to answer questions related to the documents in its knowledge base of USSC policies and guidance. 
        - If there is no reference it can pull from, it will tell you it can not answer the question instead of making up an answer that is not grounded.
    - How can I see the difference between RAG and using a LLM without my data for context - where is the value?
        - You can chat with a **RAG Agent** that has domain-specific knowledge on USSC and then check out the **LLM Playground** to ask Cohere and Meta foundational models.
        - Try asking both of them `What is VICAR` to see the difference between a grounded response from domain specific knowledge and a hallucination.  

    ##### What LLM models are available in the LLM Playground?
    - **Command R** or `cohere.command-r-08-2024` is the default and is a smaller-scale language model than Command R+. While Command R offers high-quality responses, it might not possess the same level of sophistication and depth.
        - Command R is suited for a wide range of applications requiring text generation, summarization, translation, or text-based classification. It’s an excellent choice for building conversational AI agents, chat based conversational applications and more. 
    - **Command R+** or `cohere.command-r-plus-08-2024` employs a larger model, resulting in enhanced performance and more sophisticated understandings.
        - Command R+ is tailored for demanding language tasks requiring deeper understanding, complexity, and nuance. It excels in applications like text generation, question-answering, sentiment analysis, and information retrieval.
    - **Llama 3.3** or `meta.llama-3.3-70b-instruct` is an open source model from Meta. 
        - This 70 billion-parameter generation model is highly performant and has a broad general knowledge, making it suitable for various tasks, from generating ideas to refining text analysis and drafting written content, such as emails, blog posts, and descriptions.
    - The [Oracle Cloud Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/chat-models.htm#chat-models) has more detailed information and is always up to date as new models become available.

    ##### Underlying Oracle Cloud Data Platform Services
    - [**Object Storage**](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm) stores private data files for the RAG knowledge base and speech to text functionality with AES256 encryption.
    - [**Generative AI Agents**](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/home.htm) provides the RAG pipeline as a PaaS service. 
    - [**Open Search**](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/home.htm) is a managed service for the knowledge base, automatically indexed for fast search. 
    - [**Generative AI**](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) Can be either shared or dedicated hosting, with your choice of Cohere and Meta for Large Language Model (LLM).
    - [**Compute**](https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm) - a E5 Flex (1 OCPU) virtual machine hosts the Streamlit app to provide the UI. 
    
    *Created by chris.pavlakos@oracle.com*
    """
)

