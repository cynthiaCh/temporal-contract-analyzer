"""Source-only lexical cues and advisory coverage, never a semantic rewriter."""
import re

GUIDANCE='''QUALIFICATION AND NEGATION SCOPE — before writing the Contract:
Separate the action, its event modifiers, and the circumstances under which the
requirement applies. A reported defect may be ACTION AND PROPERTY AND CONTEXT.
Repairing that defect means prohibiting that combined event; it does NOT by
itself require prohibiting ACTION in every form. Preserve genuine modifiers,
quantifiers and negation scope from the source. Do not discard a modifier just
because the resulting unqualified rule is simpler to state.
For example, "writes with an obsolete revision" does not imply "never writes".
"Publishes stale output after replacement" does not imply "never publishes".
Keep conditions inside the event that is prohibited when that is the source
meaning. A particular permitted strategy is not the only required strategy.
Use this same rule for every task, independent of names, language or class.

The payload contains lexical qualifier_cues from TASK with exact source span
IDs. They are source-text reminders, not policy annotations or expected answers;
some prepositions may be irrelevant. Read the full source, determine which
modifiers actually constrain the defect/requirement, and preserve their meaning
in the Contract and claims. Equivalent wording is allowed. Do not blindly turn
every cue into a new requirement. Your self-consistency check must compare each
normative paraphrase with its source, including omitted modifiers and stronger
absolute prohibitions. Mark a genuine unresolved policy conflict instead of
inventing certainty. Python will NOT fix, complete or weaken your output.
'''

PATTERN=re.compile(r'\b(?:without|with|unless|only\s+(?:when|if)|while|after|before)\b',re.I)
STOP={'with','without','unless','only','when','while','after','before','the','and','its','that','this','from','into','for','then','must','not','with','are','was'}

def cues(task,catalog):
 result=[]
 for line_number,line in enumerate(task.splitlines(),1):
  for match in PATTERN.finditer(line):
   start=match.start();end=min(len(line),start+80)
   # These are lexical contexts only; no dependency attachment is asserted.
   boundary=re.search(r'[.;,]',line[start:end])
   if boundary:end=start+boundary.start()
   quote=line[start:end].rstrip();end=start+len(quote)
   refs=[r['id'] for r in catalog['entries'] if r['file']=='TASK' and r['line']==line_number and r['start_column']<end and r['end_column']>start]
   result.append({'cue':match.group(),'file':'TASK','line':line_number,'start_column':start,'end_column':end,'quote':quote,'evidence_ids':refs,'status':'lexical_context_not_semantic_policy'})
 return result

def coverage(task,contract,catalog):
 """Flag potentially lost source words; synonyms/translations need AI review."""
 words=set(re.findall(r'[a-z]+',contract.lower()));findings=[]
 for row in cues(task,catalog):
  keywords={w for w in re.findall(r'[a-z]+',row['quote'].lower()) if len(w)>2 and w not in STOP}
  missing=sorted(keywords-words)
  if missing:findings.append({'source_cue':row,'missing_literal_words':missing,'meaning':'Possible omission or equivalent paraphrase; execution-agent semantic review must decide.'})
 return {'status':'advisory_only','findings':findings,'semantic_review_required':True,'automatic_validity_decision':None,'contract_rewritten':False}
