import sys
import os

# Ensure the local root package is loaded first
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Remove sdk/python from sys.path if present to prevent collision
sys.path = [p for p in sys.path if not p.endswith(os.path.join("sdk", "python"))]

