class PublicationWindow
 def initialize;@arrived=0;@published=0;end
 def arrive;@arrived+=1;end
 def publish(order);return false if order<=@published;@published=order;true;end
end
# Preservation sessions use block observers and distinct Struct visits.
Visit=Struct.new(:id,:file,:handle,:window)
module Cancellation
 def cancel
  return if @aborted
  @aborted=true;@stop.call;@env.call('cancel',@file['token'],@number)
 end
end
class Attempt
 include Cancellation
 attr_reader :file,:number,:aborted
 def initialize(env,file,number,active=-> {1},audit=->(f){},view=->(f,o){})
  @env,@file,@number,@aborted=env,file,number,false;@stop=->{};env.call('transport',file['token'],number)
  if file['feed']
   callback=env.bind(->(packet){
    next if @aborted;order=active.call;next if order.nil?
    deliver=->(frame){ audit.call(frame);view.call(frame,order)}
    value=env.call('decode',file['token'],packet,env.bind(deliver));deliver.call(value['frame']) unless value['deferred']
   })
   subscription=env.call('listen',file['token'],callback);env.call('start',file['token'])
   @stop=-> {env.call('unlisten',file['token'],subscription)};@stop.call if @aborted
  end
 end
end
class Session
 def initialize(env);@env=env;@visit=nil;@serial=0;@attempts=0;@tasks={};@disposed=false;end
 def current(v);@visit.equal?(v);end
 def enqueue(v,kind)
  @attempts+=1;n=@attempts;entry={fileId:v.file['id'],attemptId:n,visitId:v.id,kind:kind};;@env.call('record',entry)
  window=v.window;h=Attempt.new(@env,v.file,n,->{current(v) ? window.arrive : nil},->(frame){@env.call('recordProgress',{fileId:v.file['id'],attemptId:n,frame:frame})},->(frame,order){@env.call('showProgress',{fileId:v.file['id'],attemptId:n,frame:frame}) if current(v)});@tasks[n]=h;h
 end
 def notice(v,h);;@env.call('showQueued',{fileId:v.file['id'],attemptId:h.number,visitId:v.id,status:'queued'});end
 def release(v);h=v.handle;v.handle=nil;h.cancel if h;end
 def select(file)
  return nil if @disposed
  @serial+=1;request=@serial;old=@visit;@visit=nil;release(old) if old
  return nil if @disposed||@serial!=request
  v=Visit.new(request,file,nil,PublicationWindow.new);@visit=v;h=enqueue(v,'select');if current(v);v.handle=h;notice(v,h);else;h.cancel;end;h
 end
 def retry
  v=@visit;return nil if !v||!v.handle||@disposed
  v.handle.cancel
  accepted=v;h=enqueue(accepted,'retry');if current(accepted);accepted.handle=h;else;h.cancel;end;notice(accepted,h) if current(accepted);h
 end
 def hide;@serial+=1;old=@visit;@visit=nil;release(old) if old;end
 def dispose;return if @disposed;@disposed=true;hide;@tasks.each_value(&:cancel);end
 def snapshot;v=@visit;{visitId:v ? v.id : nil,fileId:v ? v.file['id'] : nil,attemptId:v&&v.handle ? v.handle.number : nil,disposed:@disposed,attempts:@attempts};end
end

class Telemetry
 attr_reader :stop
 def initialize(env,file)
  callback=env.bind(->(packet){deliver=->(frame){env.call('recordDelta',frame)};value=env.call('decode',file['token'],packet,env.bind(deliver));deliver.call(value['frame']) unless value['deferred']})
  env.call('start',file['token']);subscription=env.call('listen',file['token'],callback)
  @stop=->{env.call('unlisten',file['token'],subscription)}
 end
end
