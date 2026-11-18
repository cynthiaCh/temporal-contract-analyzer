import java.io.*;
import java.util.*;
import javax.script.*;

// Nashorn is used only for trusted wire JSON parsing, never application code.
public final class Driver implements Workflow.Environment {
    final BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
    final ScriptEngine json=new ScriptEngineManager().getEngineByName("nashorn");
    Workflow.Store store;
    final Workflow.Archive archive=new Workflow.Archive();
    final Map<Integer,Runnable> callbacks=new HashMap<>(); int serial;
    Workflow.Workspace workspace; Workflow.Preview preview;
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
    public Workflow.Store store() { return store; }
    public Object schedule(Runnable callback,int delay) { int id=++serial;callbacks.put(id,callback);return call("schedule",id,delay); }
    public void cancel(Object handle) { call("cancel",handle); }
    public void output(String kind,Object value) { call(kind,value); }
    public void write(String id,String text) { call("write",id,text); }
    public Map<String,Object> capture(Map<String,Object> value) { return (Map<String,Object>)call("capture",value); }
    void dispatch(Map<String,Object> message) {
        String method=(String)message.get("method");List<Object> a=(List<Object>)message.get("args");Object result=null;
        switch(method) {
            case "storeInit":store=new Workflow.Store((Map<String,Object>)a.get(0));break;
            case "storeRead":result=store.read((String)a.get(0));break;
            case "storeWrite":result=store.write((String)a.get(0),(String)a.get(1));break;
            case "storeSubscribe":result=store.subscribe(event->call("subscriber",a.get(0),event));break;
            case "storeUnsubscribe":store.stop(((Number)a.get(0)).intValue());break;
            case "archiveCapture":result=archive.capture((Map<String,Object>)a.get(0));break;
            case "archiveSubscribe":result=archive.subscribe(event->call("subscriber",a.get(0),event));break;
            case "archiveUnsubscribe":archive.stop(((Number)a.get(0)).intValue());break;
            case "archiveList":result=archive.list();break;
            case "init":workspace=new Workflow.Workspace(this);break;
            case "previewInit":preview=new Workflow.Preview(this);break;
            case "previewQuery":preview.query((String)a.get(0));break;
            case "previewHide":preview.hide();break;
            case "invoke":callbacks.remove(((Number)a.get(0)).intValue()).run();break;
            case "open":workspace.open((String)a.get(0));break;
            case "edit":workspace.edit((String)a.get(0));break;
            case "close":workspace.close();break;
            case "submit":result=workspace.submit();break;
            case "dispose":workspace.dispose();break;
            default:throw new IllegalArgumentException(method);
        }
        emit("result",result);
    }
    public static void main(String[] args) { Driver env=new Driver();Map<String,Object> message;while((message=env.read())!=null)env.dispatch(message); }
}
