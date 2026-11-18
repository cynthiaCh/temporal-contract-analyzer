import java.io.*;
import java.util.*;
import javax.script.*;
import java.util.function.Consumer;
import java.util.concurrent.CompletableFuture;

// Nashorn is used only for trusted wire JSON parsing, never application code.
public final class Driver implements Workflow.Environment {
    final BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
    final ScriptEngine json=new ScriptEngineManager().getEngineByName("nashorn");
    final Map<Integer,Consumer<Object>> callbacks=new HashMap<>();int serial;
    final Map<Integer,Workflow.Controller> controllers=new HashMap<>();
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
    Object call(String kind,Object... args) {
        Map<String,Object> message=new LinkedHashMap<>();message.put("call",kind);message.put("args",Arrays.asList(args));System.out.println(encode(message));System.out.flush();
        for(;;) { Map<String,Object> next=read();if(next==null)throw new IllegalStateException("RPC EOF");if(next.containsKey("reply"))return next.get("reply");dispatch(next); }
    }
    int bind(Consumer<Object> fn){int id=++serial;callbacks.put(id,fn);return id;}
    public void defer(Runnable fn){call("defer",bind(value->fn.run()));}
    public CompletableFuture<Object> resolve(String kind,int key,Object frame){
      CompletableFuture<Object> result=new CompletableFuture<>();int id=bind(result::complete);
      Map<String,Object> reply=(Map<String,Object>)call(kind,key,frame,id);
      if(!Boolean.TRUE.equals(reply.get("deferred")))callbacks.remove(id).accept(reply.get("value"));
      return result;
    }
    public int schedule(Runnable fn,int delay){return integer(call("schedule",bind(value->fn.run()),delay));}
    public void cancel(int handle){call("cancel",handle);}
    public void output(String kind,int key,Object value){call(kind,key,value);}
    int integer(Object n){return ((Number)n).intValue();}
    void dispatch(Map<String,Object> message){String method=(String)message.get("method");List<Object>a=(List<Object>)message.get("args");Object result=null;
      switch(method){
      case "create":controllers.put(integer(a.get(0)),new Workflow.Controller(this,integer(a.get(0)),(Map<String,Object>)a.get(1)));break;
      case "call":result=controllers.get(integer(a.get(0))).call((String)a.get(1),(List<Object>)a.get(2));break;
      case "invoke":callbacks.remove(integer(a.get(0))).accept(a.get(1));break;
      default:throw new IllegalArgumentException(method);
      }emit("result",result);
    }
    public static void main(String[] args) { Driver env=new Driver();Map<String,Object> message;while((message=env.read())!=null)env.dispatch(message); }
}
