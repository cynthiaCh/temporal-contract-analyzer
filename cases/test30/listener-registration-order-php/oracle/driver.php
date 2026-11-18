<?php
require $argv[1].'/src/workflow.php';
function emit($v){echo json_encode($v)."\n";flush();}
class Host {
 private $callbacks=[],$serial=0,$feeds=[],$workspaces=[];
 function call($kind,...$args){emit(['call'=>$kind,'args'=>$args]);while(($line=fgets(STDIN))!==false){$m=json_decode($line,true);if(array_key_exists('reply',$m))return $m['reply'];$this->dispatch($m);}throw new Exception('EOF');}
 function bind($fn){$id=++$this->serial;$this->callbacks[$id]=$fn;return $id;}
 function invoke($id,$value){$fn=$this->callbacks[$id];unset($this->callbacks[$id]);$fn($value);}
 function defer($fn){$this->call('defer',$this->bind(function($v)use($fn){$fn();}));}
 function resolve($kind,$key,$frame,$fn){$id=$this->bind($fn);$r=$this->call($kind,$key,$frame,$id);if(!$r['deferred'])$this->invoke($id,$r['value']);}
 function output($kind,$key,$value){$this->call($kind,$key,$value);}
 function dispatch($m){$a=$m['args'];$result=null;switch($m['method']){
 case 'feed':$this->feeds[$a[0]]=new Channel($this,$a[0],$a[1]);break;
 case 'workspace':$this->workspaces[$a[0]]=new Workspace($this,$a[0]);break;
 case 'select':$this->workspaces[$a[0]]->select($this->feeds[$a[1]],$a[2]);break;
 case 'hide':$this->workspaces[$a[0]]->hide();break;
 case 'start':$this->feeds[$a[0]]->connect($a[1]);break;
 case 'delta':$this->feeds[$a[0]]->update();break;
 case 'listeners':$result=count($this->feeds[$a[0]]->listeners);break;
 case 'invoke':$this->invoke($a[0],$a[1]);break;
 case 'metrics':collect_metrics($this,$a[0],$this->feeds[$a[1]]);break;
 default:throw new Exception($m['method']);
 }emit(['result'=>$result]);}
}
$host=new Host();while(($line=fgets(STDIN))!==false)$host->dispatch(json_decode($line,true));
