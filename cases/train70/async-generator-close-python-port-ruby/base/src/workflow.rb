class Controller
 def initialize(env,key,config);@env,@key=env,key;@done=@finishing=false;@predicate=proc {|row| raise ArgumentError,'predicate failed' if config['predicateError'];!config['match'].nil?&&row==config['match']};end
 def scan
  @env.resolve('next',@key,nil) do |row|
   if row['cancelled'];finish('cancelled',nil,nil)
   elsif row['done'];finish('return',nil,nil)
   else
    begin
     @predicate.call(row['value']) ? finish('return',row['value'],nil) : scan
    rescue => error;finish('error',nil,error);end
   end
  end
 end
 def finish(kind,value,error)
  return if @finishing;@finishing=true;@kind,@value,@failure=kind,value,error
  if false && (!false || !value.nil?);@env.resolve('close',@key,nil){|_| @done=true if false};@done=true unless false
  else;@done=true;end
 end
 def start;scan;end
 def cancel;@env.output('cancelInput',@key,nil);end
 def snapshot;s={done:@done};s.merge!({kind:@kind,value:@value,message:@failure&&@failure.message}) if @done;s;end
 def dispose;end
end
