import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# --- 1. THE MASTER PROMPT ---
SYSTEM_PROMPT = """
You are an expert data storytelling and insight rewriting assistant designed to help analysts transform raw data insights into clear, audience‑specific narratives. Adopt a high-level strategic partner persona that synthesizes data into actionable executive insights.

Your primary objective is to rewrite or rephrase insights provided by analysts into three distinct tones, while preserving factual accuracy and analytical integrity. 

Core Rules & Input Handling:
* Interpret the input accurately before rewriting.
* Clearly infer insights if they are implied, but NEVER fabricate data or assumptions.
* If the input is incomplete or ambiguous, ask for clarification.
* Prioritize performance efficiency and behavioral analysis over raw data reporting. Explain the "why" behind the data.

Style & Formatting Guidelines:
* Concise & Scannable: Restrict narratives to 2–4 sentences per section to maintain executive-level brevity. 
* Lead-In Headlines: Begin each section with a bold, descriptive headline.
* Terminology: Use professional, precise metrics. Incorporate industry shorthand where appropriate (KPI, CPA, CVR, ROAS, VCR, CTV).
* Action-Oriented: Lead recommendations with strong verbs (Leverage, Capitalize, Optimize). Use performance qualifiers (steadily outperformed, successfully stabilized).
* Persona Storytelling: Give user groups intuitive labels (e.g., "Strategic Community Influencers").

Output Structure (Unless the user is specifically asking for a revision):
Produce clearly labeled sections containing a Headline and a Subheading/Body for:
1. Analytical Version
2. Executive Summary Version
3. Business / CSM Version
"""

# --- 2. SET UP THE WEB UI ---
st.set_page_config(page_title="Insight Rewriter Pro", page_icon="📊", layout="centered")
st.title("📊 Insight Rewriter Pro")
st.write("Upload data or screenshots, and refine the insights through conversation.")

# Initialize memory arrays
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = [] # Keeps track of files so we don't upload them twice

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    st.divider()
    st.header("📎 Upload Data")
    uploaded_files = st.file_uploader(
        "Upload CSV, XML, TXT, or Screenshots", 
        accept_multiple_files=True, 
        type=['csv', 'xml', 'txt', 'png', 'jpg', 'jpeg']
    )
    st.caption("Files will be attached to your next message.")

    st.divider()
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.messages = []
        st.session_state.processed_files = []
        st.rerun()

# --- 3. CONVERSATIONAL MEMORY DISPLAY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Show text
        if message.get("content"):
            st.markdown(message["content"])
        # Show images if any
        if message.get("images"):
            for img_dict in message["images"]:
                st.image(img_dict["img_obj"], width=250)

# --- 4. CHAT INPUT & GENERATION ---
if prompt := st.chat_input("Ask me to analyze the uploaded data, or paste raw insights..."):
    
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first.")
    else:
        # Process newly uploaded files
        attached_text_content = ""
        attached_images = []

        if uploaded_files:
            for file in uploaded_files:
                # Create a unique ID so we only process each file once
                file_id = f"{file.name}_{file.size}"
                
                if file_id not in st.session_state.processed_files:
                    st.session_state.processed_files.append(file_id)
                    
                    # Handle Text-based Data (CSV, XML, TXT)
                    if file.type in ["text/csv", "text/xml", "text/plain"] or file.name.endswith(('.csv', '.xml', '.txt')):
                        attached_text_content += f"\n\n--- Content of {file.name} ---\n"
                        attached_text_content += file.getvalue().decode("utf-8")
                    
                    # Handle Images (Screenshots)
                    elif file.type.startswith("image/"):
                        attached_images.append({
                            "bytes": file.getvalue(),
                            "mime_type": file.type,
                            "img_obj": Image.open(file) # Used to display in Streamlit UI
                        })

        # Combine the user prompt with the text data
        full_prompt = prompt
        if attached_text_content:
            full_prompt += f"\n\n[USER ATTACHED DATA FILE]:\n{attached_text_content}"

        # 1. Save the user's message to memory
        st.session_state.messages.append({
            "role": "user", 
            "content": full_prompt,
            "images": attached_images,
            "display_prompt": prompt # We save just the prompt so the UI doesn't show massive CSV walls of text
        })

        # 2. Display the user's message in the UI immediately
        with st.chat_message("user"):
            st.markdown(prompt)
            if attached_text_content:
                st.info("📄 Data file(s) successfully attached and read by the AI.")
            for img_dict in attached_images:
                st.image(img_dict["img_obj"], width=250)

        # 3. Generate the AI's response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data and generating insights..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # Format the memory for Gemini (including images and text)
                    gemini_history = []
                    for msg in st.session_state.messages:
                        role = "user" if msg["role"] == "user" else "model"
                        parts = []
                        
                        # Add Text Part
                        if msg.get("content"):
                            parts.append(types.Part.from_text(text=msg["content"]))
                        
                        # Add Image Parts
                        if msg.get("images"):
                            for img_dict in msg["images"]:
                                parts.append(
                                    types.Part.from_bytes(
                                        data=img_dict["bytes"],
                                        mime_type=img_dict["mime_type"]
                                    )
                                )
                        
                        gemini_history.append(types.Content(role=role, parts=parts))

                    # Send to model
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=gemini_history,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.3,
                        )
                    )
                    
                    # Display the new response
                    response_text = response.text
                    st.markdown(response_text)
                    
                    # Save response to memory
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                except Exception as e:
                    st.error(f"An error occurred: {e}")
