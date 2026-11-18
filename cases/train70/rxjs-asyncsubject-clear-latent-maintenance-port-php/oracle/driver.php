<?php
require $argv[1].'/src/workflow.php';
function emit($v){echo json_encode($v)."\n";flush();}
class Host {
 private $callbacks=[],$serial=0,$controllers=[];
 function call($kind,...$args){emit(['call'=>$kind,'args'=>$args]);while(($line=fgets(STDIN))!==false){$m=json_decode($line,true);if(array_key_exists('reply',$m))return $m['reply'];$this->dispatch($m);}throw new Exception('EOF');}
 function bind($fn){$id=++$this->serial;$this->callbacks[$id]=$fn;return $id;}
 function invoke($id,$value){$fn=$this->callbacks[$id];unset($this->callbacks[$id]);$fn($value);}
 function defer($fn){$this->call('defer',$this->bind(function($v)use($fn){$fn();}));}
 function resolve($kind,$key,$frame,$fn){$id=$this->bind($fn);$r=$this->call($kind,$key,$frame,$id);if(!$r['deferred'])$this->invoke($id,$r['value']);}
 function schedule($fn,$delay){return $this->call('schedule',$this->bind(function($v)use($fn){$fn();}),$delay);}
 function cancel($handle){$this->call('cancel',$handle);}
 function output($kind,$key,$value){$this->call($kind,$key,$value);}
 function dispatch($m){$a=$m['args'];$result=null;switch($m['method']){
 case 'create':$this->controllers[$a[0]]=new Controller($this,$a[0],$a[1]);break;
 case 'call':$result=$this->controllers[$a[0]]->{$a[1]}(...$a[2]);break;
 case 'invoke':$this->invoke($a[0],$a[1]);break;
 default:throw new Exception($m['method']);
 }emit(['result'=>$result]);}
}
$host=new Host();while(($line=fgets(STDIN))!==false)$host->dispatch(json_decode($line,true));
