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
type Receipt struct { ID string `json:"id"`; Text string `json:"text"` }
type Archive struct { receipts []Receipt;listeners map[int]func(Receipt);serial int }
func(a *Archive) Subscribe(fn func(Receipt))int{if a.listeners==nil{a.listeners=map[int]func(Receipt){}};a.serial++;a.listeners[a.serial]=fn;return a.serial}
func(a *Archive) Stop(token int){delete(a.listeners,token)}
func(a *Archive) Capture(value Value) Receipt {
    receipt:=Receipt{value["id"].(string),value["text"].(string)};a.receipts=append(a.receipts,receipt);tokens:=[]int{};for token:=range a.listeners{tokens=append(tokens,token)};sort.Ints(tokens);for _,token:=range tokens{if fn,ok:=a.listeners[token];ok{fn(receipt)}};return receipt
}
func(a *Archive) List() []Receipt { result:=[]Receipt{};return append(result,a.receipts...) }
type Environment interface {
    Store() *Store
    Schedule(func(),int) interface{}
    Cancel(interface{})
    Output(string,interface{})
    Write(string,string)
    Capture(Value) interface{}
}
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
type Visit struct { id,text string; token int; task *Trailing }
type Confirmation struct{current func()*Visit;emit func(interface{});owner *Visit}
func BindConfirmation(current func()*Visit,emit func(interface{}))*Confirmation{return &Confirmation{current,emit,current()}}
func(c *Confirmation) Active()bool{return c.owner!=nil&&c.owner==c.current()}
func(c *Confirmation) Show(receipt interface{}){if c.Active(){c.emit(receipt)}}
type Workspace struct { env Environment; current *Visit; navigation uint64 }
func NewWorkspace(env Environment) *Workspace { return &Workspace{env:env} }
func(w *Workspace) retire() {
    leaving:=w.current;w.current=nil
    if leaving!=nil { w.env.Store().Stop(leaving.token) };w.env.Output("document",nil)
    if leaving!=nil {leaving.task.Flush()}
}
func(w *Workspace) Open(id string) {
    w.env.Output("notice",nil);w.navigation++;request:=w.navigation;w.retire()
    if request!=w.navigation {return}
    token:=w.env.Store().Subscribe(func(event Value){if event["id"]==id {w.env.Output("status",event)}})
    task:=NewTrailing(w.env,120,func(text string){w.env.Write(id,text)})
    w.current=&Visit{id,w.env.Store().Read(id),token,task};w.env.Output("document",Value{"id":id,"text":w.current.text})
}
func(w *Workspace) Edit(text string) { if w.current==nil {return};w.current.text=text;w.current.task.Push(text) }
func(w *Workspace) Close() { w.env.Output("notice",nil);w.navigation++;w.retire() }
func(w *Workspace) Submit() interface{} {
    confirmation:=BindConfirmation(func()*Visit{return w.current},func(receipt interface{}){w.env.Output("notice",receipt)})
    visit:=w.current;if visit==nil {return nil};snapshot:=Value{"id":visit.id,"text":visit.text}
    
    
    
    
    receipt:=w.env.Capture(snapshot)
    
    confirmation.Show(receipt)
    return receipt
}
func(w *Workspace) Dispose() { w.Close() }
type Preview struct { task *Trailing }
func NewPreview(env Environment) *Preview {
    return &Preview{NewTrailing(env,40,func(query string){env.Output("preview",Value{"query":query})})}
}
func(p *Preview) Query(text string) { p.task.Push(text) }
func(p *Preview) Hide() { p.task.Cancel() }
