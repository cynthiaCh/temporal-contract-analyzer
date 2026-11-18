# A catalog editing visit carries the block that owns its eventual write.
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
class Archive
  def initialize; @receipts = [];@listeners={};@serial=0;end
  def capture(snapshot)
    receipt = {id: snapshot['id'].dup.freeze, text: snapshot['text'].dup.freeze}.freeze
    @receipts << receipt
    @listeners.to_a.each{|token,fn|fn.call(receipt) if @listeners.key?(token)}
    receipt
  end
  def subscribe(&fn);@serial+=1;@listeners[@serial]=fn;@serial;end
  def stop(token);@listeners.delete(token);end
  def list; @receipts.map(&:dup); end
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
class Confirmation
  def initialize(current,emit);@current,@emit=current,emit;@owner=current.call;end
  def active;!@owner.nil?&&@owner.equal?(@current.call);end
  def show(receipt);@emit.call(receipt);end
end
CatalogVisit = Struct.new(:id, :text, :token, :task)
class Workspace
  def initialize(env); @env, @current, @navigation = env, nil, 0; end
  def retire
    leaving = @current
    @current = nil
    @env.store.stop(leaving.token) if leaving
    @env.output('document', nil)
    leaving.task.flush if leaving
  end
  def open(id)
    id = id.dup.freeze
    @env.output('notice', nil)
    @navigation += 1
    request = @navigation
    retire
    return if request != @navigation
    token = @env.store.subscribe { |event| @env.output('status', event) if event[:id] == id }
    task = Trailing.new(@env, 120) { |text| @env.write(id, text) }
    @current = CatalogVisit.new(id, @env.store.read(id), token, task)
    @env.output('document', {id: id, text: @current.text})
  end
  def edit(text)
    return unless @current
    text = text.dup.freeze
    @current.text = text
    @current.task.push(text)
  end
  def close
    @env.output('notice', nil)
    @navigation += 1
    retire
  end
  def submit
    confirmation=Confirmation.new(proc{@current},proc{|receipt|@env.output('notice',receipt)})
    visit = @current
    return nil unless visit
    snapshot = {id: visit.id, text: visit.text}
    visit.task.flush
    
    
    
    receipt = @env.capture(snapshot)
    
    confirmation.show(receipt)
    receipt
  end
  def dispose; close; end
end
class Preview
  def initialize(env)
    @task = Trailing.new(env, 40) { |query| env.output('preview', {query: query}) }
  end
  def query(text); @task.push(text); end
  def hide; @task.cancel; end
end
