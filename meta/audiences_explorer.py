"""
Meta Audiences Explorer
AI-powered audience discovery and recommendations using Meta's Detailed Targeting API
"""

import streamlit as st
import requests
from typing import Dict, List, Any, Optional
import json
from shared.gemini_client import get_gemini_client


# Meta Graph API version
API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def normalize_account_id(account_id: str) -> str:
    """Ensure account_id has act_ prefix (but not double)"""
    if account_id.startswith("act_"):
        return account_id
    return f"act_{account_id}"


def search_targeting(
    account_id: str,
    access_token: str,
    query: str,
    limit_type: Optional[str] = None,
    limit: int = 30
) -> List[Dict]:
    """Search for targeting options using Meta's Detailed Targeting API"""
    normalized_id = normalize_account_id(account_id)
    url = f"{BASE_URL}/{normalized_id}/targetingsearch"
    
    params = {
        "q": query,
        "limit": limit,
        "access_token": access_token
    }
    
    if limit_type:
        params["limit_type"] = limit_type
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        st.error(f"Targeting search error: {e}")
        return []


def browse_targeting(
    account_id: str,
    access_token: str,
    limit_type: Optional[str] = None
) -> List[Dict]:
    """Browse available targeting categories"""
    normalized_id = normalize_account_id(account_id)
    url = f"{BASE_URL}/{normalized_id}/targetingbrowse"
    
    params = {"access_token": access_token}
    if limit_type:
        params["limit_type"] = limit_type
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        st.error(f"Targeting browse error: {e}")
        return []


def generate_business_context(account_name: str) -> Dict[str, str]:
    """Use Gemini to generate business context from account name"""
    client = get_gemini_client()
    
    prompt = f"""Based on this Meta Ads account name, infer the business details:

Account Name: "{account_name}"

Analyze the account name and generate:
1. A business description (2-3 sentences about what the business likely does)
2. The most likely industry category
3. A target audience description

Return ONLY a JSON object like this:
{{
    "business_description": "Description here...",
    "industry": "E-commerce / Retail",
    "target_audience": "Target audience description..."
}}

Industry must be one of: E-commerce / Retail, SaaS / Technology, Health & Wellness, Finance / Insurance, Education, Real Estate, Travel & Hospitality, Food & Beverage, Fashion & Beauty, Entertainment, B2B Services, Non-profit, Other

Return ONLY valid JSON, no other text."""

    system_instruction = "You are a business analyst. Infer business details from account names. Return only valid JSON."
    
    response = client.generate_content(prompt, system_instruction)
    
    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(cleaned)
        except:
            pass
    
    return {
        "business_description": "",
        "industry": "E-commerce / Retail",
        "target_audience": ""
    }


def generate_search_terms(
    business_description: str,
    industry: str,
    target_audience: str
) -> List[str]:
    """Use Gemini to generate relevant search terms for audience discovery"""
    client = get_gemini_client()
    
    prompt = f"""Generate 15 specific search terms/keywords to find relevant Meta Ads audiences for this business:

Business: {business_description}
Industry: {industry}
Target Audience: {target_audience}

Requirements:
1. Include interest-based terms (hobbies, activities, brands)
2. Include behavior-based terms (purchase behaviors, device usage)
3. Include demographic-related terms (life events, job titles)
4. Be specific, not generic (e.g., "luxury car enthusiasts" not just "cars")
5. Think about competitor brands and complementary products

Return ONLY a JSON array of strings, no other text. Example:
["term1", "term2", "term3"]"""

    system_instruction = "You are a Meta Ads targeting specialist. Return only valid JSON arrays."
    
    response = client.generate_content(prompt, system_instruction)
    
    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            terms = []
            for line in response.split("\n"):
                line = line.strip().strip("-").strip("*").strip('"').strip("'")
                if line and len(line) > 2 and len(line) < 50:
                    terms.append(line)
            return terms[:15]
    
    return []


def filter_relevant_audiences(
    audiences: List[Dict],
    business_description: str,
    target_audience: str
) -> List[Dict]:
    """Use Gemini to filter and rank audiences by relevance"""
    if not audiences:
        return []
    
    client = get_gemini_client()
    
    audience_summary = []
    for i, aud in enumerate(audiences[:50]):
        audience_summary.append({
            "index": i,
            "name": aud.get("name", ""),
            "description": aud.get("description", ""),
            "path": " > ".join(aud.get("path", [])),
            "size_lower": aud.get("audience_size_lower_bound", 0),
            "size_upper": aud.get("audience_size_upper_bound", 0)
        })
    
    prompt = f"""Analyze these Meta Ads audiences for relevance to this business:

Business: {business_description}
Target Audience: {target_audience}

Available Audiences:
{json.dumps(audience_summary, indent=2)}

Task:
1. Select the TOP 10 most relevant audiences for this business
2. Explain briefly why each is relevant (1 sentence)
3. Assign a relevance score from 1-10

Return a JSON array with this structure:
[
  {{"index": 0, "name": "Audience Name", "relevance_score": 9, "reason": "Why it's relevant"}},
  ...
]

Return ONLY the JSON array, no other text."""

    system_instruction = "You are a Meta Ads targeting expert. Analyze audience relevance objectively. Return only valid JSON."
    
    response = client.generate_content(prompt, system_instruction)
    
    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            
            ranked = json.loads(cleaned)
            
            result = []
            for item in ranked:
                idx = item.get("index", -1)
                if 0 <= idx < len(audiences):
                    aud = audiences[idx].copy()
                    aud["relevance_score"] = item.get("relevance_score", 5)
                    aud["ai_reason"] = item.get("reason", "")
                    result.append(aud)
            
            return sorted(result, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
        except Exception as e:
            st.warning(f"AI filtering error, showing all results: {e}")
            return audiences[:10]
    
    return audiences[:10]


def format_audience_size(lower: int, upper: int) -> str:
    """Format audience size range for display"""
    def format_num(n):
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        elif n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        else:
            return str(n)
    
    if lower and upper:
        return f"{format_num(lower)} - {format_num(upper)}"
    elif upper:
        return f"< {format_num(upper)}"
    elif lower:
        return f"> {format_num(lower)}"
    else:
        return "Unknown"


def display_audience_results(audiences: List[Dict], show_ai_reason: bool = False):
    """Display audience results in a compact table format"""
    import pandas as pd
    
    if not audiences:
        st.info("No audiences to display.")
        return
    
    # Build table data
    table_data = []
    for aud in audiences:
        row = {
            "Audience": aud.get('name', 'Unknown'),
            "Size": format_audience_size(
                aud.get('audience_size_lower_bound', 0),
                aud.get('audience_size_upper_bound', 0)
            ),
            "Path": ' > '.join(aud.get('path', [])) if aud.get('path') else '-'
        }
        
        if show_ai_reason:
            row["Score"] = f"{aud.get('relevance_score', 5)}/10"
            row["Why Relevant"] = aud.get('ai_reason', '-')
        
        if aud.get('description'):
            row["Description"] = aud.get('description', '')
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=400
    )



def render_audiences_explorer(account_id: str, access_token: str):
    """Render the Audiences Explorer interface"""
    st.header("🎯 Audiences Explorer")
    st.caption("Discover and analyze detailed targeting options with AI-powered recommendations")
    
    # Initialize session state for this component
    if "explorer_mode" not in st.session_state:
        st.session_state.explorer_mode = None
    if "explorer_results" not in st.session_state:
        st.session_state.explorer_results = []
    if "explorer_search_query" not in st.session_state:
        st.session_state.explorer_search_query = ""
    if "explorer_autofill_done" not in st.session_state:
        st.session_state.explorer_autofill_done = False
    if "explorer_business_desc" not in st.session_state:
        st.session_state.explorer_business_desc = ""
    if "explorer_target_audience" not in st.session_state:
        st.session_state.explorer_target_audience = ""
    
    # Get account name for AI context
    selected_account_name = st.session_state.get('selected_meta_account_name', '')
    
    # Business context inputs with AI auto-fill button
    with st.expander("📝 Define Your Business Context", expanded=True):
        # Add AI auto-fill button at the top
        if selected_account_name:
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn2:
                if st.button("✨ Auto-fill with AI", key="ai_autofill_btn", help="Use AI to fill business context based on account name"):
                    with st.spinner("🤖 Analyzing account and generating business context..."):
                        context = generate_business_context(selected_account_name)
                        
                        # Check if we got valid response
                        business_desc = context.get("business_description", "")
                        target_audience = context.get("target_audience", "")
                        industry = context.get("industry", "E-commerce / Retail")
                        
                        if business_desc or target_audience:
                            st.session_state.explorer_business_desc = business_desc
                            st.session_state.explorer_target_audience = target_audience
                            st.session_state.explorer_industry = industry
                            # Also update widget keys directly (Streamlit requires this)
                            st.session_state.audience_business_desc_input = business_desc
                            st.session_state.audience_target_desc_input = target_audience
                            st.session_state.autofill_success = True
                        else:
                            # AI failed - provide simple fallback based on account name
                            fallback_desc = f"Business related to {selected_account_name}"
                            fallback_audience = "Adults interested in this product/service"
                            st.session_state.explorer_business_desc = fallback_desc
                            st.session_state.explorer_target_audience = fallback_audience
                            st.session_state.explorer_industry = "E-commerce / Retail"
                            # Also update widget keys
                            st.session_state.audience_business_desc_input = fallback_desc
                            st.session_state.audience_target_desc_input = fallback_audience
                            st.session_state.autofill_success = False
                        st.rerun()
            with col_btn1:
                st.caption(f"📊 Account: **{selected_account_name}** - Click 'Auto-fill with AI' to generate context")
                # Show feedback from autofill - only show if error
                if 'autofill_success' in st.session_state:
                    if not st.session_state.autofill_success:
                        st.warning("⚠️ AI quota exceeded - using basic fallback. Please edit manually.")
                    # Clear the flag
                    del st.session_state.autofill_success
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_desc = st.text_area(
                "Business Description",
                value=st.session_state.explorer_business_desc,
                placeholder="e.g., Premium organic skincare brand targeting health-conscious women...",
                height=100,
                key="audience_business_desc_input"
            )
            # Update session state
            st.session_state.explorer_business_desc = business_desc
            
        with col2:
            industries = [
                "E-commerce / Retail", "SaaS / Technology", "Health & Wellness",
                "Finance / Insurance", "Education", "Real Estate",
                "Travel & Hospitality", "Food & Beverage", "Fashion & Beauty",
                "Entertainment", "B2B Services", "Non-profit", "Other"
            ]
            # Get current industry from session or default
            current_industry = st.session_state.get('explorer_industry', 'E-commerce / Retail')
            try:
                industry_index = industries.index(current_industry)
            except ValueError:
                industry_index = 0
            
            industry = st.selectbox("Industry", options=industries, index=industry_index, key="audience_industry")
            st.session_state.explorer_industry = industry
            
            target_audience_desc = st.text_input(
                "Target Audience",
                value=st.session_state.explorer_target_audience,
                placeholder="e.g., Women 25-45, health-conscious, high income...",
                key="audience_target_desc_input"
            )
            st.session_state.explorer_target_audience = target_audience_desc
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 AI-Powered Discovery", type="primary", use_container_width=True):
            st.session_state.explorer_mode = "ai"
            st.session_state.explorer_results = []
    
    with col2:
        if st.button("🔍 Manual Search", use_container_width=True):
            st.session_state.explorer_mode = "manual"
            st.session_state.explorer_results = []
    
    with col3:
        if st.button("📂 Browse Categories", use_container_width=True):
            st.session_state.explorer_mode = "browse"
            st.session_state.explorer_results = []
    
    st.markdown("---")
    
    # Handle different modes
    mode = st.session_state.explorer_mode
    
    # AI-Powered Discovery
    if mode == "ai":
        if not business_desc or not target_audience_desc:
            st.warning("Please fill in the business description and target audience first.")
        else:
            # Show results if we have them
            if st.session_state.explorer_results:
                st.subheader("🎯 Recommended Audiences")
                display_audience_results(st.session_state.explorer_results, show_ai_reason=True)
            else:
                # Run the search
                with st.spinner("🤖 Generating search terms with AI..."):
                    search_terms = generate_search_terms(business_desc, industry, target_audience_desc)
                
                if search_terms:
                    
                    with st.expander("📋 Generated Search Terms", expanded=False):
                        st.write(", ".join(search_terms))
                    
                    all_audiences = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, term in enumerate(search_terms):
                        status_text.text(f"Searching: {term}")
                        results = search_targeting(account_id, access_token, term, limit=20)
                        all_audiences.extend(results)
                        progress_bar.progress((i + 1) / len(search_terms))
                    
                    status_text.empty()
                    
                    # Remove duplicates
                    seen_ids = set()
                    unique_audiences = []
                    for aud in all_audiences:
                        aud_id = aud.get("id")
                        if aud_id and aud_id not in seen_ids:
                            seen_ids.add(aud_id)
                            unique_audiences.append(aud)
                    
                    if unique_audiences:
                        st.info(f"Found {len(unique_audiences)} unique audiences")
                        
                        # Store all audiences for later display
                        st.session_state.explorer_all_audiences = unique_audiences
                        
                        with st.spinner("🧠 Analyzing relevance with AI..."):
                            st.session_state.explorer_results = filter_relevant_audiences(
                                unique_audiences, business_desc, target_audience_desc
                            )
                        
                        # Display AI recommendations
                        st.subheader("🎯 AI Recommended Audiences (Top 10)")
                        display_audience_results(st.session_state.explorer_results, show_ai_reason=True)
                        
                        # Show all audiences in expander
                        with st.expander(f"📊 View All {len(unique_audiences)} Fetched Audiences", expanded=False):
                            display_audience_results(unique_audiences, show_ai_reason=False)
                        
                        # Download button for all audiences
                        import pandas as pd
                        all_data = []
                        for aud in unique_audiences:
                            all_data.append({
                                "ID": aud.get('id', ''),
                                "Name": aud.get('name', ''),
                                "Type": aud.get('type', ''),
                                "Description": aud.get('description', ''),
                                "Path": ' > '.join(aud.get('path', [])) if aud.get('path') else '',
                                "Size Lower": aud.get('audience_size_lower_bound', 0),
                                "Size Upper": aud.get('audience_size_upper_bound', 0)
                            })
                        
                        df_all = pd.DataFrame(all_data)
                        csv = df_all.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Download All Audiences (CSV)",
                            data=csv,
                            file_name="meta_audiences_export.csv",
                            mime="text/csv",
                            key="download_all_audiences"
                        )
                    else:
                        st.warning("No audiences found. Try different search terms or check the business description.")
                else:
                    st.error("Failed to generate search terms. Please try again.")
    
    # Manual Search
    elif mode == "manual":
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                value=st.session_state.explorer_search_query,
                placeholder="e.g., fitness, technology, luxury...",
                key="manual_search_input"
            )
        
        with col2:
            limit_type = st.selectbox(
                "Type Filter",
                options=["All", "interests", "behaviors", "industries", "life_events", "income"],
                key="manual_limit_type"
            )
        
        # Search button
        if st.button("🔍 Search", use_container_width=True):
            if search_query:
                st.session_state.explorer_search_query = search_query
                with st.spinner("Searching..."):
                    st.session_state.explorer_results = search_targeting(
                        account_id,
                        access_token,
                        search_query,
                        limit_type=None if limit_type == "All" else limit_type,
                        limit=50
                    )
                st.rerun()
        
        # Display results
        if st.session_state.explorer_results:
            display_audience_results(st.session_state.explorer_results)
        elif st.session_state.explorer_search_query:
            st.info("No audiences found for this query.")
    
    # Browse Categories
    elif mode == "browse":
        if not st.session_state.explorer_results:
            with st.spinner("Loading categories..."):
                st.session_state.explorer_results = browse_targeting(account_id, access_token)
            st.rerun()
        else:
            categories = st.session_state.explorer_results
            
            grouped = {}
            for cat in categories:
                cat_type = cat.get('type', 'other')
                if cat_type not in grouped:
                    grouped[cat_type] = []
                grouped[cat_type].append(cat)
            
            for cat_type, items in grouped.items():
                with st.expander(f"📂 {cat_type.replace('_', ' ').title()} ({len(items)})", expanded=False):
                    for item in items[:20]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"• {item.get('name', 'Unknown')}")
                        with col2:
                            size = format_audience_size(
                                item.get('audience_size_lower_bound', 0),
                                item.get('audience_size_upper_bound', 0)
                            )
                            st.caption(size)
