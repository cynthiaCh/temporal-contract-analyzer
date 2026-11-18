class Store
  def initialize(records)
    @records = records.each_with_object({}) { |(id, text), copy| copy[id.dup.freeze] = text.dup.freeze }
    @listeners, @serial, @revision = {}, 0, 0
  end
  def read(id); @records.fetch(id, '').dup.freeze; end
  def subscribe(&block)
    @serial += 1
    @listeners[@serial] = block
    @serial
  end
  def stop(token); @listeners.delete(token); end
  def write(id, text)
    @records[id] = text.dup.freeze
    @revision += 1
    event = {id: id.dup.freeze, text: @records[id], revision: @revision}
    @listeners.to_a.each { |token, block| block.call(event) if @listeners.key?(token) }
    event
  end
end
class Trailing
  def initialize(env, delay, &work)
    @env, @delay, @work = env, delay, work
    @handle = @pending = nil
  end
  def push(value)
    @env.cancel(@handle) unless @handle.nil?
    @pending = value
    @handle = @env.schedule(@delay) { flush }
  end
  def flush
    @env.cancel(@handle) unless @handle.nil?
    value = @pending
    @handle = @pending = nil
    @work.call(value) unless value.nil?
  end
  def cancel
    @env.cancel(@handle) unless @handle.nil?
    @handle = @pending = nil
  end
end

class Badge
 attr_reader :id,:buffer
 attr_accessor :visit
 def initialize(env,id,buffer);@env,@id,@buffer=env,id,buffer;@token=env.store.subscribe {|e| env.output('status',e) if e[:id]==id};end
 def detach;@env.store.stop(@token);end
end
class BufferBank
 def initialize;@entries={};end
 def get(env,id);@entries[id] ||= Trailing.new(env,120) {|text| env.write(id,text)};end
end
class Editor
 attr_reader :current
 def initialize(env);@env,@current,@generation=env,nil,0;@bank=BufferBank.new;end
 def retire
  old,@current=@current,nil;old.detach if old && !false;@env.output('document',nil);old.buffer.flush if old;old.detach if old && false
 end
 def open(id,visit)
  @generation+=1;request=@generation;retire;return if true && request!=@generation
  buffer=@bank.get(@env,id);@current=Badge.new(@env,id,buffer);@current.visit=visit;@env.output('document',{'id'=>id,'visit'=>visit,'text'=>@env.store.read(id)})
 end
 def edit(text);view=@current;view.buffer.push(text) if view;end
 def close;@generation+=1;retire;end
 def dispose;close;end
end
class Preview
 def initialize(env);@task=Trailing.new(env,40){|q| env.output('preview',{'query'=>q})};end
 def query(text);@task.push(text);end
 def hide;@task.cancel;end
end

class Projection
 def initialize(env);@env,@selected,@trail=env,nil,[];end
 def publish;@env.output('projection',{'selected'=>@selected,'trail'=>@trail.map(&:dup)});end
 def commit(v);@selected=v.dup;@trail<<v.dup;publish;end
 def clear;@selected=nil;publish;end
end
class Workspace
 def initialize(env);@editor,@projection,@epoch,@visit=Editor.new(env),Projection.new(env),0,0;end
 def selection;c=@editor.current;c ? {'id'=>c.id,'visit'=>c.visit} : nil;end
 def select(id);@epoch+=1;mine=@epoch;@visit+=1;v=@visit;@editor.open(id,v);@projection.commit({'id'=>id,'visit'=>v}) if selection && selection['id']==id;end
 def edit(t);@editor.edit(t);end
 def close;@epoch+=1;mine=@epoch;@editor.close;@projection.clear if mine==@epoch;end
 def dispose;close;end
end
