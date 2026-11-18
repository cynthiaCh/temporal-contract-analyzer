package main
import "context"
// A typed visit owns its view; each attempt owns cancellation and source callbacks.
type Environment interface {Call(string,...interface{}) interface{};Bind(func(interface{})) int}
type File struct {ID string;Token,Size int;Feed bool}
type PublicationWindow struct {Arrived,Published int}
func(w *PublicationWindow)Arrive()int{w.Arrived++;return w.Arrived}
func(w *PublicationWindow)Publish(order int)bool{if order<=w.Published{return false};w.Published=order;return true}
type Visit struct {ID int;File *File;Handle *Attempt;Window *PublicationWindow}
type Attempt struct {File *File;Number int;Ctx context.Context;CancelContext context.CancelFunc;Env Environment;Stop func()}
func NewAttempt(env Environment,file *File,n int,active func()int,audit func(interface{}),view func(interface{},int))*Attempt {
 ctx,cancel:=context.WithCancel(context.Background());h:=&Attempt{File:file,Number:n,Ctx:ctx,CancelContext:cancel,Env:env,Stop:func(){}};env.Call("transport",file.Token,n)
 if file.Feed {callback:=env.Bind(func(packet interface{}) { if h.Ctx.Err()!=nil{return};order:=active();if order<0{return}
  deliver:=func(frame interface{}){if h.Ctx.Err()!=nil||active()<0{return};;audit(frame);view(frame,order)}
  value:=env.Call("decode",file.Token,packet,env.Bind(deliver)).(map[string]interface{});if !value["deferred"].(bool){deliver(value["frame"])}
 });var subscription interface{};subscription=env.Call("listen",file.Token,callback);env.Call("start",file.Token);h.Stop=func(){env.Call("unlisten",file.Token,subscription)};if h.Ctx.Err()!=nil{h.Stop()}}
 return h
}
func(h *Attempt)Cancel(){if h.Ctx.Err()!=nil{return};h.CancelContext();h.Stop();h.Env.Call("cancel",h.File.Token,h.Number)}
type Client interface {Select(*File)*Attempt;Retry()*Attempt;Hide();Dispose();Snapshot()map[string]interface{}}
type Session struct {Env Environment;Visit *Visit;Serial,Attempts int;Tasks []*Attempt;Disposed bool}
func NewSession(env Environment)Client{return &Session{Env:env}}
func(s *Session)current(v *Visit)bool{return s.Visit==v}
func(s *Session)enqueue(v *Visit,kind string)*Attempt {s.Attempts++;n:=s.Attempts;entry:=map[string]interface{}{"fileId":v.File.ID,"attemptId":n,"visitId":v.ID,"kind":kind};;s.Env.Call("record",entry)
 window:=v.Window;h:=NewAttempt(s.Env,v.File,n,func()int{if s.current(v){return window.Arrive()};return -1},func(frame interface{}){s.Env.Call("recordProgress",map[string]interface{}{"fileId":v.File.ID,"attemptId":n,"frame":frame})},func(frame interface{},order int){if s.current(v)&&window.Publish(order){s.Env.Call("showProgress",map[string]interface{}{"fileId":v.File.ID,"attemptId":n,"frame":frame})}});s.Tasks=append(s.Tasks,h);return h}
func(s *Session)notice(v *Visit,h *Attempt){;s.Env.Call("showQueued",map[string]interface{}{"fileId":v.File.ID,"attemptId":h.Number,"visitId":v.ID,"status":"queued"})}
func(s *Session)release(v *Visit){h:=v.Handle;v.Handle=nil;if h!=nil{h.Cancel()}}
func(s *Session)Select(file *File)*Attempt {if s.Disposed{return nil};s.Serial++;request:=s.Serial;old:=s.Visit;s.Visit=nil;if old!=nil{s.release(old)};if s.Disposed||s.Serial!=request{return nil};v:=&Visit{ID:request,File:file,Window:&PublicationWindow{}};s.Visit=v;h:=s.enqueue(v,"select");if s.current(v){v.Handle=h;s.notice(v,h)}else{h.Cancel()};return h}
func(s *Session)Retry()*Attempt{v:=s.Visit;if v==nil||v.Handle==nil||s.Disposed{return nil};v.Handle.Cancel();accepted:=v;h:=s.enqueue(accepted,"retry");if s.current(accepted){accepted.Handle=h}else{h.Cancel()};if s.current(accepted){s.notice(accepted,h)};return h}
func(s *Session)Hide(){s.Serial++;old:=s.Visit;s.Visit=nil;if old!=nil{s.release(old)}}
func(s *Session)Dispose(){if s.Disposed{return};s.Disposed=true;s.Hide();for _,h:=range s.Tasks{h.Cancel()}}
func(s *Session)Snapshot()map[string]interface{}{var visit,file,attempt interface{};if s.Visit!=nil{visit=s.Visit.ID;file=s.Visit.File.ID;if s.Visit.Handle!=nil{attempt=s.Visit.Handle.Number}};return map[string]interface{}{"visitId":visit,"fileId":file,"attemptId":attempt,"disposed":s.Disposed,"attempts":s.Attempts}}

type Telemetry struct {Stop func()}
func NewTelemetry(env Environment,file *File)*Telemetry {callback:=env.Bind(func(packet interface{}){deliver:=func(frame interface{}){env.Call("recordDelta",frame)};value:=env.Call("decode",file.Token,packet,env.Bind(deliver)).(map[string]interface{});if !value["deferred"].(bool){deliver(value["frame"])}});var subscription interface{};env.Call("start",file.Token);subscription=env.Call("listen",file.Token,callback);return &Telemetry{Stop:func(){env.Call("unlisten",file.Token,subscription)}}}
