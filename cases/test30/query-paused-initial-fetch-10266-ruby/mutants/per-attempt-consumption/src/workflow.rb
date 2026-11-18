class Session
 Attempt=Struct.new(:number,:previous,:options,:settled,:consumed,:retry_cancelled,:failures,:queued)
 Query=Struct.new(:key,:state,:observers,:attempt,:consumed)
 def initialize(env,initial);@env=env;@cache={};@handles={};@online=initial.fetch('online',true);@focused=initial.fetch('focused',true);@serial=@fetch_serial=0;end
 def eligible(a);@focused&&(a.options.fetch('networkMode','online')=='always'||@online);end
 def active(q,a);q.attempt.equal?(a)&&!a.settled;end
 def cancel(q,a);return if a.settled;a.settled=true;q.state=a.previous.dup;q.state['fetchStatus']='idle';@env.call('abort',q.key,a.number);end
 def invoke(q,a)
  a.queued=false;return unless active(q,a);q.state['fetchStatus']='fetching';a.consumed=false
  getter=@env.bind(proc{|_|a.consumed=true;nil})
  done=@env.bind(proc do |value|
   next unless active(q,a)
   if value['ok'];a.settled=true;q.state.merge!('data'=>value['value'],'status'=>'success','fetchStatus'=>'idle')
   elsif !a.retry_cancelled&&a.failures<a.options.fetch('retry',0)
    a.failures+=1
    token=@env.bind(proc do |_|
     next unless active(q,a)
     if a.retry_cancelled;a.settled=true;q.state.merge!('status'=>'error','fetchStatus'=>'idle');next;end
     if eligible(a);invoke(q,a);else;q.state['fetchStatus']='paused';end
    end);@env.call('schedule',token,a.options.fetch('retryDelay',10))
   else;a.settled=true;q.state.merge!('status'=>'error','fetchStatus'=>'idle');end
   nil
  end);@env.call('request',q.key,a.number,getter,done)
 end
 def resume(q)
  a=q.attempt
  if a&&active(q,a)&&q.state['fetchStatus']=='paused'&&eligible(a)&&!a.queued
   a.queued=true;token=@env.bind(proc do |_|
    a.queued=false;next unless active(q,a)
    if a.failures>0&&a.retry_cancelled;a.settled=true;q.state.merge!('status'=>'error','fetchStatus'=>'idle');next;end
    invoke(q,a);nil
   end);@env.call('defer',token)
  end
 end
 def subscribe(key,options)
  data=options['initialData'];q=@cache[key]||=Query.new(key,{'status'=>data.nil? ? 'pending' : 'success','fetchStatus'=>'idle','data'=>data},{},nil,false)
  @serial+=1;handle=@serial;@handles[handle]=q;q.observers[handle]=true
  if q.attempt&&!q.attempt.settled;q.attempt.retry_cancelled=false;resume(q)
  else
   @fetch_serial+=1;a=Attempt.new(@fetch_serial,q.state.dup,options,false,false,false,0,false);q.attempt=a;@env.call('newAttempt',key,a.number)
   if options.fetch('networkMode','online')!='online'||@online;invoke(q,a);else;q.state['fetchStatus']='paused';end
  end;handle
 end
 def unsubscribe(handle)
  q=@handles.delete(handle);return unless q;q.observers.delete(handle)
  if q.observers.empty?;a=q.attempt;if a&&!a.settled;if a.consumed||(q.state['fetchStatus']=='paused'&&q.state['status']=='pending');cancel(q,a);else;a.retry_cancelled=true;end;end;end
 end
 def handle(name,args)
  case name
  when 'subscribe';return subscribe(*args)
  when 'unsubscribe';unsubscribe(*args);return nil
  when 'snapshot';return @cache[args[0]].state.dup
  when 'dispose';@handles.keys.each{|h|unsubscribe(h)};return nil
  when 'online';@online=args[0]
  when 'focus';@focused=args[0]
  else;raise name
  end
  @cache.values.dup.each{|q|resume(q)};nil
 end
end
