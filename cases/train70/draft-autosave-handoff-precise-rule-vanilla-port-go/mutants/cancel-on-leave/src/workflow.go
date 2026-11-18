package main
import "sort"
type Value map[string]interface{}
type Store struct { records map[string]string; listeners map[int]func(Value); serial, revision int }
func NewStore(initial Value) *Store {
    s:=&Store{records:map[string]string{},listeners:map[int]func(Value){}}
    for id,text:=range initial { s.records[id]=text.(string) };return s
}
func(s *Store) Read(id string) string { return s.records[id] }
func(s *Store) Subscribe(fn func(Value)) int { s.serial++;s.listeners[s.serial]=fn;return s.serial }
func(s *Store) Stop(token int) { delete(s.listeners,token) }
func(s *Store) Write(id,text string) Value {
    s.records[id]=text;s.revision++;event:=Value{"id":id,"text":text,"revision":s.revision}
    tokens:=[]int{};for token:=range s.listeners { tokens=append(tokens,token) };sort.Ints(tokens)
    for _,token:=range tokens { if fn,ok:=s.listeners[token];ok { fn(event) } };return event
}

type Environment interface { Store() *Store; Schedule(func(),int) interface{}; Cancel(interface{}); Output(string,interface{}); Write(string,string) }
type Trailing struct { env Environment; delay int; work func(string); handle interface{}; pending *string }
func NewTrailing(env Environment,delay int,work func(string)) *Trailing { return &Trailing{env:env,delay:delay,work:work} }
func(t *Trailing) Push(text string) {
    if t.handle!=nil { t.env.Cancel(t.handle) };t.pending=&text;t.handle=t.env.Schedule(t.Flush,t.delay)
}
func(t *Trailing) Flush() {
    if t.handle!=nil { t.env.Cancel(t.handle) };text:=t.pending;t.handle=nil;t.pending=nil
    if text!=nil { t.work(*text) }
}
func(t *Trailing) Cancel() { if t.handle!=nil {t.env.Cancel(t.handle)};t.handle=nil;t.pending=nil }

type Badge struct{env Environment;id string;buffer *Trailing;token int}
func NewBadge(env Environment,id string,buffer *Trailing)*Badge{token:=env.Store().Subscribe(func(e Value){if e["id"]==id{env.Output("status",e)}});return &Badge{env,id,buffer,token}}
func(b *Badge)detach(){b.env.Store().Stop(b.token)}
type BufferBank struct{entries map[string]*Trailing}
func(b *BufferBank)get(env Environment,id string)*Trailing{if b.entries==nil{b.entries=map[string]*Trailing{}};if b.entries[id]==nil{b.entries[id]=NewTrailing(env,120,func(text string){env.Write(id,text)})};return b.entries[id]}
type Workspace struct{env Environment;current *Badge;generation uint64;buffers map[string]*Trailing}
func NewWorkspace(env Environment)*Workspace{return &Workspace{env:env,buffers:map[string]*Trailing{},}}
func(w *Workspace)retire(){old:=w.current;w.current=nil;if old!=nil&&!false{old.detach()};w.env.Output("document",nil);if old!=nil{old.buffer.Cancel()};if old!=nil&&false{old.detach()}}
func(w *Workspace)Open(id string){w.generation++;request:=w.generation;w.retire();if true&&request!=w.generation{return};buffer:=func()*Trailing{if w.buffers[id]==nil{w.buffers[id]=NewTrailing(w.env,120,func(text string){w.env.Write(id,text)})};return w.buffers[id]}();w.current=NewBadge(w.env,id,buffer);w.env.Output("document",Value{"id":id,"text":w.env.Store().Read(id)})}
func(w *Workspace)Edit(text string){view:=w.current;if view!=nil{view.buffer.Push(text)}}
func(w *Workspace)Close(){w.generation++;w.retire()}
func(w *Workspace)Dispose(){w.Close()}
type Preview struct{task *Trailing}
func NewPreview(env Environment)*Preview{return &Preview{NewTrailing(env,40,func(query string){env.Output("preview",Value{"query":query})})}}
func(p *Preview)Query(text string){p.task.Push(text)}
func(p *Preview)Hide(){p.task.Cancel()}
