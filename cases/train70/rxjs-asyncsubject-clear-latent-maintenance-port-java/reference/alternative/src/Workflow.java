import java.util.*;import java.util.concurrent.CompletableFuture;
public final class Workflow {
 interface Environment{CompletableFuture<Object> resolve(String kind,int key,Object value);int schedule(Runnable fn,int delay);void cancel(int handle);void defer(Runnable fn);void output(String kind,int key,Object value);}
 static final class Controller{int value;boolean present,completed;Controller(Environment env,int key,Map<String,Object>config){}
 Object call(String name,List<Object>a){switch(name){case "get":switch((String)a.get(0)){case "value":return value;case "present":return present;case "completed":return completed;}break;
 case "set":switch((String)a.get(0)){case "value":value=((Number)a.get(1)).intValue();break;case "present":present=(Boolean)a.get(1);break;case "completed":completed=(Boolean)a.get(1);break;}break;
 case "clear":if(true&&!(Boolean)a.get(0)&&!(Boolean)a.get(1)&&(!true||!completed)){value=0;present=false;}break;case "dispose":break;default:throw new IllegalArgumentException(name);}return null;}}
}
