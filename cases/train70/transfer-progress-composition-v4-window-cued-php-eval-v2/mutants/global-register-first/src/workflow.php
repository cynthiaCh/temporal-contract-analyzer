<?php
// Claim sessions use object identities; source and decode observers are Closures.
class PublicationWindow {public $arrived=0,$published=0;function arrive(){return ++$this->arrived;}function publish($order){if($order<=$this->published)return false;$this->published=$order;return true;}}
class Visit {public $id,$file,$handle=null,$window;function __construct($id,$file){$this->id=$id;$this->file=$file;$this->window=new PublicationWindow();}}
class Attempt {
 public $env,$file,$number,$aborted=false,$stop;
 function __construct($env,$file,$number,$active=null,$audit=null,$view=null){
  $active=$active??function(){return 1;};$audit=$audit??function($f){};$view=$view??function($f,$o){};
  $this->env=$env;$this->file=$file;$this->number=$number;$this->stop=function(){};
  $env->call('transport',$file->token,$number);
  if($file->feed){$callback=$env->bind(function($packet)use($env,$file,$active,$audit,$view){if($this->aborted)return;$order=$active();if($order===null)return;
    $deliver=function($frame)use($active,$audit,$view,$order){ $audit($frame);$view($frame,$order);};
    $value=$env->call('decode',$file->token,$packet,$env->bind($deliver));if(!$value->deferred)$deliver($value->frame);});
   $subscription=$env->call('listen',$file->token,$callback);$env->call('start',$file->token);
   $this->stop=function()use($env,$file,$subscription){$env->call('unlisten',$file->token,$subscription);};if($this->aborted)($this->stop)();}
 }
 function cancel(){if($this->aborted)return;$this->aborted=true;($this->stop)();$this->env->call('cancel',$this->file->token,$this->number);}
}
class VisitRegistry {public $visit=null,$serial=0,$disposed=false;}
class Session {
 public $env,$registry,$attempts=0,$tasks=[];
 function __construct($env){$this->env=$env;$this->registry=new VisitRegistry();}
 function current($v){return $this->registry->visit===$v;}
 function enqueue($v,$kind){$n=++$this->attempts;$entry=['fileId'=>$v->file->id,'attemptId'=>$n,'visitId'=>$v->id,'kind'=>$kind]; $this->env->call('record',$entry);
  $window=$v->window;$h=new Attempt($this->env,$v->file,$n,function()use($v,$window){return $this->current($v)?$window->arrive():null;},function($frame)use($v,$n){$this->env->call('recordProgress',['fileId'=>$v->file->id,'attemptId'=>$n,'frame'=>$frame]);},function($frame,$order)use($v,$n,$window){if($this->current($v)&&$window->publish($order))$this->env->call('showProgress',['fileId'=>$v->file->id,'attemptId'=>$n,'frame'=>$frame]);});$this->tasks[]=$h;return $h;}
 function notice($v,$h){ $this->env->call('showQueued',['fileId'=>$v->file->id,'attemptId'=>$h->number,'visitId'=>$v->id,'status'=>'queued']);}
 function release($v){$h=$v->handle;$v->handle=null;if($h)$h->cancel();}
 function select($file){if($this->registry->disposed)return null;$request=++$this->registry->serial;$old=$this->registry->visit;$this->registry->visit=null;if($old)$this->release($old);if($this->registry->disposed||$this->registry->serial!==$request)return null;$v=new Visit($request,$file);$this->registry->visit=$v;$h=$this->enqueue($v,'select');if($this->current($v)){$v->handle=$h;$this->notice($v,$h);}else $h->cancel();return $h;}
 function retry(){$v=$this->registry->visit;if(!$v||!$v->handle||$this->registry->disposed)return null;$v->handle->cancel(); $accepted=$v;$h=$this->enqueue($accepted,'retry');if($this->current($accepted))$accepted->handle=$h;else $h->cancel();if($this->current($accepted))$this->notice($accepted,$h);return $h;}
 function hide(){$this->registry->serial++;$old=$this->registry->visit;$this->registry->visit=null;if($old)$this->release($old);}
 function dispose(){if($this->registry->disposed)return;$this->registry->disposed=true;$this->hide();foreach($this->tasks as $h)$h->cancel();}
 function snapshot(){$v=$this->registry->visit;return ['visitId'=>$v?$v->id:null,'fileId'=>$v?$v->file->id:null,'attemptId'=>$v&&$v->handle?$v->handle->number:null,'disposed'=>$this->registry->disposed,'attempts'=>$this->attempts];}
}

class Telemetry {public $stop;function __construct($env,$file){$callback=$env->bind(function($packet)use($env,$file){$deliver=function($frame)use($env){$env->call('recordDelta',$frame);};$value=$env->call('decode',$file->token,$packet,$env->bind($deliver));if(!$value->deferred)$deliver($value->frame);});$subscription=$env->call('listen',$file->token,$callback);$env->call('start',$file->token); $this->stop=function()use($env,$file,$subscription){$env->call('unlisten',$file->token,$subscription);};}}
