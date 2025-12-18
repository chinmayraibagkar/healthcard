"""
HealthCard Chatbot Component
Digital marketing expert chatbot powered by Gemini
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from shared.gemini_client import get_gemini_client
import json


SYSTEM_INSTRUCTION = """You are an expert digital marketing consultant specializing in Meta Ads and Google Ads optimization. You have access to the HealthCard dashboard data which shows health check results for advertising accounts.

Your role is to:
1. Analyze the health check results and provide actionable insights
2. Give specific tips and recommendations to improve ad performance
3. Warn about critical issues that need immediate attention
4. Answer questions about digital marketing best practices
5. Explain what specific checks mean and why they matter

When providing advice:
- Be specific and actionable
- Prioritize issues by impact
- Use bullet points for clarity
- Include relevant industry benchmarks when applicable
- Suggest A/B testing opportunities

Formatting guidelines:
- Use markdown for structure
- Use emojis sparingly to highlight key points (✅, ⚠️, ❌, 💡)
- Keep responses concise but comprehensive
"""


def format_dashboard_context(
    meta_results: Optional[Dict] = None,
    google_results: Optional[Dict] = None,
    selected_platform: str = "meta"
) -> str:
    """Format dashboard data as context for the chatbot"""
    context_parts = []
    
    context_parts.append(f"**Current Platform:** {selected_platform.upper()}")
    context_parts.append("")
    
    if meta_results:
        context_parts.append("## Meta Ads Health Check Results:")
        for category, checks in meta_results.items():
            if isinstance(checks, list):
                context_parts.append(f"\n### {category.title()}")
                for check in checks:
                    if isinstance(check, dict):
                        name = check.get('name', 'Unknown Check')
                        status = check.get('status', 'unknown')
                        score = check.get('score', 'N/A')
                        message = check.get('message', '')
                        affected = check.get('affected_count', 0)
                        total = check.get('total_count', 0)
                        
                        status_emoji = "✅" if status == "pass" else "⚠️" if status == "warning" else "❌"
                        context_parts.append(f"- {status_emoji} **{name}**: {message} (Score: {score}, Affected: {affected}/{total})")
    
    if google_results:
        context_parts.append("\n## Google Ads Health Check Results:")
        for category, checks in google_results.items():
            if isinstance(checks, list):
                context_parts.append(f"\n### {category.title()}")
                for check in checks:
                    if isinstance(check, dict):
                        name = check.get('check_name', check.get('name', 'Unknown Check'))
                        status = check.get('status', 'unknown')
                        score = check.get('score', 'N/A')
                        message = check.get('message', '')
                        affected = check.get('affected_percentage', check.get('affected_count', 0))
                        
                        status_emoji = "✅" if status == "pass" else "⚠️" if status == "warning" else "❌"
                        context_parts.append(f"- {status_emoji} **{name}**: {message} (Score: {score}%, Affected: {affected}%)")
    
    if not meta_results and not google_results:
        context_parts.append("*No health check results available yet. Please run a health check first.*")
    
    return "\n".join(context_parts)


def generate_ai_response(full_system_instruction: str) -> str:
    """Generate AI response for the last user message"""
    client = get_gemini_client()
    
    # Convert messages to Gemini format
    gemini_messages = [
        {"role": "user" if m["role"] == "user" else "model", "parts": m["content"]}
        for m in st.session_state.chat_messages
    ]
    
    response = client.chat(
        messages=gemini_messages,
        system_instruction=full_system_instruction
    )
    
    return response if response else "I'm having trouble connecting. Please try again."


def render_chatbot():
    """Render the chatbot interface in an expander or sidebar"""
    
    # Initialize chat history and pending action
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "pending_quick_action" not in st.session_state:
        st.session_state.pending_quick_action = None
    
    # Get dashboard context
    meta_results = st.session_state.get('meta_results', {})
    # Google Ads stores results in 'results' key (not 'google_results')
    google_results = st.session_state.get('results', {})
    selected_platform = st.session_state.get('selected_platform', 'meta')
    
    dashboard_context = format_dashboard_context(meta_results, google_results, selected_platform)
    
    # Full system prompt with context
    full_system_instruction = f"""{SYSTEM_INSTRUCTION}

## Current Dashboard Data:
{dashboard_context}
"""
    
    # Chat container
    st.markdown("### 🤖 Marketing AI Assistant")
    st.caption("Ask questions about your health check results or get digital marketing advice")
    
    # Handle pending quick action - generate response immediately
    if st.session_state.pending_quick_action:
        prompt = st.session_state.pending_quick_action
        st.session_state.pending_quick_action = None
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🤖 Analyzing your data..."):
            response = generate_ai_response(full_system_instruction)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # Display chat messages
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_messages:
            st.info("👋 Hi! Click a quick action below or ask me anything about your ad performance.")
        else:
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your ad performance..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Generate response
        with st.spinner("🤖 Thinking..."):
            response = generate_ai_response(full_system_instruction)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💡 Summary", use_container_width=True, help="Get an overview of your health check results"):
            st.session_state.pending_quick_action = "Please provide a brief summary of my current health check results and highlight the top 3 priorities I should focus on."
            st.rerun()
    
    with col2:
        if st.button("⚠️ Issues", use_container_width=True, help="List all critical issues"):
            st.session_state.pending_quick_action = "What are the critical issues and warnings in my account that need immediate attention? List them in order of priority."
            st.rerun()
    
    with col3:
        if st.button("🔄 Clear", use_container_width=True, help="Clear chat history"):
            st.session_state.chat_messages = []
            st.session_state.pending_quick_action = None
            st.rerun()


def render_chatbot_expander():
    """Render chatbot in an expander for sidebar or main area"""
    with st.expander("🤖 AI Marketing Assistant", expanded=False):
        render_chatbot()
