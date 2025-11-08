"""
Pytest configuration for test discovery and path setup.
"""
import sys
import os

# Get absolute paths
tests_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(tests_dir)

# Add src directory to Python path for imports
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Add single_agent directory for direct imports
single_agent_path = os.path.join(src_path, 'single_agent')
sys.path.insert(0, single_agent_path)

# Change to project root so cache paths work
os.chdir(project_root)
