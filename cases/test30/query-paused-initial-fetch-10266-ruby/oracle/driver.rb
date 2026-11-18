require 'json'
load ARGV[0]+'/src/workflow.rb'
$callbacks={};$sessions={};$serial=0
class Env
 def initialize(w);@w=w;end
 def bind(fn);$serial+=1;$callbacks[$serial]=fn;$serial;end
 def call(name,*args)
  send_json({'call'=>name,'args'=>[@w]+args})
  loop do
   m=JSON.parse(STDIN.gets);return m['reply'] if m.key?('reply');answer(m)
  end
 end
end
def send_json(v);STDOUT.puts(JSON.generate(v));STDOUT.flush;end
def dispatch(m)
 name=m['method'];a=m['args'];return $callbacks[a[0]].call(a[1]) if name=='invoke'
 if name=='init';$sessions[a[0]]=Session.new(Env.new(a[0]),a[1]);return nil;end
 $sessions[a[0]].handle(name,a.drop(1))
end
def answer(m);send_json({'result'=>dispatch(m)});end
STDIN.each_line{|line|answer(JSON.parse(line))}
