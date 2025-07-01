import streamlit as st
from openai import OpenAI
import requests
import json
import time
import datetime
from typing import Dict, List, Optional
import re
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Existential Companion",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UX
st.markdown("""
<style>
    /* Main container max width */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .hero-image {
        width: 100%;
        max-width: 600px;
        height: auto;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #1976d2;
        margin-left: 2rem;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #7b1fa2;
        margin-right: 2rem;
    }
    
    .theme-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Big Talk Button */
    .talk-button {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
    }
    
    .talk-btn {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 20px 40px;
        font-size: 24px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        min-width: 200px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .talk-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
    }
    
    .talk-btn.recording {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
        animation: pulse 1.5s infinite;
    }
    
    .talk-btn.recording:hover {
        box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Audio player styling */
    .audio-player {
        margin: 1rem 0;
        text-align: center;
    }
    
    .audio-player audio {
        width: 100%;
        max-width: 400px;
        border-radius: 25px;
    }
    
    /* Input styling */
    .stTextArea textarea {
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        font-size: 16px;
        padding: 15px;
    }
    
    .stTextArea textarea:focus {
        border-color: #2a5298;
        box-shadow: 0 0 10px rgba(42, 82, 152, 0.1);
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 25px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .talk-btn {
            font-size: 20px;
            padding: 15px 30px;
            min-width: 150px;
        }
        
        .user-message, .ai-message {
            margin-left: 0;
            margin-right: 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.conversation_history = []
    st.session_state.life_themes = []
    st.session_state.user_profile = {}
    st.session_state.current_month = 1
    st.session_state.session_count = 0
    st.session_state.consent_given = False
    st.session_state.api_keys_set = False

# Safety keywords for risk detection
SAFETY_KEYWORDS = [
    'suicide', 'kill myself', 'end it all', 'want to die', 'hurt myself',
    'self harm', 'cutting', 'overdose', 'jumping', 'hanging'
]

# Monthly prompt frameworks
MONTHLY_PROMPTS = {
    1: {
        "theme": "Orientation & Life Audit",
        "description": "Understanding where you are and what feels 'off'",
        "sample_prompts": [
            "What part of your daily routine feels most automatic or disconnected?",
            "If you could change one thing about how you spend your time, what would it be?",
            "What used to bring you joy that doesn't anymore?",
            "When did you last feel truly engaged with what you were doing?"
        ],
        "focus_areas": ["current_state", "disconnection", "routine_audit", "engagement_patterns"]
    },
    2: {
        "theme": "Mortality & Time Awareness",
        "description": "Confronting the finite nature of life and time",
        "sample_prompts": [
            "Imagine your 75-year-old self looking back. What do they wish you had done differently?",
            "What would you regret not doing if you only had five years left?",
            "How do you want to be remembered by the people closest to you?",
            "What legacy do you want to leave behind?"
        ],
        "focus_areas": ["future_regrets", "legacy", "time_consciousness", "mortality_reflection"]
    },
    3: {
        "theme": "Freedom & Personal Agency",
        "description": "Exploring choice, control, and authentic decision-making",
        "sample_prompts": [
            "What choices do you make on autopilot every day?",
            "Where in your life do you feel most free? Least free?",
            "What would you do if you weren't afraid of judgment?",
            "What responsibilities could you let go of without real consequence?"
        ],
        "focus_areas": ["autonomy", "fear_patterns", "authentic_choices", "responsibility_audit"]
    },
    4: {
        "theme": "Connection & Authentic Relationships",
        "description": "Examining isolation, intimacy, and being truly known",
        "sample_prompts": [
            "Who really knows the real you? What parts do you hide?",
            "What would deeper connection look like in your relationships?",
            "When do you feel most lonely, even when surrounded by people?",
            "What prevents you from being more vulnerable with others?"
        ],
        "focus_areas": ["intimacy", "vulnerability", "loneliness", "authentic_connection"]
    },
    5: {
        "theme": "Vision & Creative Imagination",
        "description": "Reconnecting with dreams, possibilities, and creative potential",
        "sample_prompts": [
            "Design a perfect day that's entirely yours. What does it feel like?",
            "What dreams did you abandon that still whisper to you?",
            "If resources weren't a constraint, what would you create or explore?",
            "What would 'enough' look like in your life?"
        ],
        "focus_areas": ["ideal_vision", "abandoned_dreams", "creative_potential", "sufficiency"]
    },
    6: {
        "theme": "Commitment & Life Integration",
        "description": "Aligning values with actions and creating sustainable change",
        "sample_prompts": [
            "What values feel worth protecting for the rest of your life?",
            "How can you honor what you've discovered about yourself?",
            "What small change could you make that would have the biggest impact?",
            "How will you remember these insights when life gets busy again?"
        ],
        "focus_areas": ["core_values", "sustainable_change", "integration", "commitment"]
    }
}

def check_api_keys():
    """Check if required API keys are configured"""
    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
        
        # Initialize OpenAI client
        if 'openai_client' not in st.session_state:
            st.session_state.openai_client = OpenAI(api_key=openai_key)
        
        return True
    except:
        st.error("🔑 OpenAI API key not configured in Streamlit secrets. Please contact the app administrator.")
        st.stop()
        return False

def detect_safety_concerns(text: str) -> bool:
    """Detect potential safety concerns in user input"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SAFETY_KEYWORDS)

def generate_safety_response():
    """Generate appropriate safety response"""
    return """I hear that you're going through a really difficult time, and I'm concerned about you. While I'm here to support your reflection, I'm not equipped to help with thoughts of self-harm.

Please reach out to someone who can provide immediate support:
- **Samaritans**: 116 123 (free, 24/7)
- **Crisis Text Line**: Text HOME to 85258
- **Emergency**: 999

Your life has value, and there are people trained to help you through this difficult period. Please don't go through this alone."""

def extract_themes_from_conversation(conversation: List[Dict]) -> List[str]:
    """Extract recurring themes from conversation history"""
    # Simple keyword-based theme extraction
    # In a full version, this would use more sophisticated NLP
    
    themes = []
    conversation_text = " ".join([msg["content"] for msg in conversation if msg["role"] == "user"])
    
    theme_keywords = {
        "Work Dissatisfaction": ["work", "job", "career", "meaningless", "unfulfilled"],
        "Relationship Concerns": ["lonely", "connection", "relationship", "family", "friends"],
        "Time Awareness": ["time", "aging", "years", "future", "past", "regret"],
        "Purpose & Meaning": ["purpose", "meaning", "point", "why", "direction"],
        "Identity Questions": ["who am i", "identity", "self", "authentic", "real me"],
        "Freedom & Control": ["trapped", "stuck", "control", "choice", "freedom"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in conversation_text.lower() for keyword in keywords):
            themes.append(theme)
    
    return themes[:5]  # Return top 5 themes

def get_ai_response(user_input: str, conversation_history: List[Dict], current_month: int) -> str:
    """Generate AI response using GPT-4"""
    
    # Check for safety concerns first
    if detect_safety_concerns(user_input):
        return generate_safety_response()
    
    # Get current month's framework
    month_info = MONTHLY_PROMPTS.get(current_month, MONTHLY_PROMPTS[1])
    
    # Build system prompt
    system_prompt = f"""You are an empathetic AI companion helping someone navigate existential questions and find meaning. You are NOT a therapist.

Current focus: {month_info['theme']} - {month_info['description']}

Your approach:
- Ask thoughtful, deeper questions that invite reflection
- Be warm but not overly enthusiastic
- Avoid therapy language or clinical terms
- Help users explore their own insights rather than giving advice
- Focus on the current month's theme when relevant
- Keep responses conversational and human-like
- If they seem stuck, offer a gentle prompt or question
- Acknowledge their thoughts before asking new questions

Remember: You're a supportive companion for self-reflection, not a counselor or life coach."""

    # Prepare messages for API
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 exchanges to manage token limits)
    recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    messages.extend(recent_history)
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    try:
        client = st.session_state.openai_client
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Much faster than gpt-4, still very good quality
            messages=messages,
            max_tokens=400,  # Slightly shorter responses for speed
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"I'm having trouble connecting right now. Could you try again? (Error: {str(e)})"

def text_to_speech(text: str, voice: str = None) -> Optional[bytes]:
    """Convert text to speech using OpenAI TTS API"""
    try:
        client = st.session_state.openai_client
        
        # Use selected voice or default to 'alloy'
        selected_voice = voice or st.session_state.get('selected_voice', 'alloy')
        
        response = client.audio.speech.create(
            model="tts-1-hd",  # Faster than tts-1, still high quality
            voice=selected_voice,
            input=text,
            response_format="mp3",
            speed=1.1  # Slightly faster speech
        )
        
        return response.content
        
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

def create_audio_player(audio_bytes: bytes, key: str = "audio_player") -> None:
    """Create an audio player for the generated speech"""
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <div class="audio-player">
            <audio controls autoplay>
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

def speech_to_text(audio_data: bytes) -> str:
    """Convert speech to text using OpenAI Whisper"""
    try:
        # Create a temporary file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        client = st.session_state.openai_client
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        return response
        
    except Exception as e:
        st.error(f"Speech recognition error: {str(e)}")
        return ""

def process_audio_input(audio_bytes: bytes):
    """Process audio input through Whisper and then to conversation"""
    if not audio_bytes:
        return
    
    # Step 1: Transcribe with clear progress
    with st.spinner("🎤 Listening... (transcribing your voice)"):
        transcribed_text = speech_to_text(audio_bytes)
    
    if transcribed_text.strip():
        # Show what was transcribed immediately
        st.info(f"💭 **You said:** \"{transcribed_text}\"")
        
        # Step 2: Process with AI - show what's happening
        with st.spinner("🤔 Thinking about your message..."):
            # Process the transcribed text as regular input
            process_user_input(transcribed_text.strip())
    else:
        st.error("🎤 Sorry, I couldn't understand what you said. Please try recording again.")
        st.rerun()

# Main App Interface

def show_consent_screen():
    """Show initial consent and onboarding"""
    st.markdown('''
    <div class="main-header">
        <h1>Existential Companion</h1>
        <p>A space for authentic self-reflection and meaning-making</p>
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=984,h=487,fit=crop/ALpnwqvBGysjXvjO/ai-agents-AVL7OZZxZ0SlROGa.png" 
             class="hero-image" alt="AI Companion" />
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to Your Reflective Journey
    
    This is a **private space** for exploring life's deeper questions through conversation with an AI companion. 
    
    **This is not therapy** - it's a tool for self-reflection and personal insight.
    """)
    
    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.markdown("""
    **Important Disclaimers:**
    - This tool is for reflection and personal insight, not mental health treatment
    - If you're experiencing thoughts of self-harm, please contact Samaritans (116 123) or emergency services (999)
    - Your conversations are private but please don't share sensitive personal information
    - Use your judgment about what to share
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("I understand and want to continue", key="consent_button", use_container_width=True):
            st.session_state.consent_given = True
            st.rerun()

def show_api_setup():
    """Show API key setup for development - only when needed"""
    st.markdown("### 🔑 Quick Setup")
    st.info("Just need to add your API keys once to get started!")
    
    with st.expander("🚀 Get Your Free API Keys", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**OpenAI API Key**")
            st.markdown("1. Go to [platform.openai.com](https://platform.openai.com/api-keys)")
            st.markdown("2. Sign up/login")
            st.markdown("3. Create new secret key")
            openai_key = st.text_input("OpenAI Key (starts with sk-)", type="password", key="openai_setup")
        
        with col2:
            st.markdown("**ElevenLabs API Key**")
            st.markdown("1. Go to [elevenlabs.io](https://elevenlabs.io)")
            st.markdown("2. Sign up (free tier available)")
            st.markdown("3. Go to Profile → API Keys")
            elevenlabs_key = st.text_input("ElevenLabs Key", type="password", key="elevenlabs_setup")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✨ Start Using App", use_container_width=True, type="primary"):
            if openai_key and elevenlabs_key:
                # Store in session state
                st.session_state.temp_openai_key = openai_key
                st.session_state.temp_elevenlabs_key = elevenlabs_key
                st.session_state.api_keys_set = True
                st.session_state.openai_client = OpenAI(api_key=openai_key)
                st.success("🎉 All set! Your app is ready.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter both API keys to continue")

def show_main_interface():
    """Show the main chat interface"""
    
    # Header
    st.markdown('''
    <div class="main-header">
        <h1>Existential Companion</h1>
        <p>Your AI partner for life's deeper questions</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Sidebar with current month info and themes
    with st.sidebar:
        st.markdown("### Current Focus")
        month_info = MONTHLY_PROMPTS[st.session_state.current_month]
        st.markdown(f"**Month {st.session_state.current_month}:** {month_info['theme']}")
        st.markdown(month_info['description'])
        
        # Voice selection
        st.markdown("### 🎙️ Voice Settings")
        voice_options = {
            "alloy": "Alloy (Balanced)",
            "echo": "Echo (Male)",
            "fable": "Fable (British)",
            "onyx": "Onyx (Deep)",
            "nova": "Nova (Young Female)",
            "shimmer": "Shimmer (Soft)"
        }
        
        selected_voice = st.selectbox(
            "Choose AI voice:",
            options=list(voice_options.keys()),
            format_func=lambda x: voice_options[x],
            index=0,
            key="voice_selection"
        )
        
        # Store voice selection
        st.session_state.selected_voice = selected_voice
        
        st.markdown("### Emerging Themes")
        if st.session_state.life_themes:
            for theme in st.session_state.life_themes[-5:]:
                st.markdown(f"• {theme}")
        else:
            st.markdown("*Themes will appear as we talk*")
        
        st.markdown("### Session Info")
        st.markdown(f"Sessions: {st.session_state.session_count}")
        st.markdown(f"Messages: {len(st.session_state.conversation_history)}")
        
        if st.button("Start New Session"):
            st.session_state.conversation_history = []
            st.session_state.session_count += 1
            st.rerun()
    
    # Main chat interface
    st.markdown("### Conversation")
    
    # Display conversation history
    for i, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message ai-message"><strong>Companion:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
            # Add audio player for AI responses if TTS is enabled
            if st.session_state.get('enable_tts', True) and len(st.session_state.conversation_history) > 0:
                # Only generate audio for the most recent AI response to avoid overwhelming
                if i == len(st.session_state.conversation_history) - 1 and message["role"] == "assistant":
                    with st.spinner("Generating speech..."):
                        audio_bytes = text_to_speech(message["content"])
                        if audio_bytes:
                            create_audio_player(audio_bytes, f"audio_{i}")
    
    # Input methods
    st.markdown("### Share Your Thoughts")
    
    # Voice input section - Functional big button
    st.markdown("### 🎤 Voice Conversation")
    
    # Initialize recording state
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    
    # Functional Talk Button with JavaScript
    st.markdown(f'''
    <div class="talk-button">
        <button class="talk-btn" id="mainTalkButton" onclick="toggleRecording()">
            <span id="buttonText">TALK</span>
        </button>
    </div>
    
    <div id="recordingStatus" style="text-align: center; margin: 1rem 0; font-weight: bold; color: #666;">
        Ready to listen
    </div>
    
    <div id="audioPlayback" style="text-align: center; margin: 1rem 0;"></div>
    
    <script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    
    async function toggleRecording() {{
        const button = document.getElementById('mainTalkButton');
        const buttonText = document.getElementById('buttonText');
        const status = document.getElementById('recordingStatus');
        
        if (!isRecording) {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ 
                    audio: {{
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100
                    }}
                }});
                
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (event) => {{
                    audioChunks.push(event.data);
                }};
                
                mediaRecorder.onstop = async () => {{
                    const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                    
                    // Create download link for the audio (temporary solution)
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audioPlayer = document.createElement('audio');
                    audioPlayer.src = audioUrl;
                    audioPlayer.controls = true;
                    audioPlayer.style.width = '100%';
                    audioPlayer.style.maxWidth = '400px';
                    audioPlayer.style.borderRadius = '25px';
                    
                    const playbackDiv = document.getElementById('audioPlayback');
                    playbackDiv.innerHTML = '<p><strong>Your recording:</strong></p>';
                    playbackDiv.appendChild(audioPlayer);
                    
                    // Add a note about using the Streamlit recorder below
                    const note = document.createElement('p');
                    note.innerHTML = '<em>⬇️ Use the recorder below to send your message to the AI</em>';
                    note.style.color = '#2a5298';
                    note.style.fontWeight = 'bold';
                    playbackDiv.appendChild(note);
                    
                    audioChunks = [];
                    status.textContent = 'Recording complete! Use the recorder below to send to AI.';
                    status.style.color = '#2a5298';
                }};
                
                mediaRecorder.start();
                isRecording = true;
                button.classList.add('recording');
                buttonText.textContent = 'STOP & SEND';
                status.textContent = 'Recording... Click STOP & SEND when finished';
                status.style.color = '#f44336';
                
            }} catch (err) {{
                console.error('Error accessing microphone:', err);
                status.textContent = 'Microphone access denied. Please enable microphone permissions.';
                status.style.color = '#f44336';
            }}
        }} else {{
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            button.classList.remove('recording');
            buttonText.textContent = 'TALK';
            status.textContent = 'Processing your recording...';
            status.style.color = '#4caf50';
        }}
    }}
    </script>
    ''', unsafe_allow_html=True)
    
    # Streamlit audio input (for actual processing) - make it more prominent
    st.markdown("**Send your voice message to the AI:**")
    audio_input = st.audio_input("🎤 Click to record and send to AI", key="audio_recorder")
    
    # Auto-process when audio is recorded
    if audio_input is not None:
        # Check if this is a new recording by comparing with previous state
        if 'last_audio_input' not in st.session_state or st.session_state.last_audio_input != audio_input:
            st.session_state.last_audio_input = audio_input
            
            # Auto-submit the audio immediately
            with st.spinner("🎤 Processing your voice message..."):
                audio_bytes = audio_input.read()
                if audio_bytes:
                    # Show brief confirmation
                    st.success("🎤 Voice message received! Processing...")
                    
                    # Process the audio
                    process_audio_input(audio_bytes)
    
    st.markdown("---")
    
    # Text input
    st.markdown("### ✍️ Text Conversation")
    st.markdown("*Prefer to type? Share your thoughts here:*")
    user_input = st.text_area(
        "What's on your mind today?", 
        height=120, 
        key="text_input", 
        value="", 
        placeholder="Type your thoughts, questions, or reflections here..."
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("💬 Send Message", use_container_width=True, disabled=not user_input.strip(), type="primary"):
            if user_input.strip():
                process_user_input(user_input.strip())
    
    with col2:
        # TTS Toggle
        tts_enabled = st.checkbox("🔊 Voice responses", value=st.session_state.get('enable_tts', True), key="tts_toggle")
        st.session_state.enable_tts = tts_enabled
    
    with col3:
        if st.button("🎤 Voice Demo", help="Test text-to-speech with a sample message"):
            demo_text = "Hello! This is how I sound. I'm here to help you explore life's deeper questions."
            with st.spinner("Generating demo voice..."):
                audio_bytes = text_to_speech(demo_text)
                if audio_bytes:
                    create_audio_player(audio_bytes, "demo_audio")
                else:
                    st.error("Voice synthesis not available. Please check your ElevenLabs API key.")
        # Note: Browser-based audio recording requires additional setup
        # For MVP, we'll focus on text input
    
    # Show sample prompts for current month
    if not st.session_state.conversation_history:
        st.markdown("### Reflection Starters")
        month_info = MONTHLY_PROMPTS[st.session_state.current_month]
        
        for i, prompt in enumerate(month_info["sample_prompts"][:2]):
            if st.button(f"💭 {prompt}", key=f"prompt_{i}"):
                process_user_input(prompt)

def process_user_input(user_input: str):
    """Process user input and generate AI response"""
    
    # Add user message to history
    st.session_state.conversation_history.append({
        "role": "user", 
        "content": user_input,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # Generate AI response with progress indicator
    with st.spinner("💭 Crafting a thoughtful response..."):
        ai_response = get_ai_response(
            user_input, 
            st.session_state.conversation_history[:-1],  # Don't include the message we just added
            st.session_state.current_month
        )
    
    # Add AI response to history
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # Extract themes periodically
    if len(st.session_state.conversation_history) % 6 == 0:  # Every 3 exchanges
        st.session_state.life_themes = extract_themes_from_conversation(
            st.session_state.conversation_history
        )
    
    st.rerun()

# Main App Logic
def main():
    # Check API configuration
    api_keys_configured = check_api_keys()
    
    # Show consent screen first
    if not st.session_state.consent_given:
        show_consent_screen()
        return
    
    # Main interface
    show_main_interface()

if __name__ == "__main__":
    main()