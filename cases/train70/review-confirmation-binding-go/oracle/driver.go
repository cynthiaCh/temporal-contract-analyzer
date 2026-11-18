package main
import("encoding/json";"os")
type Driver struct {
    input *json.Decoder; output *json.Encoder
    store *Store;archive Archive;workspace *Workspace;preview *Preview
    callbacks map[int]func();serial int
}
func(d *Driver) call(kind string,args ...interface{}) interface{} {
    if err:=d.output.Encode(Value{"call":kind,"args":args});err!=nil{panic(err)}
    for {message:=Value{};if err:=d.input.Decode(&message);err!=nil{panic(err)}
        if value,ok:=message["reply"];ok{return value};d.dispatch(message)
    }
}
func(d *Driver) Store() *Store{return d.store}
func(d *Driver) Schedule(fn func(),delay int) interface{} {d.serial++;d.callbacks[d.serial]=fn;return d.call("schedule",d.serial,delay)}
func(d *Driver) Cancel(handle interface{}){d.call("cancel",handle)}
func(d *Driver) Output(kind string,value interface{}){d.call(kind,value)}
func(d *Driver) Write(id,text string){d.call("write",id,text)}
func(d *Driver) Capture(value Value) interface{}{return d.call("capture",value)}
func(d *Driver) dispatch(message Value){
    method:=message["method"].(string);a:=message["args"].([]interface{});var result interface{}
    switch method {
    case "storeInit":d.store=NewStore(Value(a[0].(map[string]interface{})))
    case "storeRead":result=d.store.Read(a[0].(string))
    case "storeWrite":result=d.store.Write(a[0].(string),a[1].(string))
    case "storeSubscribe":result=d.store.Subscribe(func(event Value){d.call("subscriber",a[0],event)})
    case "storeUnsubscribe":d.store.Stop(int(a[0].(float64)))
    case "archiveCapture":result=d.archive.Capture(Value(a[0].(map[string]interface{})))
    case "archiveSubscribe":result=d.archive.Subscribe(func(event Receipt){d.call("subscriber",a[0],event)})
    case "archiveUnsubscribe":d.archive.Stop(int(a[0].(float64)))
    case "archiveList":result=d.archive.List()
    case "init":d.workspace=NewWorkspace(d)
    case "previewInit":d.preview=NewPreview(d)
    case "previewQuery":d.preview.Query(a[0].(string))
    case "previewHide":d.preview.Hide()
    case "invoke":id:=int(a[0].(float64));fn:=d.callbacks[id];delete(d.callbacks,id);fn()
    case "open":d.workspace.Open(a[0].(string))
    case "edit":d.workspace.Edit(a[0].(string))
    case "close":d.workspace.Close()
    case "submit":result=d.workspace.Submit()
    case "dispose":d.workspace.Dispose()
    default:panic(method)
    };if err:=d.output.Encode(Value{"result":result});err!=nil{panic(err)}
}
func main(){d:=&Driver{input:json.NewDecoder(os.Stdin),output:json.NewEncoder(os.Stdout),callbacks:map[int]func(){}}
    for{message:=Value{};if err:=d.input.Decode(&message);err!=nil{return};d.dispatch(message)}
}
