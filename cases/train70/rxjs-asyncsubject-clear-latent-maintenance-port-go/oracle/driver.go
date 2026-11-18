package main
import("encoding/json";"os")
type Host struct{input *json.Decoder;output *json.Encoder;callbacks map[int]func(interface{});controllers map[int]*Controller;serial int}
func(d *Host)call(kind string,args ...interface{})interface{}{if err:=d.output.Encode(Value{"call":kind,"args":args});err!=nil{panic(err)};for{m:=Value{};if err:=d.input.Decode(&m);err!=nil{panic(err)};if v,ok:=m["reply"];ok{return v};d.dispatch(m)}}
func(d *Host)bind(fn func(interface{}))int{d.serial++;d.callbacks[d.serial]=fn;return d.serial}
func(d *Host)invoke(id int,v interface{}){fn:=d.callbacks[id];delete(d.callbacks,id);fn(v)}
func(d *Host)Defer(fn func()){d.call("defer",d.bind(func(_ interface{}){fn()}))}
func(d *Host)Resolve(kind string,key int,frame interface{},fn func(interface{})){id:=d.bind(fn);r:=d.call(kind,key,frame,id).(map[string]interface{});if !r["deferred"].(bool){d.invoke(id,r["value"])}}
func(d *Host)Schedule(fn func(),delay int)int{return integer(d.call("schedule",d.bind(func(_ interface{}){fn()}),delay))}
func(d *Host)Cancel(handle int){d.call("cancel",handle)}
func(d *Host)Output(kind string,key int,value interface{}){d.call(kind,key,value)}
func integer(v interface{})int{return int(v.(float64))}
func(d *Host)dispatch(m Value){a:=m["args"].([]interface{});var result interface{};switch m["method"].(string){
case "create":d.controllers[integer(a[0])]=NewController(d,integer(a[0]),Value(a[1].(map[string]interface{})))
case "call":result=d.controllers[integer(a[0])].Call(a[1].(string),a[2].([]interface{}))
case "invoke":d.invoke(integer(a[0]),a[1])
default:panic(m["method"])
};if err:=d.output.Encode(Value{"result":result});err!=nil{panic(err)}}
func main(){d:=&Host{input:json.NewDecoder(os.Stdin),output:json.NewEncoder(os.Stdout),callbacks:map[int]func(interface{}){},controllers:map[int]*Controller{}};for{m:=Value{};if err:=d.input.Decode(&m);err!=nil{return};d.dispatch(m)}}
