import os
import sys
from pathlib import Path

# Aggiungi la directory root del progetto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root)) 