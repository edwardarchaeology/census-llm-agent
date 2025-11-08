"""Run the Shiny GUI."""
import subprocess
import sys

print("=" * 60)
print("Louisiana Census Data Explorer - Shiny Version")
print("=" * 60)
print()
print("Starting Shiny app...")
print("Access the app at: http://localhost:8000")
print("Press Ctrl+C to stop")
print()

# Run shiny
subprocess.run([
    sys.executable, "-m", "shiny", "run",
    "gui/shiny_app.py",
    "--reload",
    "--port", "8000"
])
