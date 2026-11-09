from pathlib import Path
from archive import sha
def frozen_input_files(root):
 return {str(p):sha(p) for p in Path(root).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name not in ["initial-freeze.json","actual-schedule.json","stop.json"] and p.suffix!=".log"}
