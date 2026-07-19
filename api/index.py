import os
import sys

# Add the root directory to the python path to import modules from the parent folder (api.py, vcbrain)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app
