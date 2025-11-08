"""
Louisiana Census Data Explorer - Streamlit GUI
Interactive web interface for querying census tract data with natural language.
"""
import sys
import os
from pathlib import Path
import time
from io import StringIO
import json
import textwrap

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# Add src directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "single_agent"))

from single_agent.mvp import run_query as run_single_agent_query
from mvp_multiagent import run_multiagent_query
from single_agent.resolver import clean_census_label
from agents.variable_agent import VariableChatAgent


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Louisiana Census Data Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# CACHING & INITIALIZATION
# ============================================================================

def check_ollama_status():
    """Check if Ollama is running and responsive."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            has_phi3 = any("phi3" in name for name in model_names)
            return {
                "running": True,
                "has_phi3": has_phi3,
                "models": model_names
            }
    except:
        pass
    return {
        "running": False,
        "has_phi3": False,
        "models": []
    }


@st.cache_resource
def init_app():
    """Initialize app resources (runs once per server restart)."""
    return {
        "initialized": True,
        "start_time": time.time()
    }


@st.cache_resource(show_spinner=False)
def get_variable_chat_helper():
    """Instantiate the variable chat agent once per session."""
    return VariableChatAgent()


@st.cache_data(ttl=3600)
def get_tract_geometries():
    """Load tract geometries for mapping (cached for 1 hour)."""
    # TODO: Load actual tract boundaries from TIGER/Line
    # For now, return None - we'll add coordinates from results
    return None


def init_session_state():
    """Initialize session state variables."""
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "current_result" not in st.session_state:
        st.session_state.current_result = None
    if "query_cache" not in st.session_state:
        st.session_state.query_cache = {}
    if "variable_chat_history" not in st.session_state:
        st.session_state.variable_chat_history = _default_variable_chat_history()


# ============================================================================
# QUERY EXECUTION
# ============================================================================

def execute_query(query: str, mode: str, verbose: bool = False, force_refresh: bool = False) -> dict:
    """Execute query and return results with metadata."""
    start_time = time.time()
    
    # Check cache first (unless force refresh)
    cache_key = f"{mode}:{query}"
    if not force_refresh and cache_key in st.session_state.query_cache:
        cached = st.session_state.query_cache[cache_key]
        return {
            **cached,
            "from_cache": True,
            "execution_time": 0.0
        }
    
    # Clear any problematic cache entries
    if force_refresh and cache_key in st.session_state.query_cache:
        del st.session_state.query_cache[cache_key]
    
    try:
        # Capture verbose output if requested
        verbose_output = None
        old_stdout = None
        
        if verbose:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
        
        try:
            # Execute query based on mode
            if mode == "multi":
                result_df = run_multiagent_query(query, verbose=verbose)
                confidence = result_df.attrs.get("confidence", None)
            else:
                result_df = run_single_agent_query(query, return_debug_info=True)
                confidence = None
        finally:
            # Always restore stdout
            if old_stdout is not None:
                if verbose:
                    verbose_output = captured_output.getvalue()
                sys.stdout = old_stdout
        
        execution_time = time.time() - start_time
        
        # Round numeric values to 2 decimal places
        if "value" in result_df.columns:
            result_df["value"] = result_df["value"].round(2)
        
        # Package results
        result = {
            "dataframe": result_df,
            "query": query,
            "mode": mode,
            "execution_time": execution_time,
            "confidence": confidence,
            "label": result_df.attrs.get("label", "Census Data"),
            "doc_context": result_df.attrs.get("doc_context", []),
            "debug_info": result_df.attrs.get("debug_info"),
            "verbose_output": verbose_output,
            "from_cache": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cache result
        st.session_state.query_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        # Restore stdout if it was redirected
        if verbose and 'old_stdout' in locals():
            sys.stdout = old_stdout
        
        # Get more detailed error information
        import traceback
        error_details = traceback.format_exc()
        
        return {
            "error": str(e),
            "error_details": error_details,
            "query": query,
            "mode": mode,
            "execution_time": time.time() - start_time
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_tract_geometry(state_fips: str, county_fips: str, tract_code: str):
    """
    Fetch tract boundary geometry from Census TIGER/Line API.
    Returns GeoJSON geometry or None if not found.
    """
    try:
        # Census TIGER/Line WMS service
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2023/MapServer/8/query"
        
        params = {
            "where": f"STATE='{state_fips}' AND COUNTY='{county_fips}' AND TRACT='{tract_code}'",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson"
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                return data["features"][0]["geometry"]
    except Exception as e:
        st.warning(f"Could not fetch geometry for tract {tract_code}: {str(e)}")
    
    return None


def parse_geoid(geoid: str):
    """Parse GEOID into state, county, and tract components."""
    if pd.isna(geoid) or len(str(geoid)) < 11:
        return None, None, None
    
    geoid_str = str(geoid)
    state_fips = geoid_str[:2]  # First 2 digits
    county_fips = geoid_str[2:5]  # Next 3 digits
    tract_code = geoid_str[5:11]  # Last 6 digits
    
    return state_fips, county_fips, tract_code


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_sidebar():
    """Render sidebar with settings and info."""
    with st.sidebar:
        st.title("🗺️ Census Explorer")
        st.markdown("---")
        
        # Ollama status check
        ollama_status = check_ollama_status()
        if ollama_status["running"]:
            if ollama_status["has_phi3"]:
                st.success("🟢 Ollama: Running with phi3:mini")
            else:
                st.warning("🟡 Ollama: Running (phi3:mini not found)")
                st.caption("Run: `ollama pull phi3:mini`")
        else:
            st.error("🔴 Ollama: Not running")
            st.caption("Run: `ollama serve`")
        
        st.markdown("---")
        
        # Mode selection
        st.subheader("⚙️ Settings")
        mode = st.radio(
            "Agent Mode",
            options=["single", "multi"],
            format_func=lambda x: f"{'⚡ Single Agent (Fast)' if x == 'single' else '🤖 Multi-Agent (Accurate)'}",
            help="Single-agent is faster (~2-5s), Multi-agent is more accurate (~8-15s) with confidence scores."
        )
        
        # Show performance warning for multi-agent
        if mode == "multi":
            st.info("⚠️ **Note:** Multi-agent mode can timeout on CPU-only systems. Single-agent mode is recommended for better performance.")
        
        verbose = st.checkbox(
            "Show detailed output",
            value=False,
            help="Display agent reasoning and intermediate steps"
        )
        
        st.markdown("---")
        
        # Info section
        st.subheader("ℹ️ About")
        st.markdown("""
        Natural language interface for Louisiana census tract data.
        
        **Coverage:**
        - All 64 Louisiana parishes
        - Census Tracts (ACS 5-Year 2023)
        
        **Available Metrics:**
        - Population & Demographics
        - Income & Poverty
        - Housing & Density
        - Age Distribution
        """)
        
        st.markdown("---")
        
        # Query history
        st.subheader("📜 Recent Queries")
        if st.session_state.query_history:
            for i, hist_query in enumerate(reversed(st.session_state.query_history[-5:])):
                if st.button(f"🔄 {hist_query[:40]}...", key=f"hist_{i}"):
                    st.session_state.prefill_query = hist_query
                    st.rerun()
        else:
            st.caption("No queries yet")
        
        # Clear cache button
        if st.button("🗑️ Clear Cache", help="Clear all cached query results"):
            st.session_state.query_cache = {}
            st.success("Cache cleared!")
        
        return mode, verbose


def render_example_queries():
    """Render example query buttons."""
    st.markdown("### 💡 Example Queries")
    
    col1, col2 = st.columns(2)
    
    examples = [
        ("Top 5 richest tracts in Orleans Parish", "What are the top 5 census tracts in Orleans Parish by median income?"),
        ("High poverty areas in Caddo", "Show me census tracts with poverty rate over 30% in Caddo Parish"),
        ("Population density in Lafayette", "What are the most densely populated tracts in Lafayette Parish?"),
        ("Low poverty in St. Tammany", "Find tracts in St. Tammany Parish with poverty rate under 10%"),
    ]
    
    for i, (label, query) in enumerate(examples):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"📊 {label}", key=f"example_{i}", width="stretch"):
                st.session_state.prefill_query = query
                st.rerun()
def _format_doc_snippet_preview(snippets, max_items: int = 3):
    if not snippets:
        return ""
    lines = []
    for snippet in snippets[:max_items]:
        title = snippet.get("heading") or snippet.get("table_id") or snippet.get("source")
        source = snippet.get("source", "")
        lines.append(f"{title} ({source})")
    remaining = len(snippets) - max_items
    if remaining > 0:
        lines.append(f"+{remaining} more source(s)")
    return " | ".join(lines)


def render_doc_references(snippets):
    if not snippets:
        return
    st.markdown("#### ACS Documentation References")
    for snippet in snippets:
        title = snippet.get("heading") or snippet.get("table_id") or snippet.get("source")
        source = snippet.get("source", "Unknown source")
        text = textwrap.shorten(snippet.get("text", ""), width=260, placeholder="…")
        st.markdown(f"- **{title}** ({source})")
        st.caption(text)


def _default_variable_chat_history():
    """Seed messages for the variable assistant chat."""
    return [{
        "role": "assistant",
        "content": (
            "Hi! I'm the Variable Assistant. Ask me about ACS variables - IDs, descriptions, "
            "and which metrics you can query in this app."
        )
    }]


def _format_variable_candidate_preview(candidates, max_items: int = 3) -> str:
    """Build a compact preview of candidate variables for the UI."""
    if not candidates:
        return ""

    lines = []
    for entry in candidates[:max_items]:
        var_id = entry.get("variable_id", "N/A")
        label = entry.get("label", "Unknown label")
        lines.append(f"{var_id} - {label}")

    remaining = len(candidates) - max_items
    if remaining > 0:
        lines.append(f"+{remaining} more suggestion(s)")

    return "\n".join(lines)


def reset_variable_chat_history():
    """Clear the chat transcript and agent memory."""
    st.session_state.variable_chat_history = _default_variable_chat_history()
    helper = get_variable_chat_helper()
    helper.reset_history()


def _handle_variable_chat_prompt(question: str):
    """Send the user's question to the chat agent and display a response."""
    agent = get_variable_chat_helper()
    st.session_state.variable_chat_history.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking ACS documentation..."):
            try:
                reply = agent.answer_question(question)
                answer = reply.get("answer", "")
                candidates = reply.get("candidates", [])
                doc_snippets = reply.get("doc_snippets", [])
            except Exception as exc:
                answer = (
                    "Unable to reach the variable assistant right now. "
                    "Please verify that Ollama is running and try again.\n\n"
                    f"Details: {exc}"
                )
                candidates = []
                doc_snippets = []

        st.markdown(answer)
        preview = _format_variable_candidate_preview(candidates)
        if preview:
            st.caption(preview)
        doc_preview = _format_doc_snippet_preview(doc_snippets)
        if doc_preview:
            st.caption(f"Sourced from: {doc_preview}")

    st.session_state.variable_chat_history.append({
        "role": "assistant",
        "content": answer,
        "candidates": candidates,
        "doc_snippets": doc_snippets
    })

    st.rerun()


def render_variable_chatbox():
    """Render the chat interface for asking about ACS variables."""
    st.markdown("### Variable Assistant")
    st.caption("Chat with the LLM to learn which ACS variables cover a topic or how to reference them.")

    clear_col, spacer_col = st.columns([1, 6])
    with clear_col:
        if st.button("Clear chat", key="clear_variable_chat"):
            reset_variable_chat_history()
            st.rerun()
    spacer_col.empty()

    for message in st.session_state.variable_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("candidates"):
                preview = _format_variable_candidate_preview(message["candidates"])
                if preview:
                    st.caption(preview)
            doc_preview = _format_doc_snippet_preview(message.get("doc_snippets", []))
            if doc_preview:
                st.caption(f"Sourced from: {doc_preview}")

    prompt = st.chat_input("Ask about ACS variables...", key="variable_chat_input")
    if prompt:
        _handle_variable_chat_prompt(prompt)

def render_map(result_df: pd.DataFrame, label: str = "Value"):
    """Render interactive map with census tracts."""
    st.markdown("### 🗺️ Interactive Map")
    
    # Try to add tract geometries and calculate bounds
    tracts_added = 0
    has_geoid = "GEOID" in result_df.columns
    geometries = []
    
    if has_geoid:
        with st.spinner("Loading tract boundaries..."):
            for idx, row in result_df.iterrows():
                geoid = row.get("GEOID")
                if pd.notna(geoid):
                    # Parse GEOID
                    state_fips, county_fips, tract_code = parse_geoid(geoid)
                    
                    if state_fips and county_fips and tract_code:
                        # Fetch geometry
                        geometry = fetch_tract_geometry(state_fips, county_fips, tract_code)
                        
                        if geometry:
                            geometries.append({
                                'geometry': geometry,
                                'value': row.get("value", 0),
                                'tract_name': row.get("tract_name", "Unknown Tract"),
                                'geoid': geoid
                            })
                            tracts_added += 1
    
    # Calculate bounds for auto-zoom
    if geometries:
        # Extract all coordinates from geometries to find bounds
        all_coords = []
        for geom_data in geometries:
            geom = geom_data['geometry']
            if geom['type'] == 'Polygon':
                all_coords.extend(geom['coordinates'][0])
            elif geom['type'] == 'MultiPolygon':
                for polygon in geom['coordinates']:
                    all_coords.extend(polygon[0])
        
        if all_coords:
            # Calculate bounding box
            lons = [coord[0] for coord in all_coords]
            lats = [coord[1] for coord in all_coords]
            
            min_lon, max_lon = min(lons), max(lons)
            min_lat, max_lat = min(lats), max(lats)
            
            # Calculate center
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            # Create map centered on tracts
            m = folium.Map(location=[center_lat, center_lon])
            
            # Fit bounds to show all tracts
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=[30, 30])
        else:
            # Fallback to Louisiana center
            m = folium.Map(location=[31.0, -92.0], zoom_start=7, tiles="OpenStreetMap")
    else:
        # Fallback to Louisiana center
        m = folium.Map(location=[31.0, -92.0], zoom_start=7, tiles="OpenStreetMap")
    
    # Add tract polygons to map
    if geometries:
        # Calculate color gradient
        values = [g['value'] for g in geometries]
        min_val = min(values)
        max_val = max(values)
        
        for display_rank, geom_data in enumerate(geometries, start=1):
            value = geom_data['value']
            tract_name = geom_data['tract_name']
            geoid = geom_data['geoid']
            geometry = geom_data['geometry']
            
            # Create color gradient (green for high, red for low)
            if len(geometries) > 1 and max_val > min_val:
                normalized = (value - min_val) / (max_val - min_val)
                # Green to Yellow to Red gradient
                if normalized > 0.5:
                    color = f"#{int(255 * (1 - normalized) * 2):02x}{255:02x}00"
                else:
                    color = f"#ff{int(255 * normalized * 2):02x}00"
            else:
                color = "#3388ff"
            
            # Add polygon to map
            folium.GeoJson(
                geometry,
                style_function=lambda x, c=color: {
                    'fillColor': c,
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.6
                },
                tooltip=folium.Tooltip(
                    f"<div style='font-family: Arial; font-size: 12px;'>"
                    f"<b>{tract_name}</b><br>"
                    f"{clean_census_label(label)}: <b>{value}</b>"
                    f"</div>",
                    sticky=False
                ),
                popup=folium.Popup(
                    f"<div style='font-family: Arial; font-size: 13px; min-width: 200px;'>"
                    f"<h4 style='margin: 0 0 10px 0; color: #333;'>{tract_name}</h4>"
                    f"<table style='width: 100%; border-collapse: collapse;'>"
                    f"<tr><td style='padding: 4px 8px 4px 0; color: #666;'>{clean_census_label(label)}:</td>"
                    f"<td style='padding: 4px 0; font-weight: bold;'>{value}</td></tr>"
                    f"<tr><td style='padding: 4px 8px 4px 0; color: #666;'>GEOID:</td>"
                    f"<td style='padding: 4px 0; font-family: monospace;'>{geoid}</td></tr>"
                    f"<tr><td style='padding: 4px 8px 4px 0; color: #666;'>Rank:</td>"
                    f"<td style='padding: 4px 0; font-weight: bold;'>#{display_rank} of {len(result_df)}</td></tr>"
                    f"</table>"
                    f"</div>",
                    max_width=400
                )
            ).add_to(m)
        
        tracts_added = len(geometries)
    
    # Display map
    if tracts_added > 0:
        st.success(f"✅ Loaded {tracts_added} tract boundaries")
        st_folium(m, width=None, height=600)
    else:
        st.info("📍 Tract boundaries not available. Showing Louisiana overview.")
        st_folium(m, width=None, height=400)
        
        # Show tract list in expander since we can't plot them
        if len(result_df) > 0 and has_geoid:
            with st.expander("📋 View Tract Details", expanded=True):
                for idx, row in result_df.iterrows():
                    tract_name = row.get('tract_name', 'Unknown Tract')
                    value = row.get('value', 'N/A')
                    geoid = row.get('GEOID', 'N/A')
                    st.markdown(f"**{idx + 1}. {tract_name}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"{label}: {value}")
                    with col2:
                        st.text(f"GEOID: {geoid}")
                    st.divider()


def render_data_table(result_df: pd.DataFrame, label: str):
    """Render interactive data table."""
    st.markdown("### 📋 Data Table")
    
    # Display label
    st.caption(f"**Metric:** {label}")
    
    # Show dataframe with interactive features
    st.dataframe(
        result_df,
        width="stretch",
        height=400,
        column_config={
            "GEOID": st.column_config.TextColumn("GEOID", width="medium"),
            "tract_name": st.column_config.TextColumn("Tract Name", width="large"),
            "value": st.column_config.NumberColumn("Value", format="%.2f"),
        }
    )
    
    # Show summary stats
    if "value" in result_df.columns:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tracts", len(result_df))
        with col2:
            st.metric("Mean", f"{result_df['value'].mean():.2f}")
        with col3:
            st.metric("Median", f"{result_df['value'].median():.2f}")
        with col4:
            st.metric("Std Dev", f"{result_df['value'].std():.2f}")


def render_download_buttons(result_df: pd.DataFrame, result: dict):
    """Render CSV, JSON, and GeoJSON download buttons."""
    st.markdown("### 📥 Download Data")
    
    col1, col2, col3 = st.columns(3)
    
    # Download results as CSV
    with col1:
        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"census_results_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )
    
    # Download as JSON (fixed icon)
    with col2:
        json_data = result_df.to_json(orient="records", indent=2)
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"census_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch"
        )
    
    # Download as GeoJSON with tract geometries
    with col3:
        if "GEOID" in result_df.columns:
            with st.spinner("Preparing GeoJSON..."):
                geojson = build_geojson(result_df, result["label"])
                if geojson:
                    st.download_button(
                        label="🗺️ Download GeoJSON",
                        data=json.dumps(geojson, indent=2),
                        file_name=f"census_tracts_{time.strftime('%Y%m%d_%H%M%S')}.geojson",
                        mime="application/geo+json",
                        width="stretch"
                    )
                else:
                    st.button(
                        "🗺️ GeoJSON (N/A)", 
                        disabled=True,
                        width="stretch",
                        help="No geometries available"
                    )
        else:
            st.button(
                "🗺️ GeoJSON (N/A)", 
                disabled=True,
                width="stretch",
                help="No GEOID column found"
            )


def build_geojson(result_df: pd.DataFrame, label: str) -> dict:
    """
    Build GeoJSON FeatureCollection from results with tract geometries.
    
    Args:
        result_df: DataFrame with GEOID and value columns
        label: Label for the metric
        
    Returns:
        GeoJSON FeatureCollection dict or None if no geometries found
    """
    features = []
    
    for idx, row in result_df.iterrows():
        geoid = row.get("GEOID")
        if pd.notna(geoid):
            # Parse GEOID
            state_fips, county_fips, tract_code = parse_geoid(geoid)
            
            if state_fips and county_fips and tract_code:
                # Fetch geometry
                geometry = fetch_tract_geometry(state_fips, county_fips, tract_code)
                
                if geometry:
                    # Build feature
                    feature = {
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "GEOID": geoid,
                            "tract_name": row.get("tract_name", "Unknown Tract"),
                            "value": float(row.get("value", 0)),
                            "metric": label,
                            "state_fips": state_fips,
                            "county_fips": county_fips,
                            "tract_code": tract_code
                        }
                    }
                    features.append(feature)
    
    if not features:
        return None
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "metric": label,
            "count": len(features),
            "generated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }



def render_query_metadata(result: dict):
    """Render query execution metadata."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mode_emoji = "⚡" if result["mode"] == "single" else "🤖"
        st.metric(
            "Mode",
            f"{mode_emoji} {result['mode'].title()}-Agent"
        )
    
    with col2:
        time_color = "🟢" if result["execution_time"] < 5 else "🟡" if result["execution_time"] < 10 else "🔴"
        st.metric(
            "Execution Time",
            f"{time_color} {result['execution_time']:.2f}s"
        )
    
    with col3:
        if result.get("confidence"):
            conf_pct = result["confidence"] * 100
            conf_emoji = "🟢" if conf_pct > 80 else "🟡" if conf_pct > 60 else "🔴"
            st.metric(
                "Confidence",
                f"{conf_emoji} {conf_pct:.0f}%"
            )
        else:
            st.metric("Confidence", "N/A")
    
    # Show cache status
    if result.get("from_cache"):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning("⚡ **Results from cache** - Code changes won't affect these results. Click 'Clear' to force refresh.")
        with col2:
            if st.button("🔄 Refresh", key="refresh_cache", help="Clear cache and re-run query"):
                st.session_state.query_cache.clear()
                st.rerun()


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application."""
    # Initialize
    app_state = init_app()
    init_session_state()
    
    # Render sidebar
    mode, verbose = render_sidebar()
    
    # Main content
    st.title("🗺️ Louisiana Census Data Explorer")
    st.markdown("Ask questions about Louisiana census tracts in natural language")
    
    # Query input
    st.markdown("### 🔍 Enter Your Query")
    
    # Check if we should auto-submit from prefill
    auto_submit = False
    default_query = ""
    if "prefill_query" in st.session_state:
        default_query = st.session_state.prefill_query
        auto_submit = True
        del st.session_state.prefill_query
    
    # Use form to prevent re-runs while typing
    with st.form("query_form"):
        query = st.text_input(
            "Query",
            value=default_query,
            placeholder="Example: What are the top 5 census tracts in Orleans Parish by poverty rate?",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.form_submit_button("🔍 Search", width="stretch")
        with col2:
            clear_clicked = st.form_submit_button("🗑️ Clear", width="stretch")
    
    # Auto-submit if prefilled from example
    if auto_submit and query:
        submitted = True
    
    # Handle clear button
    if clear_clicked:
        st.session_state.current_result = None
        st.rerun()
    
    # Show example queries if no current result
    if not st.session_state.current_result:
        render_example_queries()
    
    # Process query
    if submitted and query:
        # Add to history
        if query not in st.session_state.query_history:
            st.session_state.query_history.append(query)
        
        # Check if we need to clear the error state
        # (if switching from error to new query)
        force_refresh = False
        if st.session_state.current_result and "error" in st.session_state.current_result:
            force_refresh = True
        
        # Execute query
        with st.spinner(f"{'⚡ Querying...' if mode == 'single' else '🤖 Multi-agent system processing... (may take 30-60 seconds)'}"):
            result = execute_query(query, mode, verbose, force_refresh=force_refresh)
        
        # Store result
        st.session_state.current_result = result
    
    # Display results
    if st.session_state.current_result:
        result = st.session_state.current_result
        
        # Check for errors
        if "error" in result:
            error_msg = result['error']
            st.error(f"❌ Error: {error_msg}")
            
            # Provide specific troubleshooting based on error type
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                st.warning("**⏱️ Request Timeout Detected**")
                st.markdown("""
                The multi-agent system took too long to process your request (>60 seconds).
                
                **Why this happens:**
                - The Variable Agent searches through 30,000+ Census variables
                - phi3:mini can be slow with complex prompts on CPU
                - Multiple agent calls add up in time
                
                **Solutions:**
                1. **Switch to Single-Agent mode** (sidebar) - Much faster! (~2-5 seconds)
                2. Wait a moment and try again (Ollama may have been busy)
                3. Try a simpler query
                
                **Recommended:** Use **Single-Agent mode** for better performance.
                Multi-Agent mode is more accurate but slower.
                """)
            elif "empty response" in error_msg.lower() or "expecting value" in error_msg.lower():
                st.warning("**⚠️ Ollama Connection Issue Detected**")
                st.markdown("""
                The LLM (Ollama) returned an empty response. This usually means:
                
                1. **Ollama is not running** - Start it with: `ollama serve`
                2. **Model is not loaded** - Load phi3:mini with: `ollama pull phi3:mini`
                3. **Ollama is slow to respond** - Wait a moment and try again
                4. **Port conflict** - Check if something else is using port 11434
                
                **Quick Check:**
                ```powershell
                # Check if Ollama is running
                ollama ps
                
                # If not, start it
                ollama serve
                
                # In another terminal, verify the model
                ollama list
                ```
                """)
            elif "json" in error_msg.lower():
                st.warning("**⚠️ LLM Response Parsing Issue**")
                st.markdown("""
                The LLM returned a response that couldn't be parsed as JSON.
                
                **This could mean:**
                - The model is having trouble with structured output
                - Try using **Single-Agent mode** instead (simpler, more reliable)
                - Or try rephrasing your question
                
                **Switch to Single-Agent mode in the sidebar** for better reliability.
                """)
                
                # Show the verbose output if available to help debug
                if result.get('verbose_output'):
                    with st.expander("🔍 View Raw Response (for debugging)"):
                        st.code(result['verbose_output'], language="text")
                
                # Show detailed error traceback if available
                if result.get('error_details'):
                    with st.expander("🐛 View Full Error Traceback (for debugging)"):
                        st.code(result['error_details'], language="python")
            else:
                st.markdown("**General Troubleshooting:**")
                st.markdown("- Make sure Ollama is running (`ollama ps`)")
                st.markdown("- Check that phi3:mini model is loaded (`ollama pull phi3:mini`)")
                st.markdown("- Verify your Census API key is set (if querying real data)")
                st.markdown("- Try **Single-Agent mode** for simpler queries")
                
                # Show detailed error traceback if available
                if result.get('error_details'):
                    with st.expander("🐛 View Full Error Traceback (for debugging)"):
                        st.code(result['error_details'], language="python")
            
            return
        
        st.markdown("---")
        
        # Show metadata
        render_query_metadata(result)
        
        st.markdown("---")
        
        # Show results in tabs
        tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📋 Table", "📥 Downloads"])
        
        with tab1:
            render_map(result["dataframe"], result["label"])
        
        with tab2:
            render_data_table(result["dataframe"], result["label"])
        
        with tab3:
            render_download_buttons(result["dataframe"], result)
        
        if result.get("doc_context"):
            render_doc_references(result["doc_context"])
        
        # Debug/Verbose information
        if verbose or result.get('verbose_output'):
            with st.expander("🔍 Detailed Query Execution Log", expanded=False):
                
                # Show captured verbose output first if available (multi-agent mode)
                if result.get('verbose_output'):
                    st.markdown("#### 🤖 Agent System Execution")
                    st.code(result['verbose_output'], language="text")
                    st.markdown("---")
                
                # Show structured debug info if available (single-agent mode)
                if result.get('debug_info'):
                    st.markdown("#### 📋 Query Analysis")
                    
                    debug = result['debug_info']
                    intent = debug.get('intent', {})
                    resolved = debug.get('resolved', {})
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Extracted Intent:**")
                        st.json({
                            "task": intent.get('task'),
                            "measure": intent.get('measure'),
                            "limit": intent.get('limit'),
                            "sort": intent.get('sort'),
                            "county_fips": intent.get('county_fips'),
                            "operator": intent.get('op'),
                            "value": intent.get('value'),
                            "range": {
                                "min": intent.get('range_min'),
                                "max": intent.get('range_max')
                            } if intent.get('range_min') or intent.get('range_max') else None
                        })
                    
                    with col2:
                        st.markdown("**Variable Resolution:**")
                        st.json({
                            "label": resolved.get('label'),
                            "variable_id": resolved.get('variable_id'),
                            "is_derived": resolved.get('is_derived'),
                            "component_variables": resolved.get('variables'),
                            "needs_area_data": resolved.get('needs_area')
                        })
                    
                    doc_snippets = resolved.get('doc_context') or result.get('doc_context', [])
                    if doc_snippets:
                        st.markdown("**Documentation Sources:**")
                        for snippet in doc_snippets:
                            title = snippet.get("heading") or snippet.get("table_id") or snippet.get("source")
                            source = snippet.get("source", "Unknown source")
                            quoted = textwrap.shorten(snippet.get("text", ""), width=200, placeholder="…")
                            st.caption(f"{title} ({source}): {quoted}")
                    
                    # Show what was queried from Census API
                    st.markdown("---")
                    st.markdown("#### Census API Query")
                    
                    if resolved.get('is_derived'):
                        st.info(f"🧮 **Derived Metric** - Computed from variables: {', '.join(resolved.get('variables', []))}")
                    else:
                        st.info(f"📊 **Direct Variable** - Census variable: `{resolved.get('variable_id')}`")
                    
                    if intent.get('county_fips'):
                        from geography import get_parish_name
                        parish_name = get_parish_name(intent.get('county_fips'))
                        st.success(f"🗺️ **Geographic Filter** - Limited to {parish_name} (FIPS: {intent.get('county_fips')})")
                    else:
                        st.warning("🗺️ **Geographic Scope** - Statewide (all Louisiana parishes)")
                
                # Show general query metadata
                st.markdown("---")
                st.markdown("#### ℹ️ Query Metadata")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Mode:** {result['mode'].title()}-Agent")
                    st.markdown(f"**Execution Time:** {result['execution_time']:.2f}s")
                
                with col2:
                    st.markdown(f"**Result Count:** {len(result['dataframe'])} tracts")
                    st.markdown(f"**Metric Label:** {result['label']}")
                
                with col3:
                    if result.get('from_cache'):
                        st.markdown("**Source:** ⚡ Cache")
                    else:
                        st.markdown("**Source:** 🌐 Live query")
                    st.markdown(f"**Timestamp:** {result.get('timestamp', 'N/A')}")
                
                # Show dataframe preview
                st.markdown("---")
                st.markdown("#### 📊 Result Data Preview")
                st.dataframe(
                    result["dataframe"],
                    width="stretch",
                    height=200
                )

    st.markdown("---")
    render_variable_chatbox()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
