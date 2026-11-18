import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import javax.script.*;
public final class Driver implements Workflow.Host {
    final BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
    final ScriptEngine json=new ScriptEngineManager().getEngineByName("nashorn");
    final List<String> tokens=new ArrayList<>();
    final List<CompletableFuture<Boolean>> futures=new ArrayList<>();
    final Map<Integer,Runnable> timers=new LinkedHashMap<>();
    final ArrayDeque<Runnable> queue=new ArrayDeque<>();
    int serial,published;Workflow.Client resource;
    static String encode(Object value) {
        if(value==null)return "null";
        if(value instanceof String) {
            StringBuilder result=new StringBuilder("\"");
            for(char ch:((String)value).toCharArray()) {
                if(ch=='"'||ch=='\\')result.append('\\').append(ch);
                else if(ch<32)result.append(String.format("\\u%04x",(int)ch));
                else result.append(ch);
            }
            return result.append('"').toString();
        }
        if(value instanceof Number || value instanceof Boolean)return value.toString();
        if(value instanceof Map) { List<String> parts=new ArrayList<>();((Map<?,?>)value).forEach((k,v)->parts.add(encode(k.toString())+":"+encode(v)));return "{"+String.join(",",parts)+"}"; }
        if(value instanceof Iterable) { List<String> parts=new ArrayList<>();for(Object v:(Iterable<?>)value)parts.add(encode(v));return "["+String.join(",",parts)+"]"; }
        throw new IllegalArgumentException("wire type "+value.getClass());
    }
    Map<String,Object> read() {
        try { String line=input.readLine();if(line==null)return null;json.put("wire",line);return (Map<String,Object>)json.eval("Java.asJSONCompatible(JSON.parse(wire))"); }
        catch(Exception error) { throw new RuntimeException(error); }
    }
    void emit(String key,Object value) { Map<String,Object> message=new LinkedHashMap<>();message.put(key,value);System.out.println(encode(message));System.out.flush(); }

    public CompletableFuture<Boolean> check(String token){tokens.add(token);CompletableFuture<Boolean> f=new CompletableFuture<>();futures.add(f);return f;}
    public Executor executor(){return queue::add;}
    public int schedule(Runnable callback){timers.put(++serial,callback);return serial;}
    public void cancel(int handle){timers.remove(handle);}
    public void publish(Map<String,Object> state){published++;}
    Object dispatch(Map<String,Object> m){
      List<Object> a=(List<Object>)m.get("args");Object result=null;
      switch((String)m.get("method")){
      case "init":resource=Workflow.create(this,(String)a.get(0),(String)a.get(1));break;
      case "start":resource.start();break;
      case "close":resource.close();break;
      case "reopen":resource.reopen((String)a.get(0));break;
      case "unmount":resource.dispose();break;
      case "resolve":futures.get(((Number)a.get(0)).intValue()).complete((Boolean)a.get(1));break;
      case "drain":while(!queue.isEmpty())queue.remove().run();break;
      case "fire":result=false;if(!timers.isEmpty()){int key=timers.keySet().iterator().next();timers.remove(key).run();result=true;}break;
      case "snapshot":result=resource.snapshot();break;
      case "inspect":Map<String,Object> out=new LinkedHashMap<>();out.put("state",resource.snapshot());out.put("requests",tokens);out.put("timers",timers.size());out.put("published",published);result=out;break;
      default:throw new IllegalArgumentException("unknown command");
      }return result;
    }
    public static void main(String[]args){Driver driver=new Driver();Map<String,Object> m;while((m=driver.read())!=null)driver.emit("result",driver.dispatch(m));}
}
