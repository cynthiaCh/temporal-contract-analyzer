import java.util.*;
import java.util.concurrent.*;
public final class Workflow {
    public interface Host {
        CompletableFuture<Boolean> check(String token);
        Executor executor();
        int schedule(Runnable callback);
        void cancel(int handle);
        void publish(Map<String,Object> state);
    }
    public interface Client {
        public void start(); void close(); void reopen(String token); void dispose(); Map<String,Object> snapshot();
    }
    static abstract class Resource implements Client {
        final Host host;int generation;Integer timer;boolean disposed;
        boolean visible=true,loading,retryScheduled;int checkCount;
        String token;final List<String> completed=new ArrayList<>();
        Resource(Host host,String token){this.host=host;this.token=token;}
        public Map<String,Object> snapshot(){Map<String,Object> s=new LinkedHashMap<>();s.put("visible",visible);s.put("loading",loading);s.put("retryScheduled",retryScheduled);s.put("checkCount",checkCount);s.put("completed",new ArrayList<>(completed));s.put("token",token);return s;}
        void publish(){if(!disposed)host.publish(snapshot());}
        void cancelRetry(){if(timer!=null)host.cancel(timer);timer=null;retryScheduled=false;}
        void invalidate(){generation++;cancelRetry(); loading=false;}
        public void start(){invalidate();visible=true;check(generation);}
        public void reopen(String next){invalidate();token=next;visible=true;check(generation);}
        void check(int requestGeneration){
            String requestToken=token;loading=true;checkCount++;publish();
            host.check(requestToken).thenAcceptAsync(ready->{
                if(disposed||!requestToken.equals(token))return;
                if(ready){cancelRetry();loading=false;if(!completed.contains(requestToken))completed.add(requestToken); publish();}
                else pending(requestGeneration);
            },host.executor());
        }
        void schedule(int requestGeneration){
            retryScheduled=true;
            timer=host.schedule(()->{if(disposed||requestGeneration!=generation)return;timer=null;retryScheduled=false;check(requestGeneration);});publish();
        }
        abstract void pending(int requestGeneration);
        public abstract void close();
        public void dispose(){disposed=true;generation++;cancelRetry();}
    }
    static final class DialogResource extends Resource {
        DialogResource(Host host,String token){super(host,token);}
        void pending(int requestGeneration){schedule(requestGeneration);}
        public void close(){visible=false;invalidate();publish();}
    }
    static final class WorkspaceJob extends Resource {
    public void start(){check(generation);}
        WorkspaceJob(Host host,String token){super(host,token);}
        void pending(int requestGeneration){schedule(requestGeneration);}
        public void close(){visible=false; publish();}
    }
    public static Client create(Host host,String surface,String token){return surface.equals("download")?new DialogResource(host,token):new WorkspaceJob(host,token);}
}
