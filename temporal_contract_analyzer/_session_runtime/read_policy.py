"""Closed read-command grammar, including candidate-file loops and literal file guards.

The filesystem namespace remains the isolation boundary. This parser grants
read commands; it does not evaluate shell syntax or execute a validation shell.
"""
import glob
import re
import shlex
from pathlib import Path

READERS={'pwd','ls','rg','cat','nl','sed','head','tail','wc','echo','printf','true','test','git','find','sort'}
CONTROL={';','&&','|','||'}

def allowed(command, workspace='/workspace'):
 if not isinstance(command,str) or any(x in command for x in ['`','$(','${!','<(','>(']):return False
 lexer=shlex.shlex(command,posix=True,punctuation_chars=';&|<>')
 lexer.whitespace_split=True;lexer.commenters='#'
 try:tokens=list(lexer)
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
  if any(len(part.encode('utf-8'))>255 and not glob.has_magic(part) for part in token.split('/')):return False
  try:
   local=root/token
   if token.startswith('/') or required or token.startswith(('./','src/')) or local.exists() or local.is_symlink() or glob.has_magic(token):
    p=Path(token);p=p if p.is_absolute() else root/p
    if not (p.resolve()==root or root in p.resolve().parents):return False
    for q in glob.glob(str(p)):
     if not (Path(q).resolve()==root or root in Path(q).resolve().parents):return False
  except (OSError,ValueError,RuntimeError):return False
  return True
 def data_ok(token):
  # Reader patterns/output text are not filenames. In particular, stat() on a
  # long rg expression raises ENAMETOOLONG in the production Python 3.9 runtime.
  # shlex removes quoting, so never infer that an escaped variable is literal.
  # Only existing, path-validated loop bindings may expand; a standalone dollar
  # or regex end anchor is data, while shell parameter/arithmetic forms are not.
  def replace(match):
   name=match.group(1) or match.group(2)
   if name not in bindings:raise ValueError('unbound shell variable')
   return bindings[name][0]
  value=re.sub(r'\$\{([A-Za-z_][A-Za-z_0-9]*)\}|\$([A-Za-z_][A-Za-z_0-9]*)',replace,token)
  return re.search(r'\$[A-Za-z_0-9{\[\(?*@#$!\-]',value) is None
 def rg_ok(args):
  flags={'--files','--hidden','--line-number','--no-line-number','--column','--no-heading','--heading',
   '--with-filename','--no-filename','--ignore-case','--case-sensitive','--smart-case','--fixed-strings',
   '--word-regexp','--line-regexp','--files-with-matches','--files-without-match','--count','--count-matches',
   '--only-matching','--invert-match','--quiet','--no-messages','--text','--multiline','--multiline-dotall',
   '--pcre2','--no-ignore','--no-ignore-vcs','--no-ignore-parent','--no-ignore-global','--no-config',
   '--json','--stats','--max-columns-preview'}
  data_flags={'-e','--regexp','-g','--glob','--iglob','-t','--type','-T','--type-not'}
  number_flags={'-A','-B','-C','-m','--after-context','--before-context','--context','--max-count',
   '--max-depth','--max-columns'}
  positional=[];explicit_pattern=False;files=False;options=True;j=0
  while j<len(args):
   arg=args[j];j+=1
   if options and arg=='--':options=False;continue
   if options and arg.startswith('-') and arg!='-':
    key,separator,value=arg.partition('=')
    if key in flags and not separator:
     files=files or key=='--files';continue
    if key in data_flags or key in number_flags or key=='--color':
     if not separator:
      if j>=len(args):return False
      value=args[j];j+=1
     if key in data_flags:
      if not data_ok(value):return False
      explicit_pattern=explicit_pattern or key in ('-e','--regexp')
     elif key in number_flags:
      if not value.isdigit() or len(value)>7:return False
     elif value not in ('never','always','auto','ansi'):return False
     continue
    if re.fullmatch(r'-[niIHhSswxFcloqavUPu]+',arg):continue
    match=re.fullmatch(r'-([ABCm])(\d{1,7})',arg)
    if match:continue
    if arg.startswith(('-e','-g','-t','-T')) and len(arg)>2:
     if not data_ok(arg[2:]):return False
     explicit_pattern=explicit_pattern or arg.startswith('-e');continue
    # This excludes pattern/ignore files, --pre helpers, compressed-file
    # helpers, symlink following, and unknown options rather than guessing.
    return False
   positional.append(arg)
  if files:
   if explicit_pattern:return False
  elif not explicit_pattern:
   if not positional or not data_ok(positional.pop(0)):return False
  return all(path_ok(arg,True) for arg in positional)
 def simple(words):
  if not words or words[0] not in READERS:return False
  if any(t in ['&','||','>','>>','<','<<','<<<',';;'] for t in words):return False
  name=words[0]
  if name=='git':return words in (['git','status','--short'],['git','--no-optional-locks','status','--short'])
  if name=='true':return len(words)==1
  if name=='test':return len(words)==3 and words[1] in ('-f','-d','-e') and path_ok(words[2],True)
  if name=='rg':return rg_ok(words[1:])
  if name in ('echo','printf'):
   if name=='printf' and any(t.startswith('-v') for t in words[1:]):return False
   return all(data_ok(t) for t in words[1:])
  if name=='find':
   args=words[1:];j=0
   while j<len(args) and not args[j].startswith('-') and args[j] not in ('!','(',')'):
    if not path_ok(args[j],True):return False
    j+=1
   if j==0:return False
   need_operand=True;depth=0
   while j<len(args):
    flag=args[j];j+=1
    if flag in ('-not','!'):need_operand=True;continue
    if flag=='(':
     depth+=1
     if depth>8:return False
     need_operand=True;continue
    if flag==')':
     if not depth or need_operand:return False
     depth-=1;need_operand=False;continue
    if flag in ('-o','-or','-a','-and'):
     if need_operand:return False
     need_operand=True;continue
    if flag=='-print':need_operand=False;continue
    if j>=len(args):return False
    value=args[j];j+=1
    if flag in ('-maxdepth','-mindepth'):
     if not value.isdigit() or not 0<=int(value)<=20:return False
    elif flag=='-type':
     if value not in ('f','d','l'):return False
    elif flag in ('-name','-iname','-path','-ipath'):
     if value.startswith('-') or not data_ok(value):return False
    elif flag=='-printf':
     if value not in ('%p\\n','%P\\n','%f\\n'):return False
    else:return False
    need_operand=False
   return depth==0 and (not need_operand or len(args)==1)
  if name=='sort':
   flags={'--numeric-sort','--reverse','--unique','--ignore-case','--ignore-leading-blanks','--version-sort'}
   for arg in words[1:]:
    if arg.startswith('-'):
     if arg not in flags and not re.fullmatch(r'-[nrufbV]+',arg):return False
    elif not path_ok(arg,True):return False
  if name=='sed':
   args=words[1:]
   if not args or args[0]!='-n' or len(args)<2:return False
   if not re.fullmatch(r'(?:\d+|\$)(?:,(?:\d+|\$))?p',args[1]):return False
   if any(t.startswith('-') for t in args[2:]):return False
  return all(path_ok(t) for t in words[1:])
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
 except (ValueError,IndexError,OSError,RuntimeError):return False

def read_command(event):
 inp=event.get('tool_input',{});name=event.get('tool_name','').lower()
 if not isinstance(inp,dict) or not any(x in name for x in ['bash','exec_command','shell']):return False
 if inp.get('workdir',inp.get('cwd','/workspace'))!='/workspace':return False
 return allowed(inp.get('command',inp.get('cmd','')))
