package main
type Value map[string]interface{}
type Environment interface{Resolve(string,int,interface{},func(interface{}));Schedule(func(),int)int;Cancel(int);Defer(func());Output(string,int,interface{})}
type Controller struct{value int;present,completed bool}
func NewController(env Environment,key int,config Value)*Controller{return &Controller{}}
func(c *Controller)Call(name string,a []interface{})interface{}{switch name{case "get":switch a[0].(string){case "value":return c.value;case "present":return c.present;case "completed":return c.completed};case "set":switch a[0].(string){case "value":c.value=int(a[1].(float64));case "present":c.present=a[1].(bool);case "completed":c.completed=a[1].(bool)};case "clear":case "dispose":default:panic(name)};return nil}
