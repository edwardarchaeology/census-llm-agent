"""
Unified CLI for Census Data Getter with configurable architecture.
Supports both single-agent and multi-agent modes.
"""
import sys
import argparse
from typing import Literal

# Architecture modes
ArchitectureMode = Literal["single", "multi"]


def run_single_agent_mode():
    """Run in single-agent mode (original mvp.py)."""
    import sys
    sys.path.insert(0, 'src/single_agent')
    from mvp import main as mvp_main
    print("=" * 80)
    print("Running in SINGLE-AGENT mode")
    print("Using: phi3:mini with single prompt")
    print("Speed: Fast (~2-5 seconds per query)")
    print("=" * 80)
    print()
    mvp_main()


def run_multi_agent_mode():
    """Run in multi-agent mode (mvp_multiagent.py)."""
    import sys
    sys.path.insert(0, 'src')
    from mvp_multiagent import main as multiagent_main
    print("=" * 80)
    print("Running in MULTI-AGENT mode")
    print("Agents: Orchestrator, Geography, Variable Resolver, Query Planner")
    print("Using: phi3:mini shared across all agents")
    print("Speed: Slower (~8-15 seconds per query)")
    print("Benefits: Better accuracy, confidence scores, conversation memory")
    print("=" * 80)
    print()
    multiagent_main()


def get_architecture_mode() -> ArchitectureMode:
    """Get architecture mode from command line args or environment."""
    import os
    
    # Check environment variable first
    env_mode = os.getenv("AGENT_MODE", "").lower()
    if env_mode in ["single", "multi"]:
        return env_mode
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Louisiana Census Data Getter - Natural Language Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Architecture Modes:
  single    Fast single-agent mode using one LLM call (default)
  multi     Multi-agent mode with specialized agents (better accuracy)

Examples:
  python main.py              # Single-agent mode (default)
  python main.py --mode multi # Multi-agent mode
  python main.py -m multi     # Multi-agent mode (short form)

Environment Variable:
  AGENT_MODE=multi python main.py  # Set via environment
        """
    )
    
    parser.add_argument(
        "-m", "--mode",
        choices=["single", "multi"],
        default="single",
        help="Architecture mode: 'single' (fast) or 'multi' (accurate)"
    )
    
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Show comparison between single and multi-agent modes"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        show_comparison()
        sys.exit(0)
    
    return args.mode


def show_comparison():
    """Display comparison between single and multi-agent modes."""
    print("=" * 80)
    print("ARCHITECTURE COMPARISON")
    print("=" * 80)
    print()
    
    print("SINGLE-AGENT MODE (--mode single)")
    print("-" * 80)
    print("Architecture:  One LLM call with complex prompt")
    print("Model:         phi3:mini")
    print("Memory:        ~2GB")
    print("Speed:         Fast (2-5 seconds per query)")
    print("Accuracy:      Good for simple queries")
    print("Features:      Basic intent extraction")
    print()
    print("Pros:")
    print("  + Fast response time")
    print("  + Simple architecture")
    print("  + Low latency")
    print()
    print("Cons:")
    print("  - No confidence scoring")
    print("  - No conversation memory")
    print("  - Less accurate on complex queries")
    print("  - Harder to debug")
    print()
    
    print("MULTI-AGENT MODE (--mode multi)")
    print("-" * 80)
    print("Architecture:  Specialized agents coordinated by orchestrator")
    print("Agents:        Orchestrator, Geography, Variable, Query Planner")
    print("Models:        All use phi3:mini (shared instance)")
    print("Memory:        ~2GB (same as single)")
    print("Speed:         Slower (8-15 seconds per query)")
    print("Accuracy:      Better, especially for complex queries")
    print("Features:      Confidence scores, conversation memory, planning")
    print()
    print("Pros:")
    print("  + Better accuracy (+30-50%)")
    print("  + Confidence scoring")
    print("  + Conversation memory for follow-ups")
    print("  + Modular and extensible")
    print("  + Better error handling")
    print("  + Easier to debug")
    print()
    print("Cons:")
    print("  - Slower response time")
    print("  - More complex architecture")
    print("  - Multiple LLM calls per query")
    print()
    
    print("RECOMMENDATIONS")
    print("-" * 80)
    print("Use SINGLE-AGENT when:")
    print("  • Speed is critical")
    print("  • Queries are simple and well-structured")
    print("  • Prototyping or testing")
    print()
    print("Use MULTI-AGENT when:")
    print("  • Accuracy is critical")
    print("  • Need confidence feedback")
    print("  • Complex or ambiguous queries")
    print("  • Production deployment")
    print("  • Need conversation context")
    print()
    print("=" * 80)


def main():
    """Main entry point with architecture selection."""
    try:
        mode = get_architecture_mode()
        
        if mode == "single":
            run_single_agent_mode()
        elif mode == "multi":
            run_multi_agent_mode()
        else:
            print(f"Error: Invalid mode '{mode}'. Use 'single' or 'multi'.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

