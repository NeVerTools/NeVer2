import sys
from pathlib import Path


# project_root = .../NeVer2
project_root = Path(__file__).resolve().parents[3]

# add src/main/NeVer2 to PYTHONPATH
sys.path.insert(0, str(project_root / "src/main/NeVer2"))