
import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions
)
from core.rag_engine import build_rag_chain, ask_question


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="MeetMind | AI Meeting Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "meeting_data" not in st.session_state:
    st.session_state.meeting_data = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "processing" not in st.session_state:
    st.session_state.processing = False


# --------------------------------------------------
# EXISTING BACKEND PIPELINE
# --------------------------------------------------

def run_pipeline(source: str, language: str = "english") -> dict:

    chunks = process_input(source)

    transcript = transcribe_all(chunks, language)

    if not transcript or not transcript.strip():
        raise ValueError("No transcription was generated.")

    title = generate_title(transcript)
    summary = summarize(transcript)

    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain
    }


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

/* Main application */
.stApp {
    background: #0B0F19;
    color: #E5E7EB;
}

/* Main content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #263244;
}

/* Headings */
h1, h2, h3 {
    color: #F9FAFB !important;
    font-weight: 700 !important;
}

/* Paragraphs */
p, label {
    color: #CBD5E1;
}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #151E2E;
    border: 1px solid #26364D;
    border-radius: 14px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #6366F1, #8B5CF6);
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    min-height: 43px;
    transition: 0.2s;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    border: none;
    color: white;
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: #111827 !important;
    color: white !important;
    border: 1px solid #334155 !important;
    border-radius: 9px !important;
}

.stSelectbox div[data-baseweb="select"] {
    background: #111827;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px;
    border-bottom: 1px solid #263244;
}

.stTabs [data-baseweb="tab"] {
    color: #94A3B8;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    color: #A78BFA !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #151E2E;
    padding: 18px;
    border: 1px solid #26364D;
    border-radius: 12px;
}

[data-testid="stMetricValue"] {
    color: #A78BFA;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #151E2E;
    border: 1px solid #26364D;
    border-radius: 12px;
    padding: 12px;
}

/* Dividers */
hr {
    border-color: #263244;
}

/* Custom classes */
.brand {
    font-size: 27px;
    font-weight: 800;
    color: #A78BFA;
    letter-spacing: -1px;
}

.tagline {
    color: #94A3B8;
    font-size: 13px;
}

.hero {
    padding: 28px;
    background: linear-gradient(120deg, #191E38, #20213D, #17253B);
    border: 1px solid #393B69;
    border-radius: 18px;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 32px;
    font-weight: 800;
    color: white;
}

.hero-text {
    color: #A5B4FC;
    font-size: 15px;
}

.section-label {
    color: #A78BFA;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.empty-state {
    background: #151E2E;
    border: 1px dashed #475569;
    padding: 35px;
    border-radius: 15px;
    text-align: center;
    color: #94A3B8;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def render_content(content):

    if content is None:
        st.info("No information available.")
        return

    if isinstance(content, list):
        if not content:
            st.info("No items found.")
        else:
            for i, item in enumerate(content, 1):
                st.markdown(f"**{i}.** {item}")

    elif isinstance(content, dict):
        st.json(content)

    else:
        st.markdown(str(content))


def process_meeting(source, language):

    try:
        with st.spinner(
            "MeetMind is analyzing your meeting... This may take a while."
        ):
            result = run_pipeline(source, language)

        st.session_state.meeting_data = result
        st.session_state.chat_history = []

        st.success("Your meeting has been successfully analyzed!")
        st.rerun()

    except Exception as e:
        st.error(f"Processing failed: {str(e)}")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="brand">🧠 MeetMind</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="tagline">Intelligent Video & Meeting Assistant</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### ⚙️ Workspace")

    input_mode = st.radio(
        "Choose input source",
        ["YouTube URL", "Upload File"]
    )

    language = st.selectbox(
        "Transcription Language",
        ["english", "hinglish"],
        index=0
    )

    st.divider()

    st.markdown("### 📌 Capabilities")

    st.markdown("""
    - 🎙️ Audio Transcription
    - 📝 AI Summarization
    - ✅ Action Item Extraction
    - 🔑 Decision Detection
    - ❓ Question Extraction
    - 💬 RAG-based Meeting Chat
    """)

    st.divider()

    if st.session_state.meeting_data:

        st.success("Meeting analyzed")

        if st.button("🗑️ Clear Workspace", use_container_width=True):
            st.session_state.meeting_data = None
            st.session_state.chat_history = []
            st.rerun()

    else:
        st.caption("No meeting loaded yet.")

    st.markdown("---")
    st.caption("Powered by LangChain & AI")


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="section-label">AI-POWERED PRODUCTIVITY</div>
    <div class="hero-title">
        Your Meetings. <span style="color:#A78BFA">Smarter.</span>
    </div>
    <div class="hero-text">
        Transform lengthy videos and meetings into actionable insights.
        Transcribe, summarize, extract decisions, and chat with your meetings.
    </div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------

if not st.session_state.meeting_data:

    st.markdown("## 🚀 Analyze a Meeting")

    st.markdown(
        "Upload your recording or paste a YouTube link to get started."
    )

    with st.container(border=True):

        if input_mode == "YouTube URL":

            source = st.text_input(
                "YouTube Video URL",
                placeholder="https://www.youtube.com/watch?v=...",
            )

            st.caption("Paste the URL of the video you want to analyze.")

            if st.button(
                "✨ Analyze ",
                use_container_width=True
            ):

                if not source.strip():
                    st.warning("Please enter a YouTube URL.")
                else:
                    process_meeting(source.strip(), language)

        else:

            uploaded_file = st.file_uploader(
                "Upload Audio / Video",
                type=[
                    "mp3", "wav", "m4a", "ogg", "flac",
                    "mp4", "mkv", "mov", "avi", "webm"
                ]
            )

            if uploaded_file:

                st.audio(uploaded_file) if uploaded_file.type.startswith(
                    "audio"
                ) else st.video(uploaded_file)

                st.caption(
                    f"Selected file: {uploaded_file.name}"
                )

            if st.button(
                "✨ Analyze ",
                use_container_width=True
            ):

                if uploaded_file is None:
                    st.warning("Please upload an audio or video file.")

                else:

                    temp_path = None

                    try:
                        suffix = os.path.splitext(
                            uploaded_file.name
                        )[1]

                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=suffix
                        ) as temp_file:

                            temp_file.write(uploaded_file.getbuffer())
                            temp_path = temp_file.name

                        process_meeting(temp_path, language)

                    finally:
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)


    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### ✨ What MeetMind can do")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("### 🎙️")
            st.markdown("**Smart Transcription**")
            st.caption(
                "Convert meeting recordings into readable transcripts."
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 🧠")
            st.markdown("**Intelligent Insights**")
            st.caption(
                "Automatically identify summaries, tasks and decisions."
            )

    with col3:
        with st.container(border=True):
            st.markdown("### 💬")
            st.markdown("**Chat with Meetings**")
            st.caption(
                "Ask questions and retrieve information using RAG."
            )


# --------------------------------------------------
# RESULTS DASHBOARD
# --------------------------------------------------

else:

    data = st.session_state.meeting_data

    st.markdown("## 📊 Meeting Dashboard")

    st.markdown(
        f"### {data['title']}"
    )

    st.caption("Your meeting has been processed successfully.")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Transcript",
            "Ready",
            "Generated"
        )

    with col2:
        st.metric(
            "Summary",
            "Ready",
            "Generated"
        )

    with col3:
        st.metric(
            "Action Items",
            len(data["action_items"])
            if isinstance(data["action_items"], list)
            else "Ready"
        )

    with col4:
        st.metric(
            "Key Decisions",
            len(data["key_decisions"])
            if isinstance(data["key_decisions"], list)
            else "Ready"
        )

    st.divider()

    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Summary",
        "🎙️ Transcript",
        "✅ Action Items",
        "🔑 Decisions",
        "❓ Questions",
        "💬 AI Chat"
    ])

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    with tab1:

        st.markdown("### 📝 Meeting Summary")

        with st.container(border=True):
            render_content(data["summary"])

        st.download_button(
            "⬇️ Download Summary",
            data=str(data["summary"]),
            file_name="meetmind_summary.txt",
            mime="text/plain"
        )

    # --------------------------------------------------
    # TRANSCRIPT
    # --------------------------------------------------

    with tab2:

        st.markdown("### 🎙️ Full Transcript")

        transcript = data["transcript"]

        st.text_area(
            "Meeting Transcript",
            value=transcript,
            height=450,
            disabled=True
        )

        st.download_button(
            "⬇️ Download Transcript",
            data=transcript,
            file_name="meetmind_transcript.txt",
            mime="text/plain"
        )

    # --------------------------------------------------
    # ACTION ITEMS
    # --------------------------------------------------

    with tab3:

        st.markdown("### ✅ Action Items")

        st.caption(
            "Tasks and follow-ups extracted from your meeting."
        )

        with st.container(border=True):
            render_content(data["action_items"])

    # --------------------------------------------------
    # KEY DECISIONS
    # --------------------------------------------------

    with tab4:

        st.markdown("### 🔑 Key Decisions")

        st.caption(
            "Important decisions identified during the discussion."
        )

        with st.container(border=True):
            render_content(data["key_decisions"])

    # --------------------------------------------------
    # OPEN QUESTIONS
    # --------------------------------------------------

    with tab5:

        st.markdown("### ❓ Open Questions")

        st.caption(
            "Questions that were raised or remain unresolved."
        )

        with st.container(border=True):
            render_content(data["open_questions"])

    # --------------------------------------------------
    # RAG CHAT
    # --------------------------------------------------

    with tab6:

        st.markdown("### 💬 Chat with your Meeting")

        st.caption(
            "Ask anything about your meeting. "
            "MeetMind will retrieve relevant context and answer."
        )

        # Chat history
        for message in st.session_state.chat_history:

            with st.chat_message(message["role"]):

                st.markdown(message["content"])

        # Chat input
        user_question = st.chat_input(
            "Ask something about your meeting..."
        )

        if user_question:

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })

            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    try:
                        answer = ask_question(
                            data["rag_chain"],
                            user_question
                        )

                        st.markdown(str(answer))

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": str(answer)
                        })

                    except Exception as e:

                        st.error(f"Chat error: {str(e)}")

