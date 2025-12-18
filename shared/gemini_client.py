"""
Gemini AI Client with Key Rotation
Provides access to Gemini 2.0 Flash for chatbot and audience analysis
"""

import google.generativeai as genai
import streamlit as st
from typing import Optional, List, Dict, Any
import random
import time


class GeminiClient:
    """Gemini client with intelligent key rotation to avoid rate limits"""
    
    def __init__(self):
        """Initialize with API keys from secrets or provided list"""
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.failed_keys = set()
        self.model_name = "gemini-2.5-flash"
        
    def _load_api_keys(self) -> List[str]:
        """Load API keys from secrets or default list"""
        # Try to get from secrets
        secrets_keys = st.secrets.get("gemini", {}).get("api_keys", [])
        if secrets_keys:
            return list(secrets_keys) if isinstance(secrets_keys, (list, tuple)) else [secrets_keys]
        
        # Fallback to single key
        single_key = st.secrets.get("gemini", {}).get("api_key", "")
        if single_key:
            return [single_key]
        
        return []
    
    def _get_next_key(self) -> Optional[str]:
        """Get next available API key with rotation"""
        if not self.api_keys:
            return None
        
        available_keys = [k for i, k in enumerate(self.api_keys) if i not in self.failed_keys]
        if not available_keys:
            # Reset failed keys and try again
            self.failed_keys.clear()
            available_keys = self.api_keys
        
        # Rotate through keys
        self.current_key_index = (self.current_key_index + 1) % len(available_keys)
        return available_keys[self.current_key_index]
    
    def _configure_client(self, api_key: str):
        """Configure genai with the given API key"""
        genai.configure(api_key=api_key)
    
    def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate content using Gemini with automatic key rotation on failure
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction for context
            max_retries: Maximum number of retry attempts with different keys
            
        Returns:
            Generated text or None if all attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            api_key = self._get_next_key()
            if not api_key:
                return None
            
            try:
                self._configure_client(api_key)
                
                # Create model with system instruction
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                if system_instruction:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        generation_config=generation_config,
                        system_instruction=system_instruction
                    )
                else:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        generation_config=generation_config
                    )
                
                response = model.generate_content(prompt)
                return response.text
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a rate limit or quota error
                if "quota" in error_str or "rate" in error_str or "429" in error_str:
                    # Mark this key as failed and try another
                    key_index = self.api_keys.index(api_key) if api_key in self.api_keys else -1
                    if key_index >= 0:
                        self.failed_keys.add(key_index)
                    time.sleep(0.5)  # Brief pause before retry
                    continue
                else:
                    # For other errors, just retry with same key after a pause
                    time.sleep(1)
                    continue
        
        # All retries failed
        if last_error:
            st.error(f"Gemini API error: {last_error}")
        return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Multi-turn chat interface with automatic key rotation on failure
        
        Args:
            messages: List of {"role": "user"|"model", "parts": "message"}
            system_instruction: Optional system instruction
            max_retries: Maximum number of retry attempts with different keys
            
        Returns:
            Model response text
        """
        last_error = None
        
        for attempt in range(max_retries):
            api_key = self._get_next_key()
            if not api_key:
                return None
            
            try:
                self._configure_client(api_key)
                
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                }
                
                if system_instruction:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        generation_config=generation_config,
                        system_instruction=system_instruction
                    )
                else:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        generation_config=generation_config
                    )
                
                chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])
                response = chat.send_message(messages[-1]["parts"])
                return response.text
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a rate limit or quota error
                if "quota" in error_str or "rate" in error_str or "429" in error_str:
                    # Mark this key as failed and try another
                    key_index = self.api_keys.index(api_key) if api_key in self.api_keys else -1
                    if key_index >= 0:
                        self.failed_keys.add(key_index)
                    time.sleep(0.5)  # Brief pause before retry
                    continue
                else:
                    # For other errors, just retry with same key after a pause
                    time.sleep(1)
                    continue
        
        # All retries failed
        if last_error:
            st.error(f"Chat error: {last_error}")
        return None


# Singleton instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
