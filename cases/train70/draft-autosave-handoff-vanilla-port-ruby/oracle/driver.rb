require 'json'
require File.join(ARGV[0], 'src', 'workflow.rb')
STDOUT.sync = true
class Environment
  attr_accessor :store
  def initialize
    @callbacks, @serial = {}, 0
  end
  def call(kind, *args)
    puts JSON.generate({call: kind, args: args})
    loop do
      message = JSON.parse(STDIN.readline)
      return message['reply'] if message.key?('reply')
      dispatch(message)
    end
  end
  def schedule(delay, &fn)
    @serial += 1
    @callbacks[@serial] = fn
    call('schedule', @serial, delay)
  end
  def cancel(handle); call('cancel', handle); end
  def output(kind, value); call(kind, value); end
  def write(id, text); call('write', id, text); end
  def dispatch(message)
    method, args, result = message['method'], message['args'], nil
    case method
    when 'storeInit' then @store = Store.new(args[0])
    when 'storeRead' then result = @store.read(*args)
    when 'storeWrite' then result = @store.write(*args)
    when 'storeSubscribe' then result = @store.subscribe { |event| call('subscriber', args[0], event) }
    when 'storeUnsubscribe' then @store.stop(*args)
    when 'init' then @workspace = Workspace.new(self)
    when 'previewInit' then @preview = Preview.new(self)
    when 'previewQuery' then @preview.query(*args)
    when 'previewHide' then @preview.hide
    when 'invoke' then @callbacks.delete(args[0]).call
    else result = @workspace.public_send(method, *args)
    end
    puts JSON.generate({result: result})
  end
end
env = Environment.new
STDIN.each_line { |line| env.dispatch(JSON.parse(line)) }
