"""Absolute-path entry point usable by Codex and isolated editor processes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from temporal_contract_analyzer.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
