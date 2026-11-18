require 'json'
require File.join(ARGV[0],'src','workflow.rb')
STDOUT.sync=true
class Host
 def initialize;@callbacks,@controllers={}, {};@serial=0;end
 def call(kind,*args)
  puts JSON.generate({call:kind,args:args})
  loop do
   m=JSON.parse(STDIN.readline);return m['reply'] if m.key?('reply');dispatch(m)
  end
 end
 def bind(fn);@serial+=1;@callbacks[@serial]=fn;@serial;end
 def defer(&fn);call('defer',bind(proc {|_| fn.call}));end
 def resolve(kind,key,frame,&fn)
  id=bind(fn);r=call(kind,key,frame,id);@callbacks.delete(id).call(r['value']) unless r['deferred']
 end
 def schedule(delay,&fn);call('schedule',bind(proc {|_| fn.call}),delay);end
 def cancel(handle);call('cancel',handle);end
 def output(kind,key,value);call(kind,key,value);end
 def dispatch(m)
  a=m['args'];result=nil
  case m['method']
  when 'create' then @controllers[a[0]]=Controller.new(self,*a)
  when 'call' then result=@controllers[a[0]].public_send(a[1],*a[2])
  when 'invoke' then @callbacks.delete(a[0]).call(a[1])
  else raise m['method']
  end
  puts JSON.generate({result:result})
 end
end
host=Host.new;STDIN.each_line {|line| host.dispatch(JSON.parse(line))}
