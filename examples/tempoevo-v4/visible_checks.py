"""Illustrative deterministic public evaluator. Candidate path is argv[-1]."""
import ast
import json
import sys
from pathlib import Path
source=(Path(sys.argv[-1])/'main.py').read_text()
try:
    tree=ast.parse(source)
    actual=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant))
    passed=actual==2
    result=dict(passed=passed,observations=[dict(check='public_value',actual=actual,expected=2,passed=passed)],regressions=[],unknowns=[])
except (SyntaxError,StopIteration) as error:
    result=dict(passed=False,observations=[dict(check='parse_or_value',passed=False,error=str(error))],regressions=[],unknowns=[])
print(json.dumps(result))
