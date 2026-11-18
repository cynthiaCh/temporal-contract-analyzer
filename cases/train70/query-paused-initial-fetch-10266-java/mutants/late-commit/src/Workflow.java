import java.util.*;import java.util.function.*;
class Workflow {
 interface Environment{int bind(Function<Object,Object> fn);Object call(String name,Object...args);}
 interface Client{Object handle(String name,List<?> args);}
 static Map<String,Object> obj(Object...values){Map<String,Object> m=new LinkedHashMap<>();for(int i=0;i<values.length;i+=2)m.put((String)values[i],values[i+1]);return m;}
 static int number(Object x){return ((Number)x).intValue();}
 static class Attempt{int number,failures;Map<String,Object> previous,options;boolean settled,consumed,retryCancelled,queued;Attempt(int n,Map<String,Object>s,Map<String,Object>o){number=n;previous=new LinkedHashMap<>(s);options=o;}}
 static class Query{String key;Map<String,Object> state;Set<Integer> observers=new HashSet<>();Attempt attempt;boolean consumed;Query(String key,Object data){this.key=key;state=obj("status",data==null?"pending":"success","fetchStatus","idle","data",data);}}
 static class Cache implements Client {
  Environment env;Map<String,Query> queries=new LinkedHashMap<>();Map<Integer,Query> handles=new LinkedHashMap<>();boolean online,focused;int serial,fetchSerial;
  Cache(Environment e,Map<String,Object> initial){env=e;online=(Boolean)initial.getOrDefault("online",true);focused=(Boolean)initial.getOrDefault("focused",true);}
  boolean eligible(Attempt a){return focused&&(a.options.getOrDefault("networkMode","online").equals("always")||online);}
  boolean active(Query q,Attempt a){return q.attempt==a&&!a.settled;}
  void cancel(Query q,Attempt a){if(a.settled)return;a.settled=true;q.state=new LinkedHashMap<>(a.previous);q.state.put("fetchStatus","idle");env.call("abort",q.key,a.number);}
  @SuppressWarnings("unchecked")void invoke(Query q,Attempt a){a.queued=false;if(!active(q,a))return;q.state.put("fetchStatus","fetching");q.consumed=false;
   int getter=env.bind(x->{q.consumed=true;return null;});int done=env.bind(x->{Map<String,Object> v=(Map<String,Object>)x;if(Boolean.TRUE.equals(v.get("ok"))){a.settled=true;q.state.put("data",v.get("value"));q.state.put("status","success");q.state.put("fetchStatus","idle");}
    else if(!a.retryCancelled&&a.failures<number(a.options.getOrDefault("retry",0))){a.failures++;int token=env.bind(y->{if(!active(q,a))return null;if(a.retryCancelled){a.settled=true;q.state.put("status","error");q.state.put("fetchStatus","idle");return null;}if(eligible(a))invoke(q,a);else q.state.put("fetchStatus","paused");return null;});env.call("schedule",token,a.options.getOrDefault("retryDelay",10));}
    else{a.settled=true;q.state.put("status","error");q.state.put("fetchStatus","idle");}return null;});env.call("request",q.key,a.number,getter,done);
  }
  void resume(Query q){Attempt a=q.attempt;if(a!=null&&active(q,a)&&q.state.get("fetchStatus").equals("paused")&&eligible(a)&&!a.queued){a.queued=true;int token=env.bind(x->{a.queued=false;if(!active(q,a))return null;if(a.failures>0&&a.retryCancelled){a.settled=true;q.state.put("status","error");q.state.put("fetchStatus","idle");return null;}invoke(q,a);return null;});env.call("defer",token);}}
  int subscribe(String key,Map<String,Object> options){Query q=queries.computeIfAbsent(key,k->new Query(k,options.get("initialData")));int h=++serial;handles.put(h,q);q.observers.add(h);if(q.attempt!=null&&!q.attempt.settled){q.attempt.retryCancelled=false;resume(q);}else{Attempt a=new Attempt(++fetchSerial,q.state,options);q.attempt=a;env.call("newAttempt",key,a.number);if(!options.getOrDefault("networkMode","online").equals("online")||online)invoke(q,a);else q.state.put("fetchStatus","paused");}return h;}
  void unsubscribe(int h){Query q=handles.remove(h);if(q==null)return;q.observers.remove(h);if(q.observers.isEmpty()){Attempt a=q.attempt;if(a!=null&&!a.settled){if(q.consumed||(q.state.get("fetchStatus").equals("paused")&&q.state.get("status").equals("pending")))cancel(q,a);else a.retryCancelled=true;}}}
  @SuppressWarnings("unchecked")public Object handle(String name,List<?> a){switch(name){case "subscribe":return subscribe((String)a.get(0),(Map<String,Object>)a.get(1));case "unsubscribe":unsubscribe(number(a.get(0)));return null;case "snapshot":return new LinkedHashMap<>(queries.get((String)a.get(0)).state);case "dispose":for(int h:new ArrayList<>(handles.keySet()))unsubscribe(h);return null;case "online":online=(Boolean)a.get(0);break;case "focus":focused=(Boolean)a.get(0);break;default:throw new IllegalArgumentException(name);}for(Query q:new ArrayList<>(queries.values()))resume(q);return null;}
 }
 @SuppressWarnings("unchecked")static Client create(Environment e,Object initial){return new Cache(e,(Map<String,Object>)initial);}
}
