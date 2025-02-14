import streamlit as st
import oci
import json
import PyPDF2
import tiktoken

if st.session_state.get("page", "Summary") != st.session_state.current_page:
    # Clear all session state data
    st.session_state.clear()
    # Store the current page for the next comparison
    st.session_state.current_page = st.session_state.get("page", "Summary")
summary_instruction = """Summarize this transcript with both an overview and detailed bullet points. Start with an overview in a couple of sentences. After that use bullet points to provide plenty of detail. Your response should be 1-2 pages long. 
Example output: 
## Overview
Short overview of the entire transcript. This is 2-3 sentences long. 
## Details
- Detail of discussion 1
- Detail of discussion 2 
- Detail of discussion 3 
... and so on
"""

# Define your Object Storage details
compartment_id = st.secrets["compartment_id"]
bucket_name = st.secrets["bucket_name"]
namespace_name = st.secrets["namespace_name"]
region = st.secrets["region"]
input_prefix = "uploads"
output_prefix = "speech-output"
final_prefix = "transcripts"

# Define LLMs from secrets.toml and set one as the default
command_r = st.secrets["command_r_ocid"]
command_plus = st.secrets["command_plus_ocid"]
llama33 = st.secrets["llama33_ocid"]
llama32 = st.secrets["llama32_ocid"]
llama31 = st.secrets["llama31_ocid"]
llm_ocid = command_plus

config = oci.config.from_file(profile_name="DEFAULT")
object_storage_client = oci.object_storage.ObjectStorageClient(config)
ai_speech_client = oci.ai_speech.AIServiceSpeechClient(config)

def chunk_transcript(transcript, chunk_size=3000, model_name="cl100k_base"):
    """Chunks a transcript based on tokens (correctly)."""
    try:
        encoding = tiktoken.get_encoding(model_name)  # Correct way to get encoding
    except ValueError:
        encoding = tiktoken.get_encoding("cl100k_base")  # Fallback
        print(f"Warning: Model '{model_name}' not found. Using 'cl100k_base'.")

    tokens = encoding.encode(transcript)
    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk = encoding.decode(tokens[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def generate_summary(transcript, summary_instruction):
  
  chunks = chunk_transcript(transcript)
  summaries = []
  for chunk in chunks:
    instruction_text = summary_instruction
    endpoint = st.secrets["llm_endpoint"]
    generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint,
    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_request = oci.generative_ai_inference.models.CohereChatRequest()
    chat_request.message = instruction_text + chunk
    chat_request.temperature = 0
    chat_request.frequency_penalty = 0
    chat_request.top_p = 0.75
    chat_request.top_k = 0
    chat_request.max_tokens = 2000
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=llm_ocid) #command-r-plus
    chat_detail.chat_request = chat_request
    chat_detail.compartment_id = compartment_id
    chat_response = generative_ai_inference_client.chat(chat_detail)
    try: 
        summary = chat_response.data.chat_response.text
        summaries.append(summary) #append the summary of each chunk
    except (AttributeError, KeyError) as e:
            print(f"Error processing response: {e}")
            summaries.append(f"Error: {e}") #append the error to the list
            continue #continue to the next chunk
    final_summary = " ".join(summaries) #combine the summaries
   # Remove duplicate "## Details" (keeping the first one)
    first_details_index = final_summary.find("## Details")
    if first_details_index != -1:
        remaining_text = final_summary[first_details_index + len("## Details"):]
        second_details_index = remaining_text.find("## Details")
        while second_details_index != -1:
            remaining_text = remaining_text[:second_details_index] + remaining_text[second_details_index + len("## Details"):]
            second_details_index = remaining_text.find("## Details")
        final_summary = final_summary[:first_details_index + len("## Details")] + remaining_text

    # **Summarize the combined summary:**
    final_instruction = """Please provide a concise summary of the following text: 
    Example output: 
            ## Overview
            Short overview of the entire text. This is 2-3 sentences long. 
            ## Details
            - Detail of discussion 1
            - Detail of discussion 2 
            - Detail of discussion 3 
            ... and so on
            """ + final_summary
    chat_request_final = oci.generative_ai_inference.models.CohereChatRequest()
    chat_request_final.message = final_instruction
    chat_request_final.temperature = 0
    chat_request_final.frequency_penalty = 0
    chat_request_final.top_p = 0.75
    chat_request_final.top_k = 0
    chat_request_final.max_tokens = 2000 # Reduced for the final summary
    chat_detail_final = oci.generative_ai_inference.models.ChatDetails()
    chat_detail_final.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=llm_ocid) #command-r-plus
    chat_detail_final.chat_request = chat_request_final
    chat_detail_final.compartment_id = compartment_id
    chat_response_final = generative_ai_inference_client.chat(chat_detail_final)

    try:
        final_summary = chat_response_final.data.chat_response.text
        return final_summary
    except (AttributeError, KeyError) as e:
        print(f"Error processing final summary response: {e}")
        return f"Error: {e}"
  return final_summary


def upload_summary_to_object_storage(summary_result, audio_file):
    """Uploads the summary to object storage."""
    summary_object_name = (
        final_prefix + "/" + audio_file.split("/")[-1] + "summary" + ".txt"
    )
    object_storage_url = f"https://objectstorage.{region}.oraclecloud.com/n/{namespace_name}/b/{bucket_name}/o/{summary_object_name}"
    try:
        summary_bytes = summary_result.encode('utf-8', errors='replace')
        object_storage_client.put_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=summary_object_name,
            put_object_body=summary_bytes
        )
        st.session_state.debug_info.update({
        "Summary file name Object Storage": summary_object_name,
        "Object Storage URL": object_storage_url,
        "Summary Status": "Ready for user!"
        })
        return summary_object_name, object_storage_url
    except oci.exceptions.ServiceError as e:
        st.session_state.debug_info.update({
        "Error uploading summary": e,
    })
        return None, None
    
def delete_objects_with_prefix(prefix):
    """Deletes objects from object storage based on prefix."""
    try:
        objects = object_storage_client.list_objects(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            prefix=prefix,
        )
        for obj in objects.data.objects:
            object_storage_client.delete_object(
                namespace_name=namespace_name,
                bucket_name=bucket_name,
                object_name=obj.name,
            )
            st.session_state.debug_info.update(
                {f"Deleted object: {obj.name}": "OK"}
            )
    except oci.exceptions.ServiceError as e:
        st.session_state.debug_info.update(
            {f"Error deleting objects with prefix {prefix}": e}
        )


def get_transcript_from_object_storage(object_name):
    """Fetches the transcript text from Object Storage."""
    try:
        get_object_response = object_storage_client.get_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name
        )
        transcript = get_object_response.data.text
        return transcript
    except oci.exceptions.ServiceError as e:
        st.error(f"Error fetching transcript: {e}")
        return None
    

def download_summary_text(res_file):
    """Downloads the summary text from Object Storage."""
    try:
        get_object_response = object_storage_client.get_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=res_file,  # Just the filename, no prefix
        )

        # Decode the content (important!):
        summary_text = get_object_response.data.content.decode('utf-8')  # Or the correct encoding

        return summary_text

    except oci.exceptions.ServiceError as e:
        st.error(f"Error downloading summary: {e}")
        return None  # Or raise the exception if you prefer

    except Exception as e:  # Catch other potential errors
        st.error(f"An error occurred: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="OWL - Summarize Document", layout="centered", initial_sidebar_state="expanded", menu_items=None)
st.logo("owl-banner.png", size="large")
st.title("OWL - Summarize Document")
st.subheader("Powered by Oracle Generative AI")
st.session_state.current_page = st.session_state.get("page", "Summarize")
st.info("Upload a text or PDF file to generate a summary, or choose an existing file.")
if "submitted" not in st.session_state:
    st.session_state.submitted = False

with st.sidebar:
    st.info("This tool allows you upload a text or PDF file to generate a summary, summarize an existing transcipt, or retrieve an already generated summary.")
    if st.button("Clear Session", type="primary", use_container_width=True):
        # st.session_state.current_page = st.session_state.get("page", "Reset")
        # st.session_state.submitted = False
        # st.session_state.summary = []
        # selected_transcript = []
        st.toast("Session cleared! You can generate a new summary now.")
        st.rerun()

file_uploader_placeholder = st.empty()
object_storage_picker_placeholder = st.empty()
generate_summary_placeholder = st.empty()
summary_picker_placeholder = st.empty()

if not st.session_state.submitted: 
# File Upload
    with file_uploader_placeholder.expander("Upload a File:", expanded=True):
        uploaded_file = st.file_uploader("Upload a text or PDF file:", type=["txt", "pdf"])

    # Object Storage Transcript Selection
    with object_storage_picker_placeholder.expander("Summarize a transcript from Object Storage:", expanded=True):
        try:
            objects = object_storage_client.list_objects(
                namespace_name=namespace_name,
                bucket_name=bucket_name,
                prefix=final_prefix + "/"  # Assuming transcripts are stored with this prefix
            )
            transcript_options = {obj.name.split("/")[-1]: obj.name for obj in objects.data.objects if obj.name.endswith(".txt") and "summary" not in obj.name}
            selected_transcript = st.selectbox("Choose a transcript:", list(transcript_options.keys()), index=None, placeholder="Select a transcript...")
        except oci.exceptions.ServiceError as e:
            st.error(f"Error listing transcripts: {e}")

with summary_picker_placeholder.expander("Retrieve an existing summary from Object Storage:"):
    summary_options = {obj.name.split("/")[-1]: obj.name  for obj in objects.data.objects if obj.name.endswith(".txt") and "summary" in obj.name}
    selected_summary = st.selectbox("Select a summary to view:",  list(summary_options.keys()), index=None, placeholder="Select a summary...")
    if selected_summary != None:
        st.session_state.submitted = True
        object_name = summary_options[selected_summary]
        summary_text = download_summary_text(object_name)
        st.session_state.summary = summary_text

    #     if summary_text:  # Check if the download was successful
    #         filename = object_name.split("/")[-1]  # Extract filename from object_name
    #         st.download_button(
    #             label="Download Summary",
    #             data=st.session_state.summary,
    #             file_name=filename,
    #             mime='text/plain',
    #             type="primary",
    #             use_container_width= True
    #         )
    #         with st.container(border=True):
    #             st.markdown(summary_text) # Display the summary
    #             st.session_state.summary = summary_text
    # try:
    #     obj = object_storage_client.get_object(
    #         namespace_name=namespace_name,
    #         bucket_name=bucket_name,
    #         object_name=object_name  # The filename, no prefix!
    #     )
    #     summary_text = obj.data.text()
    #     print(summary_text) # Or write to a file
    # except oci.exceptions.ServiceError as e:
    #     print(f"Error: {e}")
    # except Exception as e:
    #     print(f"Error: {e}")


# Generate Summary Button
    if generate_summary_placeholder.button("Generate Summary", type="primary", use_container_width=True):
        st.session_state.submitted = True
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                text_content = uploaded_file.read().decode("utf-8")
                st.session_state.text_content = text_content
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
                st.session_state.text_content = text_content
            else:
                st.error("Unsupported file type. Please upload a text or PDF file.")
        elif selected_transcript:
            st.session_state.transcript = get_transcript_from_object_storage(transcript_options[selected_transcript])
        else:
            st.warning("Please select a transcript or upload a file.")

# Clear UI elements and show spinner
if st.session_state.submitted:
    file_uploader_placeholder.empty()
    object_storage_picker_placeholder.empty()
    summary_picker_placeholder.empty()
    generate_summary_placeholder.empty()

    if "summary" not in st.session_state:
        with st.spinner("Generating Summary..."):
            if "text_content" in st.session_state:
                summary = generate_summary(st.session_state.text_content, summary_instruction)
            else:
                summary = generate_summary(st.session_state.transcript, summary_instruction)
            st.session_state.summary = summary  # Store the summary in session state


# Display Summary
if "summary" in st.session_state:
    st.download_button(
    label="Download Summary",
    type="primary",
    use_container_width= True,
    data=st.session_state.summary,
    file_name="OWL-Summary",
    mime="text/plain",
    key="download_transcript"
    )
    with st.expander("View Summary:", expanded=True):
        st.markdown(st.session_state.summary)
