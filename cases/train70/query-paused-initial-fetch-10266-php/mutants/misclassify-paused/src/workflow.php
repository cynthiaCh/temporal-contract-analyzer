<?php
class FetchAttempt {
 public $number,$previous,$options,$settled=false,$consumed=false,$retryCancelled=false,$failures=0,$queued=false;
 function __construct($number,$state,$options){$this->number=$number;$this->previous=$state;$this->options=$options;}
}
class CachedQuery {
 public $key,$state,$observers=[],$attempt=null,$consumed=false;
 function __construct($key,$data){$this->key=$key;$this->state=['status'=>$data!==null?'success':'pending','fetchStatus'=>'idle','data'=>$data];}
}
class Session {
 private $env,$cache=[],$handles=[],$online,$focused,$serial=0,$fetchSerial=0;
 function __construct($env,$initial){$this->env=$env;$this->online=$initial['online']??true;$this->focused=$initial['focused']??true;}
 function eligible($a){return $this->focused&&(($a->options['networkMode']??'online')==='always'||$this->online);}
 function active($q,$a){return $q->attempt===$a&&!$a->settled;}
 function cancel($q,$a){if($a->settled)return;$a->settled=true;$q->state=$a->previous;$q->state['fetchStatus']='idle';$this->env->call('abort',$q->key,$a->number);}
 function invoke($q,$a){$a->queued=false;if(!$this->active($q,$a))return;$q->state['fetchStatus']='fetching';$q->consumed=false;
  $getter=$this->env->bind(function($_)use($q){$q->consumed=true;return null;});
  $done=$this->env->bind(function($value)use($q,$a){if(!$this->active($q,$a))return;if($value['ok']){$a->settled=true;$q->state=array_merge($q->state,['data'=>$value['value'],'status'=>'success','fetchStatus'=>'idle']);}
   elseif(!$a->retryCancelled&&$a->failures<($a->options['retry']??0)){$a->failures++;$retry=$this->env->bind(function($_)use($q,$a){if(!$this->active($q,$a))return;if($a->retryCancelled){$a->settled=true;$q->state['status']='error';$q->state['fetchStatus']='idle';return;}if($this->eligible($a))$this->invoke($q,$a);else $q->state['fetchStatus']='paused';});$this->env->call('schedule',$retry,$a->options['retryDelay']??10);}
   else{$a->settled=true;$q->state['status']='error';$q->state['fetchStatus']='idle';}return null;});$this->env->call('request',$q->key,$a->number,$getter,$done);
 }
 function resume($q){$a=$q->attempt;if($a&&$this->active($q,$a)&&$q->state['fetchStatus']==='paused'&&$this->eligible($a)&&!$a->queued){$a->queued=true;$token=$this->env->bind(function($_)use($q,$a){$a->queued=false;if(!$this->active($q,$a))return;if($a->failures&&$a->retryCancelled){$a->settled=true;$q->state['status']='error';$q->state['fetchStatus']='idle';return;}$this->invoke($q,$a);});$this->env->call('defer',$token);}}
 function subscribe($key,$options){if(!isset($this->cache[$key]))$this->cache[$key]=new CachedQuery($key,$options['initialData']??null);$q=$this->cache[$key];$handle=++$this->serial;$this->handles[$handle]=$q;$q->observers[$handle]=true;if($q->attempt&&!$q->attempt->settled){$q->attempt->retryCancelled=false;$this->resume($q);}else{$a=new FetchAttempt(++$this->fetchSerial,$q->state,$options);$q->attempt=$a;$this->env->call('newAttempt',$key,$a->number);if(($options['networkMode']??'online')!=='online'||$this->online)$this->invoke($q,$a);else $q->state['fetchStatus']='paused';}return $handle;}
 function unsubscribe($handle){$q=$this->handles[$handle]??null;if(!$q)return;unset($this->handles[$handle],$q->observers[$handle]);if(count($q->observers)===0){$a=$q->attempt;if($a&&!$a->settled){if($q->consumed||$q->state['fetchStatus']==='paused')$this->cancel($q,$a);else $a->retryCancelled=true;}}}
 function handle($name,$args){switch($name){case 'subscribe':return $this->subscribe(...$args);case 'unsubscribe':$this->unsubscribe($args[0]);return null;case 'snapshot':return $this->cache[$args[0]]->state;case 'dispose':foreach(array_keys($this->handles)as $h)$this->unsubscribe($h);return null;case 'online':$this->online=$args[0];break;case 'focus':$this->focused=$args[0];break;default:throw new Exception($name);}foreach($this->cache as $q)$this->resume($q);return null;}
}
