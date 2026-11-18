"""Closed read-command grammar, including candidate-file loops and literal file guards.

The filesystem namespace remains the isolation boundary. This parser grants
read commands; it does not evaluate shell syntax or execute a validation shell.
"""
import glob
import re
import shlex
from pathlib import Path

READERS={'pwd','ls','rg','cat','nl','sed','head','tail','wc','echo','printf','true','git','sort'}
CONTROL={';','&&','|','||'}

def _without_comments(command):
 """Preserve shell statement boundaries, quoted hashes and continuations."""
 out=[];quote=None;escaped=False;word_start=True;i=0
 while i<len(command):
  char=command[i]
  if escaped:
   out.append(char);escaped=False;word_start=False;i+=1;continue
  if quote!="'" and char=='\\' and i+1<len(command) and command[i+1]=='\n':
   i+=2;continue
  if quote=="'":
   out.append(char)
   if char==quote:quote=None
   i+=1;continue
  if char=='\\':
   out.append(char);escaped=True;word_start=False;i+=1;continue
  if quote=='"':
   out.append(char)
   if char==quote:quote=None
   i+=1;continue
  if char in ("'",'"'):
   out.append(char);quote=char;word_start=False;i+=1;continue
  if char=='#' and word_start:
   newline=command.find('\n',i)
   if newline<0:break
   out.append('\n');word_start=True;i=newline+1;continue
  out.append(char);word_start=char.isspace() or char in ';&|<>';i+=1
 return ''.join(out)

def allowed(command, workspace='/workspace'):
 if not isinstance(command,str) or any(x in command for x in ['`','$(','${!','<(','>(']):return False
 lexer=shlex.shlex(_without_comments(command),posix=True,punctuation_chars=';&|<>\n')
 lexer.whitespace=' \t\r';lexer.whitespace_split=True;lexer.commenters=''
 try:
  tokens=[]
  for token in lexer:
   if '\n' in token:
    if all(c in ';\n' for c in token):token=';'
    elif token.rstrip('\n') in ('&&','|','||'):token=token.rstrip('\n')
   tokens.append(token)
 except ValueError:return False
 # Discarding stderr to the null device is not a candidate write.
 cleaned=[];j=0
 while j<len(tokens):
  if tokens[j:j+3]==['2','>','/dev/null']:j+=3;continue
  cleaned.append(tokens[j]);j+=1
 tokens=cleaned
 if any(t and all(c in ';&|<>' for c in t) and t not in CONTROL for t in tokens):return False
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
  if name=='git':return words in (['git','status','--short'],['git','--no-optional-locks','status','--short'])
  if name=='true':return len(words)==1
  if name=='rg' and any(t.startswith(('--pre','--hostname-bin','--files-from','--ignore-file')) for t in words[1:]):return False
  if name=='sort':
   # Accept display sorting only, not output files, temporary-directory
   # overrides, external compressors, or auxiliary input-file switches.
   options=True
   for arg in words[1:]:
    if options and arg=='--':options=False;continue
    if options and arg.startswith('-') and not (re.fullmatch(r'-[bnrfusVh]+',arg) or arg in {
     '--numeric-sort','--reverse','--unique','--ignore-case','--ignore-leading-blanks',
     '--stable','--version-sort','--human-numeric-sort'}):return False
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
   marker=stop if isinstance(stop,str) else 'done'
   if stop and tokens[i]==marker:return seen and not need
   if tokens[i]==';':
    i+=1
    if not seen:continue
    need=False
    continue
   if tokens[i] in ['&&','|','||']:
    if need or not seen:return False
    i+=1;need=True;continue
   if not need and seen and tokens[i-1]!=';':return False
   if tokens[i]=='if':
    i+=1
    if i+5>=len(tokens) or tokens[i]!='[' or tokens[i+1] not in ('-f','-d','-e') or tokens[i+3:i+6]!=[']',';','then']:return False
    if '$' in tokens[i+2] or not path_ok(tokens[i+2],True):return False
    i+=6
    if not sequence('fi') or i>=len(tokens) or tokens[i]!='fi':return False
    i+=1
   elif tokens[i]=='for':
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
    while i<len(tokens) and tokens[i] not in CONTROL and not (stop and tokens[i]==marker):
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
