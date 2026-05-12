import streamlit as st
from google import genai
from google.genai import types

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
* Lead-In Headlines: Begin each section with a bold, descriptive headline that summarizes the primary takeaway.
* Terminology: Use professional, precise metrics. Incorporate industry shorthand where appropriate (KPI, CPA, CVR, ROAS, VCR, CTV, OLV, LLM, iCAC).
* Action-Oriented: Lead recommendations with strong verbs (Leverage, Capitalize, Optimize, Strengthen, Activate). Use performance qualifiers (steadily outperformed, successfully stabilized).
* Persona Storytelling: Give user groups intuitive, human-readable labels (e.g., "Strategic Community Influencers").

Output Structure:
For every request, produce clearly labeled sections containing a Headline and a Subheading/Body for:
1. Analytical Version
2. Executive Summary Version
3. Business / CSM Version
"""

# --- 2. SET UP THE WEB UI ---
st.set_page_config(page_title="Insight Rewriter Pro", page_icon="📊", layout="centered")
st.title("📊 Insight Rewriter Pro")
st.write("Transform raw data insights into audience‑specific narratives instantly.")

# Sidebar for the API Key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("[Get your free API key here](https://aistudio.google.com/app/apikey)")

# Main input area
user_input = st.text_area("Paste raw data insights, tables, or bullet points here:", height=200)

# Generate Button
if st.button("Rewrite Insights", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first.")
    elif not user_input.strip():
        st.warning("⚠️ Please paste some data or insights to rewrite.")
    else:
        with st.spinner("Analyzing and rewriting..."):
            try:
                # Initialize the Gemini API client
                client = genai.Client(api_key=api_key)
                
                # Generate the response
                response = client.models.generate_content(
                    model="gemini-2.5-flash", # Using the fastest standard model
                    contents=user_input,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3, # Low temp for analytical accuracy
                    )
                )
                
                # Display the results
                st.success("Success!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
