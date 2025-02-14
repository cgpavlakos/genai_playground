import json
import time
import oci
import os
import streamlit as st
import tiktoken

## IDEA FOR NEW FEATURE - GENERATE SUMMARY PAGE
# Choose from existing transcripts on object storage
# Upload text or PDF 

#summary_instruction = st.secrets["instruction"] 

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

# Speech configuration
model_type = "WHISPER_MEDIUM"  # or "WHISPER_MEDIUM" or "ORACLE"
language_code = "en"  # "en-US" for ORACLE "en" for whisper

# Clients
config = oci.config.from_file(profile_name="DEFAULT")
object_storage_client = oci.object_storage.ObjectStorageClient(config)
ai_speech_client = oci.ai_speech.AIServiceSpeechClient(config)

def chunk_transcript(transcript, chunk_size=3000, model_name="cl100k_base"):
    st.toast("Estimating tokens and chunking transcript accordingly")
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
  st.toast("Generating summary with OCI Generative AI")
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
        st.toast("Processing complete")
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

def upload_audio_file(audio_file):
    """Uploads an audio file to Object Storage."""
    audio_upload_name = input_prefix + "/" + audio_file.name
    object_storage_client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket_name,
        object_name=audio_upload_name,
        put_object_body=audio_file.read(),  # Use read() to get the file content
    )
    st.toast("Successfully uploaded input file to Object Storage")
    return audio_upload_name

def create_speech_job(audio_upload_name, filename): 
    """Creates a speech transcription job."""
    st.toast("Starting transcription process for: " + filename)  
    create_transcription_job_response = ai_speech_client.create_transcription_job(
        create_transcription_job_details=oci.ai_speech.models.CreateTranscriptionJobDetails(
            compartment_id=compartment_id,
            input_location=oci.ai_speech.models.ObjectListInlineInputLocation(
                location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
                object_locations=[
                    oci.ai_speech.models.ObjectLocation(
                        namespace_name=namespace_name,
                        bucket_name=bucket_name,
                        object_names=[audio_upload_name],
                    )
                ],
            ),
            output_location=oci.ai_speech.models.OutputLocation(
                namespace_name=namespace_name,
                bucket_name=bucket_name,
                prefix=output_prefix,
            ),
            #display_name=filename,
            model_details=oci.ai_speech.models.TranscriptionModelDetails(
                domain="GENERIC",
                model_type=model_type,
                language_code=language_code,
                transcription_settings=oci.ai_speech.models.TranscriptionSettings(
                    diarization=oci.ai_speech.models.Diarization(
                        is_diarization_enabled=True
                    )
                ),
            ),
        )
    )

    job_id = create_transcription_job_response.data.id
    out_loc = create_transcription_job_response.data.output_location.prefix
    st.session_state.debug_info.update({
        "Job ID": job_id,
        "Location": out_loc
    })
    return job_id, out_loc

def wait_for_job_completion(job_id, out_loc):
    """Waits for a speech transcription job to complete,
    updating the timer every second."""

    start_time = time.time()
    last_api_call_time = time.time()  # Initialize last API call time

    # Use st.empty to create placeholders for the UI elements
    status_container = st.empty()
    time_container = st.empty()
    
    status = None

    while True:
        try:
            # Make API call every 10 seconds
            if time.time() - last_api_call_time >= 5:
                get_transcription_job_response = ai_speech_client.get_transcription_job(
                    transcription_job_id=job_id
                )
                status = get_transcription_job_response.data.lifecycle_state
                status_container.write(f"Status: {status}")  # Use st.header for status
                last_api_call_time = time.time()  # Update last API call time

            if status == "SUCCEEDED":
                #st.toast(f"Transcription time:", f"{minutes:02d}:{seconds:02d}")
                break

            # Update timer every second
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_container.metric("Elapsed time", f"{minutes:02d}:{seconds:02d}")  # Use st.metric for time
            time.sleep(1)  # Sleep for 1 second

        except oci.exceptions.ServiceError as e:
            st.error(f"An error occurred: {e}")
            break

    ori_name = (
        get_transcription_job_response.data.input_location.object_locations[0]
        .object_names[0]
    )

    res_file = (
        out_loc
        + namespace_name
        + "_"
        + bucket_name
        + "_"
        + ori_name
        + ".json"
    )
    st.session_state.debug_info.update({
        "Uploaded file: ": ori_name,
        "Speech JSON file: ": res_file.split("/")[-1]
    })
    return res_file

def download_speech_json(res_file):
    """Downloads the transcript from Object Storage."""
    st.toast("Fetching speech json output")
    get_object_response = object_storage_client.get_object(
        namespace_name=namespace_name,
        bucket_name=bucket_name,
        http_response_content_type="text/plain",
        object_name=res_file,
    )
    json_data = json.loads(get_object_response.data.content)
    st.session_state.debug_info.update({
        "Get JSON from Object Storage": "OK"
    })
  
    return json_data

def create_transcript(json_data):
    """Creates a formatted transcript from JSON data."""
    st.toast("Formatting transcript from raw json")
    transcript = ""
    # Check if 'transcriptions' exists in json_data
    if isinstance(json_data.get("transcriptions"), list) and len(json_data["transcriptions"]) > 0:
        for entry in json_data["transcriptions"][0]["tokens"]:
            text = entry["token"]
            # if current_speaker != speaker_index:
            #     speaker_name = speaker1_name if speaker_index == 0 else speaker2_name
            #     transcript += f"\n\n{speaker_name}: {text} "
            #     current_speaker = speaker_index
            # else:
            transcript += f"{text} "
        st.session_state.debug_info.update({
        "Clean up transcipt": "OK"
    })
    return transcript

def upload_transcript_to_object_storage(transcript, audio_file, model_type):
    """Uploads the transcript to object storage."""
    st.toast("Uploading formatted transcript to object storage")
    transcript_object_name = (
        final_prefix + "/" + audio_file.split("/")[-1] + model_type + ".txt"
    )
    object_storage_url = f"https://objectstorage.{region}.oraclecloud.com/n/{namespace_name}/b/{bucket_name}/o/{transcript_object_name}"
    try:
        transcript_bytes = transcript.encode('utf-8', errors='replace')
        object_storage_client.put_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=transcript_object_name,
            put_object_body=transcript_bytes,
        )
        st.session_state.debug_info.update({
        "Transcript file name Object Storage": transcript_object_name,
        "Object Storage URL": object_storage_url,
        "Transcript Status": "Ready for user!"
        })
        return transcript_object_name, object_storage_url
    except oci.exceptions.ServiceError as e:
        st.session_state.debug_info.update({
        "Error uploading transcript": e,
    })
        return None, None

# Streamlit UI
st.set_page_config(page_title="OWL", 
                   layout="centered", 
                   initial_sidebar_state="expanded", menu_items=None)
logo_image_path = "owl-banner.png"
st.logo(logo_image_path, size="large") 
st.session_state.current_page = st.session_state.get("page", "OWL")
st.session_state.debug_info = {"Session State": "OK",}

if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.header("Oracle Workspace Listen (OWL)")
st.subheader("Powered by Oracle Speech and Generative AI")
st.info("Upload any audio or video file and then click transcribe.")

with st.sidebar:
    st.info("Oracle Workspace Listen (OWL) is envisioned as an internal tool that utilizes Oracle Cloud Platform services to accept an audio file as input and return to the user a full transcript and, optionally, a short summarization.")
    st.info("When using OWL, your data stays within your Oracle Cloud Tenancy. This means that data privacy is assured through our best-in-class security capabilities and your confidential data is never shared with third parties.")
    if st.button("Clear Session", type="primary", use_container_width=True, help="Remove the existing file, clear session, and start over."):
        st.session_state.clear()
        st.session_state.submitted = False
        st.toast("Session cleared! You can now upload a new file.")
        st.rerun()
    # with st.expander("Admin Controls"):
    #     if st.button("Clear All Files", help="Clear all files from object storage.", type="primary", use_container_width=True,):
    #         # delete_objects_with_prefix(input_prefix + "/") 
    #         # delete_objects_with_prefix(final_prefix + "/")
    #         # delete_objects_with_prefix(output_prefix + "/")
    #         st.toast("Deleted all files from Object Storage!")
    #     # if st.button("Clear Uploads", help="Clear all uploaded audio/video files."):
    #     #     delete_objects_with_prefix(input_prefix + "/")  # Add "/" to avoid deleting unintended objects
    #     # if st.button("Clear Transcripts", help="Clear all generated transcripts."):
    #     #     delete_objects_with_prefix(final_prefix + "/")
    #     # if st.button("Clear Speech Output", help="Clear all intermediate speech output files."):
    #     #     delete_objects_with_prefix(output_prefix + "/")
    # with st.expander("Debug Info"):
    #     for key, value in st.session_state.debug_info.items():
    #         st.write(f"{key}: {value}")


file_uploader_placeholder = st.empty()
transcribe_button_placeholder = st.empty()
summary_checkbox_placeholder = st.empty()
create_summary = True

if not st.session_state.submitted: 
    uploaded_file = file_uploader_placeholder.file_uploader("Upload an audio or video file and then click transcribe.", 
    help="Allowed file types: aac, ac3, amr, au, flac, m4a, mkv, mp3, mp4, oga, ogg, wav, webm")
    if transcribe_button_placeholder.button("Transcribe",type="primary",help="This will take about 3-4 minutes for a 20 minute recording.", use_container_width = True) and uploaded_file is not None:
        st.session_state.submitted = True
        filename = uploaded_file.name
        st.session_state.debug_info.update({
            "Starting transcription job for": filename
        })
    if summary_checkbox_placeholder.checkbox("Generate Summary", help="Check this box to also generate a summary.", value=True ):
        create_summary = True
        st.session_state.debug_info.update({
            "Generate Short Summary": "True"
        })

if st.session_state.submitted:
    # Clear the placeholders to remove the elements from the UI
    file_uploader_placeholder.empty()
    transcribe_button_placeholder.empty()
    summary_checkbox_placeholder.empty() 

if st.session_state.submitted and "transcript" not in st.session_state:
    with st.spinner("Transcribing..."):
        audio_upload_name = upload_audio_file(uploaded_file)
        filename = uploaded_file.name 
        job_id, out_loc = create_speech_job(audio_upload_name, filename)
        res_file = wait_for_job_completion(job_id, out_loc)
        json_data = download_speech_json(res_file)
        transcript = create_transcript(json_data)
        st.session_state.transcript = transcript

        if transcript:
            (
                transcript_object_name,
                object_storage_url,
            ) = upload_transcript_to_object_storage(
                transcript, audio_upload_name, model_type
            )
            st.session_state.transcript_object_name = transcript_object_name  
            if create_summary:
                summary = generate_summary(st.session_state.transcript, summary_instruction) # Pass summary_instruction here
                if summary:
                    (
                        summary_object_name,
                        summary_object_url,
                    ) = upload_summary_to_object_storage(
                        summary, audio_upload_name
                    )
                    st.session_state.summary_object_name = summary_object_name
                    st.session_state.summary = summary


if "transcript" in st.session_state and st.session_state.transcript:
    st.download_button(
        label="Download Transcript",
        type="primary",
        use_container_width= True,
        data=st.session_state.transcript,
        file_name=st.session_state.transcript_object_name,
        mime="text/plain",
        key="download_transcript" 
    )
    if not create_summary and "summary_object_name" not in st.session_state:
        with st.expander("Show Transcript"):
            st.text_area("Transcript", value=st.session_state.transcript, height=300)


    if create_summary and "summary_object_name" in st.session_state:
        st.download_button(
            label="Download Summary",
            use_container_width= True,
            type="primary",
            data=st.session_state.summary,
            file_name=st.session_state.summary_object_name,
            mime="text/plain",
            key="download_summary"
        )
        with st.expander("Show Transcript"):
            st.text_area("Transcript", value=st.session_state.transcript, height=300)
        with st.expander("Show Summary"):
            st.markdown(st.session_state.summary)