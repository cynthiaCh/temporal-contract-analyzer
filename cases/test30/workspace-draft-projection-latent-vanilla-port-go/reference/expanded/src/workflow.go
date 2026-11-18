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

type Badge struct{env Environment;id string;visit uint64;buffer *Trailing;token int}
func NewBadge(env Environment,id string,buffer *Trailing)*Badge{token:=env.Store().Subscribe(func(e Value){if e["id"]==id{env.Output("status",e)}});return &Badge{env:env,id:id,buffer:buffer,token:token}}
func(b *Badge)detach(){b.env.Store().Stop(b.token)}
type BufferBank struct{entries map[string]*Trailing}
func(b *BufferBank)get(env Environment,id string)*Trailing{if b.entries==nil{b.entries=map[string]*Trailing{}};if b.entries[id]==nil{b.entries[id]=NewTrailing(env,120,func(text string){env.Write(id,text)})};return b.entries[id]}
type Editor struct{env Environment;current *Badge;generation uint64;bank BufferBank}
func NewEditor(env Environment)*Editor{return &Editor{env:env,}}
func(w *Editor)retire(){old:=w.current;w.current=nil;if old!=nil&&!false{old.detach()};w.env.Output("document",nil);if old!=nil{old.buffer.Flush()};if old!=nil&&false{old.detach()}}
func(w *Editor)Open(id string,visit uint64){w.generation++;request:=w.generation;w.retire();if true&&request!=w.generation{return};buffer:=w.bank.get(w.env,id);w.current=NewBadge(w.env,id,buffer);w.current.visit=visit;w.env.Output("document",Value{"id":id,"visit":visit,"text":w.env.Store().Read(id)})}
func(w *Editor)Edit(text string){view:=w.current;if view!=nil{view.buffer.Push(text)}}
func(w *Editor)Close(){w.generation++;w.retire()}
func(w *Editor)Dispose(){w.Close()}
type Preview struct{task *Trailing}
func NewPreview(env Environment)*Preview{return &Preview{NewTrailing(env,120,func(query string){env.Output("preview",Value{"query":query})})}}
func(p *Preview)Query(text string){p.task.Push(text)}
func(p *Preview)Hide(){p.task.Cancel()}

type Projection struct{env Environment;selected Value;trail []Value}
func(p *Projection)publish(){p.env.Output("projection",Value{"selected":p.selected,"trail":p.trail})}
func(p *Projection)commit(v Value){p.selected=v;p.trail=append(p.trail,v);p.publish()}
func(p *Projection)clear(){p.selected=nil;p.publish()}
type Workspace struct{editor *Editor;projection *Projection;epoch,visit uint64}
func NewWorkspace(env Environment)*Workspace{return &Workspace{editor:NewEditor(env),projection:&Projection{env:env,trail:[]Value{}}}}
func(w *Workspace)Selection()interface{}{if w.editor.current==nil{return nil};c:=w.editor.current;return Value{"id":c.id,"visit":c.visit}}
func(w *Workspace)Select(id string){w.epoch++;mine:=w.epoch;_ = mine;w.visit++;v:=w.visit;w.editor.Open(id,v);if mine==w.epoch{w.projection.commit(Value{"id":id,"visit":v})}}
func(w *Workspace)Edit(t string){w.editor.Edit(t)}
func(w *Workspace)Close(){w.epoch++;mine:=w.epoch;_ = mine;w.editor.Close();if mine==w.epoch{w.projection.clear()}}
func(w *Workspace)Dispose(){w.Close()}
