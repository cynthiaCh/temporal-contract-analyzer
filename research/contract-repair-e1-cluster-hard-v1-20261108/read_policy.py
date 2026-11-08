"""Closed read-command grammar, including ordinary candidate-file for loops.

The filesystem namespace remains the isolation boundary. This parser grants
read commands; it does not evaluate shell syntax or execute a validation shell.
"""
import glob
import re
import shlex
from pathlib import Path

READERS={'pwd','ls','rg','cat','nl','sed','head','tail','wc','echo','printf'}
CONTROL={';','&&','|'}

def allowed(command, workspace='/workspace'):
 if not isinstance(command,str) or any(x in command for x in ['`','$(','${!','<(','>(']):return False
 lexer=shlex.shlex(command,posix=True,punctuation_chars=';&|<>')
 lexer.whitespace_split=True;lexer.commenters='#'
 try:tokens=list(lexer)
 except ValueError:return False
 root=Path(workspace).resolve();bindings={};i=0
 def expand(token):
  def replace(match):
   name=match.group(1) or match.group(2)
   if name not in bindings:raise ValueError('unbound shell variable')
   return bindings[name][0]
  # The variable values have all been path-validated on loop admission.
  result=re.sub(r'\$\{([A-Za-z_][A-Za-z_0-9]*)\}|\$([A-Za-z_][A-Za-z_0-9]*)',replace,token)
  if '$' in result:raise ValueError('unsupported expansion')
  return result
 def path_ok(token,required=False):
  token=expand(token)
  if token.startswith('~') or any(p=='..' for p in token.split('/')):return False
  local=root/token
  if token.startswith('/') or required or token.startswith(('./','src/')) or local.exists() or local.is_symlink() or glob.has_magic(token):
   p=Path(token);p=p if p.is_absolute() else root/p
   try:
    if not (p.resolve()==root or root in p.resolve().parents):return False
    for q in glob.glob(str(p)):
     if not (Path(q).resolve()==root or root in Path(q).resolve().parents):return False
   except (OSError,ValueError):return False
  return True
 def simple(words):
  if not words or words[0] not in READERS:return False
  if any(t in ['&','||','>','>>','<','<<','<<<',';;'] for t in words):return False
  if any(not path_ok(t) for t in words[1:]):return False
  name=words[0]
  if name=='rg' and any(t.startswith(('--pre','--hostname-bin','--files-from','--ignore-file')) for t in words[1:]):return False
  if name=='sed':
   args=words[1:]
   if not args or args[0]!='-n' or len(args)<2:return False
   if not re.fullmatch(r'(?:\d+|\$)(?:,(?:\d+|\$))?p',args[1]):return False
   if any(t.startswith('-') for t in args[2:]):return False
  if name=='printf' and any(t=='-v' for t in words[1:]):return False
  return True
 def sequence(stop=False):
  nonlocal i
  need=True;seen=False
  while i<len(tokens):
   if stop and tokens[i]=='done':return seen and not need
   if tokens[i]==';':
    i+=1
    if not seen:continue
    need=False
    continue
   if tokens[i] in ['&&','|']:
    if need or not seen:return False
    i+=1;need=True;continue
   if not need and seen and tokens[i-1]!=';':return False
   if tokens[i]=='for':
    i+=1
    if i+2>=len(tokens) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',tokens[i]):return False
    var=tokens[i];i+=1
    if var in bindings or tokens[i]!='in':return False
    i+=1;values=[]
    while i<len(tokens) and tokens[i]!=';':
     if tokens[i] in ['&&','|','&','||','>','<'] or not path_ok(tokens[i],True):return False
     values.append(expand(tokens[i]));i+=1
    if not values or i+1>=len(tokens) or tokens[i+1]!='do':return False
    i+=2;bindings[var]=values
    if not sequence(True):return False
    if i>=len(tokens) or tokens[i]!='done':return False
    i+=1;del bindings[var]
   else:
    words=[]
    while i<len(tokens) and tokens[i] not in CONTROL and not (stop and tokens[i]=='done'):
     words.append(tokens[i]);i+=1
    if not simple(words):return False
   seen=True;need=False
  return seen and not need and not stop
 try:return sequence() and i==len(tokens)
 except (ValueError,IndexError):return False

def read_command(event):
 inp=event.get('tool_input',{});name=event.get('tool_name','').lower()
 if not isinstance(inp,dict) or not any(x in name for x in ['bash','exec_command','shell']):return False
 if inp.get('workdir',inp.get('cwd','/workspace'))!='/workspace':return False
 return allowed(inp.get('command',inp.get('cmd','')))
