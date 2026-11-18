import java.io.*;import java.util.*;import java.util.function.*;import javax.script.*;
public class Driver {
 static final BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
 static final ScriptEngine json=new ScriptEngineManager().getEngineByName("nashorn");
 static final Map<Integer,Function<Object,Object>> callbacks=new HashMap<>();static final Map<Integer,Workflow.Client> sessions=new HashMap<>();static int serial;
 static int num(Object x){return ((Number)x).intValue();}
 static class Env implements Workflow.Environment {int w;Env(int w){this.w=w;}public int bind(Function<Object,Object> fn){callbacks.put(++serial,fn);return serial;}public Object call(String name,Object...args){List<Object> all=new ArrayList<>();all.add(w);all.addAll(Arrays.asList(args));send(Workflow.obj("call",name,"args",all));for(;;){Map<String,Object> m=read();if(m.containsKey("reply"))return m.get("reply");answer(m);}}}
 static String encode(Object v){if(v==null)return "null";if(v instanceof String){StringBuilder s=new StringBuilder("\"");for(char c:((String)v).toCharArray()){if(c=='"'||c=='\\')s.append('\\').append(c);else if(c<32)s.append(String.format("\\u%04x",(int)c));else s.append(c);}return s.append('"').toString();}if(v instanceof Number||v instanceof Boolean)return v.toString();if(v instanceof Map){List<String> items=new ArrayList<>();for(Object item:((Map<?,?>)v).entrySet()){Map.Entry<?,?> e=(Map.Entry<?,?>)item;items.add(encode(e.getKey().toString())+":"+encode(e.getValue()));}return "{"+String.join(",",items)+"}";}if(v instanceof Collection){List<String> items=new ArrayList<>();for(Object item:(Collection<?>)v)items.add(encode(item));return "["+String.join(",",items)+"]";}throw new IllegalArgumentException("non-JSON value");}
 static void send(Object v){System.out.println(encode(v));System.out.flush();}
 @SuppressWarnings("unchecked") static Map<String,Object> read(){try{String line=input.readLine();if(line==null)throw new EOFException();json.put("wire",line);return (Map<String,Object>)json.eval("Java.asJSONCompatible(JSON.parse(wire))");}catch(Exception e){throw new RuntimeException(e);}}
 static Object dispatch(Map<String,Object> m){String name=(String)m.get("method");List<?> a=(List<?>)m.get("args");if(name.equals("invoke"))return callbacks.get(num(a.get(0))).apply(a.get(1));int w=num(a.get(0));if(name.equals("init")){sessions.put(w,Workflow.create(new Env(w),a.get(1)));return null;}return sessions.get(w).handle(name,a.subList(1,a.size()));}
 static void answer(Map<String,Object> m){send(Workflow.obj("result",dispatch(m)));}
 public static void main(String[]args){try{for(;;)answer(read());}catch(RuntimeException e){if(!(e.getCause() instanceof EOFException))throw e;}}
}
