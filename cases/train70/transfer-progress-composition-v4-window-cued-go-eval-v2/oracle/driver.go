package main
import("bufio";"encoding/json";"fmt";"os")
var reader=bufio.NewReader(os.Stdin)
var telemetry=map[int]*Telemetry{}
var callbacks=map[int]func(interface{}){}
var sessions=map[int]Client{}
var handles=map[string]*Attempt{}
var files=map[int]*File{}
var serial int
type Env struct{W int}
func number(x interface{})int{return int(x.(float64))}
func send(v interface{}){b,e:=json.Marshal(v);if e!=nil{panic(e)};fmt.Println(string(b))}
func read()map[string]interface{}{line,e:=reader.ReadBytes('\n');if e!=nil{panic(e)};var m map[string]interface{};if e=json.Unmarshal(line,&m);e!=nil{panic(e)};return m}
func(e *Env)Bind(fn func(interface{}))int{serial++;callbacks[serial]=fn;return serial}
func(e *Env)Call(name string,args ...interface{})interface{}{send(map[string]interface{}{"call":name,"args":append([]interface{}{e.W},args...)});for{m:=read();if reply,ok:=m["reply"];ok{return reply};answer(m)}}
func fileObject(x interface{})*File{v:=x.(map[string]interface{});token:=number(v["token"]);if f,ok:=files[token];ok{return f};f:=&File{ID:v["id"].(string),Token:token,Size:number(v["size"]),Feed:v["feed"].(bool)};files[token]=f;return f}
func remember(w int,h *Attempt)interface{}{if h==nil{return nil};handles[fmt.Sprint(w,":",h.Number)]=h;return h.Number}
func dispatch(m map[string]interface{})interface{}{name:=m["method"].(string);a:=m["args"].([]interface{});if name=="invoke"{callbacks[number(a[0])](a[1]);return nil};w:=number(a[0]);switch name{
 case "telemetryStart":telemetry[w]=NewTelemetry(&Env{w},fileObject(a[1]));return nil
 case "telemetryStop":telemetry[w].Stop();return nil
 case "init":sessions[w]=NewSession(&Env{w});return nil
 case "standalone":return remember(w,NewAttempt(&Env{w},fileObject(a[1]),number(a[2]),func()int{return 1},func(interface{}){},func(interface{},int){}))
 case "cancelHandle":handles[fmt.Sprint(w,":",number(a[1]))].Cancel();return nil
 case "select":return remember(w,sessions[w].Select(fileObject(a[1])))
 case "retry":return remember(w,sessions[w].Retry())
 case "hide":sessions[w].Hide();return nil
 case "dispose":sessions[w].Dispose();return nil
 case "snapshot":return sessions[w].Snapshot()
 };panic("unknown method "+name)}
func answer(m map[string]interface{}){send(map[string]interface{}{"result":dispatch(m)})}
func main(){for{line,e:=reader.ReadBytes('\n');if e!=nil{return};var m map[string]interface{};if e=json.Unmarshal(line,&m);e!=nil{panic(e)};answer(m)}}
