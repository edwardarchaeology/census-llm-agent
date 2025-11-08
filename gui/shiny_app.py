"""
Louisiana Census Data Explorer - Shiny for Python
Simple, clean interface without caching issues.
"""
import sys
from pathlib import Path
import pandas as pd
import json

# Add src directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "single_agent"))

from shiny import App, ui, render, reactive
from htmltools import HTML
from single_agent.mvp import run_query as run_single_agent_query

# ============================================================================
# UI
# ============================================================================

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(HTML("""
            body { background-color: #f5f5f5; }
            .app-header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                margin-bottom: 2rem;
                border-radius: 8px;
            }
            .card { 
                background: white;
                padding: 1.5rem;
                margin-bottom: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .example-btn {
                margin: 0.25rem;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
            }
            .example-btn:hover {
                background: #e9ecef;
            }
            .status-ok { color: #28a745; font-weight: bold; }
            .status-error { color: #dc3545; font-weight: bold; }
        """))
    ),
    
    # Header
    ui.div(
        {"class": "app-header"},
        ui.h1("🗺️ Louisiana Census Data Explorer"),
        ui.p("Ask questions about Louisiana census tracts in natural language")
    ),
    
    # Main content
    ui.layout_sidebar(
        # Sidebar
        ui.sidebar(
            ui.h4("⚙️ Settings"),
            ui.input_radio_buttons(
                "mode",
                "Agent Mode",
                choices={
                    "single": "⚡ Single Agent (Fast)",
                    "multi": "🤖 Multi-Agent (Accurate)"
                },
                selected="single"
            ),
            ui.input_checkbox("verbose", "Show detailed output", value=False),
            ui.hr(),
            ui.h4("ℹ️ About"),
            ui.p("Natural language interface for Louisiana census tract data."),
            ui.tags.ul(
                ui.tags.li("All 64 Louisiana parishes"),
                ui.tags.li("Census Tracts (ACS 5-Year 2023)"),
                ui.tags.li("Population, Income, Poverty data")
            ),
            ui.hr(),
            ui.output_ui("ollama_status"),
        ),
        
        # Main content area
        ui.div(
            # Query input
            ui.div(
                {"class": "card"},
                ui.h3("🔍 Enter Your Query"),
                ui.input_text(
                    "query",
                    "",
                    placeholder="Example: What are the top 5 census tracts in Orleans Parish by median income?",
                    width="100%"
                ),
                ui.input_action_button("search", "🔍 Search", class_="btn-primary"),
                ui.input_action_button("clear", "🗑️ Clear", class_="btn-secondary"),
            ),
            
            # Example queries
            ui.div(
                {"class": "card"},
                ui.h4("💡 Example Queries"),
                ui.output_ui("example_buttons")
            ),
            
            # Results
            ui.output_ui("results")
        )  # close ui.div (main content area)
    )  # close ui.layout_sidebar
)  # close ui.page_fluid

# ============================================================================
# SERVER
# ============================================================================

def server(input, output, session):
    # Reactive values
    result_data = reactive.Value(None)
    error_msg = reactive.Value(None)
    is_loading = reactive.Value(False)
    loading_status = reactive.Value("")
    
    # Ollama status
    @output
    @render.ui
    def ollama_status():
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return ui.div(
                    {"class": "status-ok"},
                    "🟢 Ollama: Running"
                )
        except:
            pass
        return ui.div(
            {"class": "status-error"},
            "🔴 Ollama: Not running"
        )
    
    # Example query buttons
    @output
    @render.ui
    def example_buttons():
        examples = [
            "What are the top 5 census tracts in Orleans Parish by median income?",
            "Show me census tracts with poverty rate over 30% in Caddo Parish",
            "What are the most densely populated tracts in Lafayette Parish?",
            "Find tracts in St. Tammany Parish with poverty rate under 10%"
        ]
        
        buttons = []
        for i, ex in enumerate(examples):
            buttons.append(
                ui.input_action_button(
                    f"example_{i}",
                    f"📊 {ex[:50]}...",
                    class_="example-btn",
                    width="100%"
                )
            )
        return ui.div(*buttons)
    
    # Handle example button clicks
    @reactive.Effect
    def _():
        for i in range(4):
            if input[f"example_{i}"]() > 0:
                examples = [
                    "What are the top 5 census tracts in Orleans Parish by median income?",
                    "Show me census tracts with poverty rate over 30% in Caddo Parish",
                    "What are the most densely populated tracts in Lafayette Parish?",
                    "Find tracts in St. Tammany Parish with poverty rate under 10%"
                ]
                ui.update_text("query", value=examples[i])
    
    # Handle search button
    @reactive.Effect
    @reactive.event(input.search)
    def execute_search():
        query = input.query()
        if not query:
            return
        
        try:
            # Clear previous results and errors
            error_msg.set(None)
            result_data.set(None)
            is_loading.set(True)
            
            # Execute query with status updates
            if input.mode() == "single":
                loading_status.set("🔍 Processing query with single agent...")
                result_df = run_single_agent_query(query, return_debug_info=True)
            else:
                from mvp_multiagent import run_multiagent_query
                loading_status.set("🤖 Initializing multi-agent system...")
                # TODO: Add callback for status updates from orchestrator
                result_df = run_multiagent_query(query, verbose=input.verbose())
            
            # Store result
            result_data.set({
                "dataframe": result_df,
                "label": result_df.attrs.get("label", "Census Data"),
                "debug_info": result_df.attrs.get("debug_info"),
                "query": query
            })
            is_loading.set(False)
            loading_status.set("")
            
        except Exception as e:
            error_msg.set(str(e))
            result_data.set(None)
            is_loading.set(False)
            loading_status.set("")
    
    # Handle clear button
    @reactive.Effect
    @reactive.event(input.clear)
    def clear_results():
        result_data.set(None)
        error_msg.set(None)
        ui.update_text("query", value="")
    
    # Display results
    @output
    @render.ui
    def results():
        # Show loading indicator
        if is_loading.get():
            return ui.div(
                {"class": "card"},
                ui.div(
                    {"class": "alert alert-info"},
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        ui.div(
                            {"class": "spinner-border spinner-border-sm me-2", "role": "status"},
                            ui.span({"class": "visually-hidden"}, "Loading...")
                        ),
                        ui.strong(loading_status.get() or "Processing query...")
                    )
                ),
                ui.p("This may take a few moments. Multi-agent queries can take 30-60 seconds.")
            )
        
        # Check for errors
        if error_msg.get():
            return ui.div(
                {"class": "card"},
                ui.div(
                    {"class": "alert alert-danger"},
                    ui.strong("❌ Error: "),
                    error_msg.get()
                ),
                ui.p("Make sure Ollama is running: ", ui.code("ollama serve"))
            )
        
        # Check for results
        result = result_data.get()
        if not result:
            return ui.div()
        
        df = result["dataframe"]
        label = result["label"]
        
        # Build results UI
        return ui.div(
            ui.div(
                {"class": "card"},
                ui.h3(f"📊 Results: {label}"),
                ui.p(f"Found {len(df)} census tracts"),
                ui.hr(),
                
                # Data table
                ui.output_data_frame("result_table"),
                
                ui.hr(),
                
                # Download buttons
                ui.h4("📥 Downloads"),
                ui.download_button("download_csv", "📊 Download CSV"),
                ui.download_button("download_json", "📋 Download JSON"),
            ),
            
            # Debug info
            ui.panel_conditional(
                "input.verbose",
                ui.div(
                    {"class": "card"},
                    ui.h4("🔍 Debug Information"),
                    ui.output_ui("debug_info")
                )
            )
        )
    
    # Render data table
    @output
    @render.data_frame
    def result_table():
        result = result_data.get()
        if result:
            df = result["dataframe"].copy()
            # Round values
            if "value" in df.columns:
                df["value"] = df["value"].round(2)
            return df
        return pd.DataFrame()
    
    # Render debug info
    @output
    @render.ui
    def debug_info():
        result = result_data.get()
        if result and result.get("debug_info"):
            debug = result["debug_info"]
            return ui.div(
                ui.h5("Intent:"),
                ui.pre(json.dumps(debug.get("intent", {}), indent=2)),
                ui.h5("Resolution:"),
                ui.pre(json.dumps({
                    "label": debug.get("resolved", {}).get("label"),
                    "variable_id": debug.get("resolved", {}).get("variable_id"),
                    "is_derived": debug.get("resolved", {}).get("is_derived")
                }, indent=2))
            )
        return ui.div()
    
    # CSV download
    @render.download(filename="census_results.csv")
    def download_csv():
        result = result_data.get()
        if result:
            df = result["dataframe"]
            yield df.to_csv(index=False)
    
    # JSON download
    @render.download(filename="census_results.json")
    def download_json():
        result = result_data.get()
        if result:
            df = result["dataframe"]
            yield df.to_json(orient="records", indent=2)

# ============================================================================
# CREATE APP
# ============================================================================

app = App(app_ui, server)
