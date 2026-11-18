import java.util.*;
import java.util.function.Consumer;

/** Compliance dossier sessions have typed lifetime and value objects. */
public final class Workflow {
    interface Environment {
        Store store();
        Object schedule(Runnable callback, int delay);
        void cancel(Object handle);
        void output(String kind, Object value);
        void write(String id, String text);
        Map<String,Object> capture(Map<String,Object> value);
    }
    static Map<String,Object> value(String id, String text) {
        Map<String,Object> result=new LinkedHashMap<>(); result.put("id",id); result.put("text",text); return result;
    }
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
    static final class Receipt {
        final String id, text;
        Receipt(Map<String,Object> snapshot) { id=(String)snapshot.get("id"); text=(String)snapshot.get("text"); }
        Map<String,Object> copy() { return value(id,text); }
    }
    static final class Archive {
        final List<Receipt> receipts=new ArrayList<>();final Map<Integer,Consumer<Map<String,Object>>> listeners=new LinkedHashMap<>();int serial;
        int subscribe(Consumer<Map<String,Object>>fn){int token=++serial;listeners.put(token,fn);return token;}
        void stop(int token){listeners.remove(token);}
        Map<String,Object> capture(Map<String,Object> snapshot) { Receipt receipt=new Receipt(snapshot); receipts.add(receipt); Map<String,Object> event=Collections.unmodifiableMap(receipt.copy());for(int token:new ArrayList<>(listeners.keySet())){Consumer<Map<String,Object>>fn=listeners.get(token);if(fn!=null)fn.accept(event);}return event; }
        List<Map<String,Object>> list() { List<Map<String,Object>> result=new ArrayList<>(); for(Receipt receipt:receipts) result.add(receipt.copy()); return result; }
    }
    static final class Trailing {
        final Environment env; final int delay; final Consumer<String> work;
        Object handle; String pending;
        Trailing(Environment env,int delay,Consumer<String> work) { this.env=env;this.delay=delay;this.work=work; }
        void push(String text) { if(handle!=null)env.cancel(handle); pending=text; handle=env.schedule(this::flush,delay); }
        void flush() { if(handle!=null)env.cancel(handle); String text=pending; handle=null;pending=null; if(text!=null)work.accept(text); }
        void cancel() { if(handle!=null)env.cancel(handle);handle=null;pending=null; }
    }
    static final class Session {
        final String id; String text; final int token; final Trailing task;
        Session(String id,String text,int token,Trailing task) { this.id=id;this.text=text;this.token=token;this.task=task; }
    }
    static final class Confirmation {
        final java.util.function.Supplier<Session> current;final Consumer<Map<String,Object>> emit;final Session owner;
        Confirmation(java.util.function.Supplier<Session> current,Consumer<Map<String,Object>> emit){this.current=current;this.emit=emit;owner=current.get();}
        boolean active(){return owner!=null&&current.get()!=null&&owner.id.equals(current.get().id);}
        void show(Map<String,Object> receipt){if(active())emit.accept(receipt);}
    }
    static final class Workspace {
        final Environment env; Session current; long navigation;
        Workspace(Environment env) { this.env=env; }
        void retire() {
            Session leaving=current; current=null;
            if(leaving!=null)env.store().stop(leaving.token);
            env.output("document",null);
            if(leaving!=null)leaving.task.flush();
        }
        void open(String id) {
            env.output("notice",null);long request=++navigation;retire();
            if(request!=navigation)return;
            int token=env.store().subscribe(event->{if(id.equals(event.get("id")))env.output("status",event);});
            Trailing task=new Trailing(env,120,text->env.write(id,text));
            current=new Session(id,env.store().read(id),token,task);
            env.output("document",value(id,current.text));
        }
        void edit(String text) { if(current==null)return; current.text=text; current.task.push(text); }
        void close() { env.output("notice",null);++navigation;retire(); }
        Map<String,Object> submit() {
            Confirmation confirmation=new Confirmation(()->current,receipt->env.output("notice",receipt));
            Session visit=current;if(visit==null)return null;
            Map<String,Object> snapshot=value(visit.id,visit.text);
            visit.task.flush();
            
            
            
            Map<String,Object> receipt=env.capture(snapshot);
            
            confirmation.show(receipt);
            return receipt;
        }
        void dispose() { close(); }
    }
    static final class Preview {
        final Trailing task;
        Preview(Environment env) { task=new Trailing(env,40,query->{Map<String,Object> value=new LinkedHashMap<>();value.put("query",query);env.output("preview",value);}); }
        void query(String text) { task.push(text); }
        void hide() { task.cancel(); }
    }
}
