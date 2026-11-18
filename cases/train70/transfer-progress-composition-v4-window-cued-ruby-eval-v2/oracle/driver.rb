require 'json'
require File.join(ARGV[0],'src','workflow.rb')
$telemetry={};$callbacks={};$sessions={};$handles={};$files={};$serial=0
class Env
 def initialize(w);@w=w;end
 def bind(fn);$serial+=1;$callbacks[$serial]=fn;$serial;end
 def call(name,*args)
  send_wire({call:name,args:[@w]+args})
  loop do
   m=JSON.parse(STDIN.gets);return m['reply'] if m.key?('reply');answer(m)
  end
 end
end
def send_wire(v);STDOUT.puts(JSON.generate(v));STDOUT.flush;end
def file_object(v);$files[v['token']]||=v;end
def remember(w,h);return nil unless h;$handles[[w,h.number]]=h;h.number;end
def dispatch(m)
 name=m['method'];a=m['args'];if name=='invoke';$callbacks[a[0]].call(a[1]);return nil;end;w=a[0]
 case name
 when 'telemetryStart';$telemetry[w]=Telemetry.new(Env.new(w),file_object(a[1]));nil
 when 'telemetryStop';$telemetry[w].stop.call;nil
 when 'init';$sessions[w]=Session.new(Env.new(w));nil
 when 'standalone';remember(w,Attempt.new(Env.new(w),file_object(a[1]),a[2]))
 when 'cancelHandle';$handles[[w,a[1]]].cancel;nil
 when 'select';remember(w,$sessions[w].select(file_object(a[1])))
 when 'retry';remember(w,$sessions[w].retry)
 else;$sessions[w].public_send(name)
 end
end
def answer(m);send_wire({result:dispatch(m)});end
STDIN.each_line{|line|answer(JSON.parse(line))}
