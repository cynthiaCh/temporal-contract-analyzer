<?php
class Channel {
 public $key,$listeners=[];private $env,$name,$serial=0;
 function __construct($env,$key,$name){$this->env=$env;$this->key=$key;$this->name=$name;}
 function listen($fn){$token=++$this->serial;$this->listeners[$token]=$fn;return $token;}
 function detach($token){unset($this->listeners[$token]);}
 function emit($kind){$value=$this->name.':'.$kind;foreach(array_keys($this->listeners)as $token)if(isset($this->listeners[$token]))($this->listeners[$token])($value);}
 function connect($mode){if($mode==='deferred')$this->env->defer(function(){$this->emit('bootstrap');});else $this->emit('bootstrap');}
 function update(){$this->emit('update');}
}
class Ticket {public $channel,$active=true,$stop;function __construct($channel){$this->channel=$channel;$this->stop=function(){};}}
class Workspace {
 private $env,$key,$current;
 function __construct($env,$key){$this->env=$env;$this->key=$key;}
 function hide(){$old=$this->current;$this->current=null;if($old){$old->active=false;($old->stop)();}}
 function select($channel,$mode){$this->hide();$visit=new Ticket($channel);$this->current=$visit;
  $deliver=function($input)use($channel,$visit){$this->env->resolve('decode',$channel->key,$input,function($value)use($channel,$visit){if($visit->active){$this->env->output("publish",$this->key,$value);}});};
  $channel->connect($mode);$token=$channel->listen($deliver);$visit->stop=function()use($channel,$token){$channel->detach($token);};
 }
}
function collect_metrics($env,$key,$channel){$events=[];$receive=function($value)use(&$events){$events[]=$value;};$channel->connect("synchronous");$token=$channel->listen($receive);
 $env->defer(function()use($env,$key,$channel,$token,&$events){$channel->update();$channel->detach($token);$env->output('metrics',$key,$events);});
}
