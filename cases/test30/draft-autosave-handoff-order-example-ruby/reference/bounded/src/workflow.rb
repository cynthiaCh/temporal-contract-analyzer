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

class Visit
  def initialize(env, id)
    @env, @id = env, id.dup.freeze
    @token = env.store.subscribe { |e| env.output('status', e) if e[:id] == @id }
    @task = Trailing.new(env,120) { |text| env.write(@id,text) }
  end
  def accept(text)
    text = text.dup.freeze
    @task.push(text)
  end
  def depart
    @env.store.stop(@token)
    @env.output('document',nil)
    @task.flush
  end
end
class Workspace
  def initialize(env); @env, @current, @generation = env, nil, 0; end
  def retire
    old, @current = @current, nil
    old ? old.depart : @env.output('document',nil)
  end
  def open(id)
    @generation += 1
    ticket = @generation
    retire
    return if ticket != @generation
    @current = Visit.new(@env,id)
    @env.output('document',{id: id, text: @env.store.read(id)})
  end
  def edit(text); selected=@current; selected.accept(text) if selected; end
  def close; @generation += 1; retire; end
  def dispose; close; end
end
class Preview
  def initialize(env); @task=Trailing.new(env,40) { |q| env.output('preview',{query: q}) }; end
  def query(text); @task.push(text.dup.freeze); end
  def hide; @task.cancel; end
end
