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

Output Structure:
Produce clearly labeled sections containing a Headline and a Subheading/Body for:
1. Analytical Version
2. Executive Summary Version
3. Business / CSM Version
"""

# --- 2. MULTI-CHAT MEMORY INITIALIZATION ---
st.set_page_config(page_title="Insight Rewriter Pro", page_icon="📊", layout="wide") # Changed to 'wide' to accommodate sidebar

# Initialize the dictionary that holds all sessions
if "sessions" not in st.session_state:
    st.session_state.sessions = {"Session 1": {"messages": [], "processed_files": []}}
    st.session_state.current_session = "Session 1"
    st.session_state.session_counter = 1

# Helper variable for the currently active session
current = st.session_state.current_session

# --- 3. SIDEBAR: NAVIGATION & UPLOADS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    st.divider()
    
    # NEW CHAT BUTTON
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        st.session_state.session_counter += 1
        new_session_name = f"Session {st.session_state.session_counter}"
        st.session_state.sessions[new_session_name] = {"messages": [], "processed_files": []}
        st.session_state.current_session = new_session_name
        st.rerun()

    # CHAT HISTORY LIST
    st.subheader("🗂️ Chat History")
    for session_name in list(st.session_state.sessions.keys()):
        # Draw a button for each past session. Disable the button if it's the one currently open.
        if st.button(
            session_name, 
            use_container_width=True, 
            disabled=(session_name == st.session_state.current_session)
        ):
            st.session_state.current_session = session_name
            st.rerun()
            
    st.divider()
    
    # FILE UPLOADER (Specific to the current session)
    st.header("📎 Upload Data")
    uploaded_files = st.file_uploader(
        f"Attach to {current}", 
        accept_multiple_files=True, 
        type=['csv', 'xml', 'txt', 'png', 'jpg', 'jpeg'],
        key=f"uploader_{current}" # Ensures uploader clears when switching sessions
    )

# --- 4. MAIN UI: DISPLAY CURRENT CHAT ---
st.title(f"📊 Insight Rewriter Pro - {current}")

# Display messages for the currently selected session
for message in st.session_state.sessions[current]["messages"]:
    with st.chat_message(message["role"]):
        if message.get("content"):
            st.markdown(message["content"])
        if message.get("images"):
            for img_dict in message["images"]:
                st.image(img_dict["img_obj"], width=250)

# --- 5. CHAT INPUT & GENERATION ---
if prompt := st.chat_input(f"Message {current}..."):
    
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first.")
    else:
        attached_text_content = ""
        attached_images = []

        # Process uploads for THIS specific session
        if uploaded_files:
            for file in uploaded_files:
                file_id = f"{file.name}_{file.size}"
                
                if file_id not in st.session_state.sessions[current]["processed_files"]:
                    st.session_state.sessions[current]["processed_files"].append(file_id)
                    
                    if file.type in ["text/csv", "text/xml", "text/plain"] or file.name.endswith(('.csv', '.xml', '.txt')):
                        attached_text_content += f"\n\n--- Content of {file.name} ---\n"
                        attached_text_content += file.getvalue().decode("utf-8")
                    
                    elif file.type.startswith("image/"):
                        attached_images.append({
                            "bytes": file.getvalue(),
                            "mime_type": file.type,
                            "img_obj": Image.open(file)
                        })

        full_prompt = prompt
        if attached_text_content:
            full_prompt += f"\n\n[USER ATTACHED DATA FILE]:\n{attached_text_content}"

        # Save user message to CURRENT session memory
        st.session_state.sessions[current]["messages"].append({
            "role": "user", 
            "content": full_prompt,
            "images": attached_images,
            "display_prompt": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            if attached_text_content:
                st.info("📄 Data file(s) successfully attached.")
            for img_dict in attached_images:
                st.image(img_dict["img_obj"], width=250)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data and generating insights..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # Package only the CURRENT session's history for the AI
                    gemini_history = []
                    for msg in st.session_state.sessions[current]["messages"]:
                        role = "user" if msg["role"] == "user" else "model"
                        parts = []
                        
                        if msg.get("content"):
                            parts.append(types.Part.from_text(text=msg["content"]))
                        
                        if msg.get("images"):
                            for img_dict in msg["images"]:
                                parts.append(types.Part.from_bytes(
                                    data=img_dict["bytes"],
                                    mime_type=img_dict["mime_type"]
                                ))
                        
                        gemini_history.append(types.Content(role=role, parts=parts))

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=gemini_history,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.3,
                        )
                    )
                    
                    response_text = response.text
                    st.markdown(response_text)
                    
                    # Save AI response to CURRENT session memory
                    st.session_state.sessions[current]["messages"].append({"role": "assistant", "content": response_text})

                except Exception as e:
                    st.error(f"An error occurred: {e}")
