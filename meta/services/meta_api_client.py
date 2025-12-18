"""
Meta API Client and Token Management
Handles authentication, rate limiting, and API calls to Meta Graph API
"""

import streamlit as st
import requests
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from meta.config.constants import API_VERSION, BASE_URL, DEFAULT_RETRY_COUNT, BASE_WAIT_TIME, REQUEST_TIMEOUT


def get_all_access_tokens() -> List[str]:
    """Get all available access tokens from secrets"""
    tokens = []
    i = 1
    while True:
        token_key = f"access_token_{i}"
        if token_key in st.secrets.get("meta", {}):
            tokens.append(st.secrets["meta"][token_key])
            i += 1
        else:
            break
    
    # Fallback to single token if numbered tokens don't exist
    if not tokens and "access_token" in st.secrets.get("meta", {}):
        tokens.append(st.secrets["meta"]["access_token"])
    
    return tokens


def get_token_for_request(token_index: int = 0) -> Optional[str]:
    """Get a specific token by index"""
    tokens = get_all_access_tokens()
    if not tokens:
        return None
    return tokens[token_index % len(tokens)]


def get_token_params(token_index: int = 0) -> Dict[str, str]:
    """Get token as params dict for API requests"""
    token = get_token_for_request(token_index)
    if token:
        return {'access_token': token}
    return {}


class TokenPool:
    """
    Manages a pool of access tokens with cooldown tracking for rate limiting.
    Rotates through tokens and handles rate limit cooldowns automatically.
    """
    
    def __init__(self, tokens: List[str]):
        self.tokens = list(tokens)
        self.cooldowns: Dict[int, float] = {}
        self.lock = threading.Lock()
        self.ptr = 0
    
    def get(self) -> Tuple[int, str]:
        """
        Get next available token, waiting if all tokens are in cooldown.
        Returns: (token_index, token_string)
        """
        with self.lock:
            n = len(self.tokens)
            
            # Try to find an available token
            for _ in range(n):
                i = self.ptr
                self.ptr = (self.ptr + 1) % n
                
                if time.time() >= self.cooldowns.get(i, 0.0):
                    return i, self.tokens[i]
            
            # All tokens in cooldown, wait for the one with shortest cooldown
            i = min(self.cooldowns, key=self.cooldowns.get, default=0)
            wait = max(0.0, self.cooldowns.get(i, 0.0) - time.time())
            
            if wait > 0:
                time.sleep(wait)
            
            return i, self.tokens[i]
    
    def cooldown(self, idx: int, seconds: float):
        """Put a token into cooldown for specified seconds"""
        with self.lock:
            self.cooldowns[idx] = time.time() + max(1.0, seconds)


def make_api_call(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = 'GET',
    max_retries: int = DEFAULT_RETRY_COUNT,
    token_index: int = 0
) -> Dict[str, Any]:
    """
    Make API call to Meta Graph API with rate limiting and exponential backoff.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        method: HTTP method (GET or POST)
        max_retries: Maximum number of retry attempts
        token_index: Index of token to use
    
    Returns:
        JSON response as dictionary
    
    Raises:
        Exception: If max retries exceeded or unrecoverable error
    """
    if params is None:
        params = {}
    
    # Add access token
    token_params = get_token_params(token_index)
    if not token_params:
        raise Exception("No access token available")
    params.update(token_params)
    
    base_wait = BASE_WAIT_TIME
    
    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code in [429, 403]:
                # Rate limiting - exponential backoff
                wait_time = base_wait * (2 ** attempt)
                time.sleep(wait_time)
            
            else:
                # Check for specific error codes that warrant retry
                error_data = response.json() if response.text else {}
                error_code = error_data.get('error', {}).get('code')
                
                if error_code in [4, 17, 32, 613]:  # Temporary errors
                    wait_time = base_wait * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
        
        except requests.exceptions.Timeout:
            wait_time = base_wait * (2 ** attempt)
            time.sleep(wait_time)
    
    raise Exception("Max retries reached for API call")


@st.cache_data(ttl=600)
def get_all_accounts() -> List[Dict[str, Any]]:
    """
    Get all accessible Meta ad accounts.
    Cached for 10 minutes to reduce API calls.
    
    Returns:
        List of account dictionaries with id, name, currency, status
    """
    try:
        token_params = get_token_params(0)
        if not token_params:
            return []
        
        url = f"{BASE_URL}/me/adaccounts"
        params = {
            'fields': 'id,name,account_status,currency',
            'limit': 100
        }
        params.update(token_params)
        
        response = requests.get(url, params=params, timeout=30)
        accounts_data = []
        
        if response.status_code == 200:
            data = response.json()
            for account in data.get('data', []):
                accounts_data.append({
                    'account_name': account.get('name', f"Account {account.get('id')}"),
                    'account_id': account.get('id'),
                    'currency': account.get('currency', 'USD'),
                    'status': account.get('account_status', 1)
                })
        
        return accounts_data
    
    except Exception as e:
        st.error(f"Error fetching accounts: {e}")
        return []
