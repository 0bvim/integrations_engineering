import sys
import os

# Add the project root directory to the Python path
# This allows imports from the 'src' directory
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
