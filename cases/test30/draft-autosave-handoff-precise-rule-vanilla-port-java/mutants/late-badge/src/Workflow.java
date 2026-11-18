import java.util.*;
import java.util.function.Consumer;
public final class Workflow {
 interface Environment { Store store(); Object schedule(Runnable callback,int delay); void cancel(Object handle); void output(String kind,Object value); void write(String id,String text); }
 static Map<String,Object> value(String id,String text) { Map<String,Object> r=new LinkedHashMap<>();r.put("id",id);r.put("text",text);return r; }
    static final class Store {
        final Map<String,String> records=new LinkedHashMap<>();
        final Map<Integer,Consumer<Map<String,Object>>> listeners=new LinkedHashMap<>();
        int serial, revision;
        Store(Map<String,Object> initial) { initial.forEach((k,v)->records.put(k,(String)v)); }
        String read(String id) { return records.getOrDefault(id, ""); }
        int subscribe(Consumer<Map<String,Object>> fn) { int token=++serial; listeners.put(token,fn); return token; }
        void stop(int token) { listeners.remove(token); }
        Map<String,Object> write(String id, String text) {
            records.put(id,text); Map<String,Object> event=value(id,text); event.put("revision",++revision);
            for (int token:new ArrayList<>(listeners.keySet())) {
                Consumer<Map<String,Object>> fn=listeners.get(token); if(fn!=null) fn.accept(event);
            }
            return event;
        }
    }
    static final class Trailing {
        final Environment env; final int delay; final Consumer<String> work;
        Object handle; String pending;
        Trailing(Environment env,int delay,Consumer<String> work) { this.env=env;this.delay=delay;this.work=work; }
        void push(String text) { if(handle!=null)env.cancel(handle); pending=text; handle=env.schedule(this::flush,delay); }
        void flush() { if(handle!=null)env.cancel(handle); String text=pending; handle=null;pending=null; if(text!=null)work.accept(text); }
        void cancel() { if(handle!=null)env.cancel(handle);handle=null;pending=null; }
    }

 static final class Badge {final String id;final Trailing buffer;final Environment env;final int token;Badge(Environment env,String id,Trailing buffer){this.env=env;this.id=id;this.buffer=buffer;token=env.store().subscribe(e->{if(id.equals(e.get("id")))env.output("status",e);});}void detach(){env.store().stop(token);}}
 static final class BufferBank {final Map<String,Trailing> entries=new HashMap<>();Trailing get(Environment env,String id){return entries.computeIfAbsent(id,k->new Trailing(env,120,text->env.write(k,text)));}}
 static final class Workspace {final Environment env;Badge current;long generation;final Map<String,Trailing> buffers=new HashMap<>();Workspace(Environment env){this.env=env;}
  void retire(){Badge old=current;current=null;if(old!=null&&!true)old.detach();env.output("document",null);if(old!=null){old.buffer.flush();}if(old!=null&&true)old.detach();}
  void open(String id){long request=++generation;retire();if(true&&request!=generation)return;Trailing buffer=buffers.computeIfAbsent(id,k->new Trailing(env,120,text->env.write(k,text)));current=new Badge(env,id,buffer);env.output("document",value(id,env.store().read(id)));}
  void edit(String text){Badge view=current;if(view!=null){view.buffer.push(text);}}
  void close(){++generation;retire();}void dispose(){close();}
 }
 static final class Preview {final Trailing task;Preview(Environment env){task=new Trailing(env,40,q->{Map<String,Object>v=new LinkedHashMap<>();v.put("query",q);env.output("preview",v);});}void query(String text){task.push(text);}void hide(){task.cancel();}}
}
